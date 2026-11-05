"""社区：帖子、评论、投票、个人页、贡献榜。

「评价」是挂在零件上的帖子（kind=review），所以这里一套接口同时服务
社区信息流与零件详情页的评价区。
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func
from sqlmodel import select

from ...content_safety import check_user_text_chunks
from ...core.config import settings
from ...crud import (apply_vote, comments_out, posts_out, touch_comment_count,
                     user_out)
from ...models import Comment, Part, Post, Rating, User, utcnow
from ...schemas import (CommentIn, CommentOut, PostIn, PostListOut, PostOut,
                        UserOut, VoteIn, VoteOut)
from ..deps import CurrentUser, Db, MaybeUser, rate_limit
from .notifications import create_notification

router = APIRouter(tags=["community"])

KINDS = ("discussion", "review", "build")


@router.get("/posts", response_model=PostListOut)
def list_posts(
    db: Db,
    user: MaybeUser,
    kind: str | None = None,
    part_id: str | None = None,
    author: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    sort: Literal["new", "top", "hot"] = "new",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Post).where(Post.hidden == False)  # noqa: E712
    if kind:
        stmt = stmt.where(Post.kind == kind)
    if part_id:
        stmt = stmt.where(Post.part_id == part_id)
    if tag:
        stmt = stmt.where(Post.tags.contains(tag))
    if q:
        stmt = stmt.where(Post.title.contains(q) | Post.body.contains(q))
    if author:
        u = db.exec(select(User).where(User.handle == author.lower())).first()
        if u is None:
            return PostListOut(total=0, limit=limit, offset=offset, items=[])
        stmt = stmt.where(Post.author_id == u.id)

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()

    if sort == "top":
        stmt = stmt.order_by(Post.pinned.desc(), Post.score.desc(), Post.created_at.desc())
    elif sort == "hot":
        # 简化的热度：互动量优先，同分看新。
        # 真要做时间衰减排序，得上权重表；这一轮先用这个够用的口径。
        hot = (Post.comment_count * 2 + Post.score)
        stmt = stmt.order_by(Post.pinned.desc(), hot.desc(), Post.created_at.desc())
    else:
        stmt = stmt.order_by(Post.pinned.desc(), Post.created_at.desc())

    rows = db.exec(stmt.offset(offset).limit(limit)).all()
    return PostListOut(total=int(total), limit=limit, offset=offset,
                       items=posts_out(db, list(rows), user.id if user else None))


@router.post("/posts", response_model=PostOut, status_code=201)
def create_post(payload: PostIn, request: Request, db: Db, user: CurrentUser):
    rate_limit(request, "post", settings.rate_max_posts, user.id)

    if payload.kind == "review":
        if not payload.part_id:
            raise HTTPException(422, "评价必须指定零件")
        if payload.rating is None:
            raise HTTPException(422, "评价必须给 1–5 分")
    if payload.kind == "build" and payload.total_price_cny:
        # 只给一个数字的整机报价没有意义：必须说明覆盖范围
        if not (payload.price_scope or "").strip():
            raise HTTPException(
                422, "整机报价必须填「覆盖范围」：这个价格包含哪些件、哪些另计")
    if payload.part_id and db.get(Part, payload.part_id) is None:
        raise HTTPException(404, "零件不存在")

    # 帖子正文同样过内容安全；长文分段检查，不能只看开头。
    safety = check_user_text_chunks(db, user.id, payload.title + "\n" + payload.body)
    if not safety.passed:
        raise HTTPException(422, "内容可能包含违规信息，请修改后再试")

    p = Post(kind=payload.kind, title=payload.title.strip(), body=payload.body,
             author_id=user.id, part_id=payload.part_id,
             tags=",".join(t.strip() for t in payload.tags.split(",") if t.strip())[:80],
             rating=payload.rating, use_case=payload.use_case,
             own_hardware=payload.own_hardware,
             total_price_cny=payload.total_price_cny,
             price_scope=payload.price_scope,
             # 「价格已核实」是站务信任标记，普通用户不能自填
             price_verified=bool(payload.price_verified and user.is_staff))
    db.add(p)

    # 评价帖是「评分 + 长评」的另一条入口；它必须和 /ratings 是同一份事实，
    # 否则页面会显示「有评价、0 人打分」。同一人同一件仍然只保留一票。
    #
    # 可见性：Rating 没有 hidden 列（本轮不改 models.py），所以站务隐藏评价帖
    # 时不能在这里给 Rating 打隐藏标记；读取评分聚合时由
    # crud.shadowed_review_keys() 按「同一人同一件存在 hidden review」派生，
    # 评价恢复后该票自动回到公开聚合。
    if payload.kind == "review" and payload.rating is not None and payload.part_id:
        row = db.exec(select(Rating).where(
            Rating.part_id == payload.part_id,
            Rating.user_id == user.id)).first()
        if row is None:
            db.add(Rating(part_id=payload.part_id, user_id=user.id,
                          score=payload.rating,
                          own_hardware=payload.own_hardware,
                          note=(payload.body or "")[:200]))
        else:
            row.score = payload.rating
            row.own_hardware = payload.own_hardware
            row.note = (payload.body or "")[:200]
            row.updated_at = utcnow()
            db.add(row)

    db.commit()
    db.refresh(p)
    return posts_out(db, [p], user.id)[0]


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Db, user: MaybeUser):
    p = db.get(Post, post_id)
    if p is None or (p.hidden and not (user and user.is_staff)):
        raise HTTPException(404, "帖子不存在")
    p.view_count += 1
    db.add(p)
    db.commit()
    db.refresh(p)
    return posts_out(db, [p], user.id if user else None)[0]


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Db, user: MaybeUser):
    post = db.get(Post, post_id)
    if post is None or (post.hidden and not (user and user.is_staff)):
        raise HTTPException(404, "帖子不存在")
    return comments_out(db, post_id, user.id if user else None)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(post_id: int, payload: CommentIn, request: Request, db: Db,
                   user: CurrentUser):
    rate_limit(request, "comment", settings.rate_max_comments, user.id)
    post = db.get(Post, post_id)
    if post is None or post.hidden:
        raise HTTPException(404, "帖子不存在")
    if payload.parent_id is not None:
        parent = db.get(Comment, payload.parent_id)
        if parent is None or parent.post_id != post_id:
            raise HTTPException(422, "父评论不属于这个帖子")
        if parent.hidden:
            raise HTTPException(422, "父评论已被隐藏")
        if parent.parent_id is not None:
            raise HTTPException(422, "只支持两级回复")

    # 内容安全：未配置微信时放行；配置且判定违规时直接拒收（社区评论没有
    # pending 态，宁可不发也不把未审内容放进公开信息流）。
    safety = check_user_text_chunks(db, user.id, payload.body)
    if not safety.passed:
        raise HTTPException(422, "内容可能包含违规信息，请修改后再试")

    c = Comment(post_id=post_id, parent_id=payload.parent_id,
                author_id=user.id, body=payload.body.strip())
    db.add(c)
    db.flush()                       # 拿 id 拼通知链接，主事务稍后一起提交

    # 通知：回复通知父评论作者；直接评论帖子通知楼主。自己回自己不通知。
    target_id = parent.author_id if payload.parent_id is not None else post.author_id
    snippet = c.body if len(c.body) <= 80 else c.body[:80] + "…"
    create_notification(
        db, target_id, type="reply",
        subject="有人回复了你的帖子" if payload.parent_id is None else "有人回复了你的评论",
        body=snippet, link=f"/console/post/{post_id}#c{c.id}",
        actor_id=user.id)

    touch_comment_count(db, post_id)
    db.refresh(c)
    return CommentOut(id=c.id or 0, post_id=c.post_id, parent_id=c.parent_id,
                      body=c.body, score=c.score, created_at=c.created_at,
                      author=user_out(db, user), my_vote=0, replies=[])


@router.post("/votes", response_model=VoteOut)
def vote(payload: VoteIn, db: Db, user: CurrentUser):
    try:
        score, mine = apply_vote(db, user, payload.target_kind, payload.target_id,
                                 payload.value)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    return VoteOut(score=score, my_vote=mine)


@router.get("/users/{handle}", response_model=UserOut)
def get_user(handle: str, db: Db):
    u = db.exec(select(User).where(User.handle == handle.lower())).first()
    if u is None:
        raise HTTPException(404, "用户不存在")
    return user_out(db, u)


@router.get("/leaderboard", response_model=list[UserOut])
def leaderboard(db: Db, limit: Annotated[int, Query(ge=1, le=50)] = 10):
    """贡献榜：按声望（收到的赞之和）排序。"""
    rows = db.exec(select(User).order_by(User.reputation.desc(),
                                         User.created_at).limit(limit)).all()
    return [user_out(db, u) for u in rows]

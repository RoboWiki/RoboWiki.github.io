"""社区：帖子、评论、投票、个人页、贡献榜。

「评价」是挂在零件上的帖子（kind=review），所以这里一套接口同时服务
社区信息流与零件详情页的评价区。
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func
from sqlmodel import Session, select

from ...content_safety import check_user_text_chunks
from ...core.config import settings
from ...crud import (apply_vote, comments_out, posts_out, touch_comment_count,
                     user_out)
from ...models import Comment, Part, Post, Rating, User, utcnow
from ...schemas import (AcceptIn, CommentIn, CommentOut, PostIn, PostListOut,
                        PostOut, PostPatchIn, UserOut, VoteIn, VoteOut)
from ..deps import CurrentUser, Db, MaybeUser, rate_limit, require_verified_email
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
    #: 问答闭环：true 只看已解决，false 只看未解决；不传不过滤。
    #: 对 discussion / review / build 一律按 accepted_comment_id 判断，
    #: 不因 kind 报错 —— 前端可能把同一个筛选器带到所有 tab。
    solved: bool | None = None,
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
    if solved is not None:
        stmt = stmt.where(Post.accepted_comment_id.is_not(None) if solved
                          else Post.accepted_comment_id.is_(None))
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
    require_verified_email(user)
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


def _editable_post(db: Session, post_id: int, user: User) -> Post:
    """取出可编辑的帖子：不存在 / 已隐藏（非站务）一律 404，越权 403。

    隐藏帖对普通作者也按 404 处理：既然公开读不到，就不该通过「403/404
    的差异」暴露它仍然存在。
    """
    p = db.get(Post, post_id)
    if p is None or (p.hidden and not user.is_staff):
        raise HTTPException(404, "帖子不存在")
    if p.author_id != user.id and not user.is_staff:
        raise HTTPException(403, "只能操作自己的帖子")
    return p


@router.patch("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, payload: PostPatchIn, request: Request, db: Db,
                user: CurrentUser):
    """编辑帖子。kind / part_id 不可改；校验按「补丁合并后」的值做。

    只改 kind 相关字段会绕过创建时的必填约束（把评价的分清空、把整机报价
    的覆盖范围删掉），所以必须拿合并后的完整状态再校验一次。
    """
    rate_limit(request, "post-update", settings.rate_max_posts, user.id)
    p = _editable_post(db, post_id, user)
    data = payload.model_dump(exclude_unset=True)

    title = p.title
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            raise HTTPException(422, "标题不能为空")
    body = p.body
    if "body" in data:
        if data["body"] is None:
            raise HTTPException(422, "正文不能为空")
        body = data["body"]
    rating = data.get("rating", p.rating)
    total_price = data.get("total_price_cny", p.total_price_cny)
    price_scope = data.get("price_scope", p.price_scope)

    if p.kind == "review":
        if not p.part_id:
            raise HTTPException(422, "评价必须指定零件")
        if rating is None:
            raise HTTPException(422, "评价必须给 1–5 分")
    if p.kind == "build" and total_price:
        # 与创建同口径：只给一个数字的整机报价没有意义
        if not (price_scope or "").strip():
            raise HTTPException(
                422, "整机报价必须填「覆盖范围」：这个价格包含哪些件、哪些另计")

    if "title" in data or "body" in data:
        safety = check_user_text_chunks(db, user.id, f"{title}\n{body}")
        if not safety.passed:
            raise HTTPException(422, "内容可能包含违规信息，请修改后再试")

    p.title = title
    p.body = body
    if "tags" in data:
        p.tags = ",".join(t.strip() for t in (data["tags"] or "").split(",")
                          if t.strip())[:80]
    if "rating" in data:
        p.rating = data["rating"]
    if "use_case" in data:
        p.use_case = data["use_case"]
    if "own_hardware" in data:
        p.own_hardware = bool(data["own_hardware"])
    if "total_price_cny" in data:
        p.total_price_cny = data["total_price_cny"]
    if "price_scope" in data:
        p.price_scope = data["price_scope"]
    if "price_verified" in data:
        # 「价格已核实」仍是站务信任标记，普通作者不能自封
        p.price_verified = bool(data["price_verified"] and user.is_staff)
    p.updated_at = utcnow()
    db.add(p)

    # 评价帖是「评分 + 长评」的入口之一，改动必须同步到 Rating，
    # 否则零件页的均分与帖子里的星级会对不上。
    if p.kind == "review" and p.part_id and p.rating is not None \
            and {"rating", "body", "own_hardware"} & data.keys():
        row = db.exec(select(Rating).where(
            Rating.part_id == p.part_id, Rating.user_id == p.author_id)).first()
        if row is None:
            db.add(Rating(part_id=p.part_id, user_id=p.author_id,
                          score=p.rating, own_hardware=p.own_hardware,
                          note=(p.body or "")[:200]))
        else:
            row.score = p.rating
            row.own_hardware = p.own_hardware
            row.note = (p.body or "")[:200]
            row.updated_at = utcnow()
            db.add(row)

    db.commit()
    db.refresh(p)
    return posts_out(db, [p], user.id)[0]


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Db, user: CurrentUser):
    """软删除：只置 hidden，保留行与评论线程，站务仍可在后台恢复/查看。"""
    p = _editable_post(db, post_id, user)
    if not p.hidden:
        p.hidden = True
        p.updated_at = utcnow()
        db.add(p)
        db.commit()
    return None


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Db, user: MaybeUser):
    post = db.get(Post, post_id)
    if post is None or (post.hidden and not (user and user.is_staff)):
        raise HTTPException(404, "帖子不存在")
    return comments_out(db, post_id, user.id if user else None)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(post_id: int, payload: CommentIn, request: Request, db: Db,
                   user: CurrentUser):
    require_verified_email(user)
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
        body=snippet, link=f"/post.html?id={post_id}#c{c.id}",
        actor_id=user.id)

    touch_comment_count(db, post_id)
    db.refresh(c)
    return CommentOut(id=c.id or 0, post_id=c.post_id, parent_id=c.parent_id,
                      body=c.body, score=c.score, created_at=c.created_at,
                      author=user_out(db, user), my_vote=0, replies=[])


@router.post("/posts/{post_id}/accept", response_model=PostOut)
def accept_comment(post_id: int, payload: AcceptIn, db: Db, user: CurrentUser):
    require_verified_email(user)
    """采纳本楼的一条回答，给回答者发通知。

    采纳状态只存在帖子上的 `accepted_comment_id`：不复制到评论行，
    换采纳 / 取消采纳都只改一个字段，读取侧也不会出现「两条都被采纳」。
    """
    p = db.get(Post, post_id)
    if p is None or (p.hidden and not user.is_staff):
        raise HTTPException(404, "帖子不存在")
    if p.author_id != user.id and not user.is_staff:
        raise HTTPException(403, "只有作者或站务可以采纳答案")

    c = db.get(Comment, payload.comment_id)
    if c is None:
        raise HTTPException(404, "评论不存在")
    if c.post_id != post_id:
        raise HTTPException(422, "评论不属于这个帖子")
    if c.hidden:
        raise HTTPException(422, "不能采纳已隐藏的评论")

    # 换采纳时先把旧答主的分扣回去，再把分记给新答主；自问自答不加分。
    if p.accepted_comment_id and p.accepted_comment_id != c.id:
        old = db.get(Comment, p.accepted_comment_id)
        if old:
            old_author = db.get(User, old.author_id)
            if old_author and old_author.id != user.id:
                old_author.reputation = max(0, int(old_author.reputation or 0) - 3)
                db.add(old_author)
    p.accepted_comment_id = c.id
    db.add(p)
    answer_author = db.get(User, c.author_id)
    if answer_author and answer_author.id != user.id:
        answer_author.reputation = int(answer_author.reputation or 0) + 3
        db.add(answer_author)
    snippet = c.body if len(c.body) <= 80 else c.body[:80] + "…"
    create_notification(db, c.author_id, type="accepted",
                        subject="你的回答被采纳了", body=snippet,
                        link=f"/post.html?id={post_id}", actor_id=user.id)
    db.commit()
    db.refresh(p)
    return posts_out(db, [p], user.id)[0]


@router.delete("/posts/{post_id}/accept", status_code=204)
def unaccept_comment(post_id: int, db: Db, user: CurrentUser):
    """取消采纳。重复调用也返回 204，语义是「确保没有采纳」。"""
    p = _editable_post(db, post_id, user)
    if p.accepted_comment_id is not None:
        c = db.get(Comment, p.accepted_comment_id)
        if c:
            answer_author = db.get(User, c.author_id)
            if answer_author and answer_author.id != user.id:
                answer_author.reputation = max(0, int(answer_author.reputation or 0) - 3)
                db.add(answer_author)
        p.accepted_comment_id = None
        p.updated_at = utcnow()
        db.add(p)
        db.commit()
    return None


@router.post("/votes", response_model=VoteOut)
def vote(payload: VoteIn, db: Db, user: CurrentUser):
    require_verified_email(user)
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

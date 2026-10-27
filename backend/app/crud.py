"""业务逻辑：序列化、投票、徽章。"""
from __future__ import annotations

from sqlmodel import Session, func, select

from .models import Comment, Part, Post, User, Vote
from .schemas import CommentOut, PostOut, UserOut


# ── 徽章（派生，不落库）──────────────────────────────────────────────────────
def badges_for(db: Session, u: User, post_count: int, comment_count: int) -> list[str]:
    out: list[str] = []
    if post_count and post_count > 0:
        out.append("首次发帖")
    if post_count >= 5:
        out.append("常驻作者")
    if comment_count >= 20:
        out.append("热心回复")
    has_review = db.exec(
        select(func.count(Post.id)).where(Post.author_id == u.id,
                                          Post.kind == "review")).one()
    if has_review:
        out.append("实测派")
    has_build = db.exec(
        select(func.count(Post.id)).where(Post.author_id == u.id,
                                          Post.kind == "build")).one()
    if has_build:
        out.append("方案作者")
    if u.reputation >= 100:
        out.append("百赞")
    if u.reputation >= 1000:
        out.append("千赞")
    if u.is_staff:
        out.append("站务")
    return out


def user_out(db: Session, u: User) -> UserOut:
    posts = db.exec(select(func.count(Post.id)).where(Post.author_id == u.id)).one()
    comments = db.exec(
        select(func.count(Comment.id)).where(Comment.author_id == u.id)).one()
    return UserOut(
        id=u.id or 0, handle=u.handle, display_name=u.display_name, bio=u.bio,
        avatar_hue=u.avatar_hue, is_staff=u.is_staff, reputation=u.reputation,
        created_at=u.created_at, post_count=int(posts or 0),
        comment_count=int(comments or 0),
        badges=badges_for(db, u, int(posts or 0), int(comments or 0)),
    )


def users_out(db: Session, ids: set[int]) -> dict[int, UserOut]:
    if not ids:
        return {}
    rows = db.exec(select(User).where(User.id.in_(ids))).all()
    return {u.id: user_out(db, u) for u in rows if u.id is not None}


# ── 投票 ────────────────────────────────────────────────────────────────────
def my_votes(db: Session, user_id: int | None, kind: str, ids: list[int]) -> dict[int, int]:
    if not user_id or not ids:
        return {}
    rows = db.exec(select(Vote).where(Vote.user_id == user_id,
                                      Vote.target_kind == kind,
                                      Vote.target_id.in_(ids))).all()
    return {v.target_id: v.value for v in rows}


def _author_of(db: Session, kind: str, target_id: int) -> int | None:
    model = Post if kind == "post" else Comment
    row = db.get(model, target_id)
    return getattr(row, "author_id", None) if row else None


def apply_vote(db: Session, user: User, kind: str, target_id: int, value: int) -> tuple[int, int]:
    """返回 (新 score, 我的票)。value=0 表示撤销。

    score 每次都从 votes 表重新聚合，不做增量加减 —— 增量在并发下会漂。
    """
    model = Post if kind == "post" else Comment
    target = db.get(model, target_id)
    if target is None:
        raise LookupError("目标不存在")

    existing = db.exec(select(Vote).where(Vote.user_id == user.id,
                                          Vote.target_kind == kind,
                                          Vote.target_id == target_id)).first()
    if value == 0:
        if existing:
            db.delete(existing)
    elif existing:
        existing.value = value
        db.add(existing)
    else:
        db.add(Vote(user_id=user.id, target_kind=kind, target_id=target_id,
                    value=value))
    db.flush()          # 先把增删改落到位，再聚合

    total = int(db.exec(
        select(func.coalesce(func.sum(Vote.value), 0))
        .where(Vote.target_kind == kind, Vote.target_id == target_id)).first() or 0)

    target = db.get(model, target_id)
    target.score = total
    db.add(target)

    # 作者声望 = 自己所有帖子与评论的得分之和
    author = db.get(User, target.author_id)
    if author is not None:
        rep_posts = db.exec(select(func.coalesce(func.sum(Post.score), 0))
                            .where(Post.author_id == author.id)).first()
        rep_comments = db.exec(select(func.coalesce(func.sum(Comment.score), 0))
                               .where(Comment.author_id == author.id)).first()
        author.reputation = int(rep_posts or 0) + int(rep_comments or 0)
        db.add(author)

    db.commit()
    return target.score, (value if value else 0)


# ── 帖子序列化 ──────────────────────────────────────────────────────────────
def post_out(p: Post, author: UserOut | None, part_title: str | None,
             my_vote: int = 0) -> PostOut:
    return PostOut(
        id=p.id or 0, kind=p.kind, title=p.title, body=p.body,
        tags=[t for t in (p.tags or "").split(",") if t],
        part_id=p.part_id, part_title=part_title, rating=p.rating,
        use_case=p.use_case, own_hardware=p.own_hardware,
        total_price_cny=p.total_price_cny, price_scope=p.price_scope,
        price_verified=p.price_verified, score=p.score,
        comment_count=p.comment_count, view_count=p.view_count,
        pinned=p.pinned, created_at=p.created_at, author=author, my_vote=my_vote,
    )


def posts_out(db: Session, posts: list[Post], viewer_id: int | None = None) -> list[PostOut]:
    authors = users_out(db, {p.author_id for p in posts})
    part_ids = {p.part_id for p in posts if p.part_id}
    parts: dict[str, str] = {}
    if part_ids:
        for r in db.exec(select(Part.id, Part.title).where(Part.id.in_(part_ids))).all():
            parts[r[0]] = r[1]
    votes = my_votes(db, viewer_id, "post", [p.id for p in posts if p.id])
    return [post_out(p, authors.get(p.author_id),
                     parts.get(p.part_id) if p.part_id else None,
                     votes.get(p.id or 0, 0)) for p in posts]


# ── 评论序列化（两级）───────────────────────────────────────────────────────
def comments_out(db: Session, post_id: int, viewer_id: int | None = None) -> list[CommentOut]:
    rows = db.exec(select(Comment).where(Comment.post_id == post_id)
                   .order_by(Comment.created_at)).all()
    authors = users_out(db, {c.author_id for c in rows})
    votes = my_votes(db, viewer_id, "comment", [c.id for c in rows if c.id])
    flat: dict[int, CommentOut] = {}
    for c in rows:
        flat[c.id or 0] = CommentOut(
            id=c.id or 0, post_id=c.post_id, parent_id=c.parent_id, body=c.body,
            score=c.score, created_at=c.created_at,
            author=authors.get(c.author_id), my_vote=votes.get(c.id or 0, 0))
    roots: list[CommentOut] = []
    for c in flat.values():
        if c.parent_id and c.parent_id in flat:
            flat[c.parent_id].replies.append(c)
        else:
            roots.append(c)
    return roots


def touch_comment_count(db: Session, post_id: int) -> None:
    n = db.exec(select(func.count(Comment.id)).where(Comment.post_id == post_id)).one()
    post = db.get(Post, post_id)
    if post is not None:
        post.comment_count = int(n or 0)
        db.add(post)
        db.commit()

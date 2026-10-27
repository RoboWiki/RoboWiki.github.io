"""文档页的讨论串。

形态参考 YunQianDoc（VitePress + giscus）：每篇文章底下直接就能说话。
这里改成自托管 —— giscus 需要公开 GitHub 仓库并开启 Discussions，
本站的数据在本地，所以用同一套用户体系自己存。

页面标识用 VitePress 的路径（`parts/actuator/cubemars`），与 giscus 的
`mapping: pathname` 等价：换标题不会掉讨论，换路径才会。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select

from ...models import User, WikiComment
from ..deps import CurrentUser, Db

router = APIRouter(prefix="/wiki", tags=["wiki"])


class CommentIn(BaseModel):
    page: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    parent_id: int | None = None


def _out(c: WikiComment, u: User | None) -> dict:
    return {
        "id": c.id,
        "page": c.page,
        "body": c.body,
        "parent_id": c.parent_id,
        "created_at": c.created_at.isoformat(),
        "author": None if u is None else {
            "handle": u.handle, "display_name": u.display_name,
            "avatar_hue": u.avatar_hue, "reputation": u.reputation,
            "is_staff": u.is_staff,
        },
    }


@router.get("/comments")
def list_comments(
    db: Db,
    page: Annotated[str | None, Query(description="VitePress 路径，如 parts/actuator/cubemars")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
):
    """一个页面的讨论串；不传 page 则返回最近的全站讨论。"""
    stmt = select(WikiComment)
    if page:
        stmt = stmt.where(WikiComment.page == page)
    rows = db.exec(stmt.order_by(WikiComment.created_at.asc()).limit(limit)).all()

    uids = {r.user_id for r in rows}
    users = {u.id: u for u in
             (db.exec(select(User).where(User.id.in_(uids))).all() if uids else [])}
    return {"page": page, "count": len(rows),
            "comments": [_out(r, users.get(r.user_id)) for r in rows]}


@router.get("/comment-counts")
def comment_counts(db: Db):
    """每页条数，供侧边栏或索引页显示「N 条讨论」。"""
    rows = db.exec(select(WikiComment.page, func.count(WikiComment.id))
                   .group_by(WikiComment.page)).all()
    return {"counts": {p: int(n) for p, n in rows},
            "total": sum(int(n) for _, n in rows)}


@router.post("/comments", status_code=201)
def create_comment(payload: CommentIn, user: CurrentUser, db: Db):
    parent = None
    if payload.parent_id is not None:
        parent = db.get(WikiComment, payload.parent_id)
        if parent is None:
            raise HTTPException(422, "要回复的那条讨论不存在")
        if parent.page != payload.page:
            raise HTTPException(422, "回复不能跨页面")
    c = WikiComment(page=payload.page.strip("/"), user_id=user.id,
                    body=payload.body.strip(),
                    parent_id=parent.id if parent else None)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c, user)


@router.delete("/comments/{cid}", status_code=204)
def delete_comment(cid: int, user: CurrentUser, db: Db):
    c = db.get(WikiComment, cid)
    if c is None:
        raise HTTPException(404, "不存在")
    if c.user_id != user.id and not user.is_staff:
        raise HTTPException(403, "只能删自己的讨论")
    for child in db.exec(select(WikiComment).where(WikiComment.parent_id == cid)).all():
        db.delete(child)
    db.delete(c)
    db.commit()
    return None

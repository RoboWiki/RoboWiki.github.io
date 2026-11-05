"""文档页的讨论串。

形态参考 YunQianDoc（VitePress + giscus）：每篇文章底下直接就能说话。
这里改成自托管 —— giscus 需要公开 GitHub 仓库并开启 Discussions，
本站的数据在本地，所以用同一套用户体系自己存。

页面标识用 VitePress 的路径（`parts/actuator/cubemars`），与 giscus 的
`mapping: pathname` 等价：换标题不会掉讨论，换路径才会。

线程模型（P1）：
  · `root_id` 把所有回复绑到同一条根讨论；分页只按根做，回复随根一起返回；
  · `status=pending` 的内容只有作者与站务看得到（内容安全拦截/待复核）；
  · 删除是软删除：`deleted_at` 落库，子节点原样保留；有可见后代的节点
    返回一个 `deleted=true` 的占位节点，前端据此保留线程形状。
响应字段只增不删：`id / page / body / parent_id / created_at / author`
保持原样，前端不需要跟着改。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import select

from ...content_safety import check_user_text_chunks
from ...core.config import settings
from ...models import User, WikiComment
from ...schemas import WikiCommentIn
from ..deps import CurrentUser, Db, MaybeUser, rate_limit
from .notifications import create_notification

router = APIRouter(prefix="/wiki", tags=["wiki"])

#: 单页最多取回的行数（含回复）。超过这个量级应该按根分页而不是整页拉。
_PAGE_ROW_CAP = 2000


def _visible(c: WikiComment, viewer: User | None) -> bool:
    if c.deleted_at is not None:
        return False
    if c.hidden or c.status == "hidden":
        return False
    if c.status == "visible":
        return True
    # pending：仅作者与站务可见
    return bool(viewer and (viewer.is_staff or viewer.id == c.user_id))


def _out(c: WikiComment, u: User | None, root_id: int | None = None) -> dict:
    deleted = c.deleted_at is not None
    # 根节点对外也给出 root_id = 自己：前端/小程序只需一个字段就能分组，
    # 不必再判断 parent_id 是否为空。库里根节点仍存 NULL（避免自引用外键）。
    if root_id is None:
        root_id = c.root_id if c.parent_id is not None else c.id
    return {
        "id": c.id,
        "page": c.page,
        # 占位节点不返回原文：作者/站务删掉的内容不应继续被读到
        "body": "" if deleted else c.body,
        "parent_id": c.parent_id,
        "root_id": root_id,
        "status": c.status,
        "hidden": bool(c.hidden or c.status == "hidden"),
        "deleted": deleted,
        "deleted_at": c.deleted_at.isoformat() if c.deleted_at else None,
        "created_at": c.created_at.isoformat(),
        "author": None if (deleted or u is None) else {
            "handle": u.handle, "display_name": u.display_name,
            "avatar_hue": u.avatar_hue, "reputation": u.reputation,
            "is_staff": u.is_staff,
        },
    }


def _ser(db, rows: list[WikiComment]) -> list[dict]:
    uids = {r.user_id for r in rows if r.deleted_at is None}
    users = {u.id: u for u in
             (db.exec(select(User).where(User.id.in_(uids))).all() if uids else [])}
    by_id = {r.id: r for r in rows if r.id is not None}
    return [_out(r, users.get(r.user_id), _root_of(r, by_id)) for r in rows]


def _root_of(c: WikiComment, by_id: dict[int, WikiComment]) -> int | None:
    """沿 parent 链回填根 id（兼容没有 root_id 的旧行）。"""
    seen: set[int] = set()
    cur: WikiComment | None = c
    while cur is not None and cur.id not in seen:
        seen.add(cur.id)
        if cur.parent_id is None:
            return cur.id
        if cur.root_id:
            return cur.root_id
        cur = by_id.get(cur.parent_id)
    return c.root_id


@router.get("/comments")
def list_comments(
    db: Db,
    user: MaybeUser,
    page: Annotated[str | None, Query(description="VitePress 路径，如 parts/actuator/cubemars")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    root_limit: Annotated[int | None, Query(ge=1, le=200)] = None,
    root_offset: Annotated[int, Query(ge=0)] = 0,
    root_id: Annotated[int | None, Query(description="只看某条根讨论的整棵子树")] = None,
):
    """一个页面的讨论串；不传 page 则返回最近的全站讨论。

    分页按**根讨论**做（`root_limit` / `root_offset`），回复永远跟着根返回，
    所以前端组树时不会出现「父节点没拉到、回复变孤儿」。`limit` 仍保留为
    单次最大行数的兼容参数。
    """
    stmt = select(WikiComment)
    if page:
        stmt = stmt.where(WikiComment.page == page)
    rows = db.exec(stmt.order_by(WikiComment.created_at.asc(), WikiComment.id.asc())
                   .limit(_PAGE_ROW_CAP)).all()
    by_id = {r.id: r for r in rows if r.id is not None}
    children: dict[int | None, list[WikiComment]] = {}
    for r in rows:
        children.setdefault(r.parent_id, []).append(r)

    shown: dict[int, bool] = {}

    def show(c: WikiComment) -> bool:
        """可见 → 返回；已删除但有可见后代 → 占位保留线程；否则整支不返回。"""
        if c.id in shown:
            return shown[c.id]
        shown[c.id] = False             # 先落哨兵，防脏数据里的环递归
        if _visible(c, user):
            shown[c.id] = True
            return True
        ok = c.deleted_at is not None and any(
            show(ch) for ch in children.get(c.id, []))
        shown[c.id] = ok
        return ok

    roots = [r for r in children.get(None, []) if show(r)]
    total_roots = len(roots)

    effective_limit = root_limit or limit
    if root_id is not None:
        node = by_id.get(root_id)
        # root_id 也可能给的是回复 id：沿链找到它所属的根
        while node is not None and node.parent_id is not None:
            node = by_id.get(node.parent_id)
        roots = [node] if node is not None and show(node) else []
        total_roots = len(roots)
        effective_limit = len(roots)
        root_offset = 0
    else:
        roots = roots[root_offset:root_offset + effective_limit]

    out: list[WikiComment] = []
    visited: set[int] = set()

    def walk(c: WikiComment) -> None:
        if c.id in visited or not show(c):
            return
        visited.add(c.id)
        out.append(c)
        for ch in children.get(c.id, []):
            walk(ch)

    for r in roots:
        walk(r)

    return {"page": page, "count": len(out), "total": len(out),
            "root_total": total_roots, "root_limit": effective_limit,
            "root_offset": root_offset, "root_id": root_id,
            "comments": _ser(db, out)}


@router.get("/comment-counts")
def comment_counts(db: Db):
    """每页条数，供侧边栏或索引页显示「N 条讨论」。

    只数公开可见的：pending/hidden/已删除都不算 —— 页面上看不到的，
    不应该在索引里显示成一条讨论。
    """
    rows = db.exec(select(WikiComment.page, func.count(WikiComment.id))
                   .where(WikiComment.hidden == False,  # noqa: E712
                          WikiComment.status == "visible",
                          WikiComment.deleted_at.is_(None))
                   .group_by(WikiComment.page)).all()
    return {"counts": {p: int(n) for p, n in rows},
            "total": sum(int(n) for _, n in rows)}


@router.post("/comments", status_code=201)
def create_comment(payload: WikiCommentIn, request: Request,
                   user: CurrentUser, db: Db):
    rate_limit(request, "wiki-comment", settings.rate_max_comments, user.id)
    body = payload.body.strip()
    if not body:
        raise HTTPException(422, "评论不能为空")
    page = payload.page.strip("/")

    parent = None
    if payload.parent_id is not None:
        parent = db.get(WikiComment, payload.parent_id)
        if parent is None:
            raise HTTPException(422, "要回复的那条讨论不存在")
        if parent.deleted_at is not None:
            raise HTTPException(422, "要回复的讨论已被删除")
        if parent.hidden or parent.status == "hidden":
            raise HTTPException(422, "要回复的讨论已被隐藏")
        if parent.page != page:
            raise HTTPException(422, "回复不能跨页面")
        if not _visible(parent, user):
            raise HTTPException(422, "要回复的讨论正在审核中")

    # 根绑定：回复的回复也落在同一条根讨论上
    root_id = None
    if parent is not None:
        root_id = parent.id if parent.parent_id is None else parent.root_id
        if root_id is None:
            by_id = {r.id: r for r in db.exec(select(WikiComment).where(
                WikiComment.page == page)).all() if r.id is not None}
            root_id = _root_of(parent, by_id)

    # 内容安全：未配置微信时放行；判定风险则落 pending 等人工复核
    safety = check_user_text_chunks(db, user.id, body)

    c = WikiComment(page=page, user_id=user.id, body=body,
                    parent_id=parent.id if parent else None,
                    root_id=root_id,
                    status="visible" if safety.passed else "pending")
    db.add(c)
    db.flush()                                  # 拿到 id 才能拼通知链接

    if parent is not None:
        snippet = body if len(body) <= 80 else body[:80] + "…"
        create_notification(
            db, parent.user_id, type="reply",
            subject="有人回复了你的讨论",
            body=snippet, link=f"/{page}#comment-{c.id}", actor_id=user.id)

    db.commit()
    db.refresh(c)
    return _out(c, user)


class WikiCommentModerationIn(BaseModel):
    action: Literal["approve", "hide"]


@router.patch("/comments/{cid}/moderation")
def moderate_comment(cid: int, payload: WikiCommentModerationIn,
                     user: CurrentUser, db: Db):
    """站务处置待审讨论：通过后公开，隐藏后从公开线程移除。"""
    if not user.is_staff:
        raise HTTPException(403, "只有站务可以审核讨论")
    c = db.get(WikiComment, cid)
    if c is None or c.deleted_at is not None:
        raise HTTPException(404, "讨论不存在")
    if payload.action == "approve":
        c.status = "visible"
        c.hidden = False
    else:
        c.status = "hidden"
        c.hidden = True
    db.add(c)
    create_notification(
        db, c.user_id, type="moderation",
        subject="你的讨论已通过审核" if payload.action == "approve" else "你的讨论已被隐藏",
        body=(c.body or "")[:120],
        link=f"/{c.page}#comment-{c.id}", actor_id=user.id)
    db.commit()
    db.refresh(c)
    return _out(c, user)


@router.delete("/comments/{cid}", status_code=204)
def delete_comment(cid: int, user: CurrentUser, db: Db):
    """软删除：作者或站务。

    子节点**不删**：删掉父节点后线程仍能展开，只是父节点变成占位。
    重复删除幂等返回 204，客户端重试不会报错。
    """
    c = db.get(WikiComment, cid)
    if c is None:
        raise HTTPException(404, "不存在")
    if c.user_id != user.id and not user.is_staff:
        raise HTTPException(403, "只能删自己的讨论")
    if c.deleted_at is None:
        c.deleted_at = datetime.now(timezone.utc)
        c.deleted_by = user.id
        db.add(c)
        db.commit()
    return None

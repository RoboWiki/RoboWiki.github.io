"""举报与内容处置。

举报只需登录，不直接改变可见性；站务在 `/admin/reports` 里决定隐藏或驳回。
隐藏是软操作：行还在，站务仍能在后台看到，恢复时原样回来。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select

from ...core.config import settings
from ...crud import touch_comment_count
from ...models import Comment, Post, Report, User, WikiComment
from ..deps import CurrentUser, Db, rate_limit
from .notifications import create_notification

router = APIRouter(tags=["reports"])

TARGETS = {
    "post": Post,
    "comment": Comment,
    "wiki_comment": WikiComment,
}


class ReportIn(BaseModel):
    target_kind: Literal["post", "comment", "wiki_comment"]
    target_id: int = Field(ge=1)
    reason: Literal["spam", "abuse", "misinfo", "other"]
    detail: str = Field(default="", max_length=500)


class ResolveIn(BaseModel):
    action: Literal["hide", "restore", "dismiss"]
    note: str = Field(min_length=2, max_length=500)


def _staff(user: User) -> None:
    if not user.is_staff:
        raise HTTPException(403, "需要站务权限")


def _get_target(db, kind: str, target_id: int):
    model = TARGETS.get(kind)
    return None if model is None else db.get(model, target_id)


def _brief(u: User | None) -> dict | None:
    if u is None:
        return None
    return {"handle": u.handle, "display_name": u.display_name,
            "is_staff": u.is_staff}


def _snapshot(db, kind: str, target_id: int) -> dict | None:
    """给审核队列一段可判断的上下文，而不是只有一个 id。"""
    if kind == "post":
        p = db.get(Post, target_id)
        if p is None:
            return None
        return {"title": p.title, "body": p.body[:300], "kind": p.kind,
                "hidden": p.hidden, "author": _brief(db.get(User, p.author_id))}
    if kind == "comment":
        c = db.get(Comment, target_id)
        if c is None:
            return None
        post = db.get(Post, c.post_id)
        return {"body": c.body[:300], "post_id": c.post_id,
                "post_title": post.title if post else None, "hidden": c.hidden,
                "author": _brief(db.get(User, c.author_id))}
    if kind == "wiki_comment":
        c = db.get(WikiComment, target_id)
        if c is None:
            return None
        return {"body": c.body[:300], "page": c.page, "hidden": c.hidden,
                "status": c.status, "deleted": c.deleted_at is not None,
                "author": _brief(db.get(User, c.user_id))}
    return None


def _wiki_thread_ids(db, root_id: int) -> list[int]:
    """整棵子树的 id（含根）。P1 之后回复可以多层，处置必须覆盖所有层。"""
    ids: list[int] = []
    seen: set[int] = set()
    frontier = [root_id]
    while frontier:
        cid = frontier.pop()
        if cid in seen:
            continue
        seen.add(cid)
        ids.append(cid)
        frontier.extend(db.exec(
            select(WikiComment.id).where(WikiComment.parent_id == cid)).all())
    return ids


def _set_hidden(db, kind: str, target_id: int, hidden: bool) -> None:
    """评论按线程处置：隐藏根评论时，回复（含多层）也不应单独留在页面上。"""
    if kind == "wiki_comment":
        for cid in _wiki_thread_ids(db, target_id):
            row = db.get(WikiComment, cid)
            if row is not None:
                row.hidden = hidden
                # 隐藏时不要覆盖 pending：否则恢复举报会把待审内容直接放成 visible。
                # 只把原本 visible 的行标成 hidden；恢复时也只还原 hidden。
                if row.deleted_at is None:
                    if hidden and row.status == "visible":
                        row.status = "hidden"
                    elif not hidden and row.status == "hidden":
                        row.status = "visible"
                db.add(row)
        return

    if kind == "comment":
        c = db.get(Comment, target_id)
        if c is None:
            return
        rows = [c] + db.exec(select(Comment).where(
            Comment.parent_id == target_id)).all()
        for row in rows:
            row.hidden = hidden
            db.add(row)
        touch_comment_count(db, c.post_id, commit=False)
        return

    row = db.get(Post, target_id)
    if row is not None:
        row.hidden = hidden
        db.add(row)


def _author_id(db, kind: str, target_id: int) -> int | None:
    if kind == "post":
        p = db.get(Post, target_id)
        return p.author_id if p is not None else None
    if kind == "comment":
        c = db.get(Comment, target_id)
        return c.author_id if c is not None else None
    if kind == "wiki_comment":
        c = db.get(WikiComment, target_id)
        return c.user_id if c is not None else None
    return None


def _target_link(db, kind: str, target_id: int) -> str | None:
    if kind == "wiki_comment":
        c = db.get(WikiComment, target_id)
        return f"/{c.page}.html#comment-{target_id}" if c is not None else None
    if kind == "post":
        return f"/post.html?id={target_id}"
    if kind == "comment":
        c = db.get(Comment, target_id)
        return f"/post.html?id={c.post_id}#c{target_id}" if c is not None else None
    return None


@router.post("/reports", status_code=201)
def create_report(payload: ReportIn, request: Request, db: Db,
                  user: CurrentUser):
    rate_limit(request, "report", settings.rate_max_reports, user.id)
    if _get_target(db, payload.target_kind, payload.target_id) is None:
        raise HTTPException(404, "举报对象不存在")

    existing = db.exec(select(Report).where(
        Report.reporter_id == user.id,
        Report.target_kind == payload.target_kind,
        Report.target_id == payload.target_id)).first()
    if existing is not None:
        raise HTTPException(409, "你已经举报过这条内容")

    r = Report(reporter_id=user.id, target_kind=payload.target_kind,
               target_id=payload.target_id, reason=payload.reason,
               detail=payload.detail.strip())
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "status": r.status,
            "created_at": r.created_at.isoformat()}


@router.get("/admin/reports")
def list_reports(
    user: CurrentUser, db: Db,
    status: Literal["open", "resolved", "dismissed", "all"] = "open",
    target_kind: Literal["post", "comment", "wiki_comment", "all"] = "all",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    _staff(user)
    stmt = select(Report)
    if status != "all":
        stmt = stmt.where(Report.status == status)
    if target_kind != "all":
        stmt = stmt.where(Report.target_kind == target_kind)

    total = int(db.exec(select(func.count()).select_from(stmt.subquery())).one())
    rows = db.exec(stmt.order_by(Report.created_at.desc())
                   .offset(offset).limit(limit)).all()
    reporters = {u.id: u for u in db.exec(select(User).where(
        User.id.in_({r.reporter_id for r in rows}))).all()} if rows else {}

    counts = {k: int(n) for k, n in db.exec(
        select(Report.status, func.count(Report.id))
        .group_by(Report.status)).all()}
    items = [{
        "id": r.id,
        "target_kind": r.target_kind,
        "target_id": r.target_id,
        "reason": r.reason,
        "detail": r.detail,
        "status": r.status,
        "resolution_note": r.resolution_note,
        "reporter": _brief(reporters.get(r.reporter_id)),
        "created_at": r.created_at.isoformat(),
        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        "target": _snapshot(db, r.target_kind, r.target_id),
    } for r in rows]
    return {"total": total, "limit": limit, "offset": offset,
            "counts": {"open": counts.get("open", 0),
                       "resolved": counts.get("resolved", 0),
                       "dismissed": counts.get("dismissed", 0)},
            "items": items}


@router.patch("/admin/reports/{report_id}")
def resolve_report(report_id: int, payload: ResolveIn, user: CurrentUser, db: Db):
    _staff(user)
    r = db.get(Report, report_id)
    if r is None:
        raise HTTPException(404, "举报不存在")
    target = _get_target(db, r.target_kind, r.target_id)
    if target is None:
        raise HTTPException(404, "举报对象已被删除")

    if payload.action == "hide":
        _set_hidden(db, r.target_kind, r.target_id, True)
        r.status = "resolved"
    elif payload.action == "restore":
        _set_hidden(db, r.target_kind, r.target_id, False)
        r.status = "resolved"
    else:
        r.status = "dismissed"

    r.resolution_note = payload.note.strip()
    r.resolver_id = user.id
    r.resolved_at = datetime.now(timezone.utc)
    db.add(r)

    # 通知处置结果：隐藏/恢复通知内容作者；驳回通知举报人。
    # 通知不阻塞处置本身 —— 写失败只会少一条提醒，举报状态照常提交。
    link = _target_link(db, r.target_kind, r.target_id)
    if payload.action == "dismiss":
        create_notification(
            db, r.reporter_id, type="moderation", subject="你的举报已处理",
            body=r.resolution_note, link=link, actor_id=user.id)
    else:
        author_id = _author_id(db, r.target_kind, r.target_id)
        subject = "你的内容已被隐藏" if payload.action == "hide" else "你的内容已恢复"
        create_notification(
            db, author_id, type="moderation", subject=subject,
            body=r.resolution_note, link=link, actor_id=user.id)

    db.commit()
    db.refresh(r)
    return {"id": r.id, "status": r.status,
            "resolution_note": r.resolution_note,
            "resolved_at": r.resolved_at.isoformat(),
            "target": _snapshot(db, r.target_kind, r.target_id)}

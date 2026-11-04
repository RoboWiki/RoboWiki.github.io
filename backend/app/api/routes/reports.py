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
                "author": _brief(db.get(User, c.user_id))}
    return None


def _set_hidden(db, kind: str, target_id: int, hidden: bool) -> None:
    """评论按线程处置：隐藏根评论时，回复也不应单独留在页面上。"""
    if kind == "wiki_comment":
        rows = [db.get(WikiComment, target_id)]
        rows += db.exec(select(WikiComment).where(
            WikiComment.parent_id == target_id)).all()
        for row in rows:
            if row is not None:
                row.hidden = hidden
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
    db.commit()
    db.refresh(r)
    return {"id": r.id, "status": r.status,
            "resolution_note": r.resolution_note,
            "resolved_at": r.resolved_at.isoformat(),
            "target": _snapshot(db, r.target_kind, r.target_id)}

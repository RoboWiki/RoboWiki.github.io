"""站内通知：列表 / 未读数 / 单条已读 / 全部已读。

通知由业务侧用 `create_notification()` 顺手写入 —— 它**不能**阻塞主流程：
发评论、处置举报先成功，通知只是结果。所以 helper 不 commit、不 flush，
失败只记日志；调用方随主事务一起落库。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ...models import Notification
from ...schemas import NotificationListOut, NotificationOut
from ..deps import CurrentUser, Db

router = APIRouter(prefix="/notifications", tags=["notifications"])

log = logging.getLogger("robowiki.notifications")


def create_notification(db: Session, user_id: int | None, *, type: str,
                        subject: str, body: str = "", link: str | None = None,
                        actor_id: int | None = None) -> Notification | None:
    """给 `user_id` 写一条通知；自己操作自己时不写。

    不 commit / 不 flush：调用方紧接着会 commit 主实体，通知随同一事务落库。
    构造/入 session 失败只记日志，绝不把已经成功的写操作一起回滚。
    """
    if not user_id or (actor_id is not None and actor_id == user_id):
        return None
    try:
        note = Notification(user_id=user_id, type=type,
                            subject=(subject or "")[:200],
                            body=(body or "")[:500], link=link)
        db.add(note)
        return note
    except Exception:                          # pragma: no cover - 防御性
        log.warning("创建通知失败，主流程继续", exc_info=True)
        return None


def _out(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id or 0, type=n.type, subject=n.subject, body=n.body,
        link=n.link, read_at=n.read_at, created_at=n.created_at)


@router.get("", response_model=NotificationListOut)
@router.get("/", response_model=NotificationListOut, include_in_schema=False)
def list_notifications(
    user: CurrentUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    unread: bool = False,
):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread:
        stmt = stmt.where(Notification.read_at.is_(None))

    total = int(db.exec(select(func.count()).select_from(stmt.subquery())).one())
    rows = db.exec(stmt.order_by(Notification.created_at.desc(),
                                 Notification.id.desc())
                   .offset(offset).limit(limit)).all()
    remaining = int(db.exec(select(func.count(Notification.id)).where(
        Notification.user_id == user.id,
        Notification.read_at.is_(None))).one())
    return NotificationListOut(total=total, unread=remaining, limit=limit,
                               offset=offset, items=[_out(n) for n in rows])


@router.get("/unread_count")
def unread_count(user: CurrentUser, db: Db):
    n = db.exec(select(func.count(Notification.id)).where(
        Notification.user_id == user.id,
        Notification.read_at.is_(None))).one()
    return {"unread": int(n or 0)}


def _own(db: Session, user, notification_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    # 别人的通知一律 404：不暴露「这条 id 存在」
    if n is None or n.user_id != user.id:
        raise HTTPException(404, "通知不存在")
    return n


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user: CurrentUser, db: Db):
    n = _own(db, user, notification_id)
    if n.read_at is None:
        n.read_at = datetime.now(timezone.utc)
        db.add(n)
        db.commit()
        db.refresh(n)
    return _out(n)


@router.post("/read-all")
def mark_all_read(user: CurrentUser, db: Db):
    rows = db.exec(select(Notification).where(
        Notification.user_id == user.id,
        Notification.read_at.is_(None))).all()
    now = datetime.now(timezone.utc)
    for n in rows:
        n.read_at = now
        db.add(n)
    db.commit()
    return {"updated": len(rows)}

"""依赖注入：会话、当前用户、限流。"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import session
from ..core.security import decode_token
from ..models import User


def get_db() -> Session:
    db = session()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[Session, Depends(get_db)]


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def current_user(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "需要登录",
                            headers={"WWW-Authenticate": "Bearer"})
    handle = decode_token(token)
    user = db.exec(select(User).where(User.handle == handle)).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


def optional_user(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    token = _bearer(authorization)
    if not token:
        return None
    try:
        handle = decode_token(token)
    except HTTPException:
        return None
    return db.exec(select(User).where(User.handle == handle)).first()


CurrentUser = Annotated[User, Depends(current_user)]
MaybeUser = Annotated[Optional[User], Depends(optional_user)]


# ── 简易限流（进程内；多副本部署要换 Redis）─────────────────────────────────
_buckets: dict[tuple[str, str], deque] = defaultdict(deque)


def rate_limit(request: Request, bucket: str, limit: int) -> None:
    ip = (request.client.host if request.client else "?") or "?"
    key = (bucket, ip)
    now = time.time()
    q = _buckets[key]
    while q and now - q[0] > settings.rate_window_s:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"操作太频繁（{settings.rate_window_s}s 内最多 {limit} 次）")
    q.append(now)


def reset_rate_limits() -> None:
    _buckets.clear()

"""依赖注入：会话、当前用户、限流。"""
from __future__ import annotations

import secrets
import threading
import time
from collections import deque
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from ..core.config import settings
from ..core.db import session
from ..core.security import decode_token, password_fingerprint
from ..models import User


def get_db() -> Session:
    db = session()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[Session, Depends(get_db)]


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth",
                         description="JWT access token")


def _bearer(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    return credentials.credentials if credentials else None


def _token_matches(user: User | None, pv: str) -> bool:
    """token 里的 pv 必须等于用户**当前**口令哈希的指纹。

    改密 / 重置密码后哈希变了，pv 对不上 —— 旧 token 自然失效，
    不需要额外的撤销表，也就不需要数据库迁移。
    """
    if user is None:
        return False
    return secrets.compare_digest(pv, password_fingerprint(user.password_hash))


def current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    token = _bearer(credentials)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "需要登录",
                            headers={"WWW-Authenticate": "Bearer"})
    handle, pv = decode_token(token)
    user = db.exec(select(User).where(User.handle == handle)).first()
    if not _token_matches(user, pv):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌无效或已过期",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def optional_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User | None:
    token = _bearer(credentials)
    if not token:
        return None
    try:
        handle, pv = decode_token(token)
    except HTTPException:
        return None
    user = db.exec(select(User).where(User.handle == handle)).first()
    return user if _token_matches(user, pv) else None


CurrentUser = Annotated[User, Depends(current_user)]
MaybeUser = Annotated[Optional[User], Depends(optional_user)]


# ── 简易限流（进程内；多副本部署要换 Redis）─────────────────────────────────
#: 桶表硬上限。API 端口若暴露且 X-Forwarded-For 可伪造，键数会随请求无限涨；
#: 超过上限就淘汰窗口外的桶，仍超则按「最久未用」丢，内存因此有界。
_MAX_BUCKETS = 5000

_buckets: dict[tuple[str, str], deque] = {}
_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    """反代后取真实客户端 IP；API 只在内网，可信 X-Forwarded-For。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip() or "?"
    return (request.client.host if request.client else "?") or "?"


def _prune_locked(now: float) -> None:
    """调用方必须持锁。先清窗口外的死桶，再按最久未用裁到上限以内。

    调用时机是「准备插入新键、且表已满」，所以这里要多让出 1 个位置，
    否则插完又超了。
    """
    window = settings.rate_window_s
    for key in [k for k, q in _buckets.items() if not q or now - q[-1] > window]:
        _buckets.pop(key, None)
    overflow = len(_buckets) - _MAX_BUCKETS + 1
    if overflow > 0:
        oldest = sorted(_buckets.items(),
                        key=lambda kv: kv[1][-1] if kv[1] else 0.0)
        for key, _q in oldest[:overflow]:
            _buckets.pop(key, None)


def rate_limit(request: Request, bucket: str, limit: int,
               identity: int | str | None = None) -> None:
    who = f"u:{identity}" if identity is not None else f"ip:{_client_ip(request)}"
    key = (bucket, who)
    now = time.time()
    with _lock:
        q = _buckets.get(key)
        if q is None:
            if len(_buckets) >= _MAX_BUCKETS:
                _prune_locked(now)  # 先腾位置，再建桶（否则新桶会被当成最旧淘汰）
            q = deque()
            _buckets[key] = q
        while q and now - q[0] > settings.rate_window_s:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, int(settings.rate_window_s - (now - q[0])) + 1)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"操作太频繁（{settings.rate_window_s}s 内最多 {limit} 次），"
                f"请 {retry}s 后再试",
                headers={"Retry-After": str(retry)},
            )
        q.append(now)


def reset_rate_limits() -> None:
    with _lock:
        _buckets.clear()

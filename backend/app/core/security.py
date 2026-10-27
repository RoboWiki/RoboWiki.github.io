"""核心工具：口令哈希、JWT、时间。"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from .config import settings

_ALGO = "HS256"
_ITER = 240_000


def now() -> datetime:
    return datetime.now(timezone.utc)


# ── 口令 ────────────────────────────────────────────────────────────────────
def hash_password(raw: str) -> str:
    """PBKDF2-HMAC-SHA256，格式 pbkdf2$迭代$盐$摘要（stdlib，无额外依赖）。"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(raw: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, dk_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", raw.encode(), bytes.fromhex(salt_hex),
                                 int(iters))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, TypeError):
        return False


# ── 令牌 ────────────────────────────────────────────────────────────────────
def create_token(sub: str) -> str:
    payload = {"sub": sub, "exp": now() + timedelta(hours=settings.token_hours),
               "iat": now()}
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGO)


def decode_token(token: str) -> str:
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[_ALGO])
        return str(data["sub"])
    except jwt.PyJWTError as exc:  # 过期 / 签名不对 / 格式错
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="令牌无效或已过期") from exc

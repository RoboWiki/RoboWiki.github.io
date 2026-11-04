"""核心工具：口令哈希、JWT、时间。"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache

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


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """固定的哑哈希：用户不存在时也拿它跑一次同成本的 PBKDF2。

    内容无人知道、也不参与任何判断，唯一作用是让「账号不存在」和「密码错」
    走同一条耗时路径，堵住登录接口的时序旁路（账号枚举）。
    """
    return hash_password(secrets.token_urlsafe(32))


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


def password_fingerprint(password_hash: str) -> str:
    """password_hash 的 16 位指纹，写进 JWT 的 `pv` 声明。

    只要口令哈希变了（改密 / 找回密码），指纹就变 → 旧 token 全部失效。
    不用数据库表，也就没有迁移；代价是 `pv` 只做等值比较、不做独立撤销。
    """
    return hashlib.sha256((password_hash or "").encode("utf-8")).hexdigest()[:16]


# ── 令牌 ────────────────────────────────────────────────────────────────────
def create_token(sub: str, password_hash: str) -> str:
    """签 token。`pv` 绑定当前口令哈希，改密即撤销。"""
    payload = {"sub": sub, "pv": password_fingerprint(password_hash),
               "exp": now() + timedelta(hours=settings.token_hours),
               "iat": now()}
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGO)


def decode_token(token: str) -> tuple[str, str]:
    """解 token，返回 (handle, pv)。

    没有 `pv` 的旧 token 一律视为无效（生产尚未上线，不保留兼容）。
    """
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[_ALGO])
        sub, pv = data["sub"], data["pv"]
    except KeyError as exc:  # 旧格式 / 手写 payload
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="令牌无效或已过期") from exc
    except jwt.PyJWTError as exc:  # 过期 / 签名不对 / 格式错
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="令牌无效或已过期") from exc
    if not isinstance(sub, str) or not isinstance(pv, str) or not pv:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="令牌无效或已过期")
    return sub, pv

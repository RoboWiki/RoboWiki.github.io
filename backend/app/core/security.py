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


def unusable_password_hash() -> str:
    """给「没有口令」的账号一个没人知道的随机哈希。

    `users.password_hash` 非空，第三方登录建出来的账号也必须有一串；
    用 `secrets.token_urlsafe(32)` 现场生成、不落任何地方，等于这串口令
    不存在。配合 `users.password_set = False` 表达「这个账号不能口令登录」。
    注意不要在登录路径上调用它 —— 那会每次登录都多跑一次 PBKDF2。
    """
    return hash_password(secrets.token_urlsafe(32))


def password_fingerprint(password_hash: str) -> str:
    """password_hash 的 16 位指纹，写进 JWT 的 `pv` 声明。

    只要口令哈希变了（改密 / 找回密码），指纹就变 → 旧 token 全部失效。
    不用数据库表，也就没有迁移；代价是 `pv` 只做等值比较、不做独立撤销。
    """
    return hashlib.sha256((password_hash or "").encode("utf-8")).hexdigest()[:16]


# ── 令牌 ────────────────────────────────────────────────────────────────────
def create_token(sub: str, password_hash: str,
                 scopes: tuple[str, ...] | None = None,
                 session_epoch: int = 0,
                 ttl_hours: int | None = None) -> str:
    """签 access token。`pv` 绑定当前口令哈希，改密即撤销。

    `scope` 是可选的**来源声明**（空格分隔，沿用 RFC 6749 的写法）：
    `password` / `github` / `wechat_mini`。它只说明「这枚 token 是用哪种方式
    换来的」，不参与授权判断 —— 老客户端忽略它、`decode_token` 也不读它，
    所以加上它不改变任何现有契约。

    `se` 是账号当前的会话代次（`users.session_epoch`）。`logout-all` 把它
    自增一次，此前签发的所有 access token 立刻失效。没有 `se` 的旧 token
    视为 0，与全新账号（epoch=0）兼容。
    """
    expires = now() + timedelta(hours=max(1, int(ttl_hours if ttl_hours is not None
                                             else settings.token_hours)))
    payload: dict = {"sub": sub, "pv": password_fingerprint(password_hash),
                     "se": int(session_epoch or 0),
                     "exp": expires, "iat": now()}
    if scopes:
        payload["scope"] = " ".join(scopes)
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGO)


def decode_token_payload(token: str) -> dict:
    """解 token，返回完整 payload（含可选 `se`）。

    `sub` / `pv` 仍是硬性要求：没有 `pv` 的旧 token 一律无效（生产尚未上线，
    不保留兼容）。`se` 缺失时补 0 —— 这是给已签发 token 的兼容路径。
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
    se = data.get("se", 0)
    if isinstance(se, bool) or not isinstance(se, int) or se < 0:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            detail="令牌无效或已过期")
    data["se"] = se
    return data


def decode_token(token: str) -> tuple[str, str]:
    """解 token，返回 (handle, pv)。保留旧签名，供调用方渐进迁移。"""
    data = decode_token_payload(token)
    return data["sub"], data["pv"]


# ── refresh / handoff：只存 hash，原文只回客户端一次 ─────────────────────────
def hash_secret(raw: str) -> str:
    """一次性凭据（refresh / handoff）落库前的摘要。"""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def new_handoff_code() -> str:
    return secrets.token_urlsafe(32)

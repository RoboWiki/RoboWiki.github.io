"""内容安全：微信小程序文本安全接口（msgSecCheck）。

原则：**安全校验是增强，不是主流程的硬依赖**。
  · 没配 AppID/Secret，或当前用户没有微信身份（拿不到 openid）→ 记录一次并放行；
  · 微信接口超时 / 报错 → 记日志、短暂冷却后放行，绝不让发评论卡死；
  · 真的判定违规（suggest != pass）→ 返回 `passed=False`，调用方决定
    （wiki 评论落 pending 待复核，社区评论直接 422）。

msgSecCheck 要求 openid 必须来自最近登录过的小程序用户，所以只能对
绑定了微信身份的用户检查；网页/邮箱用户走人工举报 + 站务处置。
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import httpx
from sqlmodel import Session, select

from .core.config import settings
from .models import Identity

log = logging.getLogger("robowiki.content_safety")

WECHAT_MINI = "wechat_mini"
#: msgSecCheck 单次 content 上限 2500 字；超长截断，不因长度整条拒收
MAX_CONTENT = 2500
#: access_token 提前 5 分钟过期，避开边界
_TOKEN_MARGIN_S = 300.0
#: 微信不可用时的冷却窗口：期间直接放行，避免每条评论都等一次超时
_FAIL_COOLDOWN_S = 60.0
#: 内容场景：2 = 评论
SCENE_COMMENT = 2


@dataclass(frozen=True)
class SafetyResult:
    """`checked=False` 表示没真调微信（未配置/冷却中），此时 `passed` 恒为 True。"""

    passed: bool
    checked: bool = False
    reason: str = ""


_lock = threading.Lock()
_token: tuple[str, float] = ("", 0.0)
_cooldown_until = 0.0
_warned_missing = False


def _credentials() -> tuple[str, str]:
    return ((settings.wechat_mp_appid or "").strip(),
            (settings.wechat_mp_secret or "").strip())


def _invalidate_token() -> None:
    global _token
    with _lock:
        _token = ("", 0.0)


def _access_token(appid: str, secret: str) -> str | None:
    """进程内缓存 access_token；拿不到返回 None（调用方按失败处理并放行）。"""
    now = time.time()
    with _lock:
        value, expires = _token
        if value and now < expires:
            return value

    url = f"{settings.wechat_api_base.rstrip('/')}/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": appid, "secret": secret}
    with httpx.Client(timeout=settings.wechat_timeout_s) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json() or {}

    token = (data.get("access_token") or "").strip()
    if not token:
        log.warning("wechat access_token missing: errcode=%s", data.get("errcode"))
        return None
    ttl = float(data.get("expires_in") or 7200)
    with _lock:
        _token = (token, time.time() + max(60.0, ttl - _TOKEN_MARGIN_S))
    return token


def _missing(reason: str) -> SafetyResult:
    global _warned_missing
    if not _warned_missing:
        log.info("内容安全检查未启用（%s），本次直接放行；后续不再提示", reason)
        _warned_missing = True
    return SafetyResult(True)


def check_text(text: str, openid: str | None = None) -> SafetyResult:
    """检查一段用户文本。永不抛异常：失败即放行，原因只进日志。"""
    global _cooldown_until

    content = (text or "").strip()
    if not content:
        return SafetyResult(True)
    if not settings.content_check_enabled:
        return _missing("content_check_enabled=false")

    appid, secret = _credentials()
    openid = (openid or "").strip()
    if not appid or not secret:
        return _missing("缺 AppID/Secret")
    if not openid:
        return _missing("当前用户没有微信 openid")

    if time.time() < _cooldown_until:
        return SafetyResult(True)

    url = f"{settings.wechat_api_base.rstrip('/')}/wxa/msg_sec_check"
    payload = {"content": content[:MAX_CONTENT], "version": 2,
               "scene": SCENE_COMMENT, "openid": openid}
    try:
        with httpx.Client(timeout=settings.wechat_timeout_s) as client:
            errcode = -1
            data: dict = {}
            for attempt in range(2):
                token = _access_token(appid, secret)
                if not token:
                    raise RuntimeError("access_token unavailable")
                resp = client.post(url, params={"access_token": token}, json=payload)
                resp.raise_for_status()
                data = resp.json() or {}
                errcode = int(data.get("errcode") or 0)
                # token 过期/失效：清缓存重试一次
                if errcode in (40001, 42001) and attempt == 0:
                    _invalidate_token()
                    continue
                break

        if errcode == 87014:                    # 旧版「内容含有违法违规内容」
            return SafetyResult(False, checked=True, reason="risky")
        if errcode != 0:
            raise RuntimeError(f"msgSecCheck errcode={errcode}")
        suggest = str((data.get("result") or {}).get("suggest") or "").lower()
        return SafetyResult(suggest in ("", "pass"), checked=True,
                            reason=suggest or "pass")
    except Exception as exc:                    # 网络 / 解析 / 微信错误
        _cooldown_until = time.time() + _FAIL_COOLDOWN_S
        log.warning("msgSecCheck 调用失败，放行本次内容（%ss 内不再尝试）：%s",
                    int(_FAIL_COOLDOWN_S), type(exc).__name__)
        return SafetyResult(True)


def openid_for(db: Session, user_id: int | None) -> str | None:
    """当前账号绑定的微信 openid；没有则 None（网页用户不做机器检查）。"""
    if not user_id:
        return None
    row = db.exec(select(Identity).where(
        Identity.user_id == user_id,
        Identity.provider == WECHAT_MINI)).first()
    return row.subject if row is not None else None


def check_user_text(db: Session, user_id: int | None, text: str) -> SafetyResult:
    """路由层入口：先看配置，再按账号取 openid。未配置时不查 identities。"""
    appid, secret = _credentials()
    if not settings.content_check_enabled or not appid or not secret:
        return check_text(text)
    return check_text(text, openid=openid_for(db, user_id))

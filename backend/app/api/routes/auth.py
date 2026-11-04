"""认证：注册 / 登录 / 我是谁 / 第三方身份。

口令登录与第三方登录**共用同一套令牌**：`sub`（handle）+ `pv`（口令哈希指纹）。
第三方渠道只在「怎么证明你是你」这一段不同，之后签出来的 JWT 完全一样，
所以社区、投稿、评分那些接口一行都不用改。
"""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
import warnings
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ...core.config import settings
from ...core.security import (create_token, dummy_password_hash, hash_password,
                              unusable_password_hash, verify_password)
from ...crud import user_out
from ...mailer import MailError, send_email
from ...models import EmailToken, Identity, User
from ...schemas import (AccountOut, ForgotIn, IdentityOut, LoginIn,
                        PasswordChangeIn, ProvidersOut, RegisterIn,
                        ResetPasswordIn, TokenOut, VerifyEmailIn, WechatMiniIn)
from ..deps import CurrentUser, Db, rate_limit

# OAuth/OIDC 的协议细节（授权码、state、PKCE）全部交给 Authlib。
# 未安装时不能让整个应用起不来：降级成「该渠道 503」。
try:  # pragma: no cover - 分支取决于环境里是否装了 authlib
    with warnings.catch_warnings():
        # authlib 在 import 时会给自己装一个 "always" 过滤器并提示内部 httpx
        # 适配层改名；两件事都与我们无关，先压掉再真正 import，免得每次启动
        # 都在日志里刷一段 DeprecationWarning。
        warnings.simplefilter("ignore")
        import authlib.deprecate  # noqa: F401
        warnings.simplefilter("ignore")
        from authlib.integrations.starlette_client import OAuth, OAuthError
    _AUTHLIB_ERROR: tuple[type[BaseException], ...] = (OAuthError,)
except ImportError:  # pragma: no cover
    OAuth = None  # type: ignore[assignment]
    _AUTHLIB_ERROR = ()

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("robowiki.auth")

#: 注册失败统一话术。邮箱冲突不再单独报错，否则注册接口就是枚举器。
_REGISTER_FAILED = "注册未完成，请检查邮箱或稍后再试"


def _account_out(db: Session, u: User) -> AccountOut:
    """UserOut（公开资料）+ 仅本人可见的邮箱 / 口令状态。"""
    base = user_out(db, u)
    return AccountOut(**base.model_dump(), email=u.email,
                      password_set=u.password_set)


@router.get("/providers", response_model=ProvidersOut)
def providers():
    """公开：当前服务端实际可用的登录渠道。

    前端先问这里再决定要不要渲染 GitHub 按钮 —— 未配置的渠道不发请求，
    避免点一下只拿到 503。`email` 始终可用（口令注册/登录是本站基线）。
    """
    return ProvidersOut(
        email=True,
        # authlib 未安装时 _github_client() 也会 503，这里必须同口径
        github=bool(OAuth is not None and settings.github_oauth_enabled),
        wechat_mini=settings.wechat_mini_enabled,
    )


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, request: Request, db: Db):
    rate_limit(request, "register", 20)
    if db.exec(select(User).where(User.handle == payload.handle)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "这个 handle 已被占用")
    if payload.email and db.exec(select(User).where(User.email == payload.email)).first():
        # 内部照样拦住重复创建，但对外只说「没注册成功」——不能变成邮箱枚举接口
        raise HTTPException(status.HTTP_400_BAD_REQUEST, _REGISTER_FAILED)

    u = User(handle=payload.handle, display_name=payload.display_name,
             email=payload.email, password_hash=hash_password(payload.password),
             avatar_hue=abs(hash(payload.handle)) % 360)
    db.add(u)
    db.commit()
    db.refresh(u)
    return TokenOut(access_token=create_token(u.handle, u.password_hash,
                                              scopes=("password",)),
                    user=_account_out(db, u))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Db):
    rate_limit(request, "login", 30)
    u = db.exec(select(User).where(User.handle == payload.handle.lower())).first()
    # 用户不存在时也拿固定的哑哈希跑一次 PBKDF2：否则「先查库、有才哈希」
    # 会让响应时长差出一个数量级，等于把账号是否存在送出去。
    stored = u.password_hash if u is not None else dummy_password_hash()
    ok = verify_password(payload.password, stored)
    if u is None or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号或密码不对")
    return TokenOut(access_token=create_token(u.handle, u.password_hash,
                                              scopes=("password",)),
                    user=_account_out(db, u))


@router.get("/me", response_model=AccountOut)
def me(user: CurrentUser, db: Db):
    return _account_out(db, user)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _issue(db: Db, user: User, purpose: str) -> str:
    now = datetime.now(timezone.utc)
    for old in db.exec(select(EmailToken).where(
            EmailToken.user_id == user.id, EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None))).all():
        old.used_at = now
        db.add(old)
    raw = secrets.token_urlsafe(32)
    db.add(EmailToken(user_id=user.id, purpose=purpose, token_hash=_hash(raw),
                      expires_at=now + timedelta(minutes=settings.email_token_minutes)))
    db.commit()
    return raw


def _consume(db: Db, raw: str, purpose: str) -> User:
    now = datetime.now(timezone.utc)
    row = db.exec(select(EmailToken).where(
        EmailToken.token_hash == _hash(raw), EmailToken.purpose == purpose,
        EmailToken.used_at.is_(None), EmailToken.expires_at > now)).first()
    if row is None:
        raise HTTPException(400, "链接/令牌无效或已过期")
    row.used_at = now
    db.add(row)
    db.commit()
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(400, "用户不存在")
    return user


@router.post("/email/verify/request")
def request_email_verify(request: Request, user: CurrentUser, db: Db):
    rate_limit(request, "email-verify", 10, user.id)
    if not user.email:
        raise HTTPException(422, "账号未填写邮箱")
    if user.email_verified:
        return {"ok": True, "email_verified": True}
    raw = _issue(db, user, "verify")
    try:
        send_email(user.email, "RoboWiki 邮箱验证",
                   f"验证令牌：{raw}\n"
                   f"有效期 {settings.email_token_minutes} 分钟。\n"
                   "在站点登录后打开「验证邮箱」输入该令牌即可。")
    except MailError as exc:
        # 已登录用户不必用「没发出去也回 200」防枚举：直接告诉他是发信环节坏了，
        # 令牌行仍有效，修好 SMTP 后重发即可（重发会作废旧令牌）。
        log.error("verify email failed user=%s: %s", user.handle, exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "验证邮件发送失败，请稍后再试") from exc
    return {"ok": True, "email_verified": False}


@router.post("/email/verify", response_model=AccountOut)
def verify_email(payload: VerifyEmailIn, db: Db):
    user = _consume(db, payload.token, "verify")
    user.email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return _account_out(db, user)


@router.post("/password/forgot", status_code=202)
def forgot_password(payload: ForgotIn, request: Request, db: Db):
    rate_limit(request, "password-forgot", 10)
    u = db.exec(select(User).where(User.email == payload.email.strip())).first()
    if u is not None:
        raw = _issue(db, u, "reset")
        try:
            send_email(u.email or "", "RoboWiki 重置密码",
                       f"重置令牌：{raw}\n"
                       f"有效期 {settings.email_token_minutes} 分钟。\n"
                       "在登录框选择「找回密码」并输入该令牌与新密码。")
        except MailError as exc:
            # 这个接口对「邮箱是否存在」必须保持同一个响应（202），所以发信失败
            # 只能记日志，不能改成 503 —— 否则 503/202 本身就是枚举信号。
            log.error("reset email failed user=%s: %s", u.handle, exc)
    # 不暴露邮箱是否存在
    return {"ok": True, "message": "如果该邮箱已注册，重置邮件已发送"}


@router.post("/password/reset")
def reset_password(payload: ResetPasswordIn, db: Db):
    user = _consume(db, payload.token, "reset")
    user.password_hash = hash_password(payload.password)
    # 找回密码 = 账号重新拥有可用口令；第三方登录建出来的账号从此也能口令登录
    user.password_set = True
    db.add(user)
    for t in db.exec(select(EmailToken).where(
            EmailToken.user_id == user.id, EmailToken.used_at.is_(None))).all():
        t.used_at = datetime.now(timezone.utc)
        db.add(t)
    db.commit()
    return {"ok": True}


@router.post("/password/change", response_model=TokenOut)
def change_password(payload: PasswordChangeIn, request: Request,
                    user: CurrentUser, db: Db):
    """改密：验当前口令 → 写新哈希 → **当场签发新 token**。

    旧 token 的 `pv` 绑定的是旧哈希，改完立刻失效；而调用方此刻明明
    已经通过验证，不该被自己的改密操作踢下线，所以响应里直接给新 token，
    前端换掉本地存储即可继续用（其他设备上的旧 token 仍然全部失效）。
    """
    rate_limit(request, "password-change", 20, user.id)
    # 统一跑一次 PBKDF2 再判结果，失败原因只有一种话术：不区分
    # 「口令没设过」和「当前密码填错」，也不回显任何账号字段。
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "当前密码不正确")

    user.password_hash = hash_password(payload.new_password)
    # 改密成功即代表这个账号有一条自己知道的口令（第三方建号也可以借此设口令）
    user.password_set = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_token(user.handle, user.password_hash,
                                  scopes=("password",)),
        user=_account_out(db, user))


# ══ 第三方身份 ═══════════════════════════════════════════════════════════════
# 统一流程（对所有渠道都一样）：
#   拿到 (provider, subject) → 找/建 Identity → 找到 user → 签现有 JWT
# 渠道差异只被压缩成「怎么拿到 (provider, subject)」这一段：
#   · GitHub —— Authlib 跑授权码 + state（协议细节不手写）
#   · 小程序 —— wx.login() 的 code 换 openid（AppSecret 只在后端）
PROVIDER_GITHUB = "github"
PROVIDER_WECHAT_MINI = "wechat_mini"


# ── GitHub（Authlib OAuth2）─────────────────────────────────────────────────
#: 已注册的 Authlib 注册表；按 (client_id, secret) 指纹缓存，测试换配置会重建
_oauth_registry = None
_oauth_fingerprint: tuple[str, str] | None = None


def _github_client():
    """已注册的 GitHub OAuth 客户端；未配置时 503（本地开发不受影响）。"""
    if OAuth is None:  # pragma: no cover - requirements 里已有 authlib
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "GitHub 登录未启用（服务端缺少 authlib）")
    if not settings.github_oauth_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "GitHub 登录未配置")
    cid = (settings.github_client_id or "").strip()
    secret = (settings.github_client_secret or "").strip()
    global _oauth_registry, _oauth_fingerprint
    if _oauth_registry is None or _oauth_fingerprint != (cid, secret):
        oauth = OAuth()
        oauth.register(
            name=PROVIDER_GITHUB,
            client_id=cid,
            client_secret=secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            # S256 PKCE 也交给 Authlib：它生成 challenge、回调时带 verifier
            client_kwargs={"scope": settings.github_oauth_scope,
                           "code_challenge_method": "S256"},
        )
        _oauth_registry, _oauth_fingerprint = oauth, (cid, secret)
    return _oauth_registry.github


def _github_redirect_uri(request: Request) -> str:
    """回调地址。反代后 request 的 host 可能是内网地址，可用 env 覆盖。"""
    base = (settings.oauth_redirect_base or "").strip()
    if base:
        return f"{base.rstrip('/')}{settings.api_v1}/auth/github/callback"
    return str(request.url_for("github_callback"))


async def _github_exchange(request: Request, client) -> dict:
    """code → token。Authlib 在这层校验 state（并负责 PKCE）。"""
    return await client.authorize_access_token(request)


async def _github_profile(client, token: dict) -> dict:
    """取 /user 与 /user/emails，归一成身份抽象要的字段。

    `subject` 用 GitHub 的数字 id：login 可以改，id 不会变。
    """
    resp = await client.get("user", token=token)
    resp.raise_for_status()
    profile = resp.json() or {}
    email = profile.get("email")
    # GitHub 上能公开展示的邮箱必然是已验证的；私有邮箱走 /user/emails 再挑
    email_verified = bool(email)
    if not email:
        rows: list[dict] = []
        try:
            eresp = await client.get("user/emails", token=token)
            eresp.raise_for_status()
            payload = eresp.json() or []
            rows = payload if isinstance(payload, list) else []
        except httpx.HTTPError:
            # 授权时没拿到 user:email（用户改过授权范围）：当一个没邮箱的账号，
            # 不该因此登不进来。并号能力降级，但登录照常。
            rows = []
        chosen = (next((r for r in rows if r.get("primary") and r.get("verified")), None)
                  or next((r for r in rows if r.get("verified")), None))
        if chosen:
            email, email_verified = chosen.get("email"), True
    return {
        "subject": "" if profile.get("id") is None else str(profile["id"]),
        "login": profile.get("login") or "",
        "name": profile.get("name") or "",
        "email": email,
        "email_verified": email_verified,
        # 只留资料快照：access_token 是凭据，不落库
        "raw": {k: profile.get(k) for k in
                ("id", "login", "name", "avatar_url", "html_url", "company",
                 "blog", "location", "created_at", "email")},
    }


@router.get("/github/login", name="github_login")
async def github_login(request: Request):
    """跳到 GitHub 授权页。state 由 Authlib 写进签名 cookie。"""
    client = _github_client()          # 未配置 → 503
    rate_limit(request, "oauth-login", 30)
    return await client.authorize_redirect(request, _github_redirect_uri(request))


@router.get("/github/callback")
async def github_callback(request: Request, db: Db):
    """回调：换 token → 取资料 → 找/建用户 → 签 JWT → 回登录页。

    `Accept: application/json` 时直接返回 TokenOut（给 H5/小程序自己处理跳转）；
    否则 302 回 `settings.site_url/login#token=<jwt>`。放 fragment 而不是
    query，是因为 fragment 不会发给服务器，也就不会进反代访问日志。
    """
    client = _github_client()          # 未配置 → 503
    rate_limit(request, "oauth-callback", 60)
    try:
        token = await _github_exchange(request, client)
        info = await _github_profile(client, token)
    except _AUTHLIB_ERROR as exc:      # state 不匹配 / 用户取消 / code 已用过
        log.warning("github oauth rejected: %s", type(exc).__name__)
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "GitHub 授权未完成，请重新登录") from exc
    except httpx.HTTPError as exc:
        log.warning("github profile fetch failed: %s", type(exc).__name__)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "GitHub 暂时不可用，请稍后再试") from exc

    subject = (info.get("subject") or "").strip()
    if not subject:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "GitHub 返回的资料不完整")
    login = (info.get("login") or "").strip()
    user = _user_for_identity(
        db, provider=PROVIDER_GITHUB, subject=subject,
        email=info.get("email"), email_verified=bool(info.get("email_verified")),
        display_name=(info.get("name") or "").strip() or None,
        handle_hint=_slug(login or subject, prefix="gh-"),
        raw=info.get("raw") or {},
    )
    access = create_token(user.handle, user.password_hash,
                          scopes=(PROVIDER_GITHUB,))
    if _wants_json(request):
        return JSONResponse(
            TokenOut(access_token=access, user=_account_out(db, user))
            .model_dump(mode="json"))
    return RedirectResponse(_login_redirect(access),
                            status_code=status.HTTP_302_FOUND)


# ── 微信小程序（jscode2session）──────────────────────────────────────────────
async def _wechat_code2session(code: str) -> dict:
    """code → openid。AppSecret 只在这里出现，绝不回传给客户端。"""
    params = {
        "appid": (settings.wechat_mp_appid or "").strip(),
        "secret": (settings.wechat_mp_secret or "").strip(),
        "js_code": code,
        "grant_type": "authorization_code",
    }
    url = f"{settings.wechat_api_base.rstrip('/')}/sns/jscode2session"
    async with httpx.AsyncClient(timeout=settings.wechat_timeout_s) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json() or {}


@router.post("/wechat/mini", response_model=TokenOut)
async def wechat_mini(payload: WechatMiniIn, request: Request, db: Db):
    """小程序登录：`wx.login()` 拿到的 code 换 openid，之后与口令登录等价。"""
    if not settings.wechat_mini_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "微信小程序登录未配置")
    rate_limit(request, "wechat-mini", 60)
    try:
        data = await _wechat_code2session(payload.code)
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("wechat jscode2session failed: %s", type(exc).__name__)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "微信登录服务暂不可用，请稍后再试") from exc

    openid = (data.get("openid") or "").strip()
    if not openid:
        # code 无效 / 已用过 / AppID 不匹配：errcode 40029、40163、41008 …
        log.warning("wechat login rejected: errcode=%s", data.get("errcode"))
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "微信登录失败，请重新进入小程序")

    unionid = (data.get("unionid") or "").strip()
    nickname = (payload.nickname or "").strip() or None
    user = _user_for_identity(
        db, provider=PROVIDER_WECHAT_MINI, subject=openid,
        email=None, email_verified=False, display_name=nickname,
        # handle 里不放 openid 原文：它是能跨会话认出人的标识
        handle_hint=_slug(f"wx-{hashlib.sha256(openid.encode()).hexdigest()[:10]}"),
        # session_key 是解密用户资料的密钥，不落库
        raw={"unionid": unionid} if unionid else {},
    )
    return TokenOut(
        access_token=create_token(user.handle, user.password_hash,
                                  scopes=(PROVIDER_WECHAT_MINI,)),
        user=_account_out(db, user))


# ── 身份管理 ────────────────────────────────────────────────────────────────
@router.get("/identities", response_model=list[IdentityOut])
def list_identities(user: CurrentUser, db: Db):
    """当前账号已绑定的第三方身份。"""
    rows = db.exec(select(Identity).where(Identity.user_id == user.id)
                   .order_by(Identity.created_at, Identity.id)).all()
    return [IdentityOut(provider=r.provider, subject=r.subject,
                        email=r.email, created_at=r.created_at) for r in rows]


@router.delete("/identities/{provider}")
def unbind_identity(provider: str, user: CurrentUser, db: Db):
    """解绑一个身份，但**不能把账号锁死**：至少留一种登录方式。"""
    rows = db.exec(select(Identity).where(Identity.user_id == user.id)).all()
    target = next((r for r in rows if r.provider == provider), None)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "未绑定该身份")
    remaining = len(rows) - 1
    if not _has_other_way_in(user, remaining):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "这是当前唯一的登录方式，请先用备份邮箱找回密码设置口令，或再绑定一个身份")
    db.delete(target)
    db.commit()
    return {"ok": True, "provider": provider, "remaining": remaining}


def _has_other_way_in(user: User, remaining_identities: int) -> bool:
    """解绑后还能不能进来：另一种身份，或一个用户自己知道的口令。

    **不算**「有已验证邮箱」：OAuth 给的邮箱可能是不收信的 noreply 地址
    （GitHub 私有邮箱就是 `123+user@users.noreply.github.com`），
    把它当退路等于给了一个假的出口。真要留退路，先用找回密码设一个口令。
    """
    return remaining_identities > 0 or user.password_set


# ── 身份抽象的内部实现 ──────────────────────────────────────────────────────
_BAD_HANDLE_CHARS = re.compile(r"[^a-z0-9_-]+")


def _slug(raw: str, *, prefix: str = "") -> str:
    """把提供方的 login/昵称压成合法 handle 前缀（2–24 位，字母数字开头）。"""
    s = _BAD_HANDLE_CHARS.sub("-", (raw or "").lower()).strip("-_")
    if prefix:
        s = f"{prefix}{s}" if s else prefix.rstrip("-_")
    if not s or not s[0].isalnum():
        s = f"u{s}"
    return s[:16].rstrip("-_") or "user"


def _claim_handle(db: Session, base: str) -> str:
    """handle 全局唯一且公开。撞了就加随机后缀，不覆盖任何人。"""
    candidate = base[:24]
    if db.exec(select(User).where(User.handle == candidate)).first() is None:
        return candidate
    for _ in range(8):
        candidate = f"{base[:16]}-{secrets.token_hex(3)}"
        if db.exec(select(User).where(User.handle == candidate)).first() is None:
            return candidate
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                        "账号标识分配失败，请稍后再试")


def _user_for_identity(db: Session, *, provider: str, subject: str,
                       email: str | None, email_verified: bool,
                       display_name: str | None, handle_hint: str,
                       raw: dict) -> User:
    """(provider, subject) → User。找不到就建，找到就复用。

    并号规则只认**提供方已验证**的邮箱：未验证邮箱并入已有账号等于
    「我先用你的邮箱注册，你再用 GitHub 一登就进了我的账号」。
    """
    ident = db.exec(select(Identity).where(Identity.provider == provider,
                                          Identity.subject == subject)).first()
    if ident is not None:
        user = db.get(User, ident.user_id)
        if user is not None:
            # 资料快照随时更新；handle / display_name 属于用户，不覆盖
            if email and not ident.email:
                ident.email = email
            ident.raw = raw
            db.add(ident)
            db.commit()
            return user
        # 身份还在、用户没了（手工删库）：清掉残行，按首次登录重建
        db.delete(ident)
        db.commit()

    user = None
    if email and email_verified:
        user = db.exec(select(User).where(User.email == email)).first()
        if user is not None and not user.email_verified:
            # 提供方已经证明这个邮箱归他所有；顺手把本站的「已验证」补上
            user.email_verified = True
            db.add(user)
            db.commit()

    if user is None:
        handle = _claim_handle(db, handle_hint)
        safe_email = email
        if email and not email_verified and \
                db.exec(select(User).where(User.email == email)).first() is not None:
            safe_email = None      # 未验证邮箱不能占用别人已注册的邮箱
        user = User(
            handle=handle,
            display_name=(display_name or handle)[:32],
            email=safe_email,
            email_verified=bool(safe_email and email_verified),
            # 没人知道这串口令：账号只能靠已绑定的身份进来
            password_hash=unusable_password_hash(),
            password_set=False,
            avatar_hue=abs(hash(handle)) % 360,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            # 并发首次登录：handle/email 被别人抢先建了，回滚后按邮箱取回
            db.rollback()
            user = (db.exec(select(User).where(User.email == email)).first()
                    if email else None)
            if user is None:
                raise
        else:
            db.refresh(user)

    ident = Identity(user_id=user.id, provider=provider, subject=subject,
                     email=email, raw=raw)
    db.add(ident)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()      # 并发回调：别人已经绑上了，重查即可
        ident = db.exec(select(Identity).where(Identity.provider == provider,
                                              Identity.subject == subject)).first()
        if ident is None:
            raise
    return user


def _wants_json(request: Request) -> bool:
    return "application/json" in (request.headers.get("accept") or "").lower()


def _login_redirect(token: str) -> str:
    return f"{settings.site_url.rstrip('/')}/login#token={token}"

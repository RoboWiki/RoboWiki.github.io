"""认证：注册 / 登录 / 我是谁 / 第三方身份。

口令登录与第三方登录**共用同一套令牌**：`sub`（handle）+ `pv`（口令哈希指纹）。
第三方渠道只在「怎么证明你是你」这一段不同，之后签出来的 JWT 完全一样，
所以社区、投稿、评分那些接口一行都不用改。
"""
from __future__ import annotations

import base64
import hashlib
import logging
import re
import secrets
import time
import warnings
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ...core.config import settings
from ...core.security import (create_token, dummy_password_hash, hash_password,
                              hash_secret, new_handoff_code, new_refresh_token,
                              unusable_password_hash, verify_password)
from ...crud import posts_out, user_out
from ...email_templates import render_email
from ...mailer import MailError, enqueue_email, send_email
from ...models import (Comment, EmailToken, HandoffCode, Identity, LoginTicket, Part,
                       Post, Rating, RefreshToken, Submission, User, UserBan)
from ...schemas import (AccountExportOut, AccountOut, AccountUpdateIn,
                        CommentExportOut, EmailChangeConfirmIn, EmailChangeIn,
                        ForgotIn, HandleIn, HandoffIn, IdentityOut, LoginIn, LogoutIn,
                        PasswordChangeIn, PasswordSetIn, ProvidersOut,
                        QrConfirmIn, QrCreateOut, QrStatusOut,
                        RatingExportOut, RefreshIn, RegisterIn, ResetPasswordIn,
                        SessionOut, SubmissionExportOut, TokenOut,
                        VerifyEmailIn, WechatMiniIn)
from ..deps import CurrentUser, Db, MaybeUser, rate_limit

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
    from ...trust import trust_level, trust_sources
    return AccountOut(**base.model_dump(), email=u.email,
                      password_set=u.password_set,
                      email_notify=u.email_notify,
                      trust_level=trust_level(db, u),
                      trust_sources=trust_sources(db, u),
                      handle_provisional=bool(u.handle_provisional))


def _queue_security_mail(db: Session, user: User, title: str, body: str) -> None:
    """安全事件邮件进 outbox：不阻塞请求，失败由 worker 重试。"""
    if not user.email or not user.email_verified:
        return
    subject, text, html = render_email(
        "security", subject=f"RoboWiki {title}", title=title, body=body)
    enqueue_email(db, to=user.email, subject=subject, text=text, html=html,
                  kind="security", user_id=user.id,
                  dedupe_key=f"security:{user.id}:{title}:{int(datetime.now().timestamp())}")
    db.commit()


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
    email = payload.email.strip().lower() if payload.email else None
    if db.exec(select(User).where(User.handle == payload.handle)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "这个 handle 已被占用")
    if email and db.exec(select(User).where(User.email == email)).first():
        # 内部照样拦住重复创建，但对外只说「没注册成功」——不能变成邮箱枚举接口。
        # 先跑一次同成本的哑哈希，避免「邮箱已存在」分支明显更快。
        verify_password(payload.password, dummy_password_hash())
        raise HTTPException(status.HTTP_400_BAD_REQUEST, _REGISTER_FAILED)

    nickname = (payload.display_name or "").strip() or payload.handle
    u = User(handle=payload.handle, display_name=nickname,
             email=email, password_hash=hash_password(payload.password),
             avatar_hue=abs(hash(payload.handle)) % 360)
    db.add(u)
    db.commit()
    db.refresh(u)

    # 注册即发验证邮件；发信失败不影响建号（邮箱账号仍可读，写入要等验证）。
    if email:
        try:
            raw = _issue(db, u, "verify")
            subject, text, html = render_email("verify", token=raw)
            send_email(email, subject, text, html)
        except Exception as exc:  # noqa: BLE001 — 邮件通道异常不能阻断注册
            log.warning("register verify mail failed: %s", type(exc).__name__)

    return _issue_session(db, u, request, scopes=("password",))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Db):
    rate_limit(request, "login", 30)
    ident = payload.handle.strip().lower()
    # 账号或邮箱都能登录：老用户不用记 handle，邮箱注册的账号也符合直觉。
    u = db.exec(select(User).where(
        (User.handle == ident) | (User.email == ident))).first()
    # 用户不存在时也拿固定的哑哈希跑一次 PBKDF2：否则「先查库、有才哈希」
    # 会让响应时长差出一个数量级，等于把账号是否存在送出去。
    stored = u.password_hash if u is not None else dummy_password_hash()
    ok = verify_password(payload.password, stored)
    if u is None or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号或密码不对")
    return _issue_session(db, u, request, scopes=("password",))


@router.get("/me", response_model=AccountOut)
def me(user: CurrentUser, db: Db):
    return _account_out(db, user)


@router.patch("/me", response_model=AccountOut)
def update_me(payload: AccountUpdateIn, request: Request, user: CurrentUser, db: Db):
    """本人编辑公开资料。邮箱与登录身份不在这里改，避免绕过验证。"""
    rate_limit(request, "profile-update", 30, user.id)
    data = payload.model_dump(exclude_unset=True)
    if "display_name" in data:
        name = (data["display_name"] or "").strip()
        if not name:
            raise HTTPException(422, "昵称不能为空")
        user.display_name = name
    if "bio" in data:
        user.bio = (data["bio"] or "").strip()
    if "avatar_hue" in data and data["avatar_hue"] is not None:
        user.avatar_hue = int(data["avatar_hue"])
    if "avatar_url" in data:
        # 已由 AccountUpdateIn 归一化：None / /media/... / http(s)
        user.avatar_url = data["avatar_url"]
    if "email_notify" in data and data["email_notify"] is not None:
        user.email_notify = bool(data["email_notify"])
    db.add(user)
    db.commit()
    db.refresh(user)
    return _account_out(db, user)


@router.patch("/handle", response_model=TokenOut)
def change_handle(payload: HandleIn, request: Request,
                  user: CurrentUser, db: Db):
    """把第三方首登生成的临时账号名改成自己的，只允许一次。

    JWT 的 subject 是 handle，改名后旧令牌自然失效；这里主动换一对新令牌，
    并吊销旧 refresh，客户端直接用返回值替换本地会话即可。
    """
    if not user.handle_provisional:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "账号名已经确定，不能再修改")
    new_handle = payload.handle
    if new_handle != user.handle:
        exists = db.exec(select(User).where(User.handle == new_handle,
                                            User.id != user.id)).first()
        if exists is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "账号名已被占用")
        user.handle = new_handle
    user.handle_provisional = False
    db.add(user)
    db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).values(revoked_at=_utcnow()))
    db.commit()
    db.refresh(user)
    return _issue_session(db, user, request)


@router.get("/export", response_model=AccountExportOut)
def export_account(user: CurrentUser, db: Db):
    """「我的数据可带走」：本人帖子 / 评论 / 评分 / 目录提案。

    只按 `user.id` 取自己的行，不含口令哈希、refresh token、一次性令牌；
    `user` 用 AccountOut（含邮箱与 email_notify），因为这就是导出给本人的。
    """
    posts = db.exec(select(Post).where(Post.author_id == user.id)
                    .order_by(Post.created_at)).all()
    comments = db.exec(select(Comment).where(Comment.author_id == user.id)
                       .order_by(Comment.created_at)).all()
    ratings = db.exec(select(Rating).where(Rating.user_id == user.id)
                      .order_by(Rating.created_at)).all()
    submissions = db.exec(select(Submission).where(
        Submission.submitter_id == user.id).order_by(Submission.created_at)).all()

    part_ids = {r.part_id for r in ratings}
    parts: dict[str, str] = {}
    if part_ids:
        for pid, title in db.exec(
                select(Part.id, Part.title).where(Part.id.in_(part_ids))).all():
            parts[pid] = title

    return AccountExportOut(
        user=_account_out(db, user),
        posts=posts_out(db, list(posts), user.id),
        comments=[CommentExportOut(
            id=c.id or 0, post_id=c.post_id, parent_id=c.parent_id,
            body=c.body, score=c.score, hidden=c.hidden,
            created_at=c.created_at) for c in comments],
        ratings=[RatingExportOut(
            part_id=r.part_id, part_title=parts.get(r.part_id), score=r.score,
            own_hardware=r.own_hardware, usage_level=r.usage_level,
            reason_tags=[t for t in (r.reason_tags or "").split(",") if t],
            note=r.note, created_at=r.created_at,
            updated_at=r.updated_at) for r in ratings],
        submissions=[SubmissionExportOut(
            id=s.id or 0, kind=s.kind, target_id=s.target_id,
            payload=s.payload, evidence=s.evidence, status=s.status,
            revision=s.revision, created_at=s.created_at,
            updated_at=s.updated_at) for s in submissions],
    )


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


# ── 会话：access 短寿命 + refresh 轮换 ───────────────────────────────────────
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _client_label(request: Request) -> str:
    """会话列表里显示的来源。优先显式 X-Client（console/mirror/mini）。"""
    raw = (request.headers.get("x-client") or "").strip().lower()
    if raw:
        cleaned = re.sub(r"[^a-z0-9_-]+", "-", raw)[:24].strip("-")
        if cleaned:
            return cleaned
    host = urlparse(request.headers.get("origin") or "").netloc.lower()
    return host[:32] or "web"


def _issue_session(db: Session, user: User, request: Request, *,
                   scopes: tuple[str, ...] | None = None,
                   family: str | None = None,
                   client: str | None = None) -> TokenOut:
    """签一对 access + refresh；登录 / 刷新 / handoff 全走这一条路。

    refresh 原文只在这里返回一次，库里只留 sha256。`family` 相同即同一条
    会话链；刷新时传旧 family，复用检测才能整链撤销。
    """
    # 封禁账号：登录 / 刷新 / handoff 都在这里被挡住（一条生效中的 UserBan）
    active_ban = db.exec(select(UserBan).where(
        UserBan.user_id == user.id, UserBan.lifted_at.is_(None))).first()
    if active_ban is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "该账号已被封禁，如有疑问请通过站内通知联系站务")

    raw_refresh = new_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_secret(raw_refresh),
        family=family or secrets.token_hex(16),
        client=(client or _client_label(request))[:32],
        expires_at=_utcnow() + timedelta(days=settings.refresh_token_days),
    ))
    db.commit()
    return TokenOut(
        access_token=create_token(user.handle, user.password_hash,
                                  scopes=scopes,
                                  session_epoch=int(user.session_epoch or 0)),
        refresh_token=raw_refresh,
        user=_account_out(db, user),
    )


def _revoke_family(db: Session, user_id: int, family: str) -> int:
    """撤销一条会话链（refresh 复用 / 单端登出）。返回受影响行数。"""
    result = db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.family == family,
        RefreshToken.revoked_at.is_(None),
    ).values(revoked_at=_utcnow()))
    db.commit()
    return result.rowcount or 0


def _revoke_all_sessions(db: Session, user_id: int) -> int:
    result = db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    ).values(revoked_at=_utcnow()))
    db.commit()
    return result.rowcount or 0


def _refresh_rejected() -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED,
                         "登录会话已失效，请重新登录",
                         headers={"WWW-Authenticate": "Bearer"})


@router.post("/refresh", response_model=TokenOut)
def refresh_session(payload: RefreshIn, request: Request, db: Db):
    """用 refresh 换新的一对 token。每次都轮换，旧值立刻作废。

    旧 refresh 被再次使用 = 它已落到第二个人手里 → 整条 family 撤销并 401。
    正常客户端只持有链末端，不会踩到这条分支。
    """
    rate_limit(request, "auth-refresh", 120)
    token_hash = hash_secret(payload.refresh_token)
    # 条件 UPDATE 保证「一次性」：并发两个请求只有一个能把 used_at 从 NULL 改掉。
    claimed = db.execute(update(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.used_at.is_(None),
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > _utcnow(),
    ).values(used_at=_utcnow()))
    if claimed.rowcount == 1:
        db.commit()
        row = db.exec(select(RefreshToken).where(
            RefreshToken.token_hash == token_hash)).first()
        user = db.get(User, row.user_id) if row is not None else None
        if user is None:
            raise _refresh_rejected()
        return _issue_session(db, user, request, family=row.family,
                             client=row.client)
    db.rollback()
    row = db.exec(select(RefreshToken).where(
        RefreshToken.token_hash == token_hash)).first()
    if row is not None and row.used_at is not None and row.revoked_at is None:
        # 复用：整条 family 作废，并自增 session_epoch，让窃取者手里尚未过期的
        # access 也立即失效（否则还能继续用 2 小时）。
        _revoke_family(db, row.user_id, row.family)
        user = db.get(User, row.user_id)
        if user is not None:
            user.session_epoch = int(user.session_epoch or 0) + 1
            db.add(user)
        db.commit()
    raise _refresh_rejected()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(user: CurrentUser, db: Db):
    """当前账号仍可用（未撤销、未轮换、未过期）的 refresh 会话。"""
    rows = db.exec(select(RefreshToken).where(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.used_at.is_(None),
        RefreshToken.expires_at > _utcnow(),
    ).order_by(RefreshToken.created_at.desc(), RefreshToken.id.desc())).all()
    return [SessionOut(id=r.id, client=r.client, created_at=r.created_at,
                       expires_at=r.expires_at) for r in rows]


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(session_id: int, user: CurrentUser, db: Db):
    """撤销自己的某个设备会话；当前 access 会自然到期，不强制全端下线。"""
    row = db.get(RefreshToken, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "会话不存在")
    if row.revoked_at is None:
        row.revoked_at = _utcnow()
        db.add(row)
        db.commit()
    return None


@router.post("/logout")
def logout(request: Request, user: CurrentUser, db: Db,
           payload: LogoutIn | None = None):
    """退出：带 refresh_token 撤销那条会话链，不带则撤销本账号全部 refresh。

    只动 refresh / access 的有效性由 pv + se 决定；`logout` 不 bump epoch，
    其他设备上的 access token 仍可用到自然过期。
    """
    rate_limit(request, "auth-logout", 60, user.id)
    token = (payload.refresh_token if payload else None) or ""
    if token:
        row = db.exec(select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.token_hash == hash_secret(token))).first()
        revoked = _revoke_family(db, user.id, row.family) if row else 0
    else:
        revoked = _revoke_all_sessions(db, user.id)
    return {"ok": True, "revoked": revoked}


@router.post("/logout-all")
def logout_all(request: Request, user: CurrentUser, db: Db):
    """全端退出：撤销所有 refresh，并自增 session_epoch 让所有 access 失效。"""
    rate_limit(request, "auth-logout-all", 30, user.id)
    revoked = _revoke_all_sessions(db, user.id)
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"ok": True, "revoked": revoked, "session_epoch": user.session_epoch}


# ── GitHub 回跳：一次性 handoff code ────────────────────────────────────────
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _allowed_return_origins() -> set[str]:
    """配置白名单 + site_url 自身。统一成 scheme://host[:port]。"""
    allowed = {o.strip().rstrip("/").lower()
               for o in settings.oauth_return_origins if o.strip()}
    site = urlparse(settings.site_url.strip())
    if site.scheme and site.netloc:
        allowed.add(f"{site.scheme}://{site.netloc.lower()}")
    return allowed


def _normalize_return_to(value: str | None) -> str | None:
    """`return_to` → 规范化 origin；未提供返回 None，非法抛 400。

    只接受纯 origin（不带 path / query / fragment）：拼接目标是
    `{origin}/login.html#code=...`，放路径进来等于开了开放重定向的口子。
    localhost / 127.0.0.1 允许任意端口（本地开发），其余必须精确命中白名单。
    """
    if value is None or not value.strip():
        return None
    parsed = urlparse(value.strip())
    try:
        parsed.port          # 越界/非数字端口会在这里抛 ValueError
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "return_to 不是合法的地址") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "return_to 不是合法的地址")
    if parsed.username or parsed.password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "return_to 不是合法的地址")
    if parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "return_to 只能是站点 origin，不能带路径")
    host = parsed.hostname.lower()
    origin = f"{parsed.scheme}://{parsed.netloc.lower()}"
    if host in _LOOPBACK_HOSTS:
        return origin
    if origin in _allowed_return_origins():
        return origin
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "return_to 不在白名单")


def _create_handoff(db: Session, user: User, return_to: str) -> str:
    raw = new_handoff_code()
    db.add(HandoffCode(
        user_id=user.id,
        code_hash=hash_secret(raw),
        return_to=return_to,
        expires_at=_utcnow() + timedelta(seconds=settings.handoff_seconds),
    ))
    db.commit()
    return raw


@router.post("/handoff", response_model=TokenOut)
def exchange_handoff(payload: HandoffIn, request: Request, db: Db):
    """一次性 code → TokenOut（60 秒有效，只能换一次）。"""
    rate_limit(request, "auth-handoff", 60)
    code_hash = hash_secret(payload.code)
    claimed = db.execute(update(HandoffCode).where(
        HandoffCode.code_hash == code_hash,
        HandoffCode.used_at.is_(None),
        HandoffCode.expires_at > _utcnow(),
    ).values(used_at=_utcnow()))
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "登录凭证无效或已过期")
    db.commit()
    row = db.exec(select(HandoffCode).where(
        HandoffCode.code_hash == code_hash)).first()
    user = db.get(User, row.user_id) if row is not None else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "登录凭证无效或已过期")
    return _issue_session(db, user, request)


def _issue(db: Db, user: User, purpose: str, meta: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    for old in db.exec(select(EmailToken).where(
            EmailToken.user_id == user.id, EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None))).all():
        old.used_at = now
        db.add(old)
    raw = secrets.token_urlsafe(32)
    db.add(EmailToken(user_id=user.id, purpose=purpose, token_hash=_hash(raw),
                      meta=meta or {},
                      expires_at=now + timedelta(minutes=settings.email_token_minutes)))
    db.commit()
    return raw


def _consume(db: Db, raw: str, purpose: str) -> tuple[User, EmailToken]:
    now = datetime.now(timezone.utc)
    token_hash = _hash(raw)
    # 条件 UPDATE 保证一次性：重置/验证令牌并发提交时只有一个能成功。
    claimed = db.execute(update(EmailToken).where(
        EmailToken.token_hash == token_hash,
        EmailToken.purpose == purpose,
        EmailToken.used_at.is_(None),
        EmailToken.expires_at > now,
    ).values(used_at=now))
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(400, "链接/令牌无效或已过期")
    db.commit()
    row = db.exec(select(EmailToken).where(
        EmailToken.token_hash == token_hash)).first()
    user = db.get(User, row.user_id) if row is not None else None
    if user is None or row is None:
        raise HTTPException(400, "用户不存在")
    return user, row


@router.post("/email/verify/request")
def request_email_verify(request: Request, user: CurrentUser, db: Db):
    rate_limit(request, "email-verify", 10, user.id)
    if not user.email:
        raise HTTPException(422, "账号未填写邮箱")
    if user.email_verified:
        return {"ok": True, "email_verified": True}
    raw = _issue(db, user, "verify")
    subject, text, html = render_email("verify", token=raw)
    try:
        send_email(user.email, subject, text, html)
    except MailError as exc:
        # 已登录用户不必用「没发出去也回 200」防枚举：直接告诉他是发信环节坏了，
        # 令牌行仍有效，修好 SMTP 后重发即可（重发会作废旧令牌）。
        log.error("verify email failed user=%s: %s", user.handle, exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "验证邮件发送失败，请稍后再试") from exc
    return {"ok": True, "email_verified": False}


@router.post("/email/verify", response_model=AccountOut)
def verify_email(payload: VerifyEmailIn, db: Db):
    user, _row = _consume(db, payload.token, "verify")
    user.email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return _account_out(db, user)


@router.post("/email/change/request")
def request_email_change(payload: EmailChangeIn, request: Request,
                         user: CurrentUser, db: Db):
    """向新邮箱发确认令牌；确认后才真正换绑。"""
    rate_limit(request, "email-change", 10, user.id)
    email = payload.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(422, "邮箱格式不正确")
    if email == (user.email or "").lower():
        raise HTTPException(422, "这已经是当前邮箱")
    taken = db.exec(select(User).where(User.email == email,
                                       User.id != user.id)).first()
    if taken is not None:
        raise HTTPException(409, "这个邮箱已被其他账号使用")
    # 已设置口令的账号换邮箱必须再验一次口令，避免被盗会话直接换绑。
    if user.password_set and not verify_password(payload.password or "",
                                                  user.password_hash):
        raise HTTPException(403, "当前密码不正确")

    raw = _issue(db, user, "change_email", {"email": email})
    subject, text, html = render_email("change_email", token=raw, email=email)
    try:
        send_email(email, subject, text, html)
    except MailError as exc:
        log.error("change email send failed user=%s: %s", user.handle, exc)
        raise HTTPException(503, "确认邮件发送失败，请稍后再试") from exc
    return {"ok": True, "email": email}


@router.post("/email/change/confirm", response_model=TokenOut)
def confirm_email_change(payload: EmailChangeConfirmIn, request: Request,
                         user: CurrentUser, db: Db):
    """确认换绑：写新邮箱、撤销全部旧会话并签发新 token。"""
    owner, row = _consume(db, payload.token, "change_email")
    if owner.id != user.id:
        raise HTTPException(400, "令牌不属于当前账号")
    email = str((row.meta or {}).get("email") or "").strip().lower()
    if not email:
        raise HTTPException(400, "令牌缺少目标邮箱，请重新发起")
    taken = db.exec(select(User).where(User.email == email,
                                       User.id != user.id)).first()
    if taken is not None:
        raise HTTPException(409, "这个邮箱已被其他账号使用")
    old_email = user.email
    user.email = email
    user.email_verified = True
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    _revoke_all_sessions(db, user.id)
    if old_email and old_email.lower() != email:
        subject, text, html = render_email(
            "security", subject="RoboWiki 邮箱已更换",
            title="邮箱已更换",
            body=f"你的 RoboWiki 账号邮箱已从 {old_email} 更换为 {email}。")
        enqueue_email(db, to=old_email, subject=subject, text=text, html=html,
                      kind="security", user_id=user.id,
                      dedupe_key=f"email-change:{user.id}:{int(datetime.now().timestamp())}")
        db.commit()
    return _issue_session(db, user, request, scopes=("email",))


@router.post("/password/forgot", status_code=202)
def forgot_password(payload: ForgotIn, request: Request, db: Db):
    rate_limit(request, "password-forgot", 10)
    u = db.exec(select(User).where(
        User.email == payload.email.strip().lower())).first()
    if u is not None:
        raw = _issue(db, u, "reset")
        subject, text, html = render_email("reset", token=raw)
        try:
            send_email(u.email or "", subject, text, html)
        except MailError as exc:
            # 这个接口对「邮箱是否存在」必须保持同一个响应（202），所以发信失败
            # 只能记日志，不能改成 503 —— 否则 503/202 本身就是枚举信号。
            log.error("reset email failed user=%s: %s", u.handle, exc)
    # 不暴露邮箱是否存在
    return {"ok": True, "message": "如果该邮箱已注册，重置邮件已发送"}


@router.post("/password/reset")
def reset_password(payload: ResetPasswordIn, db: Db):
    user, _row = _consume(db, payload.token, "reset")
    user.password_hash = hash_password(payload.password)
    # 找回密码 = 账号重新拥有可用口令；第三方登录建出来的账号从此也能口令登录
    user.password_set = True
    user.email_verified = True
    # 口令被重置意味着「可能有别人拿到过账号」：所有旧会话（access + refresh）
    # 一并作废，不能留下一条能用 refresh 续出 access 的漏网链。
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    for t in db.exec(select(EmailToken).where(
            EmailToken.user_id == user.id, EmailToken.used_at.is_(None))).all():
        t.used_at = datetime.now(timezone.utc)
        db.add(t)
    db.commit()
    _revoke_all_sessions(db, user.id)
    _queue_security_mail(db, user, "密码已重置",
                         "你的密码已通过邮箱重置，所有旧会话已失效。")
    return {"ok": True}


@router.post("/password/change", response_model=TokenOut)
def change_password(payload: PasswordChangeIn, request: Request,
                    user: CurrentUser, db: Db):
    """改密：验当前口令 → 写新哈希 → **当场签发新 token**。

    旧 token 的 `pv` 绑定的是旧哈希，改完立刻失效；refresh 也全部撤销
    （改密后旧设备的刷新链不该继续活着）。调用方已通过验证，所以响应里
    直接给一对新 token，其他设备上的旧 token / refresh 全部失效。
    """
    rate_limit(request, "password-change", 20, user.id)
    # 统一跑一次 PBKDF2 再判结果，失败原因只有一种话术：不区分
    # 「口令没设过」和「当前密码填错」，也不回显任何账号字段。
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "当前密码不正确")

    user.password_hash = hash_password(payload.new_password)
    # 改密成功即代表这个账号有一条自己知道的口令（第三方建号也可以借此设口令）
    user.password_set = True
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    _revoke_all_sessions(db, user.id)
    _queue_security_mail(db, user, "密码已修改",
                         "你的 RoboWiki 密码已修改，其他设备上的会话已全部失效。")
    return _issue_session(db, user, request, scopes=("password",))


@router.post("/password/set", response_model=TokenOut)
def set_password(payload: PasswordSetIn, request: Request,
                 user: CurrentUser, db: Db):
    """给第三方建号首次设置本站密码；已设过的走 /password/change。"""
    rate_limit(request, "password-set", 10, user.id)
    if user.password_set:
        raise HTTPException(409, "本站密码已设置，请使用修改密码")
    user.password_hash = hash_password(payload.password)
    user.password_set = True
    # 设密等于新增一条登录方式：旧 access/refresh 全部作废，只保留本次签发的新会话。
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    _revoke_all_sessions(db, user.id)
    _queue_security_mail(db, user, "本站密码已设置",
                         "你的 RoboWiki 账号已设置本站密码；旧会话已全部失效。")
    return _issue_session(db, user, request, scopes=("password",))


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
async def github_login(request: Request, return_to: str | None = None):
    """跳到 GitHub 授权页。state 由 Authlib 写进签名 cookie。

    `return_to` 是登录完成后要回去的站点 origin（主域 / GitHub Pages 镜像 /
    localhost）。先在这里校验白名单并存进 OAuth session，回调时再取出；
    回调只 302 一个一次性 code，JWT 不出现在 Location。
    """
    client = _github_client()          # 未配置 → 503
    rate_limit(request, "oauth-login", 30)
    origin = _normalize_return_to(return_to)
    if origin:
        request.session["oauth_return_to"] = origin
    else:
        request.session.pop("oauth_return_to", None)
    return await client.authorize_redirect(request, _github_redirect_uri(request))


@router.get("/github/callback")
async def github_callback(request: Request, db: Db):
    """回调：换 token → 取资料 → 找/建用户 → 发放会话 → 回登录页。

    三条出口：
      · `Accept: application/json` → 直接返回 TokenOut（H5/小程序自己跳转）；
      · 授权时带了 `return_to` → 302 `{return_to}/login.html#code=<一次性 code>`，
        静态镜像再用 `POST /auth/handoff` 换 TokenOut；JWT 不落 Location；
      · 未带 `return_to`（旧客户端/主站直连）→ 保持原有
        `site_url/login.html#token=<jwt>`，避免破坏既有调用方。
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
    return_to = request.session.pop("oauth_return_to", None)
    out = _issue_session(db, user, request, scopes=(PROVIDER_GITHUB,),
                         client="github")
    if _wants_json(request):
        return JSONResponse(out.model_dump(mode="json"))
    if return_to:
        # 静态镜像：Location 里只有 60 秒、一次性的 code，没有 JWT
        code = _create_handoff(db, user, return_to)
        return RedirectResponse(f"{return_to.rstrip('/')}/login.html#code={code}",
                                status_code=status.HTTP_302_FOUND)
    return RedirectResponse(_login_redirect(out.access_token),
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
async def wechat_mini(payload: WechatMiniIn, request: Request, db: Db,
                     user: MaybeUser):
    """小程序登录 / 绑定微信。

    未登录：按 openid 找/建账号并签会话（与口令登录等价）。
    已登录：把该 openid 绑到当前账号（用于邮箱 / GitHub 账号补一种登录方式）；
    若 openid 已属于别的账号则 409，避免把两个账号误并。
    """
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
    if user is not None:
        bound = db.exec(select(Identity).where(
            Identity.provider == PROVIDER_WECHAT_MINI,
            Identity.subject == openid)).first()
        if bound is not None and bound.user_id != user.id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "该微信已绑定其他账号；请先在网页账号中心解绑，或直接用该微信登录")
        if bound is None:
            db.add(Identity(user_id=user.id, provider=PROVIDER_WECHAT_MINI,
                            subject=openid, email=None,
                            raw={"unionid": unionid} if unionid else {}))
            db.commit()
        return _issue_session(db, user, request,
                              scopes=(PROVIDER_WECHAT_MINI,), client="mini")

    user = _user_for_identity(
        db, provider=PROVIDER_WECHAT_MINI, subject=openid,
        email=None, email_verified=False, display_name=nickname,
        # handle 里不放 openid 原文：它是能跨会话认出人的标识
        handle_hint=_slug(f"wx-{hashlib.sha256(openid.encode()).hexdigest()[:10]}"),
        # session_key 是解密用户资料的密钥，不落库
        raw={"unionid": unionid} if unionid else {},
    )
    return _issue_session(db, user, request,
                          scopes=(PROVIDER_WECHAT_MINI,), client="mini")


# ── 微信扫码登录（网页意图 + 个人小程序确认器）────────────────────────────────
# 流程：网页 POST /auth/wechat/qr 拿小程序码 → 用户扫码进小程序确认页 →
# 小程序 POST /auth/wechat/qr/confirm（ticket + wx.login code）→ 网页轮询
# GET /auth/wechat/qr/status，confirmed 时取走会话。ticket 一次性、5 分钟过期。
_QR_TICKET_TTL = 300          # 二维码有效期（秒）
_wx_token_cache: dict[str, tuple[str, float]] = {}


def _qr_ticket_ttl() -> int:
    return _QR_TICKET_TTL


async def _wechat_access_token() -> str:
    """stable_token：不会像旧接口那样一取就顶掉别的 token，缓存到过期前 10 分钟。"""
    now = time.time()
    cached = _wx_token_cache.get("default")
    if cached and cached[1] > now:
        return cached[0]
    payload = {
        "grant_type": "client_credential",
        "appid": (settings.wechat_mp_appid or "").strip(),
        "secret": (settings.wechat_mp_secret or "").strip(),
        "force_refresh": False,
    }
    url = f"{settings.wechat_api_base.rstrip('/')}/cgi-bin/stable_token"
    async with httpx.AsyncClient(timeout=settings.wechat_timeout_s) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
    token = (data.get("access_token") or "").strip()
    if not token:
        log.warning("wechat stable_token failed: errcode=%s", data.get("errcode"))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "获取微信 access_token 失败，请稍后再试")
    ttl = max(600, min(int(data.get("expires_in") or 7200), 7200) - 600)
    _wx_token_cache["default"] = (token, now + ttl)
    return token


async def _wechat_qr_image(ticket: str) -> bytes:
    """调 getwxacodeunlimit 拿小程序码；失败时微信返回 JSON 而不是图片。"""
    token = await _wechat_access_token()
    url = f"{settings.wechat_api_base.rstrip('/')}/wxa/getwxacodeunlimit"
    async with httpx.AsyncClient(timeout=settings.wechat_timeout_s) as client:
        resp = await client.post(url, params={"access_token": token}, json={
            "scene": ticket,
            "page": "pages/login/confirm/index",
            # 体验版 / 未发布页面也能出码；真机扫码要求该页面至少是体验版
            "check_path": False,
            "width": 280,
        })
        resp.raise_for_status()
        if "image" not in (resp.headers.get("content-type") or ""):
            data = resp.json() or {}
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"生成小程序码失败（errcode={data.get('errcode')}）")
        return resp.content


def _prune_tickets(db: Session) -> None:
    """过期票据顺手清掉：这张表只存 5 分钟的状态，别让它长草。"""
    db.execute(delete(LoginTicket).where(LoginTicket.expires_at <= _utcnow()))
    db.commit()


@router.post("/wechat/qr", response_model=QrCreateOut)
async def wechat_qr_create(request: Request, db: Db):
    """网页发起扫码登录：签发 ticket 并生成指向小程序确认页的小程序码。"""
    if not settings.wechat_mini_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "微信扫码登录未配置")
    rate_limit(request, "wechat-qr", 30)
    _prune_tickets(db)
    # 32 位 hex 正好是 scene 上限（32 个可见字符）；scene 里只放 ticket。
    ticket = secrets.token_hex(16)
    db.add(LoginTicket(ticket=ticket,
                       expires_at=_utcnow() + timedelta(seconds=_qr_ticket_ttl())))
    db.commit()

    try:
        qrcode = base64.b64encode(await _wechat_qr_image(ticket)).decode()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("wechat qrcode failed: %s", type(exc).__name__)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "生成小程序码失败，请稍后再试") from exc
    return QrCreateOut(ticket=ticket, qrcode=qrcode, expires_in=_qr_ticket_ttl())


@router.post("/wechat/qr/confirm", response_model=dict)
async def wechat_qr_confirm(payload: QrConfirmIn, request: Request, db: Db):
    """小程序确认页调用：把这次 ticket 与扫码人的微信身份绑定，签发会话。"""
    if not settings.wechat_mini_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "微信扫码登录未配置")
    rate_limit(request, "wechat-qr-confirm", 60)
    now = _utcnow()
    ticket = db.get(LoginTicket, payload.ticket.strip())
    if ticket is None or ticket.expires_at <= now:
        raise HTTPException(status.HTTP_410_GONE,
                            "二维码已过期，请在网页刷新后重试")
    if ticket.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "这次登录已确认过，请在网页重新生成二维码")

    try:
        data = await _wechat_code2session(payload.code)
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("wechat qr confirm code2session failed: %s", type(exc).__name__)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "微信登录服务暂不可用，请稍后再试") from exc
    openid = (data.get("openid") or "").strip()
    if not openid:
        log.warning("wechat qr confirm rejected: errcode=%s", data.get("errcode"))
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "微信登录失败，请重新扫码")

    unionid = (data.get("unionid") or "").strip()
    user = _user_for_identity(
        db, provider=PROVIDER_WECHAT_MINI, subject=openid,
        email=None, email_verified=False, display_name=None,
        handle_hint=_slug(f"wx-{hashlib.sha256(openid.encode()).hexdigest()[:10]}"),
        raw={"unionid": unionid} if unionid else {},
    )
    out = _issue_session(db, user, request,
                         scopes=(PROVIDER_WECHAT_MINI,), client="web-qr")

    # 原子占用：并发两次确认只能成功一次（status 条件更新）
    result = db.execute(update(LoginTicket).where(
        LoginTicket.ticket == ticket.ticket,
        LoginTicket.status == "pending",
        LoginTicket.expires_at > now,
    ).values(status="confirmed",
             session=out.model_dump(mode="json"),
             confirmed_at=now))
    db.commit()
    if not result.rowcount:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "这次登录已确认过，请在网页重新生成二维码")
    return {"ok": True}


@router.get("/wechat/qr/status", response_model=QrStatusOut)
def wechat_qr_status(ticket: str, request: Request, db: Db):
    """网页轮询：confirmed 时返回会话并**立刻删除票据**（一次性，防重放）。"""
    rate_limit(request, "wechat-qr-status", 120)
    row = db.get(LoginTicket, ticket.strip())
    if row is None:
        return QrStatusOut(status="expired")
    if row.expires_at <= _utcnow():
        db.delete(row)
        db.commit()
        return QrStatusOut(status="expired")
    if row.status != "confirmed" or not row.session:
        return QrStatusOut(status="pending")
    payload = QrStatusOut(status="confirmed", token=TokenOut(**row.session))
    db.delete(row)
    db.commit()
    return payload


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


def _can_claim_unverified(db: Session, user: User) -> bool:
    """未验证邮箱账号只有在没有任何其他身份时，才允许被已验证的提供方认领。"""
    if user.email_verified:
        return False
    return db.exec(select(Identity).where(Identity.user_id == user.id)).first() is None


def _claim_unverified(db: Session, user: User) -> None:
    """提供方已证明邮箱归属：保留账号数据，但清掉占位口令和旧会话。

    先注册受害者邮箱、再等受害者用 GitHub 登录的攻击者，不能继续用口令进来。
    """
    user.email_verified = True
    user.password_hash = unusable_password_hash()
    user.password_set = False
    user.session_epoch = int(user.session_epoch or 0) + 1
    db.add(user)
    db.commit()
    _revoke_all_sessions(db, user.id)


def _user_for_identity(db: Session, *, provider: str, subject: str,
                       email: str | None, email_verified: bool,
                       display_name: str | None, handle_hint: str,
                       raw: dict) -> User:
    """(provider, subject) → User。找不到就建，找到就复用。

    并号规则只认**提供方已验证**的邮箱，且要区分存量账号有没有验证过：
      · 已验证账号：直接并入；
      · 未验证且没有任何第三方身份：认领并清掉占位口令/旧会话；
      · 未验证但已经绑过别的身份：不并，另建账号 —— 否则攻击者可以先占邮箱
        再绑自己的 GitHub，等受害者登录时把受害者并进攻击者控制的账号。
    """
    email = email.strip().lower() if email else None
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
    created_user = False
    existing_email_user = None
    if email:
        existing_email_user = db.exec(select(User).where(User.email == email)).first()
    if email and email_verified and existing_email_user is not None:
        if _can_claim_unverified(db, existing_email_user):
            _claim_unverified(db, existing_email_user)
            user = existing_email_user
        elif existing_email_user.email_verified:
            user = existing_email_user

    if user is None:
        created_user = True
        handle = _claim_handle(db, handle_hint)
        # 未验证邮箱不能占用别人已注册的邮箱；已验证但邮箱已被别的身份占用，
        # 同样不能硬塞，否则会撞唯一约束甚至误并号。
        safe_email = email if (email and email_verified
                               and existing_email_user is None) else None
        user = User(
            handle=handle,
            display_name=(display_name or handle)[:32],
            email=safe_email,
            email_verified=bool(safe_email and email_verified),
            # 没人知道这串口令：账号只能靠已绑定的身份进来
            password_hash=unusable_password_hash(),
            password_set=False,
            # 首登自动生成的名字是临时的，允许用户改一次
            handle_provisional=True,
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
                # 无邮箱的并发首次登录（微信/GitHub 无邮箱）撞 handle：让客户端重试，
                # 不要把 IntegrityError 变成 500。
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "账号创建冲突，请重试") from None
            if not user.email_verified:
                if _can_claim_unverified(db, user):
                    _claim_unverified(db, user)
                else:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        "该邮箱已绑定其他账号，请使用原登录方式")
            created_user = False
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
        winner = db.get(User, ident.user_id)
        if winner is None:
            raise
        if created_user:
            # 本请求新建的账号没抢到身份，不能把会话签到一个没有身份的孤儿账号上。
            db.delete(user)
            db.commit()
        return winner
    return user


def _wants_json(request: Request) -> bool:
    return "application/json" in (request.headers.get("accept") or "").lower()


def _login_redirect(token: str) -> str:
    return f"{settings.site_url.rstrip('/')}/login.html#token={token}"

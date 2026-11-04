"""认证：注册 / 登录 / 我是谁。"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from ...core.config import settings
from ...core.security import (create_token, dummy_password_hash, hash_password,
                              verify_password)
from ...crud import user_out
from ...mailer import send_email
from ...models import EmailToken, User
from ...schemas import (ForgotIn, LoginIn, RegisterIn, ResetPasswordIn,
                        TokenOut, UserOut, VerifyEmailIn)
from ..deps import CurrentUser, Db, rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

#: 注册失败统一话术。邮箱冲突不再单独报错，否则注册接口就是枚举器。
_REGISTER_FAILED = "注册未完成，请检查邮箱或稍后再试"


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
    return TokenOut(access_token=create_token(u.handle, u.password_hash),
                    user=user_out(db, u))


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
    return TokenOut(access_token=create_token(u.handle, u.password_hash),
                    user=user_out(db, u))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, db: Db):
    return user_out(db, user)


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
    send_email(user.email, "RoboWiki 邮箱验证",
               f"验证令牌：{raw}\n"
               f"有效期 {settings.email_token_minutes} 分钟。\n"
               "在站点登录后打开「验证邮箱」输入该令牌即可。")
    return {"ok": True, "email_verified": False}


@router.post("/email/verify", response_model=UserOut)
def verify_email(payload: VerifyEmailIn, db: Db):
    user = _consume(db, payload.token, "verify")
    user.email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(db, user)


@router.post("/password/forgot", status_code=202)
def forgot_password(payload: ForgotIn, request: Request, db: Db):
    rate_limit(request, "password-forgot", 10)
    u = db.exec(select(User).where(User.email == payload.email.strip())).first()
    if u is not None:
        raw = _issue(db, u, "reset")
        send_email(u.email or "", "RoboWiki 重置密码",
                   f"重置令牌：{raw}\n"
                   f"有效期 {settings.email_token_minutes} 分钟。\n"
                   "在登录框选择「找回密码」并输入该令牌与新密码。")
    # 不暴露邮箱是否存在
    return {"ok": True, "message": "如果该邮箱已注册，重置邮件已发送"}


@router.post("/password/reset")
def reset_password(payload: ResetPasswordIn, db: Db):
    user = _consume(db, payload.token, "reset")
    user.password_hash = hash_password(payload.password)
    db.add(user)
    for t in db.exec(select(EmailToken).where(
            EmailToken.user_id == user.id, EmailToken.used_at.is_(None))).all():
        t.used_at = datetime.now(timezone.utc)
        db.add(t)
    db.commit()
    return {"ok": True}

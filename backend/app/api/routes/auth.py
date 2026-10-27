"""认证：注册 / 登录 / 我是谁。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from ...core.security import create_token, hash_password, verify_password
from ...crud import user_out
from ...models import User
from ...schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..deps import CurrentUser, Db, rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, request: Request, db: Db):
    rate_limit(request, "register", 20)
    if db.exec(select(User).where(User.handle == payload.handle)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "这个 handle 已被占用")
    if payload.email and db.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "这个邮箱已注册")

    u = User(handle=payload.handle, display_name=payload.display_name,
             email=payload.email, password_hash=hash_password(payload.password),
             avatar_hue=abs(hash(payload.handle)) % 360)
    db.add(u)
    db.commit()
    db.refresh(u)
    return TokenOut(access_token=create_token(u.handle), user=user_out(db, u))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Db):
    rate_limit(request, "login", 30)
    u = db.exec(select(User).where(User.handle == payload.handle.lower())).first()
    if u is None or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号或密码不对")
    return TokenOut(access_token=create_token(u.handle), user=user_out(db, u))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, db: Db):
    return user_out(db, user)

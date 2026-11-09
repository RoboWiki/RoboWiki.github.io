"""可信度：绑定/验证的来源越多，可信度越高。

权限不按等级细分：只要有一种可信来源就能参与写入，没有任何来源则只读。
等级只用于展示与后续的权重（例如排序、审核优先级），不改变接口权限。
"""
from __future__ import annotations

from sqlmodel import Session, select

from .models import Identity, User

PROVIDERS = ("wechat_mini", "github")

SOURCE_LABELS = {
    "email": "邮箱已验证",
    "wechat_mini": "微信",
    "github": "GitHub",
    "staff": "站务",
}


def trust_sources(db: Session, user: User) -> list[str]:
    if user.is_staff:
        return ["staff"]
    out: list[str] = []
    if user.email_verified:
        out.append("email")
    rows = db.exec(select(Identity.provider).where(
        Identity.user_id == user.id).order_by(Identity.id)).all()
    for provider in rows:
        if provider in PROVIDERS and provider not in out:
            out.append(provider)
    return out


def trust_level(db: Session, user: User) -> int:
    """0 = 无可信来源；1–3 = 来源数量（站务固定 3）。"""
    if user.is_staff:
        return 3
    return min(3, len(trust_sources(db, user)))

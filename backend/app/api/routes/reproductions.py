"""方案复现记录。

一条记录回答的是「这套方案到底装得出来吗」，而不是「你喜不喜欢它」。

口径：
    · 只有三态：success / partial / failed —— 工程复现不存在 3.5 星
    · 一人一方案一条，重复提交是改结论，不是刷记录
    · changes 记录「相对原方案改了什么」，这比结论本身更有信息量
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlmodel import select

from ...models import Reproduction, utcnow
from ..deps import CurrentUser, Db, MaybeUser

router = APIRouter(prefix="/reproductions", tags=["reproductions"])

OUTCOMES = ("success", "partial", "failed")


class ReproductionIn(BaseModel):
    outcome: Literal["success", "partial", "failed"]
    changes: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=500)

    @field_validator("changes", "note")
    @classmethod
    def _strip(cls, value: str) -> str:
        return (value or "").strip()


def _summary(rows: list[Reproduction], viewer_id: int | None) -> dict:
    tally = {key: 0 for key in OUTCOMES}
    latest = None
    for row in rows:
        if row.outcome in tally:
            tally[row.outcome] += 1
        if latest is None or row.updated_at > latest:
            latest = row.updated_at
    mine_row = next((r for r in rows if r.user_id == viewer_id), None) if viewer_id else None
    return {
        "build_id": rows[0].build_id if rows else "",
        "total": len(rows),
        **tally,
        "updated_at": latest.isoformat() if latest else None,
        "mine": None if mine_row is None else {
            "outcome": mine_row.outcome,
            "changes": mine_row.changes,
            "note": mine_row.note,
            "updated_at": mine_row.updated_at.isoformat(),
        },
    }


@router.get("/{build_id}")
def get_reproductions(build_id: str, db: Db, user: MaybeUser):
    """公开读数：任何人可看，登录后才带 mine。"""
    rows = db.exec(select(Reproduction).where(Reproduction.build_id == build_id)).all()
    out = _summary(list(rows), user.id if user else None)
    out["build_id"] = build_id
    return out


@router.post("/{build_id}", status_code=201)
def record_reproduction(build_id: str, payload: ReproductionIn, user: CurrentUser, db: Db):
    """记录或更新一次复现结论。同一人同一方案只保留一条。"""
    if not build_id.strip():
        raise HTTPException(422, "build_id 不能为空")

    row = db.exec(select(Reproduction).where(
        Reproduction.build_id == build_id,
        Reproduction.user_id == user.id,
    )).first()

    created = row is None
    if row is None:
        row = Reproduction(build_id=build_id, user_id=user.id,
                           outcome=payload.outcome, changes=payload.changes,
                           note=payload.note)
        db.add(row)
    else:
        row.outcome = payload.outcome
        row.changes = payload.changes
        row.note = payload.note
        row.updated_at = utcnow()
        db.add(row)
    db.commit()

    rows = db.exec(select(Reproduction).where(Reproduction.build_id == build_id)).all()
    out = _summary(list(rows), user.id)
    out["created"] = created
    return out

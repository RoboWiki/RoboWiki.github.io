"""零件评分。

一人一件一票，可改（唯一约束保证不是刷票）。

为什么评分必须自托管：
    giscus 只有 reaction，没有 1–5 分档；而「这个件到底值不值」需要一个
    能聚合、能画分布、能参与排序的数。评论继续交给 giscus（GitHub 账号门槛
    由它兜住），评分进本站库 —— 两者分工，不重复。

口径纪律同样适用：
    · 未评分过的件返回 count=0，绝不返回「0 分」——0 分是差评，没评不是
    · 分布一起返回，只看均分会把「5 人 5 分」和「1 人 5 分 + 4 人 1 分」看成一样
    · own_hardware 单独统计：装过机的人打的分和「看参数打的」权重不同
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select

from ...models import Part, Rating, User, utcnow
from ..deps import CurrentUser, Db, MaybeUser

router = APIRouter(prefix="/ratings", tags=["ratings"])


class RateIn(BaseModel):
    score: int = Field(ge=1, le=5)
    own_hardware: bool = False
    note: str = Field(default="", max_length=200)


def _summary(rows: list[Rating]) -> dict:
    """一次算清均分、分布、装机比例。"""
    n = len(rows)
    if n == 0:
        return {"count": 0, "avg": None, "histogram": {str(i): 0 for i in range(1, 6)},
                "own_hardware_count": 0, "mine": None}
    hist = {str(i): 0 for i in range(1, 6)}
    for r in rows:
        hist[str(r.score)] = hist.get(str(r.score), 0) + 1
    return {
        "count": n,
        "avg": round(sum(r.score for r in rows) / n, 2),
        "histogram": hist,
        "own_hardware_count": sum(1 for r in rows if r.own_hardware),
        "mine": None,
    }


@router.get("/summary")
def summary(db: Db):
    """全站聚合，供静态站构建时烤成 JSON。

    静态部署（GitHub Pages）没有后端，所以 build_wiki.py 会把这个结果
    写进 ratings.json 一起发布 —— 页面读到的是「上次构建时」的真实聚合值。
    """
    rows = db.exec(select(Rating)).all()
    by: dict[str, list[Rating]] = {}
    for r in rows:
        by.setdefault(r.part_id, []).append(r)
    out = {pid: _summary(rs) for pid, rs in by.items()}
    return {"total_ratings": len(rows), "parts": out}


@router.get("/{part_id}")
def get_part_rating(part_id: str, db: Db, user: MaybeUser):
    if db.get(Part, part_id) is None:
        raise HTTPException(404, "零件不存在")
    rows = db.exec(select(Rating).where(Rating.part_id == part_id)).all()
    out = _summary(rows)
    if user is not None:
        mine = next((r for r in rows if r.user_id == user.id), None)
        if mine is not None:
            out["mine"] = {"score": mine.score, "own_hardware": mine.own_hardware,
                           "note": mine.note, "updated_at": mine.updated_at.isoformat()}
    return {"part_id": part_id, **out}


@router.post("/{part_id}", status_code=201)
def rate_part(part_id: str, payload: RateIn, user: CurrentUser, db: Db):
    """打分 OR 改分。同一人同一件只有一条记录。"""
    if db.get(Part, part_id) is None:
        raise HTTPException(404, "零件不存在")

    row = db.exec(select(Rating).where(Rating.part_id == part_id,
                                       Rating.user_id == user.id)).first()
    if row is None:
        row = Rating(part_id=part_id, user_id=user.id, score=payload.score,
                     own_hardware=payload.own_hardware, note=payload.note.strip())
        db.add(row)
        created = True
    else:
        row.score = payload.score
        row.own_hardware = payload.own_hardware
        row.note = payload.note.strip()
        row.updated_at = utcnow()
        db.add(row)
        created = False
    db.commit()

    rows = db.exec(select(Rating).where(Rating.part_id == part_id)).all()
    out = _summary(rows)
    out["mine"] = {"score": row.score, "own_hardware": row.own_hardware,
                   "note": row.note, "updated_at": row.updated_at.isoformat()}
    return {"created": created, "part_id": part_id, **out}


@router.delete("/{part_id}", status_code=204)
def unrate(part_id: str, user: CurrentUser, db: Db):
    row = db.exec(select(Rating).where(Rating.part_id == part_id,
                                       Rating.user_id == user.id)).first()
    if row is None:
        raise HTTPException(404, "还没有打过分")
    db.delete(row)
    db.commit()
    return None


@router.get("")
def top_rated(
    db: Db,
    user: MaybeUser,
    category: Annotated[str | None, Query()] = None,
    min_count: Annotated[int, Query(ge=1, le=50)] = 1,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
):
    """按均分排零件。`min_count` 是样本量门槛 —— 只有 1 票的 5.0 不该压过 20 票的 4.6。"""
    rows = db.exec(select(Rating)).all()
    by: dict[str, list[Rating]] = {}
    for r in rows:
        by.setdefault(r.part_id, []).append(r)

    items = []
    for pid, rs in by.items():
        if len(rs) < min_count:
            continue
        p = db.get(Part, pid)
        if p is None or (category and p.category != category):
            continue
        s = _summary(rs)
        items.append({"part_id": pid, "model": p.model, "vendor": p.vendor,
                      "category": p.category, **{k: s[k] for k in
                                                 ("count", "avg", "own_hardware_count")}})
    items.sort(key=lambda x: (-(x["avg"] or 0), -x["count"]))
    return {"min_count": min_count, "total": len(items), "items": items[:limit]}

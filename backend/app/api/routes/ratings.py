"""零件评分。

一人一件一票，可改（唯一约束保证不是刷票）。

为什么评分必须自托管：
    giscus 只有 reaction，没有 1–5 分档；而「这个件到底值不值」需要一个
    能聚合、能画分布、能参与排序的数。评论继续交给 giscus（GitHub 账号门槛
    由它兜住），评分进本站库 —— 两者分工，不重复。

口径纪律（全部收敛到 rating_stats.aggregate）：
    · 未评分过的件返回 count=0、avg=None，绝不返回「0 分」——0 分是差评
    · 分布一起返回，只看均分会把「5 人 5 分」和「1 人 5 分 + 4 人 1 分」看成一样
    · own_hardware 单独统计：装过机的人打的分和「看参数打的」权重不同
    · 排序用贝叶斯收缩后的 rank_score；1 条 5 分不该压过 20 条 4.6
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import select

from ...crud import shadowed_review_keys
from ...models import Part, Rating, utcnow
from ...rating_stats import aggregate
from ..deps import CurrentUser, Db, MaybeUser

router = APIRouter(prefix="/ratings", tags=["ratings"])


class RateIn(BaseModel):
    score: int = Field(ge=1, le=5)
    own_hardware: bool = False
    note: str = Field(default="", max_length=200)


def _mine_out(row: Rating | None, *, hidden: bool = False) -> dict | None:
    if row is None:
        return None
    return {"score": row.score, "own_hardware": row.own_hardware,
            "note": row.note, "updated_at": row.updated_at.isoformat(),
            # 评价帖被隐藏时这票不进公开聚合；作者仍然看得到、可以撤销
            "hidden": hidden}


def _summary(rows: list[Rating], viewer_id: int | None = None,
             shadowed: set[tuple[str, int]] | None = None) -> dict:
    """一次算清均分、分布、装机比例、四维与排序分。

    `rows` 直接交给 rating_stats.aggregate：/ratings/{part}、/ratings/summary
    与 top_rated 因此共用同一套口径，不会出现「页面 4.6 / 接口 4.2」。

    `shadowed` 是「评价帖已被隐藏」的 (part_id, user_id)：这些票不计入公开
    聚合，但 mine 仍返回给作者，并标记 hidden。
    """
    shadowed = shadowed or set()
    visible = [r for r in rows if (r.part_id, r.user_id) not in shadowed]
    out = aggregate(visible)
    mine_row = (next((r for r in rows if r.user_id == viewer_id), None)
                if viewer_id is not None else None)
    out["mine"] = _mine_out(
        mine_row,
        hidden=bool(mine_row and (mine_row.part_id, mine_row.user_id) in shadowed))
    return out


def _group(rows: list[Rating]) -> dict[str, list[Rating]]:
    by: dict[str, list[Rating]] = {}
    for r in rows:
        by.setdefault(r.part_id, []).append(r)
    return by


@router.get("/summary")
def summary(db: Db):
    """全站聚合，供静态站构建时烤成 JSON。

    静态部署（GitHub Pages）没有后端，所以 build_wiki.py 会把这个结果
    写进 ratings.json 一起发布 —— 页面读到的是「上次构建时」的真实聚合值。

    形状与 /ratings/{part} 同源：count / avg / histogram / own_hardware_*
    / dims_* / usage_* / low_sample / confidence / rank_score。n=0 的零件
    avg 为 None（未知），不是 0 分。
    """
    rows = db.exec(select(Rating)).all()
    shadowed = shadowed_review_keys(db)
    parts = {pid: _summary(rs, shadowed=shadowed)
             for pid, rs in _group(rows).items()}
    return {
        "total_ratings": sum(p["count"] for p in parts.values()),
        "parts": parts,
    }


@router.get("/{part_id}")
def get_part_rating(part_id: str, db: Db, user: MaybeUser):
    if db.get(Part, part_id) is None:
        raise HTTPException(404, "零件不存在")
    rows = db.exec(select(Rating).where(Rating.part_id == part_id)).all()
    return {"part_id": part_id,
            **_summary(rows, user.id if user is not None else None,
                       shadowed_review_keys(db, part_id))}


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
    return {"created": created, "part_id": part_id,
            **_summary(rows, user.id, shadowed_review_keys(db, part_id))}


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
    """按 rank_score 排零件。

    `min_count` 是样本量门槛；排序用贝叶斯收缩后的分数，而不是裸均分 ——
    只有 1 票的 5.0 不该压过 20 票的 4.6。返回里仍保留 avg/count，方便
    客户端显示「4.6（20 人）」而不是只看到一个排序分。
    """
    rows = db.exec(select(Rating)).all()
    shadowed = shadowed_review_keys(db)

    items = []
    for pid, rs in _group(rows).items():
        s = _summary(rs, shadowed=shadowed)
        if s["count"] < min_count:
            continue
        p = db.get(Part, pid)
        if p is None or (category and p.category != category):
            continue
        items.append({"part_id": pid, "model": p.model, "vendor": p.vendor,
                      "category": p.category,
                      "count": s["count"], "avg": s["avg"],
                      "own_hardware_count": s["own_hardware_count"],
                      "low_sample": s["low_sample"],
                      "rank_score": s["rank_score"]})

    items.sort(key=lambda x: (-(x["rank_score"] or 0), -x["count"]))
    return {"min_count": min_count, "total": len(items), "items": items[:limit]}

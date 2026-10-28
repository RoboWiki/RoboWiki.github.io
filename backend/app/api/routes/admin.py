"""后台：零件数据的修正入口。

两条硬规则：
  1. **每次改动都留痕** —— 写 part_edits（字段、旧值、新值、依据、来源链接、谁改的）；
  2. **改完必须能回答「凭什么」** —— note 与 source_url 是这个站的立身之本，
     没有依据的改动和编造数据没有区别。

只开放给 is_staff。用户端只读。
"""
from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select

from ...models import Part, PartEdit, User
from ..deps import CurrentUser, Db
from .catalog import CATEGORY_LABELS, SUBTYPE_LABELS, _attach_reviews, part_out

router = APIRouter(prefix="/admin", tags=["admin"])

#: 可直接改的行级字段
COLUMNS = {"price_cny", "url", "source_tier", "verified", "last_checked",
           "notes", "origin", "category", "subtype", "vendor", "model", "title"}

#: specs 里允许改的字段（与 pipeline/validate.py 的白名单一致）
SPEC_KEYS = {
    "tau_peak_Nm", "tau_rated_Nm", "tau_basis", "speed_noload_rpm", "speed_rated_rpm",
    "gear", "mass_kg", "od_mm", "l_mm", "rotor_inertia_kgm2", "inertia_basis",
    "armature_kgm2", "voltage_V", "voltage_range_V", "kt_Nm_per_A", "r_phase_ohm",
    "l_phase_uh", "pole_pairs", "i_peak_A", "i_rated_A", "frictionloss_Nm",
    "damping_Nms_rad", "encoder", "comm", "driver_integrated", "ip",
    "image_url", "image_source",
}


class PatchIn(BaseModel):
    #: {"specs.tau_peak_Nm": 40.0, "price_cny": 1290, "source_tier": "A"}
    changes: dict[str, Any] = Field(min_length=1)
    note: str = Field(min_length=2, max_length=500,
                      description="依据：哪份 datasheet 的哪一页 / 哪封厂商邮件")
    source_url: str | None = Field(default=None, max_length=500)


class EditOut(BaseModel):
    id: int
    part_id: str
    field: str
    old_value: str | None
    new_value: str | None
    note: str
    source_url: str | None
    editor: str | None
    created_at: str


def _staff(user: User) -> None:
    if not user.is_staff:
        raise HTTPException(403, "需要站务权限")


def _split(key: str) -> tuple[str, str]:
    """'specs.gear' -> ('specs','gear')；'price_cny' -> ('columns','price_cny')"""
    if key.startswith("specs."):
        return "specs", key.split(".", 1)[1]
    return "columns", key


def _coerce(field: str, value: Any) -> Any:
    if value is None or value == "":
        return None
    if field.startswith("image_"):
        return str(value)
    if field in ("tau_basis", "inertia_basis", "encoder", "comm", "notes", "origin",
                 "url", "last_checked", "ip", "voltage_range_V",
                 "category", "subtype", "vendor", "model", "title"):
        return str(value)
    if field == "driver_integrated":
        return bool(value)
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise HTTPException(422, f"{field} 需要数值，收到 {value!r}") from None
    return num


@router.get("/stats")
def admin_stats(user: CurrentUser, db: Db):
    """数据缺口看板。

    口径纪律同样适用于看板本身：**只在字段有意义的品类里统计**。
    `tau_rated_Nm` / `armature_kgm2` 对主控和传感器没有意义，
    把它们算进缺口会虚增 41 个（曾经就犯过这个错）。
    """
    _staff(user)

    def count(*where) -> int:
        stmt = select(func.count(Part.id))
        for w in where:
            stmt = stmt.where(w)
        return int(db.exec(stmt).one())

    is_act = Part.category == "actuator"
    no_rated_spec = func.json_extract(Part.specs, "$.tau_rated_Nm").is_(None)
    no_arm_spec = func.json_extract(Part.specs, "$.armature_kgm2").is_(None)
    no_img_spec = func.json_extract(Part.specs, "$.image_url").is_(None)

    total = count(Part.id > "")
    act_total = count(is_act)
    return {
        "parts": total,
        "actuators": act_total,
        # 全局口径
        "no_image": count(no_img_spec),
        "no_url": count(Part.url.is_(None)),
        "no_price": count(Part.price_cny.is_(None)),
        "unverified": count(Part.verified == False),      # noqa: E712
        "tier_B": count(Part.source_tier == "B"),
        "tier_C": count(Part.source_tier == "C"),
        # 仅执行器口径（这两个字段对主控/传感器无意义）
        "no_rated_torque": count(is_act, no_rated_spec),
        "no_armature": count(is_act, no_arm_spec),
        "edits": int(db.exec(select(func.count(PartEdit.id))).one()),
        # 看板自己也要能被核对：说明每个数字的分母
        "scopes": {
            "no_image": f"全部 {total} 个零件",
            "no_url": f"全部 {total} 个零件",
            "no_price": f"全部 {total} 个零件",
            "unverified": f"全部 {total} 个零件",
            "no_rated_torque": f"仅 {act_total} 个执行器（该字段对主控/传感器无意义）",
            "no_armature": f"仅 {act_total} 个执行器",
        },
    }


@router.get("/parts")
def admin_parts(
    user: CurrentUser, db: Db,
    category: str | None = None,
    q: str | None = None,
    gap: Annotated[str | None, Query(description="no_image|no_url|no_armature|no_rated|no_price|unverified")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    _staff(user)
    stmt = select(Part)
    if category:
        stmt = stmt.where(Part.category == category)
    if q:
        stmt = stmt.where(Part.search.contains(q.lower()))
    if gap == "no_image":
        stmt = stmt.where(func.json_extract(Part.specs, "$.image_url").is_(None))
    elif gap == "no_url":
        stmt = stmt.where(Part.url.is_(None))
    elif gap == "no_armature":
        # 这两个字段只对执行器有意义，筛选时也必须同口径，否则会混进 41 个主控/传感器
        stmt = stmt.where(Part.category == "actuator",
                          func.json_extract(Part.specs, "$.armature_kgm2").is_(None))
    elif gap == "no_rated":
        stmt = stmt.where(Part.category == "actuator",
                          func.json_extract(Part.specs, "$.tau_rated_Nm").is_(None))
    elif gap == "no_price":
        stmt = stmt.where(Part.price_cny.is_(None))
    elif gap == "unverified":
        stmt = stmt.where(Part.verified == False)  # noqa: E712

    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = db.exec(stmt.order_by(Part.vendor, Part.model)
                   .offset(offset).limit(limit)).all()
    items = [part_out(p) for p in rows]
    _attach_reviews(db, items)
    return {"total": int(total), "items": items}


@router.get("/parts/{part_id}")
def admin_part(part_id: str, user: CurrentUser, db: Db):
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    edits = db.exec(select(PartEdit).where(PartEdit.part_id == part_id)
                    .order_by(PartEdit.created_at.desc()).limit(100)).all()
    editors = {u.id: u.display_name for u in
               db.exec(select(User).where(User.id.in_({e.editor_id for e in edits
                                                       if e.editor_id}))).all()}
    out = part_out(p)
    out["history"] = [{
        "id": e.id, "field": e.field, "old_value": e.old_value,
        "new_value": e.new_value, "note": e.note, "source_url": e.source_url,
        "editor": editors.get(e.editor_id), "created_at": e.created_at.isoformat(),
    } for e in edits]
    return out


@router.patch("/parts/{part_id}")
def admin_patch(part_id: str, payload: PatchIn, user: CurrentUser, db: Db):
    """改字段。每个改动写一条 PartEdit；note/source_url 必填。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")

    specs = dict(p.specs or {})
    changed = 0
    for key, raw in payload.changes.items():
        where, field = _split(key)
        if where == "specs":
            if field not in SPEC_KEYS:
                raise HTTPException(422, f"specs.{field} 不在可改字段列表内")
            old = specs.get(field)
            new = _coerce(field, raw)
            if old == new:
                continue
            specs[field] = new
            target = f"specs.{field}"
        else:
            if field not in COLUMNS:
                raise HTTPException(422, f"{field} 不是可改字段")
            old = getattr(p, field)
            new = _coerce(field, raw)
            if field == "verified":
                new = bool(raw)
            if old == new:
                continue
            setattr(p, field, new)
            target = field

        db.add(PartEdit(part_id=part_id, field=target,
                        old_value=None if old is None else str(old),
                        new_value=None if new is None else str(new),
                        editor_id=user.id, note=payload.note,
                        source_url=payload.source_url))
        changed += 1

    if not changed:
        return {"ok": True, "changed": 0, "note": "没有实际变化"}

    p.specs = specs
    if "last_checked" not in payload.changes:
        from datetime import date
        p.last_checked = date.today().isoformat()
    p.search = " ".join(str(x) for x in (
        p.vendor, p.vendor_cn, p.model, p.title,
        specs.get("comm"), specs.get("encoder"), p.notes) if x).lower()
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"ok": True, "changed": changed, "part": part_out(p)}


@router.post("/parts/{part_id}/verify")
def admin_verify(part_id: str, user: CurrentUser, db: Db,
                 note: Annotated[str, Query(min_length=2)] = "逐项核对官方 datasheet"):
    """标记「已核对」并打时间戳 —— 与改字段走同一套留痕。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    from datetime import date
    today = date.today().isoformat()
    for field, new in (("verified", True), ("last_checked", today)):
        old = getattr(p, field)
        setattr(p, field, new)
        db.add(PartEdit(part_id=part_id, field=field,
                        old_value=str(old), new_value=str(new),
                        editor_id=user.id, note=note, source_url=p.url))
    db.add(p)
    db.commit()
    return {"ok": True, "verified": True, "last_checked": today}


@router.get("/history")
def admin_history(user: CurrentUser, db: Db,
                  limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """全站最近的修改流水。"""
    _staff(user)
    rows = db.exec(select(PartEdit).order_by(PartEdit.created_at.desc())
                   .limit(limit)).all()
    editors = {u.id: u.display_name for u in
               db.exec(select(User).where(User.id.in_({e.editor_id for e in rows
                                                       if e.editor_id}))).all()}
    return [{"id": e.id, "part_id": e.part_id, "field": e.field,
             "old_value": e.old_value, "new_value": e.new_value, "note": e.note,
             "source_url": e.source_url, "editor": editors.get(e.editor_id),
             "created_at": e.created_at.isoformat()} for e in rows]

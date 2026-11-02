"""后台：零件数据的修正入口。

硬规则：**后台不写目录**。PATCH / verify 只生成 submission，
审核通过后由 worker 产出 PR / release，`parts` 仍是 release 的只读投影。
note 与 source_url 必填 —— 没有依据的改动和编造数据没有区别。

只开放给 is_staff。用户端只读。
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select

from ...catalog_fields import SPEC_KEYS, TOP_FIELDS, split_field
from ...models import Part, PartEdit, Submission, User
from ..deps import CurrentUser, Db
from .catalog import _attach_reviews, part_out

router = APIRouter(prefix="/admin", tags=["admin"])


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
    return split_field(key)


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
    no_rated_spec = Part.specs["tau_rated_Nm"].as_string().is_(None)
    no_arm_spec = Part.specs["armature_kgm2"].as_string().is_(None)
    no_img_spec = Part.specs["image_url"].as_string().is_(None)

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
        stmt = stmt.where(Part.specs["image_url"].as_string().is_(None))
    elif gap == "no_url":
        stmt = stmt.where(Part.url.is_(None))
    elif gap == "no_armature":
        # 这两个字段只对执行器有意义，筛选时也必须同口径，否则会混进 41 个主控/传感器
        stmt = stmt.where(Part.category == "actuator",
                          Part.specs["armature_kgm2"].as_string().is_(None))
    elif gap == "no_rated":
        stmt = stmt.where(Part.category == "actuator",
                          Part.specs["tau_rated_Nm"].as_string().is_(None))
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
        "source": "release",
    } for e in edits]
    out["proposals"] = _proposals(db, part_id)
    return out


def _proposals(db, part_id: str, limit: int = 20) -> list[dict]:
    rows = db.exec(select(Submission).where(Submission.target_id == part_id)
                   .order_by(Submission.created_at.desc()).limit(limit)).all()
    return [{
        "submission_id": s.id, "status": s.status,
        "fields": sorted(s.payload or {}),
        "diff": (s.evidence or {}).get("preview") or [],
        "note": (s.evidence or {}).get("note"),
        "source_url": (s.evidence or {}).get("source_url"),
        "created_at": s.created_at.isoformat(),
    } for s in rows]


def _propose(db, p: Part, changes: dict[str, Any], diff: list[dict],
             user: User, note: str, source_url: str | None) -> Submission:
    s = Submission(kind="part_patch", target_id=p.id, payload=changes,
                   evidence={"note": note, "source_url": source_url,
                             "preview": diff},
                   submitter_id=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.patch("/parts/{part_id}")
def admin_patch(part_id: str, payload: PatchIn, user: CurrentUser, db: Db):
    """生成字段变更提案。目录不动，note/source_url 必填。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")

    specs = dict(p.specs or {})
    changes: dict[str, Any] = {}
    diff: list[dict] = []
    for key, raw in payload.changes.items():
        where, field = _split(key)
        if where == "specs":
            if field not in SPEC_KEYS:
                raise HTTPException(422, f"specs.{field} 不在可改字段列表内")
            old = specs.get(field)
            new = _coerce(field, raw)
        else:
            if field not in TOP_FIELDS:
                raise HTTPException(422, f"{field} 不是可改字段")
            old = getattr(p, field)
            new = bool(raw) if field == "verified" else _coerce(field, raw)
        if old == new:
            continue
        changes[key] = new
        diff.append({"field": key, "old_value": old, "new_value": new})

    if not diff:
        return {"ok": True, "changed": 0, "note": "没有实际变化"}

    if "last_checked" not in changes:
        changes["last_checked"] = date.today().isoformat()
        diff.append({"field": "last_checked", "old_value": p.last_checked,
                     "new_value": changes["last_checked"]})

    s = _propose(db, p, changes, diff, user, payload.note, payload.source_url)
    return {"ok": True, "changed": len(diff), "submission_id": s.id,
            "status": s.status, "diff": diff,
            "preview": {"part_id": part_id, "changes": changes},
            "note": "已提交审核；目录在 release 后才会更新"}


@router.post("/parts/{part_id}/verify")
def admin_verify(part_id: str, user: CurrentUser, db: Db,
                 note: Annotated[str, Query(min_length=2)] = "逐项核对官方 datasheet"):
    """标记「已核对」也走提案：verified/last_checked 不能绕过 release。"""
    _staff(user)
    p = db.get(Part, part_id)
    if p is None:
        raise HTTPException(404, "零件不存在")
    today = date.today().isoformat()
    changes: dict[str, Any] = {}
    diff: list[dict] = []
    for field, new in (("verified", True), ("last_checked", today)):
        old = getattr(p, field)
        if old == new:
            continue
        changes[field] = new
        diff.append({"field": field, "old_value": old, "new_value": new})
    if not diff:
        return {"ok": True, "changed": 0, "note": "已经是核对状态"}
    s = _propose(db, p, changes, diff, user, note, p.url)
    return {"ok": True, "changed": len(diff), "submission_id": s.id,
            "status": s.status, "diff": diff}


@router.get("/history")
def admin_history(user: CurrentUser, db: Db,
                  limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """提案 + 已发布修改的流水，按时间倒序。"""
    _staff(user)
    edits = db.exec(select(PartEdit).order_by(PartEdit.created_at.desc())
                    .limit(limit)).all()
    proposals = db.exec(select(Submission).order_by(Submission.created_at.desc())
                        .limit(limit)).all()
    user_ids = {e.editor_id for e in edits if e.editor_id} | {
        s.submitter_id for s in proposals if s.submitter_id}
    editors = {u.id: u.display_name for u in
               db.exec(select(User).where(User.id.in_(user_ids))).all()} \
        if user_ids else {}
    rows = [{
        "id": f"edit-{e.id}", "part_id": e.part_id, "field": e.field,
        "old_value": e.old_value, "new_value": e.new_value, "note": e.note,
        "source_url": e.source_url, "editor": editors.get(e.editor_id),
        "created_at": e.created_at.isoformat(), "source": "release",
        "status": "released",
    } for e in edits]
    rows += [{
        "id": f"submission-{s.id}", "submission_id": s.id,
        "part_id": s.target_id, "field": ", ".join(sorted(s.payload or {})),
        "old_value": None, "new_value": None,
        "note": (s.evidence or {}).get("note"),
        "source_url": (s.evidence or {}).get("source_url"),
        "editor": editors.get(s.submitter_id),
        "created_at": s.created_at.isoformat(), "source": "proposal",
        "status": s.status,
    } for s in proposals]
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows[:limit]

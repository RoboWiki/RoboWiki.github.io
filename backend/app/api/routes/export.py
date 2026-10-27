"""导出：Draft 的 actuators.yaml + MuJoCo 关节参数。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlmodel import select

from ...models import Part
from ..deps import Db

router = APIRouter(prefix="/export", tags=["export"])


def _yaml_row(p: Part) -> str | None:
    s = p.specs
    tp, mass = s.get("tau_peak_Nm"), s.get("mass_kg")
    if not tp or not mass:
        return None
    gear, rpm = s.get("gear"), s.get("speed_noload_rpm")
    od, l = s.get("od_mm"), s.get("l_mm")
    j, basis = s.get("rotor_inertia_kgm2"), s.get("inertia_basis")

    def v(x):
        return "null" if x is None else x

    return (
        f"- name: {p.model}\n"
        f"  vendor: {p.vendor}\n"
        f"  source: {p.url or 'null'}\n"
        f"  tau_peak_Nm: {tp}\n"
        f"  mass_kg: {mass}\n"
        f"  no_load_rpm: {v(rpm)}\n"
        f"  P_peak_W: null\n"
        f"  gear: {v(gear)}\n"
        f"  OD_mm: {v(od)}\n"
        f"  L_mm: {v(l)}\n"
        f"  rotor_inertia:\n"
        f"    value: {round(j * 1e7, 3) if j else 'null'}\n"
        f"    unit: g.cm2\n"
        f"    kind: {basis or 'rotor'}\n"
        f"    source: {p.url or 'null'}\n"
        f'  notes: "{(p.notes or "")[:120]}"\n'
        f"  checked: '{p.last_checked or ''}'\n"
    )


@router.get("/draft")
def export_draft(
    db: Db,
    ids: Annotated[str | None, Query(description="逗号分隔；留空=导出所有有 armature 的执行器")] = None,
):
    if ids:
        wanted = [x for x in ids.split(",") if x]
        rows = db.exec(select(Part).where(Part.id.in_(wanted))).all()
    else:
        rows = db.exec(select(Part).where(
            Part.category == "actuator",
            func.json_extract(Part.specs, "$.armature_kgm2").isnot(None),
        ).order_by(Part.vendor, Part.model)).all()

    yaml_rows, mjcf = [], []
    for p in rows:
        y = _yaml_row(p)
        if y:
            yaml_rows.append(y)
        s = p.specs
        arm = s.get("armature_kgm2")
        if arm:
            rpm = s.get("speed_noload_rpm")
            mjcf.append({
                "part_id": p.id, "model": p.model, "armature": arm,
                "actuatorfrcrange": s.get("tau_peak_Nm"),
                "velocity_limit_rad_s": round(rpm * 3.141592653589793 / 30, 3)
                if rpm else None,
            })
    return {
        "n": len(mjcf),
        "actuators_yaml": "\n".join(yaml_rows),
        "mjcf_joints": mjcf,
        "note": "armature = N²·J。力矩-转速包络不在 MJCF 里，需在控制器侧实现。",
    }

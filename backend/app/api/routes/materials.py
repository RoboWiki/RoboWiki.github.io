"""材质库只读 API：材料 / 工艺列表、详情、分组。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from ...core.config import settings
from ...materials import (find_material, groups, load_materials,
                          public_material)

router = APIRouter(prefix="/materials", tags=["materials"])


def _matches(r: dict, q: str) -> bool:
    if not q:
        return True
    hay = " ".join(str(x) for x in (
        r.get("id"), r.get("name"), r.get("name_en"), r.get("model"),
        r.get("title"), r.get("family_label"), r.get("group_label"),
        " ".join(r.get("aliases") or []),
    ) if x).lower()
    return q.lower() in hay


@router.get("")
def list_materials(
    category: str | None = None,
    group: str | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    rows = load_materials()
    if category:
        rows = [r for r in rows if r.get("category") == category]
    if group:
        rows = [r for r in rows if r.get("group") == group]
    if q:
        rows = [r for r in rows if _matches(r, q)]
    return {
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "data_version": settings.data_version,
        "site_url": settings.site_url,
        "groups": groups(),
        "items": [public_material(r) for r in rows[offset:offset + limit]],
    }


@router.get("/meta")
def materials_meta():
    rows = load_materials()
    return {
        "total": len(rows),
        "materials": sum(1 for r in rows if r.get("category") == "material"),
        "processes": sum(1 for r in rows if r.get("category") == "process"),
        "groups": groups(),
        "data_version": settings.data_version,
        "site_url": settings.site_url,
    }


@router.get("/{item_id}")
def get_material(item_id: str):
    r = find_material(item_id)
    if r is None:
        raise HTTPException(404, "材料或工艺不存在")
    out = public_material(r)
    out["data_version"] = settings.data_version
    out["site_url"] = settings.site_url
    out["related"] = []
    refs = list(r.get("processes") or [])
    refs += list((r.get("specs") or {}).get("materials") or [])
    for rid in refs:
        x = find_material(rid)
        if x:
            out["related"].append({"id": x["id"], "name": x.get("name"),
                                   "category": x.get("category")})
    return out

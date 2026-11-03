"""材质库只读投影：从 release 的 data/materials 读取，不落库。

材料不是厂商 SKU，数量小（当前 36 条），按文件 mtime 缓存即可；写入仍走核心仓 PR。
"""
from __future__ import annotations

import json
from pathlib import Path

from .core.config import settings

_cache: dict[str, object] = {"stamp": None, "rows": []}


def _stamp(d: Path) -> tuple:
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in d.glob("*.json"))) \
        if d.exists() else ()


def load_materials() -> list[dict]:
    d = Path(settings.data_dir) / "materials"
    stamp = _stamp(d)
    if _cache["stamp"] == stamp:
        return _cache["rows"]  # type: ignore[return-value]
    rows: list[dict] = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            rows.extend(r for r in data if isinstance(r, dict))
    rows.sort(key=lambda r: (r.get("group") or "", r.get("name") or r.get("id") or ""))
    _cache["stamp"], _cache["rows"] = stamp, rows
    return rows


def groups() -> list[dict]:
    out: dict[str, dict] = {}
    for r in load_materials():
        gid = r.get("group") or "other"
        g = out.setdefault(gid, {"id": gid, "label": r.get("group_label") or gid,
                                 "count": 0})
        g["count"] += 1
    return list(out.values())


def public_material(r: dict) -> dict:
    """白名单投影：保留来源、规格、关联，不暴露内部缓存字段。"""
    return {
        "id": r.get("id"),
        "category": r.get("category"),
        "group": r.get("group"),
        "group_label": r.get("group_label"),
        "family": r.get("family"),
        "family_label": r.get("family_label"),
        "name": r.get("name"),
        "name_en": r.get("name_en"),
        "model": r.get("model"),
        "title": r.get("title"),
        "source_tier": r.get("source_tier"),
        "verified": bool(r.get("verified")),
        "last_checked": r.get("last_checked"),
        "origin": r.get("origin"),
        "url": r.get("url"),
        "sources": r.get("sources") or [],
        "specs": r.get("specs") or {},
        "forms": r.get("forms") or [],
        "applications": r.get("applications") or [],
        "pros": r.get("pros") or [],
        "cons": r.get("cons") or [],
        "notes": r.get("notes") or "",
        "processes": r.get("processes") or [],
        "suppliers": r.get("suppliers") or [],
    }


def find_material(item_id: str) -> dict | None:
    for r in load_materials():
        if r.get("id") == item_id:
            return r
    return None

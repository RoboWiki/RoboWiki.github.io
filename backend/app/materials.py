"""材质库只读投影：从 release 的 data/materials 读取，不落库。

材料不是厂商 SKU，数量小（当前 36 条），按文件 mtime 缓存即可；写入仍走`RoboWiki` 仓 PR。
"""
from __future__ import annotations

import json
from pathlib import Path

from .core.config import settings

_cache: dict[str, object] = {"stamp": None, "rows": [], "suppliers": None}


def _supplier_names() -> dict[str, str]:
    """渠道 id → 名称。材质 API 不把 suppliers.json 烤进响应，但引用要能显示人名。"""
    if _cache["suppliers"] is not None:
        return _cache["suppliers"]  # type: ignore[return-value]
    out: dict[str, str] = {}
    p = Path(settings.data_dir) / "suppliers.json"
    try:
        rows = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict) and r.get("id"):
                    out[str(r["id"])] = str(r.get("name") or r["id"])
    except (OSError, json.JSONDecodeError):
        out = {}
    _cache["suppliers"] = out
    return out


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


def material_web_path(r: dict) -> str:
    """与 pipeline/build_materials.py 的 _slug 同规则。

    小程序不再自己从 id 猜 URL；服务端直接给 canonical 路径。
    """
    rid = str(r.get("id") or "")
    prefix = "mat-" if r.get("category") == "material" else "proc-"
    base = rid[len(prefix):] if rid.startswith(prefix) else rid
    keep = "".join(ch if (ch.isalnum() and ch.isascii()) else "-" for ch in base.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    slug = keep.strip("-") or "item"
    href = "process-" + slug if r.get("category") == "process" else slug
    return f"/materials/{href}.html"


def public_material(r: dict) -> dict:
    """白名单投影：保留来源、规格、关联，不暴露内部缓存字段。"""
    names = _supplier_names()
    suppliers = []
    for s in r.get("suppliers") or []:
        sid = s.get("supplier_id") or s.get("id")
        suppliers.append({
            **s,
            "id": sid,
            "name": names.get(str(sid)) or s.get("name") or sid,
        })
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
        "suppliers": suppliers,
        "web_path": material_web_path(r),
    }


def find_material(item_id: str) -> dict | None:
    for r in load_materials():
        if r.get("id") == item_id:
            return r
    return None

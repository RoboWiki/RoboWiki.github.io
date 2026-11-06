"""方案库只读投影：从 release 的 data/robots 读取，不落库。

方案不是部件 SKU，数量小（当前 21 条），按文件 mtime 缓存即可；
写入仍走 `RoboWiki` 仓 PR。slug 规则必须与 pipeline/build_robots.py 一致，
否则服务端给的 web_path 会和静态站对不上。
"""
from __future__ import annotations

import json
from pathlib import Path

from .core.config import settings

_cache: dict[str, object] = {"stamp": None, "rows": [], "ecosystems": {}}

#: 列表卡片上的四项关键参数：字段 → (中文标签, 单位)。
#: 单位只补在纯数值上；源数据若已写成「3 h（空载）」这类字符串就原样保留。
_KEY_SPECS = (
    ("dof", "自由度", "自由度"),
    ("mass_kg", "质量", "kg"),
    ("endurance_h", "续航", "h"),
    ("payload_kg", "负载", "kg"),
)


def _slug(rid: str) -> str:
    """与 pipeline/build_robots.py::slug 同规则。"""
    base = rid[len("struct-"):] if rid.startswith("struct-") else rid
    keep = "".join(ch if (ch.isalnum() and ch.isascii()) else "-"
                   for ch in base.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-") or "robot"


def _stamp(d: Path) -> tuple:
    """机器人分片 + 生态映射的 mtime 一起当缓存戳。"""
    files = sorted(d.glob("*.json")) if d.exists() else []
    eco = d.parent / "robot_ecosystem.json"
    return tuple((p.name, p.stat().st_mtime_ns) for p in files) + \
        (("__eco__", eco.stat().st_mtime_ns) if eco.exists() else ())


def _load_ecosystems() -> dict:
    p = Path(settings.data_dir) / "robot_ecosystem.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    robots = data.get("robots") if isinstance(data, dict) else None
    return robots if isinstance(robots, dict) else {}


def load_builds() -> list[dict]:
    d = Path(settings.data_dir) / "robots"
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
    for r in rows:
        slug = _slug(str(r.get("id") or ""))
        r["slug"] = slug
        r["web_path"] = f"/builds/{slug}.html"
    rows.sort(key=lambda r: (r.get("vendor_cn") or r.get("vendor") or "",
                             r.get("model") or r.get("title") or "",
                             r.get("id") or ""))
    _cache["stamp"], _cache["rows"] = stamp, rows
    _cache["ecosystems"] = _load_ecosystems()
    return rows


def ecosystems() -> dict:
    """ecosystem_id → {label,count,roles,projects}。"""
    load_builds()
    return _cache["ecosystems"]  # type: ignore[return-value]


def find_build(build_id: str) -> dict | None:
    for r in load_builds():
        if r.get("id") == build_id:
            return r
    return None


def _fmt_spec(value: object, unit: str) -> str | None:
    """null 跳过；纯数值补单位，字符串（常已带单位/工况）原样返回。"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        text = f"{value:g}"
        return f"{text} {unit}" if unit else text
    text = str(value).strip()
    return text or None


def key_specs(r: dict) -> list[dict]:
    specs = r.get("specs") or {}
    out: list[dict] = []
    for key, label, unit in _KEY_SPECS:
        value = _fmt_spec(specs.get(key), unit)
        if value is not None:
            out.append({"key": key, "label": label, "value": value})
    return out


def public_build(r: dict) -> dict:
    """白名单投影：保留展示与溯源字段，不把内部缓存字段带出去。"""
    specs = r.get("specs") or {}
    return {
        "id": r.get("id"),
        "slug": r.get("slug") or _slug(str(r.get("id") or "")),
        "subtype": r.get("subtype"),
        "subtype_label": r.get("subtype_label"),
        "vendor": r.get("vendor"),
        "vendor_cn": r.get("vendor_cn"),
        "model": r.get("model"),
        "title": r.get("title"),
        "url": r.get("url"),
        "source_tier": r.get("source_tier"),
        "verified": bool(r.get("verified")),
        "last_checked": r.get("last_checked"),
        "price_cny": r.get("price_cny"),
        "image_url": specs.get("image_url"),
        "key_specs": key_specs(r),
        "web_path": r.get("web_path") or f"/builds/{_slug(str(r.get('id') or ''))}.html",
    }


def build_detail(r: dict, eco: dict) -> dict:
    """列表字段 + 完整规格、说明与开源生态条目。"""
    specs = r.get("specs") or {}
    out = public_build(r)
    out.update({
        "specs": specs,
        "notes": r.get("notes") or "",
        "origin": r.get("origin"),
        "ecosystem": eco.get(str(specs.get("ecosystem_id") or "")),
    })
    return out

"""构建期分享产物：每个部件一张可转发的 JSON 卡。

不做 PNG 渲染（需要字体/图像依赖）；先把“一句话 + 参数 + 来源 + 版本 + URL”
做成稳定 JSON，Web 组件、QQ 机器人、后续分享图都从这里取同一份文案。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


def _fmt(v, unit: str = "") -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, float):
        s = f"{v:g}"
    else:
        s = str(v)
    return f"{s}{unit}"


def _summary(specs: dict) -> str:
    parts = []
    for label, key, unit in (
        ("峰值", "tau_peak_Nm", " N·m"),
        ("额定", "tau_rated_Nm", " N·m"),
        ("电压", "voltage_V", " V"),
        ("质量", "mass_kg", " kg"),
    ):
        v = _fmt(specs.get(key), unit)
        if v:
            parts.append(f"{label} {v}")
    return " · ".join(parts[:4])


def _params(specs: dict) -> list[dict]:
    out = []
    for label, key, unit in (
        ("峰值扭矩", "tau_peak_Nm", " N·m"),
        ("额定扭矩", "tau_rated_Nm", " N·m"),
        ("减速比", "gear", ":1"),
        ("电压", "voltage_V", " V"),
        ("质量", "mass_kg", " kg"),
        ("通信", "comm", ""),
        ("编码器", "encoder", ""),
    ):
        v = _fmt(specs.get(key), unit)
        if v:
            out.append({"label": label, "value": v})
    return out


def build(rows: list[dict], slugs: dict[str, str], out: Path,
          site_url: str, data_version: str) -> int:
    base = out / "public" / "share"
    if base.exists():
        shutil.rmtree(base)
    (base / "parts").mkdir(parents=True, exist_ok=True)

    index: list[dict] = []
    for r in rows:
        rid = r["id"]
        slug = slugs.get(rid)
        if not slug:
            continue
        cat = r["category"]
        specs = r.get("specs") or {}
        url = f"{site_url.rstrip('/')}/parts/{cat}/{slug}"
        title = r["title"]
        summary = _summary(specs)
        tier = r.get("source_tier", "B")
        checked = r.get("last_checked") or ""
        image = specs.get("image_url")
        params = _params(specs)

        copy = "\n".join(x for x in [
            f"[部件] {title}",
            summary,
            f"{tier} 级来源 · 最近核对 {checked} · 数据 {data_version}",
            url,
        ] if x)

        payload = {
            "kind": "part",
            "id": rid,
            "title": title,
            "summary": summary,
            "params": params,
            "source_tier": tier,
            "last_checked": checked,
            "data_version": data_version,
            "canonical_url": url,
            "image_url": (site_url.rstrip("/") + image) if image else None,
            "copy_text": copy,
        }
        d = base / "parts" / cat
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        index.append({
            "path": f"/parts/{cat}/{slug}",
            "json": f"/share/parts/{cat}/{slug}.json",
            "title": title,
            "summary": summary,
            "data_version": data_version,
        })

    (base / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(index)

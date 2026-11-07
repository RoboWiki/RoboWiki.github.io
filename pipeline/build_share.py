"""构建期分享产物：每个部件/材质一张可转发的 JSON 卡。

JSON 是文案的唯一来源；分享图由浏览器按这份 JSON 用 Canvas 绘制，
避免构建链依赖字体/图像库，也避免每个页面预生成几十 MB 图片。
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


#: 材质/工艺分享卡上最有判别度的字段；与页面标签保持一致，不引入第二套口径。
_MAT_FACTS = [
    ("密度", "density_g_cm3", " g/cm³"),
    ("弹性模量", "modulus_GPa", " GPa"),
    ("抗拉强度", "tensile_MPa", " MPa"),
    ("长期温度", "service_temp_C", " °C"),
]
_PROC_FACTS = [
    ("公差", "tolerance_mm", " mm"),
    ("表面粗糙度", "surface_ra_um", " µm"),
    ("层高", "layer_height_mm", " mm"),
    ("最小壁厚", "min_wall_mm", " mm"),
]


def _material_facts(r: dict) -> list[dict]:
    specs = r.get("specs") or {}
    facts = _MAT_FACTS if r.get("category") == "material" else _PROC_FACTS
    out: list[dict] = []
    for label, key, unit in facts:
        v = _fmt(specs.get(key), unit)
        if v:
            if key == "modulus_GPa" and specs.get("modulus_kind") == "弯曲":
                label = "弯曲模量"
            out.append({"key": key, "label": label, "value": v})
    return out


def build_materials(rows: list[dict], pub: Path, site_url: str,
                    data_version: str) -> int:
    """材质/工艺分享卡；追加进 share/index.json，供 ShareBox 与二维码复用。"""
    base = pub / "share" / "materials"
    base.mkdir(parents=True, exist_ok=True)
    index_path = pub / "share" / "index.json"
    index: list[dict] = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = []

    written = 0
    for r in rows:
        href = r.get("_href")
        if not href:
            continue
        kind = "process" if r.get("category") == "process" else "material"
        title = r.get("name") or r["id"]
        params = _material_facts(r)
        summary = " · ".join(f"{x['label']} {x['value']}" for x in params[:4])
        url = f"{site_url.rstrip('/')}/materials/{href}.html"
        tier = r.get("source_tier", "B")
        checked = r.get("last_checked") or ""
        copy = "\n".join(x for x in [
            f"[{'工艺' if kind == 'process' else '材质'}] {title}",
            summary,
            f"{tier} 级来源 · 最近核对 {checked} · 数据 {data_version}",
            url,
        ] if x)

        payload = {
            "kind": kind,
            "id": r["id"],
            "title": title,
            "summary": summary,
            "params": params,
            "use_cases": r.get("applications") or [],
            "source_tier": tier,
            "verified": bool(r.get("verified")),
            "last_checked": checked,
            "data_version": data_version,
            "canonical_url": url,
            "image_url": None,
            "copy_text": copy,
        }
        (base / f"{href}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        index.append({
            "id": r["id"],
            "path": f"/materials/{href}",
            "url": url,
            "json": f"/share/materials/{href}.json",
            "title": title,
            "summary": summary,
            "source_tier": tier,
            "verified": bool(r.get("verified")),
            "last_checked": checked,
            "data_version": data_version,
        })
        written += 1

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return written



#: 每个品类一句话里最有用的字段；顺序即展示顺序
_FACTS: dict[str, list[tuple[str, str, str]]] = {
    "actuator": [("峰值", "tau_peak_Nm", " N·m"), ("额定", "tau_rated_Nm", " N·m"),
                 ("电压", "voltage_V", " V"), ("质量", "mass_kg", " kg")],
    "controller_high": [("NPU", "npu_tops", " TOPS"), ("CPU", "cpu", ""),
                        ("内存", "ram_gb", " GB"), ("功耗", "power_max_w", " W")],
    "controller_low": [("MCU", "mcu", ""), ("CAN", "can", ""),
                       ("电压", "voltage_in_V", " V")],
    "motor_driver": [("MCU", "mcu", ""), ("CAN", "can", ""),
                      ("最高电压", "voltage_max_V", " V")],
    "imu": [("陀螺", "gyro_range_dps", " °/s"), ("接口", "iface", ""),
            ("噪声", "noise", "")],
    "camera": [("深度", "depth_range_m", " m"), ("视场", "fov", ""),
               ("帧率", "fps", " fps")],
    "lidar": [("量程", "range_m", " m"), ("视场", "fov", ""),
              ("点频", "points_per_s", " pts/s")],
    "connector": [("位数", "positions", " pin"), ("间距", "pitch_mm", " mm"),
                  ("电流", "current_rated_A", " A"), ("电压", "voltage_rated_V", " V"),
                  ("线规", "wire_awg", ""), ("插拔", "mating_cycles", " 次")],
    "module": [("接口", "iface", ""), ("CAN", "can", ""),
               ("电压", "voltage_V", " V")],
    "chip": [("封装", "package", ""), ("料号", "lcsc_part", ""),
             ("输入", "voltage_in", ""), ("输出", "voltage_out", "")],
    "open_hw": [("输入", "voltage_in", ""), ("输出", "voltage_out", ""),
                ("电流", "current_out", ""), ("接口", "iface", "")],
}
_GENERIC = [("电压", "voltage_V", " V"), ("接口", "iface", ""),
            ("CAN", "can", ""), ("通道", "channel", "")]


def _spec_lines(category: str, specs: dict) -> list[dict]:
    out = []
    for label, key, unit in _FACTS.get(category, []) + _GENERIC:
        v = _fmt(specs.get(key), unit)
        if v and not any(x["label"] == label for x in out):
            out.append({"key": key, "label": label, "value": v})

    # 传感器 / 芯片的结构化参数在 specs.params（中文标签 → 值）；
    # 不读它，83 张分享卡会只剩空 summary。
    if len(out) < 4:
        params = specs.get("params")
        if isinstance(params, dict):
            for k, v in params.items():
                if len(out) >= 4:
                    break
                text = _fmt(v)
                if text:
                    out.append({"key": f"param:{k}", "label": str(k), "value": text})
    return out


def _summary(category: str, specs: dict) -> str:
    return " · ".join(f"{x['label']} {x['value']}"
                      for x in _spec_lines(category, specs)[:4])


def _params(category: str, specs: dict) -> list[dict]:
    return _spec_lines(category, specs)[:7]


def build(rows: list[dict], slugs: dict[str, str], pub: Path,
          site_url: str, data_version: str) -> int:
    base = pub / "share"
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
        url = f"{site_url.rstrip('/')}/parts/{cat}/{slug}.html"
        title = r["title"]
        summary = _summary(cat, specs)
        tier = r.get("source_tier", "B")
        verified = bool(r.get("verified")) and tier == "A"
        checked = r.get("last_checked") or ""
        image = specs.get("image_url")
        params = _params(cat, specs)

        copy = "\n".join(x for x in [
            f"[部件] {title}",
            summary,
            f"{tier} 级来源 · {'已核对' if verified else '最近检查'} {checked} · 数据 {data_version}",
            url,
        ] if x)

        payload = {
            "kind": "part",
            "id": rid,
            "title": title,
            "summary": summary,
            "params": params,
            "use_cases": specs.get("use_cases") or [],
            "source_tier": tier,
            "verified": verified,
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
            "id": rid,
            "path": f"/parts/{cat}/{slug}",
            "url": url,
            "json": f"/share/parts/{cat}/{slug}.json",
            "title": title,
            "summary": summary,
            "source_tier": tier,
            "verified": verified,
            "last_checked": checked,
            "data_version": data_version,
        })

    (base / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(index)

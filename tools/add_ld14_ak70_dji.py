"""A 组收尾三件：
① 乐动 LD14 入库（微雪官方 wiki 参数表）
② CubeMars AK70-10 入库（cubemars.com/cn 官方产品页：10:1、Ø89×50.25、621 g、
   额定 8.3 / 峰值 24.8 N·m、空载 480 rpm、24/48 V）
③ 大疆 GM6020 / M2006：官方页只给「最大持续扭矩」，没有峰值/堵转值
   → 填额定并把「无峰值」写进 notes，不再让 tau_peak 空着像个漏填
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
TODAY = "2026-10-31"


def append(path: pathlib.Path, rows: list[dict]) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    ids = {r.get("id") for r in data}
    for r in rows:
        if r["id"] not in ids:
            data.append(r)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  {path.name}: {len(data)} 条")


# ── ① LD14 ─────────────────────────────────────────────────────
ld14 = {
    "id": "sens-ldrobot-ld14", "category": "lidar", "subtype": "mechanical",
    "vendor": "乐动 LDROBOT", "vendor_cn": "乐动",
    "model": "LD14", "title": "乐动 LD14 三角测距雷达",
    "url": "https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14",
    "source_tier": "B", "verified": 0, "last_checked": TODAY, "price_cny": None,
    "origin": "微雪 Wiki《Triangulation LiDAR LD14》产品参数表（2026-10-31 抓取）；型号属乐动 LDROBOT",
    "notes": ("三角测量法，非 DTOF；量程 0.15–8 m、采样 2300 Hz、扫描 6 Hz、角分辨率 ≤1°。"
              "精度分三段：5 mm(<1 m) / 1.5%(1–6 m) / 2%(6–8 m)，已写进 accuracy。"
              "微雪商城另有 LD14P（0.1–8 m、4000 Hz），是不同型号，未合并。"),
    "specs": {
        "range_m": 8, "range_note": "0.15–8 m（三角测距，无反射率分档）",
        "points_per_s": 2300, "fps": 6, "iface": "UART 115200",
        "voltage_V": 5, "power_w": 1.3, "size_mm": "96.3×59.8×38.8",
        "accuracy": "5 mm(<1 m)；1.5% 实际距离(1–6 m)；2%(6–8 m)",
        "temp_range_C": "-10~40", "fov": "360°",
        "image_url": None, "image_source": None,
        "doc_url": "https://www.waveshare.net/wiki/Triangulation_LiDAR_LD14",
        "doc_pdf": None, "repo_urls": None, "repo_license": None,
    },
}

# ── ② CubeMars AK70-10 ────────────────────────────────────────
ak70 = {
    "id": "cubemars-ak70-10", "category": "actuator", "subtype": "planetary",
    "vendor": "CubeMars", "vendor_cn": "CubeMars",
    "model": "AK70-10", "title": "CubeMars AK70-10 关节模组（KV100）",
    "url": "https://www.cubemars.com/cn/product/ak70-10-kv100-robotic-actuator.html",
    "source_tier": "B", "verified": 0, "last_checked": TODAY, "price_cny": None,
    "origin": "CubeMars 中文站产品页（2026-10-31 抓取）",
    "notes": "10:1 行星减速、支持位置/速度/力矩/MIT 混合模式、驱动与编码器集成；24/48 V 双电压。",
    "specs": {
        "gear": 10, "tau_rated_Nm": 8.3, "tau_peak_Nm": 24.8, "tau_basis": "peak",
        "speed_noload_rpm": 480, "mass_kg": 0.621, "od_mm": 89, "l_mm": 50.25,
        "voltage_range_V": "24~48",
        "doc_url": "https://www.cubemars.com/cn/product/ak70-10-kv100-robotic-actuator.html",
        "doc_pdf": None, "repo_urls": None, "repo_license": None,
        "image_url": None, "image_source": None,
    },
}

append(ROOT / "data/catalog/lidar/ldrobot.json", [ld14])
append(ROOT / "data/catalog/actuator/cubemars.json", [ak70])

# ── ③ 大疆：额定已填、明确「官方无峰值」───────────────────────────
DJI_NOTE = ("【官方口径】大疆产品页只给「额定扭矩（最大持续扭矩）」与「1 N·m 下最大转速」，"
            "没有峰值/堵转扭矩；tau_peak 保持 null 是如实记录，不是漏填。"
            "来源：robomaster.com 官方组件页，2026-10-31 核对。")
f = ROOT / "data/catalog/actuator/dji-robomaster.json"
rows = json.loads(f.read_text(encoding="utf-8"))
for r in rows:
    m = str(r.get("model"))
    sp = r.setdefault("specs", {})
    if m == "GM6020":
        sp.setdefault("tau_rated_Nm", 1.2)
        sp["voltage_V"] = sp.get("voltage_V") or 24
        sp["speed_noload_rpm"] = sp.get("speed_noload_rpm") or 320
        sp["speed_rated_rpm"] = sp.get("speed_rated_rpm") or 132
        sp["i_rated_A"] = sp.get("i_rated_A") or 1.62
        r["notes"] = (r.get("notes") or "") + " " + DJI_NOTE
    if m == "M2006 P36":
        sp.setdefault("tau_rated_Nm", 1.0)
        sp["speed_noload_rpm"] = sp.get("speed_noload_rpm") or 500
        sp["gear"] = sp.get("gear") or 36
        r["notes"] = (r.get("notes") or "") + " " + DJI_NOTE
f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("大疆 GM6020 / M2006：额定已填，峰值缺失原因写进 notes")

# 厂商登记（乐动已有）

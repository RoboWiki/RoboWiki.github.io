"""按用户勾选落地：① 高擎 10 款 ② STACKFORCE 2 款 ③ 雷达 STL-27L + LD19（停产照收）⑤ 两条价格回填。

微雪模块（④）按要求不做。

纪律：
  · 高擎官网产品表只给 尺寸/重量/减速比/扭矩（部分给转速），字段不足我们 A 级键集，
    所以标 B，并在 notes 写明「官网产品表，字段不全，缺 XX」——不假装 A。
  · STACKFORCE 参数表较全（电压/电流/功率/扭矩/转速/减速比/相电阻/相电感），仍标 B：
    一手来源是 Seeed wiki + 厂商 PDF，未取到原厂官网规格页。
  · LD19 已停产：照收，但 price 留空、notes 写清「停产下架，二手/库存为主」。
  · 品牌名：高擎 → "High Torque Robotics 高擎动力"；STACKFORCE 中文名未核实 → vendor_cn 留空。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
TODAY = "2026-10-31"
SRC_HT = "High Torque Robotics 官网产品页（hightorquerobotics.com/product，2026-10-31）"
SRC_SF = ("Seeed wiki zh-CN《Stackforce 系列电机》+ 厂商 PDF《新版6010关节电机用户文档V1.1》"
          "（2026-10-31）；原厂官网规格页未取到")
SRC_LD = "微雪 Wiki / 商城（2026-10-31）；型号属乐动 LDROBOT"


def act(subtype: str, vid: str, model: str, vendor: str, cn: str, url: str,
        origin: str, notes: str, specs: dict) -> dict:
    return {
        "id": vid, "category": "actuator", "subtype": subtype,
        "vendor": vendor, "vendor_cn": cn, "model": model,
        "title": f"{vendor.split()[0]} {model}", "url": url,
        "source_tier": "B", "verified": 0, "last_checked": TODAY, "price_cny": None,
        "origin": origin, "notes": notes, "specs": {k: v for k, v in specs.items() if v is not None},
    }


# ── ① 高擎 10 款（官网表：尺寸/重量/减速比/扭矩）────────────────
HT = [
    # model, L, H, 重量g, 减速比, 额定N·m, 堵转N·m, 空载rpm, 额定rpm, 功率W
    ("HTDW-5036-02-DNE", 50, 47.4, 323, 36, 6, None, None, None, None),
    ("HTDW-5036-02-CNE", 50, 47.4, 345, 36, None, 21, None, None, None),
    ("HTDW-6036-02-DNE", 60, 56, 565, 36, 10, None, None, None, None),
    ("HTDW-6036-02-CNE", 60, 56, 570, 36, None, None, 60, None, None),
    ("HTDW-7535-02-CNE", 75, 56, 850, 35, None, 60, None, None, None),
    ("HTPU-7033-04-CNE", 140.5, 36.9, 808, 33, 20, 50, 48, 40, 84),
    ("HTPU-6035-04-CNE", 115, 37, 558, 35, 10, 36, 60, 50, 52),
    ("HTCP-5031-06-CYC", 50, 53, 385, 31, 4, None, None, None, None),
    ("HTCP-4531-06-CYC", 44, 44.9, 237, 31, 2, None, None, None, None),
    ("HTPW-7507-02-DNE", 75, 35, 390, 7, 4, None, None, None, None),
]
HT_ROWS = []
for model, L, H, mass, gear, tau_r, tau_l, rpm_nl, rpm_r, power in HT:
    specs = {
        "gear": gear, "mass_kg": round(mass / 1000, 4),
        "tau_rated_Nm": tau_r, "tau_peak_Nm": tau_l,
        "tau_basis": "peak" if tau_l else ("rated" if tau_r else None),
        "speed_noload_rpm": rpm_nl, "speed_rated_rpm": rpm_r,
        "power_w": power, "od_mm": L, "l_mm": H,
    }
    miss = [k for k, v in (("额定扭矩", tau_r), ("堵转/峰值扭矩", tau_l),
                           ("转速", rpm_nl or rpm_r), ("功率", power),
                           ("电压", None), ("极对数", None), ("编码器", None)) if not v]
    HT_ROWS.append(act(
        "planetary", f"hightorque-{model.lower()}", model,
        "High Torque Robotics 高擎动力", "高擎动力",
        "https://www.hightorquerobotics.com/product", SRC_HT,
        f"官网产品表只给外形/重量/减速比/扭矩（部分给转速）；缺 {'、'.join(miss)}，"
        f"故标 B，不按 A 级键集补空值。系列：{model.split('-')[0]}。",
        specs,
    ))

# ── ② STACKFORCE 6010 / 8108 ────────────────────────────────────
SF = [
    # model, I(A), P(W), tau_r, tau_p, rpm_r, rpm_max, OD, H, mass, R, L_uH
    ("6010", 10.5, 240, 5, 11, 120, 270, 80, 47, 392, 0.48, 368),
    ("8108", 7.5, 180, 7.5, 22, 110, 320, 97, 46, 395, 0.439, 403),
]
SF_ROWS = [
    act("planetary", f"stackforce-{m}", m, "STACKFORCE", "",
        "https://github.com/Seeed-Projects/Stackforce-Motor-SDK", SRC_SF,
        f"8:1、MIT 协议、CAN 2.0 1 Mbps 或 CANFD 5 Mbps、双磁编；缺极对数与编码器位数。"
        f"厂商中文名未核实，vendor_cn 留空。",
        {"gear": 8, "voltage_V": 24, "i_rated_A": i, "power_w": p,
         "tau_rated_Nm": tr, "tau_peak_Nm": tp, "tau_basis": "peak",
         "speed_rated_rpm": rr, "speed_noload_rpm": rmax,
         "od_mm": od, "l_mm": h, "mass_kg": round(mass / 1000, 4),
         "r_phase_ohm": r, "l_phase_uh": lu,
         "iface": "CAN 2.0 1 Mbps / CANFD 5 Mbps（MIT 协议）"})
    for m, i, p, tr, tp, rr, rmax, od, h, mass, r, lu in SF
]

# ── ③ 雷达：STL-27L（在售）+ LD19（停产）─────────────────────────
def lidar(vid: str, model: str, notes: str, specs: dict, tier: str = "B") -> dict:
    base = {"id": vid, "category": "lidar", "subtype": "mechanical",
            "vendor": "乐动 LDROBOT", "vendor_cn": "乐动",
            "model": model, "title": f"乐动 {model}", "url": "https://www.ldrobot.com/",
            "source_tier": tier, "verified": 0, "last_checked": TODAY, "price_cny": None,
            "origin": SRC_LD, "notes": notes,
            "specs": {k: v for k, v in specs.items() if v is not None}}
    return base


LIDARS = [
    lidar("sens-ldrobot-stl27l", "STL-27L",
          "单线 DTOF；量程按反射率分档（80% 白靶 25 m / 4% 黑靶 10 m）。"
          "微雪商城在售（SKU 24782），渠道价未公开，price 留空。",
          {"range_m": 25, "range_note": "0.03–25 m @80% 白靶；0.03–10 m @4% 黑靶",
           "points_per_s": 21600, "fps": 13, "iface": "UART",
           "voltage_V": 5, "ip": "IP65", "size_mm": "38.6×38.6×33.5",
           "accuracy": "±15 mm @0.03–2 m"}),
    lidar("sens-ldrobot-ld19", "LD19",
          "⚠️ 已停产：微雪商城原文「本产品已停产下架，推荐选购抗强光升级替代方案」。"
          "仍收录 —— 赛季里二手/库存渠道常见，价格与在售价不可比，price 留空。",
          {"range_m": 12, "range_note": "0.02–12 m @80% 白靶",
           "points_per_s": 4500, "fps": 10, "iface": "UART 230400",
           "voltage_V": 5, "power_w": 0.9, "size_mm": "38.6×38.6×33.5",
           "accuracy": "10 mm @0.3–12 m", "ip": "IP54"}),
]


def append(path: pathlib.Path, rows: list[dict]) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    ids = {r.get("id") for r in data}
    for r in rows:
        if r["id"] not in ids:
            data.append(r)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  {path.name}: {len(data)} 条")


def main() -> None:
    act_dir = ROOT / "data/catalog/actuator"
    append(act_dir / "hightorque.json", HT_ROWS)
    append(act_dir / "stackforce.json", SF_ROWS)

    ld = ROOT / "data/catalog/lidar/ldrobot.json"
    append(ld, LIDARS)

    # ⑤ 价格回填
    for f, model, price in (
        (ROOT / "data/catalog/lidar/third-party.json", "Mid-70", 5999.0),
        (act_dir / "cubemars.json", "AK80-6", 3288.0),
    ):
        rows = json.loads(f.read_text(encoding="utf-8"))
        for r in rows:
            if str(r.get("model")) == model:
                r["price_cny"] = price
                r["notes"] = (r.get("notes") or "") + (
                    f" 【价格 {price:.0f} 元，官方渠道在售，2026-10-31 核实】")
        f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 厂商登记
    tp = ROOT / "data/taxonomy.json"
    tax = json.loads(tp.read_text(encoding="utf-8"))
    for name, meta in (
        ("High Torque Robotics 高擎动力", {"slug": "hightorque", "cn": "高擎动力"}),
        ("STACKFORCE", {"slug": "stackforce", "cn": ""}),
        ("乐动 LDROBOT", {"slug": "ldrobot", "cn": "乐动"}),
    ):
        if name not in tax["vendors"]:
            tax["vendors"][name] = meta
            print("  登记厂商:", name)
    tp.write_text(json.dumps(tax, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

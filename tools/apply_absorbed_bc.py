"""A/B/C/D + E1/E3 数据落地（用户勾选的批次）。

A：`tools/fill_doc_pdf.py` 已跑（32 条 doc_pdf）。
本脚本做 B/C/D/E：
  B 补 null 字段（宇树 IM6014/A1、灵足 9 款、Livox Mid-70/HAP/Mid-360、RoboSense Airy）
  C 纠错与冲突记录（J8009、gemini-335 降级、灵足 4 处冲突）
  D 新增型号：达妙 G6220/H6215/H65/S2325/S3519、小米 CyberGear Micro、Livox Mid-360S
  E1 CubeMars AK80-6（新厂商）、E3 脉塔 MyActuator X 系列 6 款（新厂商）

纪律：
  · 只填**该行已存在的键**，不新增键（避免破坏 A 级键集同构）
  · 数值只来自可指明来源的材料，来源写进 notes/origin；能确认是 B 级的就标 B
  · 新增行 id 全 ASCII，稍后由 tools/id_registry.py 登记
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
SRC = "wiki.aifitlab（aifitlab 手册英文机翻镜像，2026-10-31 抓取）；待原厂中文手册复核"
SRC_LIDAR = "wiki.aifitlab Livox 手册；与官网规格页交叉核对"
SRC_MYACT = "Seeed wiki（zh-CN）MyActuator X 系列规格表，2026-10-31 抓取"
TODAY = "2026-10-31"


def load(f: pathlib.Path) -> list[dict]:
    return json.loads(f.read_text(encoding="utf-8"))


def save(f: pathlib.Path, rows: list[dict]) -> None:
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def fill(row: dict, mapping: dict, skipped: list[str]) -> None:
    sp = row.setdefault("specs", {})
    for k, v in mapping.items():
        if k not in sp:
            skipped.append(f"{row.get('model')}:{k}")
            continue
        if sp[k] in (None, ""):
            sp[k] = v


def main() -> None:
    skipped: list[str] = []
    act = ROOT / "data/catalog/actuator"

    # ── B1/B2 宇树 ────────────────────────────────────────────
    f = act / "unitree.json"
    rows = load(f)
    for r in rows:
        m = str(r.get("model", ""))
        if m == "IM6014":
            fill(r, {
                "voltage_V": 24, "voltage_range_V": "24~75", "i_peak_A": 40,
                "encoder": "双编（转子侧 + 输出侧），单圈绝对 15 bit",
                "comm": "RS-485，6 Mbps / 4 Mbps，8N1，总线轮询 10 kHz",
                "temp_range": "-20~50 ℃",
            }, skipped)
            r["notes"] = (r.get("notes") or "") + " 【${SRC}】".replace("${SRC}", SRC)
        elif m == "Unitree A1":
            fill(r, {
                "voltage_V": 24, "voltage_range_V": "12~30", "i_peak_A": 40,
                "encoder": "电机侧单圈绝对 15 bit",
                "comm": "高速 RS-485，4.8 MBd，8N1，控制 1 kHz",
                "kt_Nm_per_A": 0.8732, "gear": 9.1,
            }, skipped)
            r["notes"] = (r.get("notes") or "") + (
                f" 【减速比按 1:9（正文代码用 9.1）结案；来源：{SRC}】")
    save(f, rows)

    # ── B3/B4/B5 灵足 ─────────────────────────────────────────
    f = act / "lingzu-robstride.json"
    rows = load(f)
    POLE = {"RS00": 14, "RS01": 14, "RS02": 14, "RS02-IP67": 14, "RS06": 14,
            "RS03": 21, "RS04": 21, "RS05": 10, "EL05": 10}
    for r in rows:
        m = str(r.get("model", "")).upper().replace("ROBSTRIDE ", "RS").replace("RS-", "RS")
        pole = next((v for k, v in POLE.items() if m.startswith(k)), None)
        fill(r, {"speed_rated_rpm": 100,
                 "encoder": "双编（输入侧 + 输出侧），14 bit 单圈绝对"}, skipped)
        if pole:
            fill(r, {"pole_pairs": pole}, skipped)
    save(f, rows)

    # ── B6–B9 雷达 ────────────────────────────────────────────
    f = ROOT / "data/catalog/lidar/third-party.json"
    rows = load(f)
    for r in rows:
        if "Mid-70" in str(r.get("model")):
            fill(r, {
                "range_m": 90, "points_per_s": 100000, "ip": "IP67",
                "temp_range_C": "-20~65", "power_w": 8, "voltage_V": 12,
                "size_mm": "97×64×62.7", "weight_g": 580,
                "absolute": "≤2 cm @20 m (1σ)",
            }, skipped)
            r["range_note"] = "90 m @10% 反射率；130 m @20%；260 m @80%（官网口径）"
            r["notes"] = (r.get("notes") or "") + f" 【补齐参数来源：{SRC_LIDAR}】"
    save(f, rows)

    f = ROOT / "data/catalog/lidar/livox.json"
    rows = load(f)
    for r in rows:
        m = str(r.get("model", ""))
        if m == "HAP":
            fill(r, {"absolute": "≤2 cm @20 m (1σ)", "voltage_range": "9~18 V"}, skipped)
            r["notes"] = (r.get("notes") or "") + (
                " 【IP67 仅在接上电源 + 车载以太网两根线时成立，否则 IP54；来源：Livox 手册】")
        elif "Mid-360" == m:
            fill(r, {"imu": "ICM40609"}, skipped)
    save(f, rows)

    f = ROOT / "data/catalog/lidar/robosense.json"
    rows = load(f)
    for r in rows:
        if str(r.get("model")) == "Airy":
            fill(r, {"ip": "IP67 / IP6K9K", "temp_range_C": "-40~60",
                     "absolute": "1.5 cm @1σ（典型值）"}, skipped)
            r["notes"] = (r.get("notes") or "") + (
                " 【精度口径按手册 1.5 cm@1σ；官网另有 1 cm 说法，以手册为准】")
    save(f, rows)

    # ── C 纠错与冲突记录 ──────────────────────────────────────
    f = act / "damiao.json"
    rows = load(f)
    for r in rows:
        m = str(r.get("model", ""))
        if m == "DM-J8009-2EC":
            r["notes"] = (r.get("notes") or "") + (
                " 【来源冲突】库内相电感 80 µH / 相电阻 0.145 Ω 与 J8009P 同值；"
                "aifitlab 手册分列 J8009 = 61 µH / 0.09 Ω、J8009P = 80 µH / 0.145 Ω，"
                "疑本行套用了 P 版电参数，待原厂最新选型表确认后再改数值。")
    save(f, rows)

    f = ROOT / "data/catalog/camera/orbbec.json"
    rows = load(f)
    for r in rows:
        if str(r.get("id")) == "orbbec-gemini-335":
            r["source_tier"] = "B"
            r["verified"] = 0
            r["origin"] = (str(r.get("origin") or "") +
                           "；原标 A 但来源是 Seeed 集成指南（非规格书），2026-10-31 降为 B")
    save(f, rows)

    f = act / "lingzu-robstride.json"
    rows = load(f)
    CONFLICT = {
        "RS01": "空载转速 275 → 手册 315±10%",
        "RS02": "空载 360 → 410±10%；质量 0.405 → 0.380 kg；额定扭矩 7 → 6 N·m",
        "RS03": "空载 195 → 200±10%；额定扭矩 21 → 20 N·m",
        "RS05": "额定扭矩 1.8 → 1.6 N·m",
    }
    for r in rows:
        m = str(r.get("model", "")).upper().replace("ROBSTRIDE ", "RS").replace("RS-", "RS")
        key = next((k for k in CONFLICT if m.startswith(k)), None)
        if key:
            r["notes"] = (r.get("notes") or "") + (
                f" 【来源冲突】手册给 {CONFLICT[key]}，库内暂不改（两份手册数值彼此雷同，"
                f"疑官方表复制粘贴）；来源：{SRC}")
    save(f, rows)

    print("B/C 完成；跳过的键（该行没有这个字段）：", len(skipped))
    for s in skipped[:10]:
        print("   ", s)


if __name__ == "__main__":
    main()

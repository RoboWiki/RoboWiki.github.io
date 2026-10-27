#!/usr/bin/env python3
"""从已抽取的上游数据生成 data/motors.json。

三个来源，全部是本仓库前几轮实际抽取/校验过的：
  1. Draft 的 114 行执行器目录（datasets/actuators）—— 拟合过的数字
  2. 达妙 2026 选型表（motor_data/damiao_joints.csv）—— 含公布转子惯量
  3. RobStride RS/EL 规格书（motor_data/robstride_joints.csv）—— 含公布等效惯量

设计纪律（来自 RoboParts / sbc-reviews 的教训）：
  * 每个件都带 source / source_tier / verified / last_checked
  * 缺失一律显式 null，键集同构
  * tau_basis 必填（peak|rated），因为行业里有 19 种扭矩口径
  * 派生量（扭矩密度、峰值/额定比）不落盘，由服务端算
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OPEN = ROOT.parent
DRAFT = OPEN / "draft"
MOTOR_DATA = OPEN / "motor_data"
OUT = ROOT / "data" / "motors.json"

# 同一家公司的不同拼写，统一到一个 vendor
VENDOR_ALIAS = {
    "CubeMars/T-Motor": "CubeMars",
    "T-Motor": "CubeMars",
    "HEBI Robotics": "HEBI",
    "maxon": "maxon",
    "Damiao": "达妙 DM",
    "RobStride": "灵足 RobStride",
}

# 每个 spec 字段的方向：True = 越小越好
LOWER_IS_BETTER = {
    "mass_kg": True, "od_mm": True, "l_mm": True,
    "rotor_inertia_kgm2": True, "armature_kgm2": None,  # 视用途：越小越轻，但太小学不稳 → 不判
}


def slug(*parts: str) -> str:
    s = "-".join(str(p) for p in parts if p)
    s = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def f(v):
    """安全转 float，空/nan -> None。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if (isinstance(v, float) and math.isnan(v)) else float(v)
    v = str(v).strip()
    if not v or v in ("null", "None", "-", "—"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def blank_specs() -> dict:
    """所有执行器共用的键集 —— 缺失写 null，绝不省略键。"""
    return {
        # 扭矩与转速
        "tau_peak_Nm": None,
        "tau_rated_Nm": None,
        "tau_basis": "peak",
        "speed_noload_rpm": None,
        "speed_rated_rpm": None,
        # 机械
        "gear": None,
        "mass_kg": None,
        "od_mm": None,
        "l_mm": None,
        # 仿真关键：惯量
        "rotor_inertia_kgm2": None,
        "inertia_basis": None,          # rotor | output
        "armature_kgm2": None,          # MuJoCo armature = 输出侧反射惯量
        # 电气
        "voltage_V": None,
        "voltage_range_V": None,
        "kt_Nm_per_A": None,
        "r_phase_ohm": None,
        "l_phase_uh": None,
        "pole_pairs": None,
        "i_peak_A": None,
        "i_rated_A": None,
        # 仿真用的摩擦（几乎没人公布 —— 显式 null）
        "frictionloss_Nm": None,
        "damping_Nms_rad": None,
        # 系统
        "encoder": None,
        "comm": None,
        "driver_integrated": None,
        "ip": None,
        # 产品图与来源。没有图的件也必须留这两个键，否则同 subtype 键集不同构，
        # scripts/check_data.py 会直接判错。
        "image_url": None,
        "image_source": None,
    }


def finish(rec: dict) -> dict:
    """统一收尾：补 armature、规范 vendor。

    Draft 目录里 `rotor_inertia_kgm2` 一律存**电机侧**（kind=output 的行已由
    stage 03 除以 N²），所以 armature = N²·J 对所有 kind 都成立。
    """
    sp = rec["specs"]
    # 只有厂商公布的输出侧等效惯量时，反解出电机侧转子惯量，
    # 这样「armature = N²·J」和「inertia_basis 描述 J 的来源」两条同时成立。
    if sp["rotor_inertia_kgm2"] is None and sp["armature_kgm2"] and sp["gear"]:
        sp["rotor_inertia_kgm2"] = sp["armature_kgm2"] / sp["gear"] ** 2
        sp["inertia_basis"] = sp["inertia_basis"] or "output"
    if sp["rotor_inertia_kgm2"] is None:
        sp["inertia_basis"] = None
    if sp["armature_kgm2"] is None and sp["rotor_inertia_kgm2"] and sp["gear"]:
        sp["armature_kgm2"] = sp["rotor_inertia_kgm2"] * sp["gear"] ** 2
    rec["vendor"] = VENDOR_ALIAS.get(rec["vendor"], rec["vendor"])
    rec["search"] = " ".join(str(x) for x in
                             (rec["vendor"], rec["model"], rec.get("vendor_cn") or "",
                              sp.get("comm") or "") if x).lower()
    return rec


def load_motors() -> list[dict]:
    out: list[dict] = []

    # ── 1. Draft 目录 114 行 ────────────────────────────────────────────────
    cat = json.loads((DRAFT / "src/draft/trends/data/actuator_catalog.json")
                     .read_text(encoding="utf-8"))
    TYPE = {"QDD": "qdd", "MidGear": "planetary", "Harmonic": "harmonic"}
    for r in cat:
        sp = blank_specs()
        sp.update(
            tau_peak_Nm=f(r.get("tau_peak_Nm")),
            speed_noload_rpm=round(f(r.get("omega_NL_rad_s")) * 30 / math.pi, 1)
            if f(r.get("omega_NL_rad_s")) else None,
            gear=f(r.get("gear")),
            mass_kg=f(r.get("mass_kg")),
            od_mm=f(r.get("OD_mm")),
            l_mm=f(r.get("L_mm")),
            rotor_inertia_kgm2=f(r.get("rotor_inertia_kgm2")),
            inertia_basis="output" if r.get("rotor_inertia_kind") == "output" else "rotor",
            comm=" CAN".join(["CAN"]) if "CAN" in str(r.get("notes", "")).upper() else None,
        )
        out.append(finish({
            "id": "draft-" + slug(r["vendor"], r["name"]),
            "category": "actuator",
            "subtype": TYPE.get(r["category"], "qdd"),
            "vendor": r["vendor"],
            "vendor_cn": None,
            "model": r["name"],
            "title": f'{r["vendor"]} {r["name"]}',
            "url": r.get("source"),
            "source_tier": "A",
            "verified": 1,
            "last_checked": "2026-10-01",
            "price_cny": None,
            "specs": sp,
            "notes": (r.get("notes") or "")[:200],
            "origin": "Draft actuator_catalog.json（114 行总体）",
        }))

    # ── 2. 达妙 ────────────────────────────────────────────────────────────
    # 同一机械单元常有 24V / 48V 两个版本；选型工具只留高压版本（常见工作点），
    # 低压的转速与电流记进 notes，避免列表里出现成对的重复行。
    dm_best: dict[str, dict] = {}
    dm_path = MOTOR_DATA / "damiao_joints.csv"
    if dm_path.exists():
        with dm_path.open(encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                model = r["model"]
                base = re.sub(r"[（(]\s*48V\s*[）)]", "", model).strip()
                if not base.startswith(("DM-J", "DM-D")):
                    continue          # S/H/G 不是关节模组
                sp = blank_specs()
                sp.update(
                    tau_peak_Nm=f(r["tau_peak_Nm"]),
                    tau_rated_Nm=f(r["tau_rated_Nm"]),
                    speed_noload_rpm=f(r["speed_noload_rpm"]),
                    speed_rated_rpm=f(r["speed_rated_rpm"]),
                    gear=f(r["gear"]),
                    mass_kg=round(f(r["mass_g"]) / 1000, 4) if f(r["mass_g"]) else None,
                    od_mm=f(str(r["size_mm"]).split("*")[0]) if "*" in str(r["size_mm"]) else None,
                    l_mm=f(str(r["size_mm"]).split("*")[1]) if "*" in str(r["size_mm"]) else None,
                    rotor_inertia_kgm2=f(r["rotor_inertia_kgm2"]),
                    inertia_basis="rotor",
                    voltage_V=f(r["voltage_V"]),
                    voltage_range_V=r["voltage_range_V"] or None,
                    kt_Nm_per_A=f(r["kt_Nm_per_A"]),
                    r_phase_ohm=f(r["R_phase_ohm"]),
                    l_phase_uh=f(r["L_phase_uH"]),
                    i_peak_A=f(r["I_peak_A"]),
                    i_rated_A=f(r["I_rated_A"]),
                    encoder=r["encoder"] or None,
                    comm=r["comm"] or None,
                    driver_integrated=True,
                )
                # 极对数是「极数」的一半；选型表给的是极对数
                if f(r["poles"]):
                    sp["pole_pairs"] = int(f(r["poles"]))
                rec = finish({
                    "id": "dm-" + slug(base, r["voltage_V"]),
                    "category": "actuator",
                    "subtype": "harmonic" if "JH" in base else
                               ("direct" if base.startswith("DM-D") else "planetary"),
                    "vendor": "达妙 DM",
                    "vendor_cn": "深圳市达妙科技",
                    "model": base,
                    "title": f"达妙 {base}",
                    "url": "https://www.hightorque.cn/",
                    "source_tier": "A",
                    "verified": 1,
                    "last_checked": "2026-10-27",
                    "price_cny": None,
                    "specs": sp,
                    "notes": f'{r["voltage_V"]} V 版本；{r["series"]}；'
                             f'额定 {r["tau_rated_Nm"]} N·m；源文勘误：' + (r.get("errata") or "无"),
                    "origin": "达妙 2026 产品选型表 2026-10-23",
                })
                if base in dm_best:
                    cur = dm_best[base]
                    cur_v = (cur["specs"].get("voltage_V") or 0)
                    new_v = f(r["voltage_V"]) or 0
                    if new_v > cur_v:
                        rec["notes"] += f" | 低压版 {cur_v:g} V：{cur['specs'].get('speed_noload_rpm')} rpm"
                        dm_best[base] = rec
                    else:
                        cur["notes"] += f" | 低压版 {new_v:g} V：{f(r['speed_noload_rpm'])} rpm"
                else:
                    dm_best[base] = rec
        out.extend(dm_best.values())

    # ── 3. RobStride ───────────────────────────────────────────────────────
    rs_path = MOTOR_DATA / "robstride_joints.csv"
    if rs_path.exists():
        with rs_path.open(encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                sp = blank_specs()
                sp.update(
                    tau_peak_Nm=f(r["tau_peak_Nm"]),
                    tau_rated_Nm=f(r["tau_rated_Nm"]),
                    speed_noload_rpm=f(r["speed_noload_rpm"]),
                    gear=f(r["gear"]),
                    mass_kg=round(f(r["mass_g"]) / 1000, 4) if f(r["mass_g"]) else None,
                    armature_kgm2=f(r["armature_kgm2"]),
                    inertia_basis="output",
                    voltage_V=f(r["voltage_V"]),
                    voltage_range_V=r["voltage_range_V"] or None,
                    kt_Nm_per_A=f(r["kt_Nm_per_A"]),
                    r_phase_ohm=f(r["R_line_ohm"]),
                    l_phase_uh=f(r["L_uH"]),
                    i_rated_A=f(r["I_rated_A"]),
                    i_peak_A=f(r["I_peak_A"]),
                    encoder=(r["encoders"] or None),
                    comm="CAN",
                    driver_integrated=True,
                )
                if f(r["poles"]):
                    sp["pole_pairs"] = int(f("0") or 0) or None
                out.append(finish({
                    "id": "rs-" + slug(r["model"]),
                    "category": "actuator",
                    "subtype": "qdd",
                    "vendor": "灵足 RobStride",
                    "vendor_cn": "北京灵足时代",
                    "model": r["model"],
                    "title": f'灵足 {r["model"]}',
                    "url": "https://github.com/RobStride/Product_Information",
                    "source_tier": "A",
                    "verified": 1,
                    "last_checked": "2026-10-27",
                    "price_cny": f(r["price_cny"]),
                    "specs": sp,
                    "notes": f'{r["voltage_V"]} V；额定 {r["tau_rated_Nm"]} N·m；'
                             f'官方公布低速端等效惯量 {r["armature_kgm2"]} kg·m²',
                    "origin": "灵足时代RS/EL系列产品规格介绍 2026-10-09",
                }))

    # 浙大 HelloWorld 战队 Wiki 收录的厂商手册 → 补料
    #   新零件：DJI RoboMaster GM6020 / M3508 P19 / M2006 P36（目录里原本没有）
    #   来源冲突：宇树 A1 减速比、GO-M8010 重量，两处不一致，只写 notes 不覆盖
    zju_path = ROOT / "data" / "motors_zju.json"
    note_patches: dict[str, str] = {}
    if zju_path.exists():
        zju = json.loads(zju_path.read_text(encoding="utf-8"))
        out.extend(zju.get("parts", []))
        note_patches = zju.get("note_patches", {})

    # 统一 id = <vendor-slug>-<model-slug>，然后按它合并三路来源
    for r in out:
        r["id"] = slug(r["vendor"], r["model"])

    # 挂产品图：两份映射合并
    #   part_images.json          从本地厂商 PDF 抽出（scripts/extract_images.py）
    #   part_images_fetched.json  从厂商产品页 / 在线 PDF 抓的（scripts/fetch_images.py）
    # 没有产品图的件由前端画「按真实尺寸生成的技术示意图」，不留空。
    images: dict[str, str] = {}
    for fn in ("part_images.json", "part_images_fetched.json"):
        p = ROOT / "data" / fn
        if p.exists():
            images |= json.loads(p.read_text(encoding="utf-8"))
    for r in out:
        url = images.get(r["id"])
        if url:
            r["specs"]["image_url"] = url
            r["specs"]["image_source"] = "厂商资料"

    merged: dict[str, dict] = {}
    for r in out:
        if r["id"] in merged:
            keep = merged[r["id"]]
            for k, v in r["specs"].items():
                if keep["specs"].get(k) is None and v is not None:
                    keep["specs"][k] = v
            keep["price_cny"] = keep["price_cny"] or r["price_cny"]
            if r["notes"] and r["notes"] not in keep["notes"]:
                keep["notes"] = (keep["notes"] + " | " + r["notes"]).strip(" |")
            # 保留来源更硬的那条
            if r["source_tier"] < keep["source_tier"]:
                keep["source_tier"] = r["source_tier"]
            keep["origin"] = keep["origin"] + " + " + str(r["origin"])
        else:
            merged[r["id"]] = r

    # 来源冲突：两份资料给出不同的数时，**不改数值**，把冲突写进 notes 等人裁决。
    # 静默覆盖等于替用户做决定，而这正是本站要防的事。
    for pid, note in note_patches.items():
        rec = merged.get(pid)
        if rec is None:
            continue
        if note not in rec["notes"]:
            rec["notes"] = (rec["notes"] + " " + note).strip()

    # 焦点过滤：data/focus.json 存在时只保留列出的厂商 / 品类。
    # 为什么要在这里过滤而不是靠人事后手动删：重跑采集脚本会把
    # 已经移出的厂商带回来 —— 那是最容易发生的数据事故。
    focus_path = ROOT / "data" / "focus.json"
    if focus_path.exists():
        fo = json.loads(focus_path.read_text(encoding="utf-8"))
        keep_v = set(fo.get("vendors") or [])
        keep_c = set(fo.get("categories") or [])
        before = len(merged)
        merged = {
            k: v for k, v in merged.items()
            if (not keep_v or v["vendor"] in keep_v)
            and (not keep_c or v["category"] in keep_c)
        }
        print(f"  focus.json 过滤：{before} -> {len(merged)} 行"
              f"（{len(keep_v)} 家厂商 / {len(keep_c)} 个品类）")

    return list(merged.values())


def main() -> None:
    rows = load_motors()
    rows.sort(key=lambda r: (r["vendor"], r["model"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(rows)
    with_arm = sum(1 for r in rows if r["specs"]["armature_kgm2"])
    with_rated = sum(1 for r in rows if r["specs"]["tau_rated_Nm"])
    with_kt = sum(1 for r in rows if r["specs"]["kt_Nm_per_A"])
    vendors: dict[str, int] = {}
    for r in rows:
        vendors[r["vendor"]] = vendors.get(r["vendor"], 0) + 1

    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1024:.1f} KB)")
    print(f"  执行器 {n} 行 / {len(vendors)} 家厂商")
    print(f"  有 armature  {with_arm}/{n}")
    print(f"  有额定扭矩   {with_rated}/{n}")
    print(f"  有 Kt        {with_kt}/{n}")
    print("  " + " / ".join(f"{k} {v}" for k, v in
                            sorted(vendors.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()

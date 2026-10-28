"""浙大 HelloWorld 战队 Wiki 的资料 → RoboSelect 补充数据。

来源：github.com/ZJU-HelloWorld/Wiki
      docs/组件说明/机器人通用组件/设备应用/电机设备组件.assets/
      11 份厂商手册 + 1 个领控电机资料包

**只录能核实到具体页表的数字。** 这些手册是「表格+图」排版，
用正则抓会把「1:1 接口」「整机重量」之类当成目标字段（试过，错得很离谱），
所以这里是人工核对 `find_tables()` 导出的表之后写死的常量，每条都带页码。

两个必须说清的结论：
  1. 宇树 A1 / GO-M8010 的手册**只给「最大扭矩」，没有额定扭矩**——
     所以这份资料并不能补上那 107 个缺额定扭矩的执行器，别指望错地方。
  2. 手册里两个数与本目录现有的（来自 Unitree 官网）**冲突**：
       A1 减速比：手册 1:9 vs 目录 6:1
       GO-M8010 重量：手册 530 g vs 目录 420 g
     不覆盖、不猜，作为「来源冲突」写进 notes 供人工裁决。
"""
from __future__ import annotations

import sys as _sys
from legacy_guard import require_legacy_ok
require_legacy_ok(__file__)

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "motors_zju.json"

SRC_WIKI = "https://github.com/ZJU-HelloWorld/Wiki"


def slug(*parts: str) -> str:
    s = "-".join(str(p) for p in parts if p)
    s = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def base(vendor: str, model: str, subtype: str, note: str) -> dict:
    return {
        "id": slug(vendor, model),
        "category": "actuator",
        "subtype": subtype,
        "vendor": vendor,
        "vendor_cn": None,
        "model": model,
        "title": f"{vendor} {model}",
        "url": SRC_WIKI,
        "source_tier": "A",
        "verified": 1,
        "last_checked": "2026-10-27",
        "price_cny": None,
        "specs": {
            "tau_peak_Nm": None, "tau_rated_Nm": None, "tau_basis": "rated",
            "speed_noload_rpm": None, "speed_rated_rpm": None,
            "gear": None, "mass_kg": None, "od_mm": None, "l_mm": None,
            "rotor_inertia_kgm2": None, "inertia_basis": None, "armature_kgm2": None,
            "voltage_V": None, "voltage_range_V": None,
            "kt_Nm_per_A": None, "r_phase_ohm": None,
            "l_phase_uh": None, "pole_pairs": None,
            "i_peak_A": None, "i_rated_A": None,
            "frictionloss_Nm": None, "damping_Nms_rad": None,
            "encoder": None, "comm": "CAN", "driver_integrated": False, "ip": None,
            "image_url": None, "image_source": None,
        },
        "notes": note,
        "origin": "ZJU-HelloWorld/Wiki · 电机设备组件.assets",
    }


# ── 新零件：RoboMaster 生态（目录里原本没有）────────────────────────────────
# 全部数值来自渲染后的参数页，逐项核对过；每个数都能指到「哪一页的哪一栏」。
PARTS: list[dict] = []

gm = base("DJI RoboMaster", "GM6020", "direct",
          "手册 p12「特征参数」表（额定电压 24V）：额定扭矩（最大连续扭矩）1.2 N·m、"
          "额定电流 1.62 A、转矩常数 741 mN·m/A、相电阻 1.8 Ω、相电感 5.78 mH、极对数 10、"
          "定位精度 13 bit、电机重量 约468 g、外径 66.7 mm、总高度 45 mm；"
          "空载调速 0–320 rpm、额定转矩下 0–132 rpm。"
          "**峰值扭矩手册未公布**：表里 0.86 N·m 是「堵转扭矩（持续堵转）」，"
          "属于热限额而非电磁峰值（比额定还小），故 tau_peak_Nm 留空。直驱无减速器。")
gm["specs"].update({
    "tau_rated_Nm": 1.2, "gear": 1.0,
    "speed_noload_rpm": 320.0, "speed_rated_rpm": 132.0,
    "voltage_V": 24.0, "kt_Nm_per_A": 0.741, "r_phase_ohm": 1.8,
    "l_phase_uh": 5780.0, "pole_pairs": 10,
    "i_rated_A": 1.62, "mass_kg": 0.468,
    "od_mm": 66.7, "l_mm": 45.0,
    "encoder": "13 bit 绝对值",
})
PARTS.append(gm)

m3508 = base("DJI RoboMaster", "M3508 P19", "planetary",
             "手册 p12「搭配 C620 电调在额定电压下的电机参数」表："
             "空载转速 482 rpm、额定转速 469 rpm、额定转矩（最大连续转矩）3 N·m、"
             "额定电流 10 A、最大效率 70%、**堵转扭矩 4.5 N·m**、堵转电流 2.5 A；"
             "p13 表：减速比 19:1、减速电机重量 365 g、极对数 7、相电阻 0.194 Ω。"
             "额定值与堵转值取自同一张 C620 表，口径一致，故峰值/额定比 1.5 可用。"
             "同页还有配 Z650 电调的一组（额定 4.6 N·m），口径不同未混用。")
m3508["specs"].update({
    "tau_rated_Nm": 3.0, "tau_peak_Nm": 4.5, "tau_basis": "peak",
    # 手册写「19:1」，但 C620 协议里转速↔转子的换算用的是 3591/187 = 19.2032。
    # 这里记协议值（可复算的精确值），名义值留在 notes 里。
    "gear": 3591.0 / 187.0,
    "speed_noload_rpm": 482.0, "speed_rated_rpm": 469.0,
    "mass_kg": 0.365, "r_phase_ohm": 0.194, "pole_pairs": 7,
    "i_rated_A": 10.0,
})
m3508["notes"] += ("｜减速比记为 3591/187 = 19.2032（C620 协议换算值），"
                   "手册名义写 19:1；按 19.0 算转子量会有 1.06% 系统偏差。"
                   "｜配 Z650 电调时额定 4.6 N·m、空载 589 rpm（不同电调口径，未混用）。")
PARTS.append(m3508)

m2006 = base("DJI RoboMaster", "M2006 P36", "planetary",
             "手册 p8「搭配 C610 电调在额定电压下的电机参数」表："
             "空载转速 500 rpm、额定转速 416 rpm、额定转矩（最大连续转矩）1 N·m、"
             "额定电流 3 A、最大效率 66%；p9 表：减速比 36:1、相电阻 461 mΩ。"
             "**峰值扭矩留空**：堵转扭矩 7 N·m 只出现在同页「配 Z650 电调」那组表里，"
             "与 C610 的额定 1 N·m 不是同一电调口径，混用会让峰值/额定比失真成 7.0。")
m2006["specs"].update({
    "tau_rated_Nm": 1.0, "gear": 36.0,
    "speed_noload_rpm": 500.0, "speed_rated_rpm": 416.0,
    "r_phase_ohm": 0.461, "i_rated_A": 3.0,
})
m2006["notes"] += "｜配 Z650 电调时：空载 777 rpm、额定 0.8 N·m、堵转 7 N·m。"
PARTS.append(m2006)

# ── 来源冲突：不覆盖，只记录 ────────────────────────────────────────────────
NOTE_PATCHES = {
    "unitree-unitree-a1": (
        "【来源冲突】宇树 A1 数据手册（ZJU-HelloWorld/Wiki 收录）p1 表："
        "减速比写 1:9、重量 605 g、最大扭矩 33.5 N·m、最大转速 21.0 rad/s@24V、"
        "转矩常数 0.8732 N·m/A；而本目录原记录（Unitree 官网）为减速比 6:1。"
        "两者不一致，未做覆盖，待人工核对实物铭牌或最新版手册。"),
    "unitree-go-m8010-6": (
        "【来源冲突】GO-M8010-6 数据手册 p3 表：重量 约530 g、尺寸 96.5×92.5×42.3 mm、"
        "最大扭矩 23.7 N·m、最大转速 30 rad/s@24V、减速比 1:6.33、转矩常数 0.63895 N·m/A；"
        "本目录原记录（Unitree 官网）重量为 420 g。重量不一致，未做覆盖。"
        "两份手册都只给「最大扭矩」，**没有额定扭矩**。"),
}


def main() -> None:
    data = {"parts": PARTS, "note_patches": NOTE_PATCHES}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"写出 {OUT.relative_to(ROOT)}")
    print(f"  新增零件 {len(PARTS)} 个（均带页码引用）：")
    for p in PARTS:
        s = p["specs"]
        print(f"    {p['model']:12s} 额定τ={s['tau_rated_Nm']} N={s['gear']} "
              f"m={s['mass_kg']} 类型={p['subtype']}")
    print(f"  来源冲突 {len(NOTE_PATCHES)} 条（只写 notes，不改数值）：")
    for k in NOTE_PATCHES:
        print(f"    {k}")


if __name__ == "__main__":
    main()

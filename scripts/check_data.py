#!/usr/bin/env python3
"""数据闸门：在把 data/*.json 灌进库之前，先拦住口径不一致。

    python scripts/check_data.py          # 退出码 0 = 全部通过
    python scripts/check_data.py --strict # 把 warning 也当失败

这套检查是这几份参考项目踩过的坑的直接产物：
  * RoboParts 的库里 torque 有 19 种表述口径、speed 有 37 种 → 这里强制 tau_basis
  * RoboParts 的库里没有一条数据达到「可直接比较」 → 这里强制 source_tier
  * sbc-reviews 的 arch 字段漂成 aarch64/arm64 两种拼法 → 这里强制枚举
  * Draft 的 `kind: output` 读错会让 armature 错 10⁴ 倍 → 这里强制复算校验
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TIERS = {"A", "B", "C"}
TAU_BASIS = {"peak", "rated"}
INERTIA_BASIS = {"rotor", "output"}

# 数值字段白名单：出现没见过的小写驼峰/拼写错误时报警，防止词表漂移
KNOWN_SPEC_KEYS = {
    # 执行器
    "tau_peak_Nm", "tau_rated_Nm", "tau_basis", "speed_noload_rpm", "speed_rated_rpm",
    "gear", "mass_kg", "od_mm", "l_mm", "rotor_inertia_kgm2", "inertia_basis",
    "armature_kgm2", "voltage_V", "voltage_range_V", "kt_Nm_per_A", "r_phase_ohm",
    "l_phase_uh", "pole_pairs", "i_peak_A", "i_rated_A", "frictionloss_Nm",
    "damping_Nms_rad", "encoder", "comm", "driver_integrated", "ip",
    "image_url", "image_source",
    # 上位机
    "soc", "cpu", "cores", "cpu_arch", "gpu", "cuda_cores", "npu_tops", "ram_gb",
    "ram_bw_gbs", "storage_gb", "power_idle_w", "power_max_w", "os", "cuda", "ros2",
    "eth", "usb", "can", "csi", "pcie", "size_mm", "weight_g",
    # 下位机
    "mcu", "clock_mhz", "ram_kb", "flash_kb", "foc_axes", "canfd",
    "current_loop_khz", "torque_mode", "voltage_in_V", "voltage_max_V", "comm_upper",
    # 传感器
    "gyro_range_dps", "accel_range_g", "odr_hz", "iface", "noise", "resolution",
    "depth_range_m", "fps", "fov", "range_m", "points_per_s", "channel", "bits",
    "absolute", "temp_range_C",
}

# 阈值（来自 RoboParts《关节参数虚标怎么辨别》的物理红线）
TD_REVIEW = 120.0      # 额定扭矩密度 > 120 N·m/kg 需复核
TD_ABSURD = 200.0      # 峰值扭矩密度 > 200 N·m/kg 几乎不可信
PR_REVIEW = 3.0        # 峰值/额定 > 3 需给持续时间
PR_ABSURD = 5.0        # > 5 基本是瞬时堵转值

# 物理量程闸门：超出去几乎一定是单位/解析错误，不是产品差异
# （这些边界就是被 μ/µ 两个码点坑过一次之后加的）
PLAUSIBLE = {
    "mass_kg": (0.005, 100.0),
    "od_mm": (10.0, 1000.0),
    "l_mm": (5.0, 1000.0),
    "gear": (1.0, 300.0),
    "speed_noload_rpm": (1.0, 20000.0),
    "tau_peak_Nm": (0.1, 5000.0),
    "tau_rated_Nm": (0.05, 5000.0),
    "rotor_inertia_kgm2": (1e-9, 0.1),
    "armature_kgm2": (1e-9, 100.0),
    "l_phase_uh": (1.0, 20000.0),
    "r_phase_ohm": (1e-4, 100.0),
    "kt_Nm_per_A": (0.001, 100.0),
    "i_peak_A": (0.1, 2000.0),
    "voltage_V": (1.0, 1000.0),
    "npu_tops": (0.1, 5000.0),
    "power_max_w": (0.1, 5000.0),
    "current_loop_khz": (0.1, 200.0),
    "bits": (1.0, 32.0),
}


def load(name: str) -> list[dict]:
    p = DATA / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="warning 也算失败")
    args = ap.parse_args()

    files = ["motors.json", "controllers_high.json", "controllers_low.json",
             "sensors.json", "offers.json"]
    errors: list[str] = []
    warns: list[str] = []
    seen_ids: dict[str, str] = {}
    rows_by_subtype: dict[str, set[str]] = {}

    for fn in files:
        rows = load(fn)
        if not rows:
            warns.append(f"{fn}: 空或不存在")
            continue

        # offers 是另一套结构，单独校验
        if fn == "offers.json":
            for r in rows:
                oid = r.get("id")
                if not oid:
                    errors.append("offers.json: 有一条没有 id")
                for k in ("kind", "title"):
                    if not r.get(k):
                        errors.append(f"offers:{oid}: 缺 {k}")
                if r.get("kind") not in {"sponsor", "coupon", "discount", "giveaway"}:
                    errors.append(f"offers:{oid}: kind={r.get('kind')!r} 未知")
                if "demo" not in r:
                    errors.append(f"offers:{oid}: 必须显式标 demo: true/false")
                if r.get("demo") is True and r.get("url"):
                    pass    # 示例条目带链接是允许的
            continue

        for r in rows:
            rid = r.get("id")
            where = f"{fn}:{rid or r.get('model') or '?'}"

            if not rid:
                errors.append(f"{fn}: 有一行没有 id")
                continue
            if rid in seen_ids:
                errors.append(f"{where}: id 重复（已在 {seen_ids[rid]} 出现）")
            seen_ids[rid] = fn

            for k in ("category", "subtype", "vendor", "model", "title"):
                if not r.get(k):
                    errors.append(f"{where}: 缺 {k}")

            tier = r.get("source_tier")
            if tier not in TIERS:
                errors.append(f"{where}: source_tier={tier!r} 不在 {sorted(TIERS)}")
            if "verified" not in r:
                errors.append(f"{where}: 缺 verified 字段（必须显式给 0/1）")

            specs = r.get("specs")
            if not isinstance(specs, dict):
                errors.append(f"{where}: specs 不是对象")
                continue

            # 键集同构：同 subtype 的键必须一致
            key = f'{r.get("category")}/{r.get("subtype")}'
            ks = set(specs)
            if key in rows_by_subtype:
                if ks != rows_by_subtype[key]:
                    only_here = sorted(ks - rows_by_subtype[key])
                    missing = sorted(rows_by_subtype[key] - ks)
                    errors.append(
                        f"{where}: 键集与同类不一致（多 {only_here}，缺 {missing}）")
            else:
                rows_by_subtype[key] = ks

            unknown = sorted(ks - KNOWN_SPEC_KEYS)
            if unknown:
                warns.append(f"{where}: 未登记的参数名 {unknown}（词表可能漂移）")

            # 物理量程：超出去基本是单位/解析 bug
            for name, (lo, hi) in PLAUSIBLE.items():
                v = specs.get(name)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if v < lo or v > hi:
                        errors.append(
                            f"{where}: {name}={v:g} 超出物理量程 [{lo:g}, {hi:g}]"
                            f" —— 检查单位换算")

            if r.get("category") == "actuator":
                tau_p = specs.get("tau_peak_Nm")
                tau_r = specs.get("tau_rated_Nm")
                basis = specs.get("tau_basis")
                mass = specs.get("mass_kg")
                ib = specs.get("inertia_basis")
                j = specs.get("rotor_inertia_kgm2")
                arm = specs.get("armature_kgm2")
                gear = specs.get("gear")

                # 执行器至少要有一个可比的扭矩值：峰值或额定。
                # 只要求峰值，会把「厂商只公布额定」的件拒之门外（GM6020、M2006 就是）；
                # 而为了过闸门去编一个峰值，才是真正的错。
                if tau_p is None and tau_r is None:
                    errors.append(f"{where}: 执行器 tau_peak_Nm 与 tau_rated_Nm 都没有")
                elif tau_p is None:
                    warns.append(f"{where}: 只公布额定扭矩 {tau_r} N·m，峰值缺失"
                                    f"（跨件按峰值排序时会排最后，这是真话不是惩罚）")
                if basis not in TAU_BASIS:
                    errors.append(f"{where}: tau_basis={basis!r} 不在 {sorted(TAU_BASIS)}")
                if ib is not None and ib not in INERTIA_BASIS:
                    errors.append(f"{where}: inertia_basis={ib!r} 不在 {sorted(INERTIA_BASIS)}")
                if (j is None) != (ib is None):
                    errors.append(f"{where}: rotor_inertia 与 inertia_basis 必须同时给或同时为空")

                # armature = N²·J 的复算校验（读错 kind 会差 10⁴ 倍）
                if j and gear and arm:
                    expect = j * gear ** 2
                    if abs(arm - expect) > 1e-9 * max(1.0, abs(expect)):
                        errors.append(
                            f"{where}: armature={arm:.6g} 与 N²·J={expect:.6g} 不符"
                            f"（差 {arm/expect:.4g}×）—— 检查 inertia_basis")
                if arm is not None and arm <= 0:
                    errors.append(f"{where}: armature 必须为正")

                if tau_p and mass:
                    td = tau_p / mass
                    if td > TD_ABSURD:
                        warns.append(f"{where}: 峰值扭矩密度 {td:.0f} N·m/kg > {TD_ABSURD:.0f}"
                                     f"（RoboParts RL-01：几乎不可信，复核分子/分母口径）")
                    elif td > TD_REVIEW:
                        warns.append(f"{where}: 峰值扭矩密度 {td:.0f} N·m/kg > {TD_REVIEW:.0f} 需复核")
                if tau_p and tau_r:
                    pr = tau_p / tau_r
                    if pr > PR_ABSURD:
                        warns.append(f"{where}: 峰值/额定 {pr:.1f} > {PR_ABSURD:.0f}"
                                     f"（RL-02：基本是瞬时堵转值）")
                    elif pr > PR_REVIEW:
                        warns.append(f"{where}: 峰值/额定 {pr:.1f} > {PR_REVIEW:.0f}"
                                     f"（RL-02：需给持续时间与初始温度）")
                if specs.get("frictionloss_Nm") is None and tau_p:
                    pass  # 允许为空；不吵

    # 覆盖率报表
    motors = load("motors.json")
    if motors:
        n = len(motors)
        with_arm = sum(1 for r in motors if r["specs"].get("armature_kgm2") is not None)
        with_rated = sum(1 for r in motors if r["specs"].get("tau_rated_Nm") is not None)
        with_kt = sum(1 for r in motors if r["specs"].get("kt_Nm_per_A") is not None)
        print(f"覆盖率  执行器 {n} 行："
              f"armature {with_arm} ({with_arm/n:.0%}) · "
              f"额定扭矩 {with_rated} ({with_rated/n:.0%}) · "
              f"Kt {with_kt} ({with_kt/n:.0%})")
        if with_arm / n < 0.5:
            warns.append(f"armature 覆盖率只有 {with_arm/n:.0%}（仿真可用性偏低）")

    print(f"检查了 {len(seen_ids)} 个实体 / {len(rows_by_subtype)} 个 subtype")
    for w in warns:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    if errors or (args.strict and warns):
        print(f"\n失败：{len(errors)} 个错误、{len(warns)} 个警告")
        return 1
    print(f"\n通过（{len(warns)} 个警告）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

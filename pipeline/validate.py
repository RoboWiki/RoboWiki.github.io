#!/usr/bin/env python3
"""数据闸门：在把 data/*.json 灌进库之前，先拦住口径不一致。

    python pipeline/validate.py          # 退出码 0 = 全部通过
    python pipeline/validate.py --strict # 把 warning 也当失败

这套检查是这几份参考项目踩过的坑的直接产物：
  * RoboParts 的库里 torque 有 19 种表述口径、speed 有 37 种 → 这里强制 tau_basis
  * RoboParts 的库里没有一条数据达到「可直接比较」 → 这里强制 source_tier
  * sbc-reviews 的 arch 字段漂成 aarch64/arm64 两种拼法 → 这里强制枚举
  * Draft 的 `kind: output` 读错会让 armature 错 10⁴ 倍 → 这里强制复算校验
"""
from __future__ import annotations

try:
    from .paths import DATA_DIR, SCHEMA_DIR
except ImportError:  # 直接 python pipeline/xxx.py 时没有包上下文
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from pipeline.paths import DATA_DIR, SCHEMA_DIR

import argparse
import json
import pathlib
from pathlib import Path
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = DATA_DIR

TIERS = {"A", "B", "C"}
TAU_BASIS = {"peak", "rated"}
INERTIA_BASIS = {"rotor", "output"}

# 数值字段白名单：出现没见过的小写驼峰/拼写错误时报警，防止词表漂移

# ── 永久 ID（数据要被外部按版本引用，id 就不能改名/复用）───────────
# 命名空间：部件/整机是裸 id；软件、供应商、协议各自带前缀。
# protocol 里的 dji-c610 与 catalog 里的 dji-c610 是两个实体，不加前缀会撞成同一条。
ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,63}$")
ID_NAMESPACES = ("software:", "supplier:", "protocol:")


def check_id_registry(root: Path, rows: list[dict]) -> list[str]:
    """① 当前 id 都在注册表 ② 老 id 没消失（改名留 alias_of、删除留 removed）
    ③ 命名与格式 ④ alias / tombstone 条目自身完整

    口径与 tools/id_registry.py:check() 必须一致：那边是操作入口，这边是数据闸门。
    """
    reg_path = DATA_DIR / "_id_registry.json"
    if not reg_path.exists():
        return ["ID 注册表不存在：data/_id_registry.json（跑 tools/id_registry.py）"]
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    known = reg.get("ids") or {}
    cur_list = [r["id"] for r in rows if r.get("id")]
    cur = set(cur_list)
    out: list[str] = []

    # 同一个 id 被两个来源产出，说明少了命名空间前缀
    for rid in sorted({i for i in cur_list if cur_list.count(i) > 1}):
        out.append(f"{rid}: 同一个 id 出现多次 —— 不同来源的实体要加命名空间前缀")

    # ① 数据里的 id 都登记过
    for rid in sorted(cur - set(known)):
        out.append(f"{rid}: id 不在注册表里（新增实体要跑 tools/id_registry.py 登记）")

    # ② 注册表里的 id 不能消失：改名 → alias_of，删除 → removed
    for rid in sorted(set(known) - cur):
        meta = known[rid] or {}
        if meta.get("removed") or meta.get("alias_of"):
            continue
        out.append(f"{rid}: 注册表里有、数据里没有 —— 改名用 --alias，删除用 --tombstone")

    # ③ 命名与格式
    for rid in sorted(cur):
        meta = known.get(rid) or {}
        plain = rid.split(":", 1)[-1]  # software:/supplier:/protocol: 是命名空间，不是 id 本体
        if not ID_RE.match(plain) and not meta.get("legacy"):
            if plain.isascii():
                out.append(f"{rid}: id 只允许小写字母/数字/连字符（2–64 字符），不要版本号后缀")
            else:
                out.append(f"{rid}: 非 ASCII id 只有历史遗留可以（标 legacy: true）")
        if ":" in rid and not rid.startswith(ID_NAMESPACES):
            out.append(f"{rid}: 未知的命名空间前缀（只认 {', '.join(ID_NAMESPACES)}）")

    # ④ 出口条目不能半残：alias 指向要落在现存 id 上，tombstone 要有时间与原因
    for rid, meta in sorted(known.items()):
        meta = meta or {}
        tgt = meta.get("alias_of")
        if meta.get("removed"):
            if rid in cur:
                out.append(f"{rid}: 标了 removed 但数据里还在 —— tombstone 只给已删除的实体")
            if not meta.get("removed_at"):
                out.append(f"{rid}: removed 缺 removed_at")
            if not meta.get("removed_reason"):
                out.append(f"{rid}: removed 缺 removed_reason")
            if tgt:
                out.append(f"{rid}: removed 与 alias_of 不能并存 —— 改名留 alias，删除留 tombstone")
        if tgt:
            if tgt == rid:
                out.append(f"{rid}: alias_of 指向自己")
            elif tgt not in known:
                out.append(f"{rid}: alias_of 指向没登记的 id（{tgt}）")
            else:
                tmeta = known[tgt] or {}
                if tmeta.get("alias_of"):
                    out.append(f"{rid}: alias_of 成了链（{tgt} 也在改名）—— 直接指最终 id")
                elif tgt not in cur and not tmeta.get("removed"):
                    # 目标是 tombstone 是合法结局：先改名、后删除，旧 id 的查询落到墓碑上
                    out.append(f"{rid}: alias_of 的目标 {tgt} 不在当前数据里（改名没改完？）")
    return out



# ── 资源许可与出处（图片能引用，就必须说明从哪来）─────────────────
def check_asset_provenance(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        sp = r.get("specs") or {}
        if sp.get("image_url") and not sp.get("image_source", "repo_license"):
            out.append(f"{r.get('id')}: 有 image_url 但没写 image_source —— 图必须能追溯出处")
        if sp.get("repo_urls") and not sp.get("repo_license"):
            out.append(f"{r.get('id')}: 引用了仓库但没写 repo_license —— 读不到就写 null")
    return out


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
    # 遥控器 / CAN 模块
    "channels", "frequency_ghz", "control_range_m", "protocol", "battery",
    "can_speed_mbps", "isolation",
    # 归档导入用到的字段（见 tools/normalize_archive.py 的 FIELD_MAP）
    "tau_stall_Nm", "tau_hold_Nm", "i_stall_A", "dims", "temp_range",
    "storage_temp_range", "meas_range", "accuracy", "response_time", "power_w",
    "motor_type", "gear_material", "housing_material", "bearing", "mounting",
    "connector", "backlash_arcmin",
    # 芯片
    "package", "cores", "clock_mhz", "flash_kb", "ram_kb", "canfd",
    # 资料链接（官方文档 / 手册 PDF / 开源仓库）
    "doc_url", "doc_pdf", "repo_urls",
    # 相机：IMU 是否为板载（Realsense 两条在用）
    "imu",
    # 电池（智能电池 / 动力电池）
    "capacity_mah", "energy_wh", "discharge_rate_c", "current_rated_A",
    "v_charge_V", "mass_g", "chem",
    # 电源类芯片（立创商城采集）
    "category_cn", "lcsc_part", "params", "price_tiers", "price_lead", "stock", "stock_lead", "lead_time", "jlc_library", "tags", "fetched_at", "voltage_in", "voltage_out", "current_out", "function_type", "output_type", "polarity", "freq", "chip_function", "charge_current", "v_float", "battery_type", "cells", "switch_type", "channels", "logic", "features", "coupon",
    # 连接器
    "positions", "positions_options", "pitch_mm", "voltage_rated_V",
    "current_basis", "contact_resistance_mohm", "insulation_resistance_mohm",
    "withstand_voltage_V", "mating_cycles", "wire_awg", "mount_type", "lock_type",
    "power_positions", "signal_positions", "signal_current_rated_A",
    "contact_layout", "instantaneous_current_A", "use_cases",
    "impedance_ohm", "freq_max_ghz", "length_m", "awg",
}

#: UI 真正会读的键。B 级行字段参差，只要求这些键存在（值可为 null），
#: 少了会渲染出空白而不是「—」，所以单独提示。
UI_KEYS = {
    "actuator": {"tau_peak_Nm", "tau_rated_Nm", "gear", "mass_kg", "voltage_V",
                 "speed_noload_rpm", "image_url"},
    "lidar": {"range_m", "image_url"},
    "camera": {"depth_range_m", "image_url"},
    "imu": {"odr_hz", "image_url"},
    "module": {"can", "image_url"},
    "remote_controller": {"channels", "control_range_m", "image_url"},
    "controller_low": {"image_url"},
    "chip": {"package", "image_url"},
    "battery": {"capacity_mah", "voltage_V", "image_url"},
    "connector": {"positions", "pitch_mm", "current_rated_A", "voltage_rated_V",
                  "mount_type", "iface", "use_cases", "image_url"},
}

# 红线的**数值**只有一份：schema/semantics.json 的 RL-01 / RL-02
# （文案和阈值都在那儿，静态站口径页、/api/semantics、MCP 也都读同一份）。
# 这里只取数不复制 —— 别在代码里再写一遍 120 / 200 / 3 / 5。
_SEMANTICS_FILE = SCHEMA_DIR / "semantics.json"
if not _SEMANTICS_FILE.is_file():
    raise RuntimeError(
        f"缺参数口径事实源：{_SEMANTICS_FILE}\n"
        "  校验阈值来自该 JSON 的 red_lines（RL-01 扭矩密度、RL-02 峰值/额定），"
        "见 schema/semantics.README.md。"
    )
_RED_LINES_BY_ID = {
    _item["id"]: _item
    for _item in json.loads(_SEMANTICS_FILE.read_text(encoding="utf-8"))["red_lines"]
}
TD_REVIEW = float(_RED_LINES_BY_ID["RL-01"]["review_above"])    # 峰值扭矩密度需复核
TD_ABSURD = float(_RED_LINES_BY_ID["RL-01"]["absurd_above"])    # 峰值扭矩密度几乎不可信
PR_REVIEW = float(_RED_LINES_BY_ID["RL-02"]["review_above"])    # 峰值/额定需给持续时间
PR_ABSURD = float(_RED_LINES_BY_ID["RL-02"]["absurd_above"])    # 基本是瞬时堵转值

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
    "channels": (1.0, 64.0),
    "frequency_ghz": (0.3, 6.0),
    "control_range_m": (1.0, 100000.0),
    "can_speed_mbps": (0.01, 20.0),
    "weight_g": (0.1, 10000.0),
    # 连接器
    "positions": (1, 100),
    "pitch_mm": (0.2, 30.0),
    "current_rated_A": (0.05, 500.0),
    "voltage_rated_V": (1.0, 2000.0),
    "contact_resistance_mohm": (0.01, 1000.0),
    "insulation_resistance_mohm": (0.1, 1e9),
    "withstand_voltage_V": (50.0, 5000.0),
    "mating_cycles": (1, 100000),
    "signal_current_rated_A": (0.01, 50.0),
    "instantaneous_current_A": (0.1, 1000.0),
    "impedance_ohm": (10.0, 1000.0),
    "freq_max_ghz": (0.01, 100.0),
}

# 材质库：材料物理量与工艺能力各自的量程。单位已写进键名，超范围基本是换算错。
MATERIAL_GROUPS = {"metal", "engineering_plastic", "printing", "composite", "elastomer", "process"}
MATERIAL_SPEC_KEYS = {
    "density_g_cm3", "modulus_GPa", "tensile_MPa", "yield_MPa", "elongation_pct",
    "hardness", "service_temp_C", "low_temp_C", "melting_C", "thermal_cond_W_mK",
    "cte_um_mK", "price_level", "price_note", "sim_note", "image_url",
    "image_source", "doc_url",
}
PROCESS_SPEC_KEYS = {
    "tolerance_mm", "tolerance_note", "surface_ra_um", "layer_height_mm",
    "min_wall_mm", "max_size", "cost_level", "lead_time", "materials",
}
MATERIAL_PLAUSIBLE = {
    "density_g_cm3": (0.5, 25.0),
    "modulus_GPa": (0.0001, 1500.0),
    "tensile_MPa": (0.1, 8000.0),
    "yield_MPa": (0.1, 8000.0),
    "elongation_pct": (0.0, 1500.0),
    "service_temp_C": (-273.0, 1500.0),
    "low_temp_C": (-273.0, 500.0),
    "melting_C": (-50.0, 4000.0),
    "thermal_cond_W_mK": (0.01, 2000.0),
    "cte_um_mK": (-20.0, 500.0),
}
PROCESS_PLAUSIBLE = {
    "tolerance_mm": (0.001, 10.0),
    "surface_ra_um": (0.001, 100.0),
    "layer_height_mm": (0.01, 10.0),
    "min_wall_mm": (0.05, 100.0),
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load(name: str) -> list[dict]:
    p = DATA / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def load_path(p: pathlib.Path) -> list[dict]:
    """按路径读 —— catalog/ 下是按厂商分文件的，不能只按文件名找。"""
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def check_materials(data_dir: Path) -> tuple[list[str], list[str], list[dict]]:
    """材料与工艺：字段齐全、物理量在量程内、材料↔工艺↔渠道交叉引用成立。"""
    errors: list[str] = []
    warns: list[str] = []
    rows: list[dict] = []
    mdir = data_dir / "materials"
    files = sorted(mdir.glob("*.json")) if mdir.exists() else []
    if not files:
        return errors, warns, rows

    supplier_ids: set[str] = set()
    sp = data_dir / "suppliers.json"
    if sp.exists():
        supplier_ids = {s["id"] for s in json.loads(sp.read_text(encoding="utf-8"))
                        if isinstance(s, dict) and s.get("id")}

    entries: list[tuple[str, dict]] = []
    for p in files:
        data = load_path(p)
        if not isinstance(data, list) or not data:
            errors.append(f"materials/{p.name}: 应为非空数组")
            continue
        for r in data:
            if not isinstance(r, dict):
                errors.append(f"materials/{p.name}: 条目不是对象")
                continue
            rows.append(r)
            entries.append((f"materials/{p.name}", r))

    by_id: dict[str, dict] = {}
    for fn, r in entries:
        rid = r.get("id")
        where = f"{fn}:{rid or '?'}"
        if not rid:
            errors.append(f"{fn}: 有一行没有 id")
            continue
        if not ID_RE.match(rid):
            errors.append(f"{where}: id 只允许小写字母/数字/连字符（2–64 字符）")
        if rid in by_id:
            errors.append(f"{where}: id 重复")
        by_id[rid] = r

        cat = r.get("category")
        if cat not in ("material", "process"):
            errors.append(f"{where}: category={cat!r} 只允许 material/process")
        elif cat == "material" and not rid.startswith("mat-"):
            errors.append(f"{where}: 材料 id 必须以 mat- 开头")
        elif cat == "process" and not rid.startswith("proc-"):
            errors.append(f"{where}: 工艺 id 必须以 proc- 开头")

        for k in ("group", "group_label", "family", "family_label", "name", "title",
                  "origin", "notes", "pros", "cons"):
            if not r.get(k):
                errors.append(f"{where}: 缺 {k}")
        if r.get("group") not in MATERIAL_GROUPS:
            errors.append(f"{where}: group={r.get('group')!r} 不在 {sorted(MATERIAL_GROUPS)}")
        if cat == "process" and r.get("group") != "process":
            errors.append(f"{where}: 工艺记录的 group 必须是 process")
        if cat == "material" and r.get("group") == "process":
            errors.append(f"{where}: 材料记录的 group 不能是 process")

        if r.get("source_tier") not in TIERS:
            errors.append(f"{where}: source_tier={r.get('source_tier')!r} 不在 {sorted(TIERS)}")
        if r.get("verified") not in (0, 1):
            errors.append(f"{where}: verified 必须显式给 0/1")
        if not DATE_RE.match(str(r.get("last_checked") or "")):
            errors.append(f"{where}: last_checked 必须是 YYYY-MM-DD")
        if r.get("url") and not str(r["url"]).startswith("http"):
            errors.append(f"{where}: url 必须是 http(s)")
        for s in r.get("sources") or []:
            if not isinstance(s, dict) or not str(s.get("url") or "").startswith("http"):
                errors.append(f"{where}: sources 条目缺 http(s) url")
                continue
            if not DATE_RE.match(str(s.get("checked_on") or "")):
                errors.append(f"{where}: sources[].checked_on 必须是 YYYY-MM-DD")
            if s.get("kind") not in ("datasheet", "reference", "manual", "vendor", "standard", "process", "other"):
                warns.append(f"{where}: sources[].kind={s.get('kind')!r} 未登记")

        forms = r.get("forms")
        if not isinstance(forms, list) or not forms:
            errors.append(f"{where}: forms 必须是非空数组")
        else:
            for f in forms:
                if not isinstance(f, dict) or not f.get("form") or not f.get("spec"):
                    errors.append(f"{where}: forms 条目必须含 form/spec")
        apps = r.get("applications")
        if not isinstance(apps, list) or not apps:
            errors.append(f"{where}: applications 必须是非空数组")

        for sup in r.get("suppliers") or []:
            if not isinstance(sup, dict):
                errors.append(f"{where}: suppliers 条目不是对象")
                continue
            sid = sup.get("supplier_id")
            if not sid:
                errors.append(f"{where}: suppliers 条目缺 supplier_id")
            elif sid not in supplier_ids:
                errors.append(f"{where}: supplier_id={sid} 不在 data/suppliers.json")
            if not sup.get("role"):
                errors.append(f"{where}: suppliers 条目缺 role")

        specs = r.get("specs")
        if not isinstance(specs, dict):
            errors.append(f"{where}: specs 不是对象")
            continue
        allowed = PROCESS_SPEC_KEYS if cat == "process" else MATERIAL_SPEC_KEYS
        unknown = sorted(set(specs) - allowed)
        if unknown:
            warns.append(f"{where}: 未登记的参数名 {unknown}（词表可能漂移）")

        if cat == "process":
            if specs.get("tolerance_mm") is None:
                errors.append(f"{where}: 工艺缺 tolerance_mm")
            if not specs.get("cost_level"):
                errors.append(f"{where}: 工艺缺 cost_level")
            for k, (lo, hi) in PROCESS_PLAUSIBLE.items():
                v = specs.get(k)
                if v is None:
                    continue
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    errors.append(f"{where}: {k} 必须是数字或 null")
                elif not (lo <= v <= hi):
                    errors.append(f"{where}: {k}={v:g} 超出合理量程 [{lo:g}, {hi:g}]")
            continue

        for k in ("density_g_cm3", "modulus_GPa", "tensile_MPa"):
            if specs.get(k) is None:
                errors.append(f"{where}: 材料缺 {k}（仿真必需）")
        for k, (lo, hi) in MATERIAL_PLAUSIBLE.items():
            v = specs.get(k)
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f"{where}: {k} 必须是数字或 null")
            elif not (lo <= v <= hi):
                errors.append(f"{where}: {k}={v:g} 超出物理量程 [{lo:g}, {hi:g}] —— 检查单位")
        ten = specs.get("tensile_MPa")
        yld = specs.get("yield_MPa")
        if isinstance(ten, (int, float)) and isinstance(yld, (int, float)) and yld > ten:
            errors.append(f"{where}: yield_MPa={yld} 大于 tensile_MPa={ten}")
        st = specs.get("service_temp_C")
        mt = specs.get("melting_C")
        if isinstance(st, (int, float)) and isinstance(mt, (int, float)) and st >= mt:
            warns.append(f"{where}: 长期工作温度 {st}°C 不低于熔点 {mt}°C，复核口径")
        lt = specs.get("low_temp_C")
        if isinstance(lt, (int, float)) and isinstance(st, (int, float)) and lt >= st:
            errors.append(f"{where}: low_temp_C={lt} 不低于 service_temp_C={st}")
        if specs.get("image_url") and not specs.get("image_source"):
            errors.append(f"{where}: 有 image_url 但没写 image_source —— 图必须能追溯出处")
        if specs.get("price_level") not in ("低", "低-中", "中", "中高", "高", None):
            errors.append(f"{where}: price_level={specs.get('price_level')!r} 不在 低/低-中/中/中高/高")

    # 交叉引用放到第二遍：文件按字母序读，材料先于工艺，前向引用不能误报
    for fn, r in entries:
        rid = r.get("id")
        if not rid:
            continue
        where = f"{fn}:{rid}"
        if r.get("category") == "process":
            mats = (r.get("specs") or {}).get("materials")
            if not isinstance(mats, list) or not mats:
                errors.append(f"{where}: 工艺缺 specs.materials（可加工材料）")
                continue
            for mid in mats:
                mr = by_id.get(mid)
                if mr is None:
                    warns.append(f"{where}: 引用的材料 {mid} 暂不存在")
                elif rid not in (mr.get("processes") or []):
                    warns.append(f"{where}: 材料 {mid} 未反向登记该工艺")
        elif r.get("category") == "material":
            procs = r.get("processes")
            if not isinstance(procs, list) or not procs:
                warns.append(f"{where}: processes 为空 —— 材料没挂加工工艺，详情页会缺一节")
                continue
            for pid in procs:
                pr = by_id.get(pid)
                if pr is None:
                    warns.append(f"{where}: 引用的工艺 {pid} 暂不存在")
                elif rid not in ((pr.get("specs") or {}).get("materials") or []):
                    warns.append(f"{where}: 工艺 {pid} 未反向收录该材料")

    if rows:
        n_mat = sum(1 for r in rows if r.get("category") == "material")
        print(f"材质 {n_mat} 条 · 工艺 {len(rows) - n_mat} 条（{len(files)} 个文件）")
    return errors, warns, rows



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="warning 也算失败")
    args = ap.parse_args()

    # 唯一事实源：catalog/<品类>/<厂商>.json（人工维护，一家一文件）。
    # 旧扁平文件已出库归档，不再作为校验输入。
    cat_dir = DATA / "catalog"
    files = sorted(cat_dir.glob("*/*.json")) if cat_dir.exists() else []
    offer_dir = DATA / "offers"
    offer_files = (sorted(offer_dir.glob("*.json")) if offer_dir.exists()
                   else ([DATA / "offers.json"] if (DATA / "offers.json").exists() else []))
    errors: list[str] = []
    warns: list[str] = []
    seen_ids: dict[str, str] = {}
    rows_by_subtype: dict[str, set[str]] = {}

    for p in files:
        fn = p.name
        rows = load_path(p)
        if not rows:
            warns.append(f"{fn}: 空或不存在")
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

            # 键集同构：只对**人工逐项核对的 A 级**行要求完全一致
            # （A 级的承诺就是「这一行字段齐、缺的也是确认过的 null」）。
            # 归档导入的 B 级行字段天然参差，只要求 UI 会读的那些键存在，
            # 否则一导入就成了 1000 多条「键集不一致」，把真问题淹掉。
            key = f'{r.get("category")}/{r.get("subtype")}'
            ks = set(specs)
            if r.get("source_tier") == "A":
                if key in rows_by_subtype:
                    if ks != rows_by_subtype[key]:
                        only_here = sorted(ks - rows_by_subtype[key])
                        missing = sorted(rows_by_subtype[key] - ks)
                        errors.append(
                            f"{where}: A 级行键集与同类不一致（多 {only_here}，缺 {missing}）")
                else:
                    rows_by_subtype[key] = ks
            else:
                need = UI_KEYS.get(r.get("category"), set())
                missing_ui = sorted(need - ks)
                if missing_ui:
                    warns.append(f"{where}: 缺 UI 读取的键 {missing_ui}（值可为 null）")

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

                # 执行器至少要有一个可比的扭矩值：峰值、额定，或**堵转**。
                # 只要求峰值，会把「厂商只公布额定」的件拒之门外（GM6020、M2006 就是）；
                # 而为了过闸门去编一个峰值，才是真正的错。
                # 堵转单列（tau_stall_Nm）：它是「锁住转子测的极限」，与峰值同量级
                # 但不是同一个量，所以既不允许它冒充峰值，也不因为它存在就拒收。
                stall = specs.get("tau_stall_Nm")
                if tau_p is None and tau_r is None and stall is None:
                    errors.append(
                        f"{where}: 执行器 tau_peak / tau_rated / tau_stall 都没有")
                elif tau_p is None and tau_r is None:
                    warns.append(f"{where}: 只公布堵转扭矩 {stall} N·m，峰值与额定都缺"
                                 f"（选型时按堵转当上限，别看均分）")
                elif tau_p is None:
                    warns.append(f"{where}: 只公布额定扭矩 {tau_r} N·m，峰值缺失"
                                    f"（跨件按峰值排序时会排最后，这是真话不是惩罚）")
                # tau_basis 只在有峰值时才需要；只有额定/堵转时留 null 是正确状态
                if tau_p is not None and basis not in TAU_BASIS:
                    errors.append(f"{where}: 有峰值但 tau_basis={basis!r} 不在 {sorted(TAU_BASIS)}")
                elif tau_p is None and basis is not None:
                    warns.append(f"{where}: 没有峰值却写了 tau_basis={basis!r}，容易误读")
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

    # 材质库：材料 / 工艺（data/materials/*.json）
    m_errors, m_warns, _material_rows = check_materials(DATA)
    errors.extend(m_errors)
    warns.extend(m_warns)

    # 优惠：另一套结构，单独校验（data/offers/*.json 或旧的 data/offers.json）
    KINDS = {"sponsor", "coupon", "discount", "giveaway", "event", "edu", "retail"}
    n_offer = 0
    for p in offer_files:
        for r in load_path(p):
            n_offer += 1
            oid = r.get("id")
            where = f"{p.name}:{oid or '?'}"
            if not oid:
                errors.append(f"{p.name}: 有一条没有 id")
            for k in ("kind", "title", "detail"):
                if not r.get(k):
                    errors.append(f"{where}: 缺 {k}")
            if r.get("kind") not in KINDS:
                errors.append(f"{where}: kind={r.get('kind')!r} 未知")
            if "demo" not in r:
                errors.append(f"{where}: 必须显式标 demo: true/false")
            # 只给价格/折扣不给条件 —— 读者会拿它当到手价
            if (r.get("price_cny") is not None or r.get("discount") is not None) \
                    and not r.get("detail"):
                errors.append(f"{where}: 有价格/折扣但没有 detail（获取条件）")
            if r.get("part_id") and r["part_id"] not in seen_ids:
                errors.append(f"{where}: part_id 不在目录里（{r['part_id']}）")
            if r.get("discount") is not None and not (0 < float(r["discount"]) < 1):
                errors.append(f"{where}: discount 应为 0–1 之间的小数")
    if n_offer:
        print(f"优惠 {n_offer} 条（{len(offer_files)} 个文件）")
    else:
        warns.append("offers: 没有优惠数据")

    # 覆盖率报表
    motors = [r for r in (load_path(f) for f in files) if True]
    act = [r for rows in motors for r in rows if r.get("category") == "actuator"]
    if act:
        n = len(act)
        with_arm = sum(1 for r in act if r["specs"].get("armature_kgm2") is not None)
        with_rated = sum(1 for r in act if r["specs"].get("tau_rated_Nm") is not None)
        with_kt = sum(1 for r in act if r["specs"].get("kt_Nm_per_A") is not None)
        with_price = sum(1 for r in act if r.get("price_cny") is not None)
        with_img = sum(1 for r in act if r["specs"].get("image_url"))
        print(f"覆盖率  执行器 {n} 行："
              f"armature {with_arm} ({with_arm/n:.0%}) · "
              f"额定扭矩 {with_rated} ({with_rated/n:.0%}) · "
              f"Kt {with_kt} ({with_kt/n:.0%}) · "
              f"价格 {with_price} ({with_price/n:.0%}) · "
              f"产品图 {with_img} ({with_img/n:.0%})")
        if with_arm / n < 0.5:
            warns.append(f"armature 覆盖率只有 {with_arm/n:.0%}（仿真可用性偏低）")

    # 永久 ID：数据将来要被外部按版本引用，id 不能改名/复用
    all_rows = []
    for _f in sorted((DATA_DIR / "catalog").glob("*/*.json")):
        all_rows += json.loads(_f.read_text(encoding="utf-8"))
    for _f in sorted((DATA_DIR / "robots").glob("*.json")):
        all_rows += json.loads(_f.read_text(encoding="utf-8"))
    for _f in sorted((DATA_DIR / "materials").glob("*.json")):
        all_rows += json.loads(_f.read_text(encoding="utf-8"))
    _sw = DATA_DIR / "software.json"
    if _sw.exists():
        for _it in json.loads(_sw.read_text(encoding="utf-8")).get("items", []):
            all_rows.append({"id": f"software:{_it['id']}", "model": _it.get("name")})
    # 供应商与协议也有稳定 id（sup-xxxxxxxx / dji-c620 这类），一并纳入注册表口径。
    # contributors.json / learn.json 没有 id 字段（见 docs/ID-POLICY.md「哪些实体不带 id」）。
    id_rows = list(all_rows)
    _sp = DATA_DIR / "suppliers.json"
    if _sp.exists():
        for _it in json.loads(_sp.read_text(encoding="utf-8")):
            if _it.get("id"):
                id_rows.append({"id": f"supplier:{_it['id']}"})
    _pr = DATA_DIR / "protocols.json"
    if _pr.exists():
        for _it in json.loads(_pr.read_text(encoding="utf-8")).get("protocols", []):
            if _it.get("id"):
                id_rows.append({"id": f"protocol:{_it['id']}"})
    errors.extend(check_id_registry(ROOT, id_rows))
    warns.extend(check_asset_provenance(all_rows))

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

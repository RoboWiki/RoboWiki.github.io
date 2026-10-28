"""把归档里的英文规格整理成项目口径，并翻译成中文。

三层输出（都放 data/_inventory/，不进 catalog）：

    products.jsonl     原始盘点（英文键原样）
    normalized.jsonl   规范化：英文键 -> 我们的字段名 + 中文标签 + 数值/单位拆开
    glossary.md        翻译对照表（人工复核用，也是以后新增厂商时的参考）

为什么必须先「整理」再「入库」：
    归档里的键写法不统一（"Rated Torque" / "Nominal Torque" / "额定扭矩"），
    单位也混（N.m / N·m / kg·cm / g·cm²）。直接进 catalog 会让「按扭矩排序」
    变成随机的 —— 同一个数被当成不同单位比较。
    所以先全部翻译并统一单位，再由人决定哪些型号够格进正式目录。

口径纪律：
    · 数值解析不出来的，写 null 并记进 unresolved，**不猜**
    · Stall ≠ Peak：伺服舵机的堵转扭矩常被当成「最大扭矩」，但两者不是一回事，
      分别落到 tau_stall_Nm 与 tau_peak_Nm，不互相顶替
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
INV = ROOT / "data" / "_inventory"

# ── 字段对照：英文键 -> (我们的字段名, 中文标签) ───────────────────────────
# 只映射**语义确定**的键；拿不准的翻译成中文但不给字段名（留在 extra）
FIELD_MAP: dict[str, tuple[str, str]] = {
    "peak torque": ("tau_peak_Nm", "峰值扭矩"),
    "max torque": ("tau_peak_Nm", "峰值扭矩"),
    "stall torque": ("tau_stall_Nm", "堵转扭矩"),
    "rated torque": ("tau_rated_Nm", "额定扭矩"),
    "nominal torque": ("tau_rated_Nm", "额定扭矩"),
    "holding torque": ("tau_hold_Nm", "保持扭矩"),
    "reduction ratio": ("gear", "减速比"),
    "gear ratio": ("gear", "减速比"),
    "rated speed": ("speed_rated_rpm", "额定转速"),
    "nominal speed": ("speed_rated_rpm", "额定转速"),
    "no-load speed": ("speed_noload_rpm", "空载转速"),
    "no load speed": ("speed_noload_rpm", "空载转速"),
    "weight": ("mass_kg", "质量"),
    "motor weight": ("mass_kg", "电机质量"),
    "rated voltage": ("voltage_V", "额定电压"),
    "nominal voltage": ("voltage_V", "额定电压"),
    "operating voltage": ("voltage_V", "工作电压"),
    "supply voltage": ("voltage_V", "供电电压"),
    "operating voltage range": ("voltage_range_V", "工作电压范围"),
    "torque constant": ("kt_Nm_per_A", "转矩常数"),
    "number of pole pairs": ("pole_pairs", "极对数"),
    "phase resistance": ("r_phase_ohm", "相电阻"),
    "phase inductance": ("l_phase_uh", "相电感"),
    "rated current": ("i_rated_A", "额定电流"),
    "nominal current": ("i_rated_A", "额定电流"),
    "peak current": ("i_peak_A", "峰值电流"),
    "stall current": ("i_stall_A", "堵转电流"),
    "rotor inertia": ("rotor_inertia_kgm2", "转子惯量"),
    "encoder type": ("encoder", "编码器类型"),
    "encoder": ("encoder", "编码器"),
    "communication protocol": ("comm", "通信协议"),
    "communication interface": ("comm", "通信接口"),
    "communication": ("comm", "通信方式"),
    "ip rating": ("ip", "防护等级"),
    "protection class": ("ip", "防护等级"),
    "backlash": ("backlash_arcmin", "背隙"),
    "dimensions": ("dims", "外形尺寸"),
    "size": ("dims", "尺寸"),
    "operating temperature range": ("temp_range", "工作温度范围"),
    "operating temperature": ("temp_range", "工作温度"),
    "working temperature": ("temp_range", "工作温度"),
    "storage temperature range": ("storage_temp_range", "储存温度范围"),
    "measurement range": ("meas_range", "量程"),
    "resolution": ("resolution", "分辨率"),
    "accuracy": ("accuracy", "精度"),
    "response time": ("response_time", "响应时间"),
    "power consumption": ("power_w", "功耗"),
    "motor type": ("motor_type", "电机类型"),
    "gear material": ("gear_material", "齿轮材质"),
    "housing material": ("housing_material", "外壳材质"),
    "case material": ("housing_material", "外壳材质"),
    "bearing": ("bearing", "轴承"),
    "mounting": ("mounting", "安装方式"),
    "connector": ("connector", "连接器"),
    "connector wire": ("connector", "连接线"),
    "noise": ("noise", "噪声"),
}

#: 没有字段名，但值得翻译成中文给人看
LABEL_ONLY = {
    "parameter": "参数",
    "model": "型号",
    "motor": "电机",
    "brand": "品牌",
    "product name": "产品名称",
    "sensor": "传感器",
    "interface": "接口",
    "high": "量程上限",
    "low": "量程下限",
    "running degree": "行程角度",
    "position sensor": "位置传感器",
    "speed constant": "转速常数",
    "insulation resistance": "绝缘电阻",
    "shock resistance": "抗冲击",
    "vibration resistance": "抗振动",
    "pulse width range": "脉宽范围",
    "working frequency": "工作频率",
    "repeat positioning accuracy": "重复定位精度",
    "gear type": "齿轮类型",
}

CSS_NOISE = ("@media", "font-size", "grid-template", "padding", "div[style",
             "margin", "display", "color", "border", "line-height", "max-width",
             "text-align", "background", "gap", "font-weight", "border-radius")

#: 单位归一：把常见的同义写法并到一个
UNIT_ALIAS = {
    "n.m": "N·m", "n·m": "N·m", "nm": "N·m", "n*m": "N·m",
    "kg.cm": "kg·cm", "kg·cm": "kg·cm", "kgcm": "kg·cm",
    "g.cm2": "g·cm²", "g·cm²": "g·cm²", "gcm2": "g·cm²", "kg.m2": "kg·m²",
    "v": "V", "a": "A", "w": "W", "rpm": "rpm", "mm": "mm", "kg": "kg", "g": "g",
    "°": "°", "deg": "°", "hz": "Hz", "khz": "kHz", "bit": "bit", "nm/a": "N·m/A",
    "mnm/a": "mN·m/A", "ohm": "Ω", "ω": "Ω", "uh": "µH", "mh": "mH",
}

NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
GEAR_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)")

#: 物理量程（与 check_data.py 同源）。换算漏掉的单位在这里被拦下，
#: 宁可留空让人复核，也不把 579 这种数写进目录。
PHYS_RANGE = {
    "mass_kg": (0.005, 100.0),
    "rotor_inertia_kgm2": (1e-9, 0.1),
    "gear": (1.0, 300.0),
    "voltage_V": (1.0, 1000.0),
    "r_phase_ohm": (1e-4, 100.0),
    "l_phase_uh": (1.0, 20000.0),
    "speed_noload_rpm": (1.0, 20000.0),
    "tau_peak_Nm": (0.01, 2000.0),
    "tau_rated_Nm": (0.01, 2000.0),
    "tau_stall_Nm": (0.01, 2000.0),
}


def num_unit(v: str) -> tuple[float | None, str]:
    """从 "3.5 N.m" / "12V" / "Approx. 740 g" 里拆出数值与单位。

    只取**紧跟在数字后面**的单位记号。早期写法是「去掉数字后把剩下的当单位」，
    遇到 "Approx. 740 g" 就得到 "Approx.  g"，于是 740 被当成 740 kg 入库。
    """
    if v is None:
        return None, ""
    s = str(v).strip().replace(",", "")
    m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*([A-Za-zµμΩ°·²³][A-Za-zµμΩ°·²³/²³\-\.]*)", s)
    if m:
        n = float(m.group(1))
        unit = m.group(2).strip(". ")
    else:
        m2 = NUM_RE.search(s)
        if not m2:
            return None, ""
        n = float(m2.group(0))
        unit = ""
    key = unit.replace(" ", "").lower().rstrip(".")
    return n, UNIT_ALIAS.get(key, unit)


def to_gear(v: str) -> float | None:
    """减速比一律取 ≥1 的方向。

    厂商写法混着来：`16:1`、`1:16`、`19.612`、`1：100`。都表示「减速 16 倍」
    —— 直接 a/b 会把 `1:16` 算成 0.0625，按减速比排序就全乱。
    """
    m = GEAR_RE.search(str(v))
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a == 0 or b == 0:
            return None
        return round(max(a, b) / min(a, b), 4)
    n, _ = num_unit(v)
    if n is None or n <= 0:
        return None
    return n if n >= 1 else round(1 / n, 4)


#: 这些字段本质是文本（"17-bit"、"EtherCAT"、"IP54"、"96x71 mm"），
#: 一律不做数值解析 —— 否则 "17-bit" 会变成 17，"IP54" 会变成 54
TEXT_FIELDS = {
    "encoder", "comm", "ip", "dims", "temp_range", "storage_temp_range",
    "meas_range", "motor_type", "gear_material", "housing_material",
    "bearing", "mounting", "connector", "resolution", "accuracy",
    "voltage_range_V", "backlash_arcmin", "response_time", "noise",
    "tau_hold_Nm__text",
}


def norm_specs(raw: dict[str, str]) -> tuple[dict, dict, dict]:
    """返回 (规范化字段, 仅翻译, 解析失败)。"""
    fields: dict = {}
    zh: dict[str, str] = {}
    unresolved: dict[str, str] = {}

    for k, v in raw.items():
        kl = k.strip().lower()
        if any(b in kl for b in CSS_NOISE):
            continue
        ent = FIELD_MAP.get(kl)
        label = ent[1] if ent else LABEL_ONLY.get(kl)
        if label is None:
            # 没收录的键：保留原文，方便下一轮扩充词表
            zh[k] = v
            continue
        zh[label] = v
        if ent is None:
            continue
        fname = ent[0]
        if fname == "gear":
            g = to_gear(v)
            # 减速比 >300 基本是把「齿数」当成了比值，宁可留空也不写错
            if g and g <= 300:
                fields[fname] = g
            else:
                unresolved[label] = v
            continue
        if fname in TEXT_FIELDS:
            fields[fname] = str(v).strip()
            continue

        n, unit = num_unit(v)
        if n is None:
            fields[fname] = str(v).strip()
            continue

        # ── 单位换算：这些字段在厂商页面里单位五花八门，不换就是错的 ──────
        u = (unit or "").replace(" ", "").lower()
        if fname == "mass_kg":
            if u in ("g", "gram", "grams"):
                n = round(n / 1000, 4)
            elif not unit and n >= 100:
                unresolved["质量（无单位，按克换算）"] = v
                n = round(n / 1000, 4)
        elif fname == "r_phase_ohm":
            if u in ("mω", "mohm", "mohm.", "mΩ".lower()):
                n = round(n / 1000, 6)
        elif fname == "l_phase_uh":
            if u in ("mh",):
                n = round(n * 1000, 3)
            elif u in ("h",):
                n = round(n * 1e6, 1)
        elif fname == "rotor_inertia_kgm2":
            if u in ("g·cm²", "g.cm2", "gcm²", "gcm2"):
                n = n * 1e-7
            elif u in ("kg·cm²", "kg.cm2", "kgcm²"):
                n = n * 1e-6
            elif u in ("g·m²", "g.m2"):
                n = n * 1e-3
            n = float(f"{n:.4g}")
        elif fname == "voltage_V":
            n = abs(n)                      # 厂商常写 -48V 表示负极
            if n > 1000 and u in ("mv",):
                n = n / 1000
        elif fname == "speed_noload_rpm":
            # "0.5 s/60°" 这类是「秒/60度」，量纲与 rpm 互逆，不能当转速用
            if re.search(r"s\s*/\s*60|sec\s*/\s*60|s/60", str(v), re.I) and n < 10:
                unresolved["转速（单位为 s/60°，与 rpm 互逆，未换算）"] = v
                continue

        fields[fname] = n
        if unit:
            fields[f"{fname}__unit"] = unit
    # 物理量程兜底：换算漏掉的单位会在这里被拦住，而不是带着 579 进目录
    for k, rng in PHYS_RANGE.items():
        v = fields.get(k)
        if isinstance(v, (int, float)) and not (rng[0] <= v <= rng[1]):
            unresolved[f"{k} 超量程"] = f"{v}（原始 {zh.get(k, '')}）"
            fields.pop(k, None)
    return fields, zh, unresolved


# ── 品类判定 ──────────────────────────────────────────────────────────────
CAT_RULES = [
    ("lidar", r"lidar|激光雷达|tof.*(scanner|雷达)"),
    ("camera", r"camera|depth cam|双目|摄像头|相机"),
    ("imu", r"\bimu\b|imu module|惯性测量|gyro|加计"),
    ("controller_high", r"jetson|raspberry|compute module|sbc|工控机|orin"),
    ("controller_low", r"driver board|controller board|控制板|主控|mcu|bridge"),
    ("module", r"encoder|gripper|夹爪|线束|cable|harness|power module|adapter"),
]


def categorise(title: str, ptype: str) -> str:
    t = f"{title} {ptype}".lower()
    for cat, pat in CAT_RULES:
        if re.search(pat, t):
            return cat
    if re.search(r"servo|motor|actuator|关节|舵机|电机|reducer", t):
        return "actuator"
    return "module"


def subtype_of(title: str, fields: dict) -> str:
    t = title.lower()
    if re.search(r"harmonic|谐波", t):
        return "harmonic"
    if re.search(r"planetary|行星", t):
        return "planetary"
    if re.search(r"qdd|quasi.direct|准直驱", t):
        return "qdd"
    if re.search(r"direct drive|无框|frameless", t):
        return "direct"
    if re.search(r"servo|舵机", t):
        return "servo"
    gear = fields.get("gear")
    if isinstance(gear, (int, float)):
        return "planetary" if gear >= 5 else "qdd"
    return "servo"


def main() -> None:
    src = INV / "products.jsonl"
    if not src.exists():
        print("先跑 inventory_archive.py")
        raise SystemExit(1)

    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]
    out = []
    cat_c = Counter()
    key_c = Counter()
    unresolved_total = 0

    for r in rows:
        fields, zh, unresolved = norm_specs(r["specs"])
        cat = categorise(r["title"] or "", r["product_type"] or "")
        cat_c[cat] += 1
        for f in fields:
            if not f.endswith("__unit"):
                key_c[f] += 1
        unresolved_total += len(unresolved)
        out.append({
            "handle": r["handle"],
            "title": r["title"],
            "vendor": r["vendor"],
            "category": cat,
            "subtype": subtype_of(r["title"] or "", fields),
            "price_min": r["price_min"],
            "price_max": r["price_max"],
            "image": (r["images"] or [None])[0],
            "fields": fields,
            "labels_zh": zh,
            "unresolved": unresolved,
        })

    with (INV / "normalized.jsonl").open("w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 词表
    lines = ["# 规格词表（英 → 中 → 我们的字段）", ""]
    lines += ["| 英文键 | 中文 | 字段名 |", "|---|---|---|"]
    for en, (fn, zhlabel) in sorted(FIELD_MAP.items()):
        lines.append(f"| {en} | {zhlabel} | `{fn}` |")
    lines += ["", "## 仅翻译（无对应字段）", "", "| 英文键 | 中文 |", "|---|---|"]
    for en, zhlabel in sorted(LABEL_ONLY.items()):
        lines.append(f"| {en} | {zhlabel} |")
    (INV / "glossary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"规范化 {len(out)} 条 -> normalized.jsonl")
    print("品类分布：")
    for k, v in cat_c.most_common():
        print(f"  {v:5d}  {k}")
    print("可用字段覆盖（Top 15）：")
    for k, v in key_c.most_common(15):
        print(f"  {v:5d}  {k}")
    print(f"解析失败条目累计 {unresolved_total} 个（已记在 unresolved 里，不猜）")


if __name__ == "__main__":
    main()

"""把归档的规范化结果生成到 data/catalog/ —— 这是「全面补充部件库」的执行步骤。

质量闸门（够格才进目录）：
    · 必须有厂商、标题、价格、至少一张图
    · 零件必须有名字与稳定 id（id 用 handle，天然唯一且可回溯到商品页）
    · 执行器必须至少有「一个扭矩值 + 减速比」——缺这两项没法选型
    · 传感器/模块必须有至少 2 个可解析字段

口径纪律：
    · 归档是厂商商品页，证据等级记 `B`（公开网页），`verified=false` 表示
      **还没逐项对过厂商手册**。站点上会显示成 B，不会冒充 A
    · 归档里的 "Stall Torque" 只落到 tau_stall_Nm，不冒充 tau_peak_Nm
    · 解析不出的字段一律不写（保持 null 缺省），不填充
    · tau_basis 只在有 peak 时写 "peak"；只有 stall/rated 时为 null

用法：
    python tools/import_archive.py            # 生成
    python tools/import_archive.py --dry-run  # 只统计不写文件
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
INV = ROOT / "data" / "_inventory"
DATA = ROOT / "data"
ARCHIVE_DATE = "2026-10-28"
SOURCE = "AI2FitLab / OpenELab 商城商品页归档"

VENDOR_SLUG = {
    "DAMIAO": "damiao", "达妙 DAMIAO": "damiao", "High Torque": "damiao",
    "hightorque": "damiao", "高擎": "damiao",
    "Unitree": "unitree", "宇树 Unitree": "unitree",
    "CubeMars": "cubemars",
    "SteadyWin": "steadywin",
    "Feetech": "feetech",
    "KST": "kst",
    "Xike Sensor": "xike-sensor",
    "Kpower": "kpower",
    "HAITAI": "haitai",
    "SITO DRIVE": "sito-drive",
    "DSpower": "dspower",
    "LKMTECH": "lkmtech",
    "WitMotion": "witmotion",
    "Livox": "livox",
    "ToFFuture": "toffuture",
    "Looper Robotics": "looper-robotics",
    "HexFellow": "hexfellow",
    "KingKong": "kingkong",
    "Link-touch": "link-touch",
    "DJI": "dji-robomaster", "RoboMaster": "dji-robomaster",
    "RobStride": "lingzu-robstride", "灵足 RobStride": "lingzu-robstride",
    "MyActuator": "myactuator",
}

#: 归档里的厂商名 -> 站内显示名。同一家的英文名/中文名/旧名都要并过来，
#: 否则会出现「达妙 DAMIAO」「DAMIAO」「High Torque」「hightorque」四个厂牌，
#: 型号也会重复出现两份。
VENDOR_ALIAS = {
    "DAMIAO": "达妙 DAMIAO", "High Torque": "达妙 DAMIAO",
    "hightorque": "达妙 DAMIAO", "高擎": "达妙 DAMIAO",
    "达妙 DM": "达妙 DAMIAO",
    "DJI": "大疆 DJI", "RoboMaster": "大疆 DJI", "DJI RoboMaster": "大疆 DJI",
    "RobStride": "灵足 RobStride",
    "Unitree": "宇树 Unitree",
}


def canon_vendor(v: str) -> str:
    v = (v or "").strip()
    return VENDOR_ALIAS.get(v, v)


#: 型号去重键：去掉厂牌、大小写、分隔符，以及无意义的词
def model_key(title: str, vendor: str = "") -> str:
    s = (title or "").lower()
    for tok in re.split(r"[\s\-_/]+", (vendor or "").lower()):
        if len(tok) >= 2:
            s = s.replace(tok, " ")
    s = re.sub(r"\b(motor|servo|actuator|module|joint|reducer|driver|board|sensor)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s[:48]

SUB_LABEL = {
    "servo": "舵机", "planetary": "行星减速", "harmonic": "谐波减速",
    "qdd": "准直驱", "direct": "直驱", "module": "模块",
}

#: 只保留这些字段进 catalog（其余留在 normalized.jsonl 备查）
KEEP_FIELDS = {
    "tau_peak_Nm", "tau_rated_Nm", "tau_stall_Nm", "gear", "speed_noload_rpm",
    "speed_rated_rpm", "mass_kg", "voltage_V", "kt_Nm_per_A", "pole_pairs",
    "i_rated_A", "i_peak_A", "i_stall_A", "r_phase_ohm", "l_phase_uh",
    "rotor_inertia_kgm2", "encoder", "comm", "ip", "dims", "temp_range",
    "meas_range", "resolution", "accuracy", "power_w", "motor_type",
}


def vslug(v: str) -> str:
    s = VENDOR_SLUG.get(v)
    if s:
        return s
    s = re.sub(r"[^a-z0-9]+", "-", (v or "unknown").lower()).strip("-")
    return s or "unknown"


def sid(vendor: str, handle: str) -> str:
    """稳定 id：厂商slug + handle 尾部。handle 来自 Shopify，天然唯一。"""
    tail = re.sub(r"[^a-z0-9]+", "-", (handle or "").lower()).strip("-")
    return f"{vslug(vendor)}-{tail}"[:96]


def qualifies(r: dict) -> tuple[bool, str]:
    if not r.get("vendor") or not r.get("title"):
        return False, "缺厂商或标题"
    if not r.get("price_min"):
        return False, "缺价格"
    if not r.get("image"):
        return False, "缺图"
    f = r.get("fields") or {}
    if r["category"] == "actuator":
        has_tau = any(k in f for k in ("tau_peak_Nm", "tau_rated_Nm", "tau_stall_Nm"))
        if not has_tau:
            return False, "执行器缺扭矩"
        if "gear" not in f:
            return False, "执行器缺减速比"
    else:
        if len([k for k in f if not k.endswith("__unit")]) < 2:
            return False, "字段不足 2 个"
    return True, ""


def to_part(r: dict) -> dict | None:
    f = {k: v for k, v in (r.get("fields") or {}).items()
         if k in KEEP_FIELDS}
    if not f:
        return None
    # 单位带过来的，附到 dims 之类的文本字段上已经在值里，这里只需要数值
    f = {k: v for k, v in f.items() if not k.endswith("__unit")}
    if "gear" in f and not isinstance(f["gear"], (int, float)):
        f.pop("gear")
    vendor = canon_vendor(r["vendor"])
    pid = sid(vendor, r.get("handle") or r["title"])
    basis = "peak" if "tau_peak_Nm" in f else None
    if "rotor_inertia_kgm2" in f:
        f["inertia_basis"] = "rotor"
    notes = []
    if "tau_stall_Nm" in f and "tau_peak_Nm" not in f:
        notes.append("仅公布堵转扭矩，未公布峰值（堵转 ≠ 峰值，不互相顶替）")
    return {
        "category": r["category"],
        "subtype": r.get("subtype") or "servo",
        "id": pid,
        "vendor": vendor,
        "model": r["title"][:90],
        "title": r["title"][:120],
        "url": f"https://aifitlab.com/products/{r.get('handle')}",
        "source_tier": "B",
        "verified": False,
        "last_checked": ARCHIVE_DATE,
        "price_cny": float(r["price_min"]),
        "origin": f"{SOURCE}（{ARCHIVE_DATE} 抓取）",
        "notes": "；".join(notes),
        "specs": {
            **{k: None for k in (
                "tau_peak_Nm", "tau_rated_Nm", "gear", "speed_noload_rpm",
                "mass_kg", "armature_kgm2", "voltage_V", "kt_Nm_per_A",
                "image_url", "image_source")},
            **f,
            "tau_basis": basis,
            "image_url": r["image"],
            "image_source": f"{SOURCE} 商品图",
        },
    }


def main() -> None:
    dry = "--dry-run" in sys.argv
    src = INV / "normalized.jsonl"
    if not src.exists():
        print("先跑 normalize_archive.py")
        raise SystemExit(1)
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]

    # 现有人工核对过的型号：按「型号去重键」建索引，归档里的同一型号不再重复进库。
    # 不这么做，达妙会被拆成 DAMIAO / High Torque 两个厂牌，且 DM-J6216P 之类
    # 同时出现「A 级手册数据」和「B 级商品页数据」两份 —— 排序和对比都会失真。
    existing_keys: dict[str, str] = {}
    for f in (DATA / "catalog").glob("*/*.json"):
        for p in json.loads(f.read_text(encoding="utf-8")):
            existing_keys[model_key(p.get("title") or p.get("model") or "", p.get("vendor") or "")] = p["id"]

    kept: dict[tuple[str, str], list[dict]] = {}
    dropped: Counter = Counter()
    cats: Counter = Counter()
    seen_ids: set[str] = set()

    for r in rows:
        ok, why = qualifies(r)
        if not ok:
            dropped[why] += 1
            continue
        mk = model_key(r["title"], canon_vendor(r["vendor"]))
        if mk in existing_keys:
            dropped["与已核对型号重复"] += 1
            continue
        part = to_part(r)
        if part is None:
            dropped["字段为空"] += 1
            continue
        # 同一型号在归档内部重复（多个 handle 卖同一件）也只留一条
        if mk in existing_keys or part["id"] in seen_ids:
            dropped["重复（归档内）"] += 1
            continue
        existing_keys[mk] = part["id"]
        seen_ids.add(part["id"])
        kept.setdefault((part["category"], vslug(part["vendor"])), []).append(part)
        cats[part["category"]] += 1

    print(f"入库 {sum(cats.values())} 条")
    for k, v in cats.most_common():
        print(f"  {v:5d}  {k}")
    if dropped:
        print("被闸门拦下：")
        for k, v in dropped.most_common():
            print(f"  {v:5d}  {k}")

    if dry:
        return

    for (cat, vs), items in kept.items():
        d = DATA / "catalog" / cat
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{vs}.json"
        if p.exists():
            # 已有的（人工核对过的）优先，归档只补 id 不存在的新型号
            old = json.loads(p.read_text(encoding="utf-8"))
            have = {x["id"] for x in old}
            add = [x for x in items if x["id"] not in have]
            if not add:
                continue
            items = old + add
            print(f"  {cat}/{vs}.json  追加 {len(add)} 条（原 {len(old)}）")
        else:
            print(f"  {cat}/{vs}.json  新建 {len(items)} 条")
        items.sort(key=lambda x: (x["vendor"], -float(x.get("price_cny") or 0)))
        p.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")


if __name__ == "__main__":
    main()

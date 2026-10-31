"""D + E1/E3：新增 14 条执行器/雷达型号 + 3 家厂商登记。

新增里只有 MyActuator 6 款有**完整可核表**（Seeed zh-CN 规格表，含额定/峰值扭矩、减速比、
空载/额定转速、kt、相电阻电感、极对数）；达妙 5 款来自 aifitlab 机翻手册（B 级，
部分减速比未给）；CyberGear Micro 与 CubeMars AK80-6 只有部分参数；Mid-360S 只确认型号存在。

纪律：没有的值一律 null；B 级标 B；所有新增行写 notes 说明来源与「待复核」。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\31560\Documents\00_open\robowiki")
TODAY = "2026-10-31"
SRC_DM = "wiki.aifitlab 达妙手册（英文机翻镜像，2026-10-31）；待原厂中文手册复核"
SRC_MY = "Seeed wiki zh-CN《脉塔 X 系列》规格表（2026-10-31 抓取）；原厂表交叉核对"
SRC_CM = "CubeMars 官网（cubemars.com/cn）AK80-6 产品页 + aifitlab 商品页手册；参数待补全"
SRC_CG = "wiki.aifitlab 小米 CyberGear Micro 手册（英文机翻镜像）；待原厂复核"


def row(**kw) -> dict:
    base = {
        "category": "actuator", "subtype": "planetary", "vendor": "", "vendor_cn": "",
        "model": "", "title": "", "url": "", "source_tier": "B", "verified": 0,
        "last_checked": TODAY, "price_cny": None, "origin": "", "notes": "",
        "specs": {},
    }
    base.update(kw)
    return base


def sp(**kw) -> dict:
    """只放有值的键；缺的一律不写（B 级行不参与 A 级键集同构约束）。"""
    return {k: v for k, v in kw.items() if v is not None}


# ── D1–D5 达妙 G/H/S 五款 ────────────────────────────────────────
DM = [
    dict(id="damiao-dm-g6220", model="DM-G6220", subtype="direct",
         title="达妙 DM-G6220 空心轴直驱电机",
         specs=sp(tau_peak_Nm=2.7, tau_rated_Nm=1.3, tau_basis="peak", gear=1,
                  speed_noload_rpm=110, pole_pairs=14, l_phase_uh=2900,
                  r_phase_ohm=3.5, mass_kg=0.4935),
         notes=f"空心轴直驱（1:1）。来源：{SRC_DM}"),
    dict(id="damiao-dm-h6215", model="DM-H6215", subtype="direct",
         title="达妙 DM-H6215 直驱电机",
         specs=sp(tau_peak_Nm=2.0, tau_rated_Nm=1.0, tau_basis="peak", gear=1,
                  speed_noload_rpm=120, pole_pairs=14, l_phase_uh=2000,
                  r_phase_ohm=2.5, mass_kg=0.360),
         notes=f"1:1 直驱。来源：{SRC_DM}"),
    dict(id="damiao-dm-h65-1ec", model="DM-H65-1EC", subtype="planetary",
         title="达妙 DM-H65-1EC 关节电机",
         specs=sp(tau_peak_Nm=21.5, tau_rated_Nm=6.0, tau_basis="peak",
                  speed_noload_rpm=120, pole_pairs=15, mass_kg=3.15,
                  encoder="17 bit 单圈绝对"),
         notes=f"减速比手册未给，gear 留空。来源：{SRC_DM}"),
    dict(id="damiao-dm-s2325-1ec", model="DM-S2325-1EC", subtype="planetary",
         title="达妙 DM-S2325-1EC 小型关节电机",
         specs=sp(tau_peak_Nm=5.0, tau_rated_Nm=1.35, tau_basis="peak",
                  speed_noload_rpm=380, pole_pairs=7, l_phase_uh=75,
                  r_phase_ohm=0.2915, mass_kg=0.1722),
         notes=f"来源：{SRC_DM}"),
    dict(id="damiao-dm-s3519-1ec", model="DM-S3519-1EC", subtype="planetary",
         title="达妙 DM-S3519-1EC 小型关节电机",
         specs=sp(tau_peak_Nm=7.8, tau_rated_Nm=3.5, tau_basis="peak",
                  speed_noload_rpm=395, pole_pairs=7, l_phase_uh=55,
                  r_phase_ohm=0.2, mass_kg=0.396),
         notes=f"来源：{SRC_DM}"),
]

# ── E3 脉塔 MyActuator X 系列（完整表）────────────────────────────
MY = [
    # model, gear, V, noload, rated, tau_r, tau_p, kt, R, L(µH), poles
    ("X2-7", 28.17, 24, 178, 142, 2.5, 7, 0.8, 0.61, 130, 13),
    ("X4-10", 12.6, 24, 317, 238, 4, 10, 0.8, 0.32, 140, 13),
    ("X4-36", 36, 24, 111, 83, 10.5, 34, 1.9, 0.35, 170, 13),
    ("X8-120", 19.61, 48, 158, 127, 43, 120, 2.4, 0.18, 310, 10),
    ("X12-320", 20, 48, 125, 100, 85, 320, 3.3, 0.12, 50, 20),
    ("X15-450", 20.25, 72, 108, 98, 145, 450, 5.8, 0.08, 140, 20),
]

# ── D6 小米 CyberGear Micro ─────────────────────────────────────
CG = dict(
    id="xiaomi-cybergear-micro", model="CyberGear Micro", subtype="qdd",
    title="小米 CyberGear 微电机（关节模组）",
    specs=sp(tau_peak_Nm=12, tau_rated_Nm=4, tau_basis="peak",
             speed_noload_rpm=296, speed_rated_rpm=240, pole_pairs=14,
             kt_Nm_per_A=0.87, r_phase_ohm=0.45, mass_kg=0.317,
             voltage_range_V="16~28", od_mm=58,
             encoder="14 bit 单圈绝对", comm="CAN 1 Mbps 扩展帧"),
    notes=f"4/12 N·m、296/240 rpm；相电感官网给 187–339 µH（区间，未入字段）。来源：{SRC_CG}",
)

# ── E1 CubeMars AK80-6 ──────────────────────────────────────────
CM = dict(
    id="cubemars-ak80-6", model="AK80-6", subtype="planetary",
    title="CubeMars AK80-6 关节模组（KV100）",
    specs=sp(tau_rated_Nm=6, tau_basis="rated", gear=6, mass_kg=0.485, voltage_V=48),
    notes=f"6:1、485 g。峰值扭矩与转速需原厂表，未填。来源：{SRC_CM}",
)

# ── D7 Livox Mid-360S ───────────────────────────────────────────
M360S = {
    "id": "livox-mid-360s", "category": "lidar", "subtype": "solid",
    "vendor": "Livox 览沃", "vendor_cn": "览沃科技",
    "model": "Mid-360S", "title": "Livox Mid-360S",
    "url": "https://www.livoxtech.com/cn/mid-360s",
    "source_tier": "B", "verified": 0, "last_checked": TODAY, "price_cny": None,
    "origin": "wiki.openelab（英文手册镜像，2026-10-31）确认型号存在；参数待核",
    "notes": "Mid-360 的后续型号，官方有独立用户手册与 Release Notes；"
             "本次只确认型号与文档存在，规格参数未逐项录入，避免猜值。",
    "specs": {"doc_url": "https://www.livoxtech.com/cn/mid-360s",
              "image_url": None, "image_source": None,
              "repo_urls": None, "repo_license": None},
}


def append(path: pathlib.Path, items: list[dict]) -> None:
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    ids = {r.get("id") for r in rows}
    for it in items:
        if it["id"] in ids:
            continue
        rows.append(it)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  {path.name}: {len(rows)} 条")


def main() -> None:
    act = ROOT / "data/catalog/actuator"
    dm = [row(**d, vendor="达妙 DAMIAO", vendor_cn="达妙科技",
              url="https://www.hightorque.cn/", origin=SRC_DM) for d in DM]
    append(act / "damiao.json", dm)

    my = [row(id=f"myactuator-{m.lower()}", model=m, vendor="脉塔 MyActuator",
              vendor_cn="脉塔智能", url="https://www.myactuator.com/", origin=SRC_MY,
              title=f"脉塔 MyActuator {m} 关节电机",
              notes=f"减速比 {g}、{v} V、额定 {tr} N·m / 峰值 {tp} N·m。来源：{SRC_MY}",
              specs=sp(tau_peak_Nm=tp, tau_rated_Nm=tr, tau_basis="peak", gear=g,
                       speed_noload_rpm=nl, speed_rated_rpm=rt, kt_Nm_per_A=kt,
                       r_phase_ohm=rr, l_phase_uh=ll, pole_pairs=pp, voltage_V=v,
                       encoder="双编 ABS-17 bit（输入）/ 17–18 bit（输出）"))
          for m, g, v, nl, rt, tr, tp, kt, rr, ll, pp in MY]
    append(act / "myactuator.json", my)

    append(act / "xiaomi.json", [row(**CG, vendor="小米 Xiaomi", vendor_cn="小米",
                                     url="https://www.mi.com/", origin=SRC_CG)])
    append(act / "cubemars.json", [row(**CM, vendor="CubeMars", vendor_cn="CubeMars",
                                       url="https://www.cubemars.com/cn/", origin=SRC_CM)])
    append(ROOT / "data/catalog/lidar/livox.json", [M360S])

    # 厂商登记
    tp = ROOT / "data/taxonomy.json"
    tax = json.loads(tp.read_text(encoding="utf-8"))
    for name, meta in (("脉塔 MyActuator", {"slug": "myactuator", "cn": "脉塔智能"}),
                       ("CubeMars", {"slug": "cubemars", "cn": "CubeMars"}),
                       ("小米 Xiaomi", {"slug": "xiaomi", "cn": "小米"})):
        if name not in tax["vendors"]:
            tax["vendors"][name] = meta
            print("  登记厂商:", name)
    tp.write_text(json.dumps(tax, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

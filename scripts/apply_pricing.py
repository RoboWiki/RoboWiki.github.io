"""录入真实价格与优惠（来源：厂商官方文件 + 天猫旗舰店页面，2026-10-28 采集）。

为什么用脚本而不是手改 JSON：
    价格是易变数据，改动必须可复查：谁、什么时候、凭什么、改了多少。
    这份表就是「凭什么」—— 每条带来源与条件；跑一次脚本能把价格重刷成表里的值，
    主数据文件里只留下结果。

数据纪律（和参数一样）：
    · 只录**有明确来源**的价格；天猫「惊爆价」属于活动价，照录但要标活动性质
    · 优惠必须带条件（谁有资格、限购多少、什么时间）；缺条件的不上卡片
    · 拿不到价就留空，不按同类估算

来源：
    [A] 达妙《关于大学生机器人竞赛电机采购优惠方案》2026-09-07 起（本地 PDF 截图）
    [B] 达妙天猫旗舰店商品页 2026-10-28
    [C] 宇树天猫旗舰店商品页 2026-10-28
    [D] 灵足官方：教育优惠（学生证或其他证明一律 9 折，联系客服改价）
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = "2026-10-28"

# ── 零售/活动价：part_id -> (价格, 来源代号) ─────────────────────────────
# 达妙天猫「惊爆价」（[B]）。同名型号后缀不同的（V1.1/V1.2）分别录，不做合并。
RETAIL_DAMIAO = {
    "达妙-dm-dm-j4310-2ec-v1-2": (599, "B"),
    "达妙-dm-dm-j4340-2ec": (899, "B"),
    "达妙-dm-dm-j4340-2ec-v1-1": (799, "B"),
    "达妙-dm-dm-j8009p-2ec-v1-1": (1899, "B"),
    "达妙-dm-dm-j8009-2ec": (1799, "B"),
    "达妙-dm-dm-j6216p-2ec": (599, "B"),
    "达妙-dm-dm-j10422p-2ec": (1999, "B"),
    "达妙-dm-dm-j6248p-2ec": (1240, "B"),
    "达妙-dm-dm-j10010l-2ec": (1199, "B"),
    "达妙-dm-dm-j10010-2ec": (1999, "B"),
    "达妙-dm-dm-j6006-2ec": (799, "B"),
    "达妙-dm-dm-j4310p-2ec": (699, "B"),
    "达妙-dm-dm-j3507-2ec": (550, "B"),
    "达妙-dm-dm-j8006-2ec-v1-1": (999, "B"),
    "达妙-dm-dm-d5730-1ec": (399, "B"),
    "达妙-dm-dm-jh17-51-2ec": (1689, "B"),
    "达妙-dm-dm-jh17-101-2ec": (1689, "B"),
    "达妙-dm-dm-jh14-51-2ec": (1499, "B"),
    "达妙-dm-dm-jh14-101-2ec": (1499, "B"),
    "达妙-dm-dm-jh11-51-2ec": (1299, "B"),
    "达妙-dm-dm-jh11-101-2ec": (1299, "B"),
}

RETAIL_UNITREE = {
    "unitree-im6014": (1800, "C"),
    "unitree-go-m8010-6": (1500, "C"),
    "unitree-unitree-a1": (2500, "C"),
}

# ── 赛事优惠：达妙官方方案 [A] ───────────────────────────────────────────
# (part_id, 优惠价, 条件)
EVENT_DAMIAO = [
    ("达妙-dm-dm-j8009-2ec", 960,
     "大学生机器人竞赛（RM/RC 等）：每个参赛队伍、每个赛事、每个赛季限购 16 台；超出部分 999 元/台"),
    ("达妙-dm-dm-j8009p-2ec", 999,
     "大学生机器人竞赛：每队每赛事每赛季限购 16 台；超出部分 1080 元/台"),
    ("达妙-dm-dm-j8006-2ec-v1-1", 800,
     "大学生机器人竞赛：统一优惠价 800 元/台，不限购"),
    ("达妙-dm-dm-j10010l-2ec", 998,
     "参赛队伍优惠价 998 元/台（非参赛统一价 1049 元/台），不限购"),
    ("达妙-dm-dm-j10010-2ec", 1500,
     "参赛队伍优惠价 1500 元/台，不限购"),
    ("达妙-dm-dm-j6248p-2ec", 999,
     "参赛队伍优惠价 999 元/台，不限购"),
    # 43 系列：按驱动电压分价，每款型号限购 20 台
    ("达妙-dm-dm-j4310-2ec-v1-2", 539,
     "43 系列 4310 · 24V 版本 539 元/台（48V 版本 579 元/台）；每队每赛事每赛季每款型号限购 20 台"),
    ("达妙-dm-dm-j4310p-2ec", 629,
     "43 系列 4310P · 24V 版本 629 元/台（48V 版本 669 元/台）；每款型号限购 20 台"),
    ("达妙-dm-dm-j4340-2ec", 709,
     "43 系列 4340 · 24V 版本 709 元/台（48V 版本 749 元/台）；每款型号限购 20 台"),
    ("达妙-dm-dm-j4340p-2ec", 799,
     "43 系列 4340P · 24V 版本 799 元/台（48V 版本 829 元/台）；每款型号限购 20 台"),
]

PURCHASE_NOTE_DAMIAO = (
    "RM 赛事参赛队伍：需使用报备的淘宝账号或邮件采购；"
    "RC 赛事参赛队伍：需提供有效参赛证明（组委会资格证明或相关官方文件）；"
    "其他机器人赛事可咨询官方优惠。线下联系人：周小姐 13560764159 / 微信 13730701033。"
)


def main() -> None:
    offers: list[dict] = []
    n_price = 0

    # 1) 零售价写进零件主数据
    cat = DATA / "catalog"
    for f in sorted(cat.glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for r in rows:
            hit = RETAIL_DAMIAO.get(r["id"]) or RETAIL_UNITREE.get(r["id"])
            if hit:
                price, src = hit
                if r.get("price_cny") != price:
                    r["price_cny"] = float(price)
                    changed = True
                if not (r.get("notes") or "").startswith("价格来源"):
                    r["notes"] = (r.get("notes") or "").strip() + (
                        f" 价格来源：{'达妙/宇树天猫旗舰店商品页' if src in 'BC' else '厂商文件'}"
                        f"（{TODAY} 抓取，属活动价，可能随活动结束变化）。")
                    changed = True
                n_price += 1
        if changed:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")

    # 2) 达妙赛事优惠
    for pid, price, cond in EVENT_DAMIAO:
        offers.append({
            "id": f"damiao-event-{pid.split('-')[-1]}",
            "vendor": "达妙 DM", "part_id": pid, "kind": "event",
            "title": "达妙大学生机器人竞赛采购优惠（2026）",
            "price_cny": price,
            "detail": f"{cond}。{PURCHASE_NOTE_DAMIAO}",
            "url": "淘宝：达妙科技企业店 / 达妙智能控制企业店 / 达妙动力",
            "starts_on": "2026-09-07", "expires_on": "2027-08-31",
            "source": "达妙《关于大学生机器人竞赛电机采购优惠方案》",
            "demo": False,
        })

    # 3) 宇树赛事优惠：买二赠一
    offers.append({
        "id": "unitree-event-buy2get1",
        "vendor": "Unitree", "part_id": None, "kind": "event",
        "title": "宇树 RM / RC 参赛队首次购买 买二赠一",
        "price_cny": None,
        "detail": ("RM、RC 参赛队凭参赛证明，首次购买可得「买二赠一」；"
                   "固定结构图纸可向客服索取下载。各型号是否参加以客服确认为准。"),
        "url": "天猫 Unitree 宇树旗舰店",
        "starts_on": "2026-01-01", "expires_on": "2027-12-31",
        "source": "宇树天猫旗舰店商品页（2026-10-28）", "demo": False,
    })

    # 4) 灵足教育优惠：9 折
    offers.append({
        "id": "lingzu-edu-90",
        "vendor": "灵足 RobStride", "part_id": None, "kind": "edu",
        "title": "灵足教育优惠：一律 9 折",
        "price_cny": None,
        "discount": 0.9,
        "detail": ("学生证或其他在读/在职教育证明均可，联系官方客服改价后下单；"
                   "适用于灵足 RS / EL 全系。是否与其它活动叠加请与客服确认。"),
        "url": "灵足时代官方客服",
        "starts_on": "2026-01-01", "expires_on": "2027-12-31",
        "source": "灵足官方（用户确认）", "demo": False,
    })

    # 5) 首页招商位：保留但明确标注是示例
    offers.append({
        "id": "offer-slot-frontpage",
        "vendor": None, "part_id": None, "kind": "sponsor",
        "title": "首页展示位（招商中）",
        "price_cny": None,
        "detail": ("厂商可申请首页/分类页展示位。本站不卖排名、不卖评分，"
                   "展示位与评分排序完全分开，且必须标注「赞助」。"),
        "url": None, "starts_on": None, "expires_on": None,
        "source": "本站规则", "demo": False,
    })

    od = DATA / "offers"
    od.mkdir(parents=True, exist_ok=True)
    by_v: dict[str, list] = {}
    for o in offers:
        key = {"达妙 DM": "damiao", "Unitree": "unitree",
               "灵足 RobStride": "lingzu-robstride"}.get(o["vendor"], "site")
        by_v.setdefault(key, []).append(o)
    for k, items in by_v.items():
        (od / f"{k}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  offers/{k}.json  {len(items)} 条")

    # 旧的合并文件留着会双重计算，删掉
    for old in ("offers.json",):
        p = DATA / old
        if p.exists():
            p.unlink()
            print(f"  删除 data/{old}（已拆到 offers/）")

    print(f"\n写入价格 {n_price} 条，优惠 {len(offers)} 条")


if __name__ == "__main__":
    main()

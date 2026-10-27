"""补齐大疆价格与宇树优惠（来源：官方商城截图，用户提供，2026-10-28）。

为什么单独一个脚本：
    这一批是在 apply_pricing 之后补的，且改动集中在两家，
    单独一份让 diff 只涉及这两家，评审时一眼能看完。

数据：
    大疆 DJI（官方商城）
        GM6020        ¥899
        M2006 P36     ¥549
        M3508 P19     ¥499
    宇树（天猫旗舰店）
        IM6014 / GO-M8010-6 都是 490 元的「首次购买/学生特价」（限购 2 个）
        IM6014 另有一条隐藏活动：RC 参赛队买二赠一，折合 490×2/3 ≈ 327/个

原则：
    优惠价**不能取代**原价展示 —— 不是所有人都能满足资格（学生证、参赛证明、
    限购台数）。所以卡片上原价与优惠价并列，各自独立颜色，不划掉原价。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = "2026-10-28"

DJI_PRICE = {
    "dji-robomaster-gm6020": 899,
    "dji-robomaster-m2006-p36": 549,
    "dji-robomaster-m3508-p19": 499,
}

# 宇树：同一型号可以有多条并行优惠，卡片显示最低那条，详情全部列出
UNITREE_OFFERS = [
    dict(id="unitree-im6014-firstbuy", part_id="unitree-im6014",
         title="IM6014 首次购买特价", price_cny=490,
         detail=("首次购买可享 490 元/个（限购 2 个，原价 1800 元/个）。"
                 "需在商品页选择对应规格或咨询客服；是否与其它活动叠加以客服确认为准。"),
         url="天猫 Unitree 宇树旗舰店", expires_on="2027-12-31"),
    dict(id="unitree-im6014-rc-b2g1", part_id="unitree-im6014",
         title="IM6014 RC 参赛队买二赠一（折合约 327 元/个）",
         price_cny=327,
         detail=("RC 参赛队凭参赛证明首次购买可得买二赠一：以 490 元/个的首购价计，"
                 "买 2 赠 1 折合约 327 元/个。需参赛资格，且限首次购买，"
                 "具体以客服确认为准 —— 这条不适用于普通用户。"),
         url="天猫 Unitree 宇树旗舰店", expires_on="2027-12-31"),
    dict(id="unitree-go-m8010-6-firstbuy", part_id="unitree-go-m8010-6",
         title="GO-M8010-6 首次购买特价", price_cny=490,
         detail=("首次购买可享 490 元/个（限购 2 个，原价 1500 元/个）。"
                 "需在商品页选择对应规格或咨询客服。"),
         url="天猫 Unitree 宇树旗舰店", expires_on="2027-12-31"),
]


def main() -> None:
    # 1) 大疆价格
    n = 0
    p = DATA / "catalog" / "actuator" / "dji-robomaster.json"
    rows = json.loads(p.read_text(encoding="utf-8"))
    for r in rows:
        price = DJI_PRICE.get(r["id"])
        if price is None:
            continue
        r["price_cny"] = float(price)
        if "价格来源" not in (r.get("notes") or ""):
            r["notes"] = ((r.get("notes") or "").strip()
                          + f" 价格来源：大疆 DJI 官方商城（{TODAY}，含税零售价）。").strip()
        n += 1
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"大疆价格写入 {n} 条")

    # 2) 宇树优惠（保留原有「买二赠一」厂商级条目）
    op = DATA / "offers" / "unitree.json"
    old = json.loads(op.read_text(encoding="utf-8")) if op.exists() else []
    keep = [o for o in old if o.get("kind") != "retail"]
    out = keep + [
        dict(kind="retail", vendor="宇树 Unitree", demo=False,
             source="天猫 Unitree 宇树旗舰店商品页（2026-10-28）",
             starts_on="2026-01-01", **o)
        for o in UNITREE_OFFERS
    ]
    op.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"宇树优惠写入 {len(out)} 条")


if __name__ == "__main__":
    main()

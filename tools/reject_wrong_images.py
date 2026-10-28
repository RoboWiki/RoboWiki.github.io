"""剔除抓错的图片 —— 错图比没图更糟。

抓图脚本按 og:image 取图，厂商官网首页的 og:image 常常是**整机宣传图**
（宇树官网给的是四足整机，不是关节电机）。挂上去会让读者以为买到的是机器人，
所以这类图一律删掉，回落成按真实尺寸画的示意图。

判定：图片文件名对应的零件拿到的图，若来自厂商首页（image_source 里是抓取脚本
且没有具体型号线索）且明显不是零件照片 —— 人工复核后加到这里。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: 抓错了的零件 id（人工复核过：图片内容是整机/无关图）
#:
#: 宇树三型（IM6014 / GO-M8010-6 / A1）原先抓到的都是四足整机宣传图，
#: 2026-10-28 已由用户提供官方电机图，登记在 data/part_images.json ——
#: 所以它们已经从这张表里摘掉了。下表是仍然有效的剔除项。
WRONG: dict[str, str] = {
    "dji-rm-board-a": "抓到的是二维码，不是开发板",
    "dji-rm-board-c": "抓到的是二维码，不是开发板",
    "unitree-l1": "抓到的是 UNITREE 商标，不是雷达",
    "unitree-l2": "抓到的是 UNITREE 商标，不是雷达",
    "nvidia-orin-nano-8gb": "抓到的是多型号拼图，看不出哪个是 Orin Nano",
    "nvidia-orin-nx-16gb": "抓到的是多型号拼图，看不出哪个是 Orin NX",
    # 达妙官网 og:image 给的是人形整机图，不是 JH 系列关节模组本体
    "达妙-dm-dm-jh11-51-2ec": "抓到的是达妙人形整机宣传图，不是 JH11 关节模组",
    "达妙-dm-dm-jh11-101-2ec": "抓到的是达妙人形整机宣传图，不是 JH11 关节模组",
    "达妙-dm-dm-jh14-51-2ec": "抓到的是达妙人形整机宣传图，不是 JH14 关节模组",
    "达妙-dm-dm-jh14-101-2ec": "抓到的是达妙人形整机宣传图，不是 JH14 关节模组",
    "达妙-dm-dm-jh17-51-2ec": "抓到的是达妙人形整机宣传图，不是 JH17 关节模组",
    "达妙-dm-dm-jh17-101-2ec": "抓到的是达妙人形整机宣传图，不是 JH17 关节模组",
    "达妙-dm-dm-jh20-51-2ec": "抓到的是达妙人形整机宣传图，不是 JH20 关节模组",
    "达妙-dm-dm-jh20-101-2ec": "抓到的是达妙人形整机宣传图，不是 JH20 关节模组",
}


def main() -> None:
    n = 0
    for f in (ROOT / "data" / "catalog").glob("*/*.json"):
        rows = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for r in rows:
            if r["id"] not in WRONG:
                continue
            s = r.setdefault("specs", {})
            if not s.get("image_url"):
                continue
            s["image_url"] = None
            s["image_source"] = None
            note = f"产品图待补：{WRONG[r['id']]}，需厂商型号页原图"
            r["notes"] = (r.get("notes") or "").strip()
            if "产品图待补" not in r["notes"]:
                r["notes"] = (r["notes"] + " " + note).strip()
            changed = True
            n += 1
            print(f"  移除 {r['id']}：{WRONG[r['id']]}")
        if changed:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(f"共移除 {n} 张错图")


if __name__ == "__main__":
    main()

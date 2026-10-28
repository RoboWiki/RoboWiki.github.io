"""厂商改名：只改**显示名**，不动 id / 文件名 / 页面 URL。

改名表：
    DJI RoboMaster  ->  大疆 DJI
    Unitree         ->  宇树 Unitree
    达妙 DM          ->  达妙 DAMIAO
    灵足 RobStride  ->  不变

为什么不能连带改 URL：
    型号页地址由 `厂商+型号` 的 ASCII 形式生成（达妙 DM → "dm-" 前缀），
    giscus 的 data-term 又是这个路径。改名若带动 slug，
    已存在的讨论会全部对不上号，外部链接也会 404。
    所以 URL 一律沿用「建页时的厂商名」，显示名随便改。
    见 build_wiki.VENDOR_URL。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

RENAME = {
    "DJI RoboMaster": "大疆 DJI",
    "Unitree": "宇树 Unitree",
    "达妙 DM": "达妙 DAMIAO",
}
#: 中文名单独维护，别和英文缩写混在一起
VENDOR_CN = {
    "大疆 DJI": "大疆",
    "宇树 Unitree": "宇树科技",
    "达妙 DAMIAO": "达妙科技",
    "灵足 RobStride": "灵足时代",
}


def main() -> None:
    n_part = n_offer = 0
    for f in sorted((DATA / "catalog").glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for r in rows:
            new = RENAME.get(r["vendor"])
            if new:
                r["vendor"] = new
                changed = True
                n_part += 1
            if r["vendor"] in VENDOR_CN:
                r["vendor_cn"] = VENDOR_CN[r["vendor"]]
        if changed:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")

    for f in sorted((DATA / "offers").glob("*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for o in rows:
            new = RENAME.get(o.get("vendor"))
            if new:
                o["vendor"] = new
                changed = True
                n_offer += 1
        if changed:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")

    print(f"零件改名 {n_part} 条 · 优惠改名 {n_offer} 条")


if __name__ == "__main__":
    main()

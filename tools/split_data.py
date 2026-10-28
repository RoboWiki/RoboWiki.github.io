"""把 data/ 拆成「一家厂商一个文件」，方便提 PR 和长期维护。

为什么拆：
    原来 motors.json 是一个 150 行的数组，两个贡献者各加一个型号就会在同一个
    文件里冲突；而且改一条数据要在 150 行里找，评审也没法只看自己那一块。
    拆成 catalog/actuator/<vendor>.json 之后，加型号 = 新增/修改一个文件，
    diff 干净、冲突面小。

目录约定（贡献者只看这个）：
    data/catalog/<category>/<vendor-slug>.json   零件（数组，一条一个型号）
    data/offers/<vendor-slug>.json               优惠（数组，一条一个活动）
    data/catalog/_schema.md                      字段说明

不动的东西：
    data/motors.json 保留为**采集产物**（build_motors.py 的输出），
    不再作为人工编辑入口；loader 优先读 catalog/，读不到再退回 motors.json。
"""
from __future__ import annotations

import sys as _sys
from _deprecated import require_legacy_ok
require_legacy_ok(__file__)

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAT = DATA / "catalog"
OFFERS = DATA / "offers"

#: 厂商名 → 文件名（文件名要稳定：以后重命名中文厂商名，也不该动 URL 和数据路径）
VENDOR_SLUG = {
    "达妙 DAMIAO": "damiao",
    "大疆 DJI": "dji-robomaster",
    "灵足 RobStride": "lingzu-robstride",
    "宇树 Unitree": "unitree",
    "CubeMars": "cubemars",
    "MyActuator": "myactuator",
    "ZeroErr": "zeroerr",
    "HEBI": "hebi",
    "SteadyWin": "steadywin",
    "maxon": "maxon",
    "Techsoft": "techsoft",
    "MIT Humanoid": "mit-humanoid",
    "FAULHABER": "faulhaber",
    "Xiaomi": "xiaomi",
}


def slugify(name: str) -> str:
    s = VENDOR_SLUG.get(name)
    if s:
        return s
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", name).strip("-").lower()
    return s or "unknown"


def main() -> None:
    CAT.mkdir(parents=True, exist_ok=True)
    OFFERS.mkdir(parents=True, exist_ok=True)

    # ── 零件：按 (品类, 厂商) 分组 ────────────────────────────────────
    src = DATA / "motors.json"
    if src.exists():
        rows = json.loads(src.read_text(encoding="utf-8"))
        groups: dict[tuple[str, str], list[dict]] = {}
        for r in rows:
            groups.setdefault((r["category"], slugify(r["vendor"])), []).append(r)
        for (cat, vslug), items in groups.items():
            d = CAT / cat
            d.mkdir(parents=True, exist_ok=True)
            items.sort(key=lambda x: (x["vendor"], x["model"]))
            (d / f"{vslug}.json").write_text(
                json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"  catalog/{cat}/{vslug}.json  {len(items)} 条")
    else:
        print("  没有 data/motors.json，跳过零件拆分")

    # ── 优惠：按厂商分组，并补上人工整理的真实活动 ──────────────────
    od = DATA / "offers.json"
    if od.exists():
        offers = json.loads(od.read_text(encoding="utf-8"))
        og: dict[str, list[dict]] = {}
        for o in offers:
            og.setdefault(slugify(o.get("vendor") or "unknown"), []).append(o)
        for vslug, items in og.items():
            p = OFFERS / f"{vslug}.json"
            if p.exists():
                items = json.loads(p.read_text(encoding="utf-8")) + items
            p.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
            print(f"  offers/{vslug}.json  {len(items)} 条")

    print("\n完成。以后人工编辑只改 data/catalog/ 与 data/offers/。")


if __name__ == "__main__":
    main()

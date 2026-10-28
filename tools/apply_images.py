"""把抓到的产品图合并进 data/catalog（人工维护的源），并登记来源。

为什么需要这一步：
    抓图脚本产出的是 id -> 路径 的映射，而目录数据现在是按厂商分文件的。
    丢进 catalog 里才算真的「有图」，否则页面仍然画示意图。

规则：
    · 只在 image_url 为空时写入 —— 不覆盖已有的、经过核对的图
    · image_source 记「抓取脚本 + 域名」，谁问都能查
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PHOTO_DIR = ROOT / "frontend" / "public" / "parts"


def main() -> None:
    # 剔除表是唯一真相：抓错的图（整机宣传图）不许再被装回来。
    # 之前 apply_images 和 reject_wrong_images 各管一半，重跑一次就把错图带回来了。
    try:
        from reject_wrong_images import WRONG as REJECTED
    except Exception:
        REJECTED = {}

    mapping: dict[str, str] = {}
    for fn in ("part_images.json", "part_images_fetched.json"):
        p = DATA / fn
        if p.exists():
            mapping.update(json.loads(p.read_text(encoding="utf-8")))

    # 只保留文件确实存在的映射（映射里有幽灵条目会让页面 404）
    mapping = {k: v for k, v in mapping.items()
               if (PHOTO_DIR / pathlib.Path(v).name).exists()}
    mapping = {k: v for k, v in mapping.items() if k not in REJECTED}

    filled = 0
    for f in sorted((DATA / "catalog").glob("*/*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for r in rows:
            img = mapping.get(r["id"])
            if not img:
                continue
            specs = r.setdefault("specs", {})
            if specs.get("image_url"):
                continue
            specs["image_url"] = img
            specs["image_source"] = f"厂商资料抓取（{pathlib.Path(img).name}）"
            changed = True
            filled += 1
        if changed:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(f"写入产品图 {filled} 条")

    total = sum(1 for f in (DATA / "catalog").glob("*/*.json")
                for r in json.loads(f.read_text(encoding="utf-8"))
                if (r.get("specs") or {}).get("image_url"))
    print(f"现有图覆盖 {total} / 46")


if __name__ == "__main__":
    main()

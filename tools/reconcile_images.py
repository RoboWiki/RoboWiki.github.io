#!/usr/bin/env python3
"""把已经落盘的产品图反查回零件 id，生成映射。

为什么需要这一步：抓取是逐件落盘的，但映射文件在最后才写；
中途被打断（比如撞上一个巨大的厂商 PDF）就会「图在盘上、映射丢了」。
这里按 safe_name 反查，避免重下。
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PARTS_DIR = ROOT / "frontend" / "public" / "parts"
PARTS = ROOT / "data" / "motors.json"
OUT = ROOT / "data" / "part_images_fetched.json"

# 与 extract_images.py / fetch_images.py 完全一致
def safe_name(part_id: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", part_id).strip("-")
    if len(s) < 4 or not re.search(r"[A-Za-z]", s):
        s = "part"
    return s[:60].lower()


def main() -> None:
    if not PARTS_DIR.exists():
        print("没有图片目录")
        return
    files = {p.stem for p in PARTS_DIR.iterdir() if p.suffix.lower() in
             (".jpg", ".jpeg", ".png", ".webp")}
    parts = json.loads(PARTS.read_text(encoding="utf-8"))

    mapping: dict[str, str] = {}
    for p in parts:
        stem = safe_name(p["id"])
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            if stem in files and (PARTS_DIR / f"{stem}{ext}").exists():
                mapping[p["id"]] = f"/parts/{stem}{ext}"
                break

    OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    total = len(parts)
    print(f"盘点：图片文件 {len(files)} 张，反查到 {len(mapping)}/{total} 个零件")
    print(f"写入 {OUT.relative_to(ROOT)}")
    missing = [p["id"] for p in parts if p["id"] not in mapping]
    if missing:
        print(f"仍缺图 {len(missing)} 个，前 8 个：")
        for m in missing[:8]:
            print("  ", m)


if __name__ == "__main__":
    main()

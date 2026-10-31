"""把 inbox/ 里丢进来的图认领到对应零件。

用法（最省事）：把图片丢进 `inbox/`，文件名用**零件 id** 或**型号**，
然后跑这一条：

    python tools/import_from_inbox.py

文件名怎么起（四种都认，按顺序匹配）：
    达妙-dm-dm-j4340-2ec-v1-1.jpg     精确 id（最稳）
    dm-j4340-2ec-v1-1.jpg             型号（大小写/空格/符号不敏感）
    dji-rm-board-a.png                归档导入的 id
    IM6014.jpg                        纯型号

认领之后它会做三件事：
    1. 拷成 console/public/parts/<id>.jpg|png（统一命名，避免中文与空格进 URL）
    2. 写进 data/part_images.json 映射
    3. 打印「没认领到的文件」与「仍然缺图的零件」

为什么要有这一步：
    手工改 data/catalog/*.json 里的 image_url 也能行，但容易写错路径、
    也容易忘了同步 wiki 的拷贝。走 inbox 就只有「文件名对不对」一个问题。

原图会被统一处理（白底、去多余留白），见 tools/normalize_images.py。
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"
PARTS = ROOT / "frontend" / "public" / "parts"
MAP = ROOT / "data" / "part_images.json"
DATA = ROOT / "data"
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def key(s: str) -> str:
    """比对用的归一化：去大小写、空格、分隔符。"""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", (s or "").lower())


def main() -> None:
    if not INBOX.exists():
        print(f"没有 inbox 目录：{INBOX}")
        return
    files = [f for f in INBOX.iterdir() if f.suffix.lower() in EXTS]
    if not files:
        print("inbox 里没有图片（.jpg / .png / .webp）")
        return

    # 建索引：id 与型号都能反查到零件
    by_id: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    for f in sorted((DATA / "catalog").glob("*/*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            by_id[key(r["id"])] = r
            by_model.setdefault(key(r.get("model") or ""), r)

    mapping = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    PARTS.mkdir(parents=True, exist_ok=True)

    ok, miss = [], []
    for f in files:
        k = key(f.stem)
        part = by_id.get(k) or by_model.get(k)
        if not part:
            miss.append(f.name)
            continue
        ext = ".png" if f.suffix.lower() == ".png" else ".jpg"
        name = f"{re.sub(r'[^a-z0-9]+', '-', part['id'].lower()).strip('-')}{ext}"
        shutil.copy2(f, PARTS / name)
        mapping[part["id"]] = f"/parts/{name}"
        ok.append((f.name, part["id"], name))

    MAP.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")

    for src, pid, name in ok:
        print(f"  ✓ {src:36s} -> {name}")
    if miss:
        print(f"\n没认领到 {len(miss)} 个（文件名既不是零件 id 也不是型号）：")
        for m in miss:
            print(f"  ✗ {m}")

    # 仍然缺图的清单
    missing = []
    for f in sorted((DATA / "catalog").glob("*/*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if not (r.get("specs") or {}).get("image_url") and r["id"] not in mapping:
                missing.append((r["id"], r.get("model"), f.parent.name))
    if missing:
        print(f"\n仍然缺图 {len(missing)} 个：")
        for pid, model, cat in missing:
            print(f"  · {pid:38s} {cat:16s} {model}")

    print("\n认领完成。接着跑：")
    print("  python tools/normalize_images.py    # 统一白底、裁掉多余留白")
    print("  python tools/apply_images.py        # 合并进 data/catalog")
    print("  python -m pipeline all              # 重新生成站点")


if __name__ == "__main__":
    sys.exit(main())

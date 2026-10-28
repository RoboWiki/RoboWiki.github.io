"""从厂商 PDF 里抽产品图，登记成零件图。

为什么优先用 PDF：
    PDF 是厂商自己发的一手资料，里面的产品图不会被防盗链、不会 404、
    也不是官网首页那种场景渲染图。而且 A 级参数的来源本来就是它 ——
    图和数的出处一致，页面上的「来源」才对得上。

用法：
    python tools/extract_pdf_cover.py <pdf> <零件id> [--page 1] [--dry-run]

    例：
    python tools/extract_pdf_cover.py "C:/Downloads/RM_M2006_P36....pdf" dji-robomaster-m2006-p36

取图规则：
    在指定页（默认前 3 页）里找**面积最大的内嵌位图** —— 手册的产品照通常
    就是这一张，其余是图标/线条图。找不到就报错，不回退到截图。
"""
from __future__ import annotations

import io
import json
import pathlib
import sys

import fitz
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PARTS = ROOT / "frontend" / "public" / "parts"
MAP = ROOT / "data" / "part_images.json"
DATA = ROOT / "data" / "catalog"


def biggest_image(doc: fitz.Document, pages: int) -> tuple[int, bytes, int, int] | None:
    best = None
    for i in range(min(pages, len(doc))):
        for img in doc[i].get_images(full=True):
            xref, w, h = img[0], img[2], img[3]
            if w * h < 40000:          # 图标/线条图跳过
                continue
            if best is None or w * h > best[2] * best[3]:
                try:
                    info = doc.extract_image(xref)
                except Exception:
                    continue
                best = (i + 1, info["image"], w, h)
    return best


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    pdf, pid = sys.argv[1], sys.argv[2]
    pages = 3
    if "--page" in sys.argv:
        pages = int(sys.argv[sys.argv.index("--page") + 1])
    dry = "--dry-run" in sys.argv

    doc = fitz.open(pdf)
    got = biggest_image(doc, pages)
    if not got:
        print(f"✗ 前 {pages} 页没找到可用产品图：{pathlib.Path(pdf).name}")
        raise SystemExit(1)
    page, blob, w, h = got
    print(f"  {pid}: p{page} {w}×{h} {len(blob) // 1024} KB")
    if dry:
        return

    im = Image.open(io.BytesIO(blob)).convert("RGB")
    im.thumbnail((900, 900))
    out = PARTS / f"{pid.lower().replace(' ', '-')}.jpg"
    im.save(out, "JPEG", quality=92)

    mapping = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    mapping[pid] = f"/parts/{out.name}"
    MAP.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")

    # 直接写进 catalog（apply_images 只在 image_url 为空时写，这里要的是替换）
    hit = False
    for f in DATA.glob("*/*.json"):
        rows = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for r in rows:
            if r["id"] == pid:
                r.setdefault("specs", {})
                r["specs"]["image_url"] = f"/parts/{out.name}"
                r["specs"]["image_source"] = f"厂商官方 PDF（{pathlib.Path(pdf).name} 第 {page} 页）"
                ch = hit = True
        if ch:
            f.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    if not hit:
        print(f"  ⚠ 目录里没有这个 id：{pid}")
    print(f"  -> {out.name}")


if __name__ == "__main__":
    main()

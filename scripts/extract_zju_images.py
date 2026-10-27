"""从 DJI RoboMaster 手册里抽 GM6020 / M3508 / M2006 的产品图。

复用 extract_images.py 的版面判据：排除整页背景、logo、太扁的尺寸图，
剩下面积最大且长宽比接近 1 的即为产品照。
文件名用 safe_name(part_id)，这样 scripts/reconcile_images.py 能自动反查回零件。
"""
from __future__ import annotations

import pathlib
import re

import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "zju"
OUT = ROOT / "frontend" / "public" / "parts"

JOBS = [
    ("RM GM6020直流无刷电机使用说明.pdf", "dji-robomaster-gm6020", "GM6020"),
    ("RM M3508直流无刷减速电机使用说明.pdf", "dji-robomaster-m3508-p19", "M3508"),
    ("RM M2006 P36直流无刷减速电机使用说明.pdf", "dji-robomaster-m2006-p36", "M2006"),
]


def pick(doc, key: str) -> tuple[bytes, str, int, str] | None:
    pages = [i for i in range(len(doc)) if key.lower() in (doc[i].get_text() or "").lower()]
    for pno in (pages or range(len(doc)))[:6]:
        page = doc[pno]
        best = None
        for im in page.get_images(full=True):
            try:
                rect = page.get_image_bbox(im)
                info = doc.extract_image(im[0])
            except Exception:
                continue
            w, h = rect.width, rect.height
            if min(w, h) < 90 or max(w, h) > 430:
                continue
            if rect.x0 < -5 or rect.y0 < -5:
                continue
            if not (0.6 <= (h / w if w else 0) <= 2.4):
                continue
            area = w * h
            if area < 9_000:
                continue
            if best is None or area > best[0]:
                best = (area, info, pno + 1, f"{int(w)}x{int(h)}pt")
        if best:
            return best[1]["image"], best[1]["ext"], best[2], best[3]
    return None


def main() -> None:
    for fname, pid, key in JOBS:
        pdf = RAW / fname
        if not pdf.exists():
            print("缺", fname)
            continue
        doc = fitz.open(str(pdf))
        hit = pick(doc, key)
        doc.close()
        if not hit:
            print(f"  ✗ {pid} 没找到可用图")
            continue
        data, ext, page, size = hit
        out = OUT / f"{pid}.{ 'jpg' if ext == 'jpeg' else ext }"
        out.write_bytes(data)
        print(f"  ✓ {pid:26s} p{page} {size:10s} -> {out.name} ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()

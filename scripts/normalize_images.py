"""把产品图的黑色背景换成白色，并裁掉多余留白。

为什么需要：
    厂商图两种底：白底（好办）和黑底。黑底图挂在白卡片上就是一个黑洞，
    一排卡片看下来参差不齐。统一成白底之后，卡片才像同一个图录里的。

做法（不动产品本体）：
    1. **只从边缘泛洪**：把与图片四边连通的近黑像素判为背景，换成白色。
       亮度阈值压得很低（默认 26），因为电机本体常常也是黑的 ——
       阈值一高就会把机身吃掉。
    2. 泛洪之后再**按内容外框裁切**并留一点内边距，去掉多余留白。
    3. 已经有白底、或四角不够黑的图，只做裁切，不做替换。

安全阀：
    · 泛洪前先算「四角是否都暗」，不是黑底图直接跳过替换
    · 替换面积超过 92% 视为「整张图都暗」→ 放弃替换，避免把图洗成纯白
    · 原图先备份到 data/_backup/<date>/parts_originals/

用法：
    python scripts/normalize_images.py --dry-run     # 只报告，不改文件
    python scripts/normalize_images.py               # 执行
"""
from __future__ import annotations

import pathlib
import shutil
import sys
from collections import deque
from datetime import date

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMGS = [ROOT / "frontend" / "public" / "parts", ROOT / "wiki" / "docs" / "public" / "parts"]
BACKUP = ROOT / "data" / "_backup" / date.today().isoformat() / "parts_originals"

DARK = 26          # 背景判定亮度上限（0–255）
PAD = 6            # 裁切后保留的内边距
MAX_FILL = 0.92    # 替换面积上限


def lum(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000


def corners_dark(im: Image.Image) -> bool:
    w, h = im.size
    px = im.load()
    pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    return all(lum(px[x, y]) < 45 for x, y in pts)


def flood_bg_to_white(im: Image.Image) -> tuple[Image.Image, float]:
    """从四边泛洪，把连通的近黑像素刷白。返回（新图, 替换比例）。"""
    im = im.copy()
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()

    def push(x, y):
        i = y * w + x
        if seen[i]:
            return
        seen[i] = 1
        if lum(px[x, y]) < DARK:
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    n = 0
    while q:
        x, y = q.popleft()
        px[x, y] = (255, 255, 255)
        n += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                seen[ny * w + nx] = 1
                if lum(px[nx, ny]) < DARK:
                    q.append((nx, ny))
    return im, n / (w * h)


def autocrop(im: Image.Image) -> Image.Image:
    """按内容外框裁切（白底视为空）。"""
    w, h = im.size
    px = im.load()
    left, top, right, bottom = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c = px[x, y]
            # 不是「接近白」就算内容
            if lum(c) < 244 or max(c) - min(c) > 18:
                if x < left:
                    left = x
                if x > right:
                    right = x
                if y < top:
                    top = y
                if y > bottom:
                    bottom = y
    if right <= left or bottom <= top:
        return im
    box = (max(0, left - PAD), max(0, top - PAD),
           min(w, right + PAD), min(h, bottom + PAD))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        return im
    return im.crop(box)


def main() -> None:
    dry = "--dry-run" in sys.argv
    src_dir = IMGS[0]
    files = sorted(f for f in src_dir.iterdir()
                   if f.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not dry:
        BACKUP.mkdir(parents=True, exist_ok=True)

    n_bg = n_crop = n_skip = 0
    for f in files:
        im = Image.open(f).convert("RGB")
        before = im.size
        note = []
        if corners_dark(im):
            im2, ratio = flood_bg_to_white(im)
            if ratio > MAX_FILL:
                note.append(f"整图过暗({ratio:.0%}) 跳过替换")
                n_skip += 1
            else:
                im = im2
                n_bg += 1
                note.append(f"黑底→白({ratio:.0%})")
        im = autocrop(im)
        if im.size != before:
            n_crop += 1
            note.append(f"裁切 {before[0]}x{before[1]}→{im.size[0]}x{im.size[1]}")
        if not note:
            continue
        print(f"  {f.name}: " + "，".join(note))
        if dry:
            continue
        if not (BACKUP / f.name).exists():
            shutil.copy2(f, BACKUP / f.name)
        ext = f.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            im.save(f, "JPEG", quality=90, optimize=True)
        else:
            im.save(f, "PNG", optimize=True)

    print(f"\n黑底转白 {n_bg} 张 · 裁切 {n_crop} 张 · 跳过 {n_skip} 张"
          + ("（dry-run，未写文件）" if dry else f" · 原图备份在 {BACKUP.relative_to(ROOT)}"))

    if not dry:
        # 文档站那份是拷贝，同步一下
        dst = IMGS[1]
        if dst.exists():
            for f in files:
                shutil.copy2(f, dst / f.name)
            print(f"已同步到 {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

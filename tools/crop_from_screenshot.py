"""从用户提供的官方商城截图里裁出产品图。

为什么这么做：
    DJI RoboMaster 的型号页图片拿不到（官网 og:image 是整站图），
    而官方商城截图里每台电机都是白底正视图 —— 直接按格裁出来，
    比留空或放示意图都更接近真实。裁完再跑 normalize_images 统一白底与留边。

用法：
    python tools/crop_from_screenshot.py <截图路径>
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "parts"

#: 截图里的格子位置（按 1830×1276 的原图坐标；脚本会按实际尺寸等比缩放）
#: (文件名, 左, 上, 右, 下)
BOXES = [
    ("dji-robomaster-gm6020.jpg", 30, 55, 450, 350),
    ("dji-robomaster-m2006-p36.jpg", 1400, 55, 1820, 350),
    ("dji-robomaster-m3508-p19.jpg", 55, 720, 385, 1035),
]
BASE_W, BASE_H = 1830, 1276


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: crop_from_screenshot.py <截图路径>")
        raise SystemExit(2)
    src = Image.open(sys.argv[1]).convert("RGB")
    sx, sy = src.width / BASE_W, src.height / BASE_H
    OUT.mkdir(parents=True, exist_ok=True)

    for name, l, t, r, b in BOXES:
        box = (int(l * sx), int(t * sy), int(r * sx), int(b * sy))
        crop = src.crop(box)
        # 只留内容：截图里产品四周是纯白，按非白像素外框收紧一点
        crop.save(OUT / name, "JPEG", quality=92)
        print(f"  {name}  {crop.width}x{crop.height}  <- {box}")

    print(f"\n写入 {len(BOXES)} 张到 {OUT.relative_to(ROOT)}")
    print("下一步：python tools/normalize_images.py  （统一白底并裁掉多余留白）")


if __name__ == "__main__":
    main()

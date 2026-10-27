"""把各手册的参数段落导出成文本，供人工核对后再定值。

为什么不用纯正则定值：这些手册是「表格 + 图」排版，正则很容易把别的数字
（比如 1:1 接口、整机重量）当成目标字段。额定扭矩这种数一旦错了，
整个峰值/额定比就是错的 —— 所以这里只负责**把原文摆出来**，定值由人来做。
"""
from __future__ import annotations

import pathlib
import re

import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "zju"
OUT = ROOT / "data" / "raw" / "zju_text"

KEYS = ["额定转矩", "额定扭矩", "峰值", "最大转矩", "额定转速", "空载", "减速比",
        "重量", "质量", "外径", "尺寸", "电压", "电流", "转矩常数", "编码器"]

FILES = [
    "宇树科技A1电机数据手册.pdf",
    "GO-M8010-6电机数据手册.pdf",
    "RM GM6020直流无刷电机使用说明.pdf",
    "RM M3508直流无刷减速电机使用说明.pdf",
    "RM M2006 P36直流无刷减速电机使用说明.pdf",
    "HWDrive CAN通信协议.pdf",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for fname in FILES:
        pdf = RAW / fname
        if not pdf.exists():
            print("缺", fname)
            continue
        doc = fitz.open(str(pdf))
        lines = []
        for pno in range(len(doc)):
            text = doc[pno].get_text() or ""
            hits = [ln.strip() for ln in text.splitlines()
                    if any(k in ln for k in KEYS)]
            if hits:
                lines.append(f"\n===== p{pno + 1} =====")
                lines.extend(hits)
        doc.close()
        out = OUT / (fname.replace(".pdf", ".txt"))
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"{fname[:38]:38s} -> {out.name} ({len(lines)} 行)")


if __name__ == "__main__":
    main()

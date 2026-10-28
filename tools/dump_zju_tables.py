"""用 PyMuPDF 的表格识别导出规格表（labels 与 values 会被还原成行列）。

先看清楚表格结构，再决定哪些数能进目录 —— 不猜。
"""
from __future__ import annotations

import pathlib

import fitz

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "zju"
OUT = ROOT / "data" / "raw" / "zju_tables"

FILES = [
    "宇树科技A1电机数据手册.pdf",
    "GO-M8010-6电机数据手册.pdf",
    "RM GM6020直流无刷电机使用说明.pdf",
    "RM M3508直流无刷减速电机使用说明.pdf",
    "RM M2006 P36直流无刷减速电机使用说明.pdf",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for fname in FILES:
        pdf = RAW / fname
        if not pdf.exists():
            continue
        doc = fitz.open(str(pdf))
        chunks = []
        for pno in range(len(doc)):
            page = doc[pno]
            try:
                tables = page.find_tables()
            except Exception:
                continue
            for ti, tb in enumerate(tables.tables):
                rows = tb.extract()
                if not rows or len(rows) < 2:
                    continue
                chunks.append(f"\n===== p{pno + 1} table{ti + 1} "
                              f"({len(rows)}×{max(len(r) for r in rows)}) =====")
                for r in rows:
                    cells = [(c or "").replace("\n", " ").strip() for c in r]
                    if any(cells):
                        chunks.append(" | ".join(cells))
        doc.close()
        out = OUT / fname.replace(".pdf", ".tables.txt")
        out.write_text("\n".join(chunks), encoding="utf-8")
        print(f"{fname[:38]:38s} -> {out.name}  ({len(chunks)} 行, {out.stat().st_size} B)")


if __name__ == "__main__":
    main()

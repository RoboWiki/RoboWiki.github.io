"""把库里的评分导成静态快照，供纯静态部署（GitHub Pages）显示。

为什么需要这一步：Pages 上没有后端，页面读不到 /api/ratings。
所以在构建前把聚合结果烤成 JSON 一起发布 —— 读者看到的是
「上次构建时」的真实聚合值，页面上也标明是快照，不假装实时。

用法：
    python scripts/export_ratings.py            # 读 roboselect.db 写到 data/ratings_snapshot.json
    python scripts/export_ratings.py --empty     # 没有库时写空快照（CI 用）
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ratings_snapshot.json"


def main() -> None:
    empty = "--empty" in sys.argv
    if empty:
        OUT.write_text(json.dumps({"total_ratings": 0, "parts": {}, "snapshot": True},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"写空快照 {OUT.relative_to(ROOT)}")
        return

    sys.path.insert(0, str(ROOT / "backend"))
    from sqlmodel import select

    from app.core.db import session
    from app.models import Rating

    db = session()
    try:
        rows = db.exec(select(Rating)).all()
    finally:
        db.close()

    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r.part_id, []).append(r)

    parts = {}
    for pid, rs in by.items():
        n = len(rs)
        hist = {str(i): 0 for i in range(1, 6)}
        for r in rs:
            hist[str(r.score)] = hist.get(str(r.score), 0) + 1
        parts[pid] = {
            "count": n,
            "avg": round(sum(r.score for r in rs) / n, 2),
            "histogram": hist,
            "own_hardware_count": sum(1 for r in rs if r.own_hardware),
            "mine": None,
        }

    OUT.write_text(json.dumps({"total_ratings": len(rows), "parts": parts,
                               "snapshot": True}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"导出 {len(rows)} 条评分 / {len(parts)} 个零件 -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""把**本地库**里的评分导成 JSON，供有后端的部署做静态预览。

注意数据源分工：
    公开站点的评分来自 **GitHub issue**（pipeline/ingest_ratings.py →
    data/ratings_snapshot.json，由 Actions 提交）。本脚本导的是自托管部署
    的本地库，写到 ratings_local.json —— 故意不同名，避免本地跑一次就把
    issue 聚合结果覆盖掉。

用法：
    python tools/export_local_ratings.py            # 读 robowiki.db → ratings_local.json
    python tools/export_local_ratings.py --empty     # 没有库时写空表
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ratings_local.json"


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

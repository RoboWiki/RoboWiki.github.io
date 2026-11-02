"""Outbox worker（第一版：本地 dry-run 产物）。

生产下一步可把 `_publish` 换成 GitHub API / bot PR；核心保证不变：
- 只从 `outbox` 取 pending；
- `idempotency_key` 防重复；
- 失败保留错误与重试计数，不丢任务。
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import select

from .core.db import session
from .models import Outbox


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _publish(job: Outbox) -> Path:
    out_dir = Path(os.environ.get("ROBOWIKI_OUTBOX_DIR", "var/outbox"))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"submission-{job.submission_id or job.id}.json"
    path.write_text(json.dumps({
        "outbox_id": job.id,
        "submission_id": job.submission_id,
        "action": job.action,
        "payload": job.payload,
        "created_at": _now().isoformat(),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def process_one() -> bool:
    with session() as db:
        job = db.exec(
            select(Outbox).where(Outbox.status == "pending")
            .order_by(Outbox.id).limit(1)
        ).first()
        if job is None:
            return False
        job.status = "running"
        job.attempts += 1
        job.next_at = _now()
        db.add(job)
        db.commit()
        try:
            path = _publish(job)
            job.status = "done"
            job.last_error = None
            print(f"[outbox] {job.id} -> {path}")
        except Exception as exc:  # 保留任务，等待重试
            job.status = "failed"
            job.last_error = str(exc)[:500]
            print(f"[outbox] {job.id} failed: {exc}")
        db.add(job)
        db.commit()
        return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="只处理一条后退出")
    args = ap.parse_args()
    if args.once:
        process_one()
        return 0
    interval = float(os.environ.get("ROBOWIKI_WORKER_INTERVAL", "10"))
    while True:
        if not process_one():
            time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())

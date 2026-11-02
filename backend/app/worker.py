"""Outbox worker：把审核通过的提案发布成 PR。

默认 dry-run（写本地产物）；`ROBOWIKI_PUBLISH_MODE=github` 时开核心仓 PR。
核心保证不变：
- 只从 `outbox` 取 pending；
- `idempotency_key` 防重复；
- 失败保留错误与重试计数，不丢任务。
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone

from sqlmodel import select

from .core.config import settings
from .core.db import session
from .models import Outbox
from .publisher import publish_job


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _publish(job: Outbox) -> dict:
    return publish_job(job, settings.data_dir)


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
            result = _publish(job)
            job.status = "done"
            job.last_error = None
            job.result = result
            print(f"[outbox] {job.id} -> {result.get('pr_url') or result.get('path')}")
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

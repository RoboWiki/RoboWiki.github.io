"""Outbox worker：把审核通过的提案发布成 PR。

默认 dry-run（写本地产物）；`ROBOWIKI_PUBLISH_MODE=github` 时开`RoboWiki` 仓 PR。
核心保证不变：
- 只从 `outbox` 取 pending；
- `idempotency_key` 防重复；
- 失败保留错误与重试计数，不丢任务。
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import and_, or_
from sqlmodel import select

from .core.config import settings
from .core.db import session
from .models import Outbox
from .publisher import publish_job


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _outbox_dir() -> Path:
    return Path(os.environ.get("ROBOWIKI_OUTBOX_DIR", "var/outbox"))


def _publish(job: Outbox) -> dict:
    if settings.publish_mode != "github":
        # dry-run 也把「产物落在哪」讲清楚：没有这行日志时，看到任务 done
        # 却找不到 PR 会以为是发布成功。
        print(f"[outbox] {job.id} dry-run：写 {_outbox_dir()}，不会创建 PR")
    return publish_job(job, settings.data_dir)


def process_one() -> bool:
    with session() as db:
        now = _now()
        job = db.exec(
            select(Outbox).where(or_(
                and_(Outbox.status == "pending", Outbox.next_at <= now),
                and_(Outbox.status == "failed", Outbox.attempts < 5,
                     Outbox.next_at <= now),
            )).order_by(Outbox.id).limit(1)
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
            if result.get("dry_run"):
                print(f"[outbox] {job.id} -> dry-run 产物 "
                      f"{result.get('file') or result.get('path') or result}")
            elif result.get("skipped"):
                print(f"[outbox] {job.id} -> skipped：{result.get('reason')}")
            else:
                print(f"[outbox] {job.id} -> "
                      f"{result.get('pr_url') or result.get('file') or result.get('path') or result}")
        except Exception as exc:  # 指数退避重试；超过 5 次才永久失败
            job.status = "pending" if job.attempts < 5 else "failed"
            job.last_error = str(exc)[:500]
            delay = min(300, 5 * 2 ** max(0, job.attempts - 1))
            job.next_at = _now() + timedelta(seconds=delay)
            print(f"[outbox] {job.id} attempt {job.attempts} failed: {exc} "
                  f"（{delay}s 后重试）")
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
    print(f"[outbox] worker 启动：mode={settings.publish_mode}"
          + ("" if settings.publish_mode == "github" else f" · 产物目录 {_outbox_dir()}"))
    interval = float(os.environ.get("ROBOWIKI_WORKER_INTERVAL", "10"))
    while True:
        if not process_one():
            time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())

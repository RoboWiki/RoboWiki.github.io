"""产物版本化信封（ADR-005）。

每个 public/*.json 产物顶层带一个 meta 头：
    {
      "schema_version": 1,
      "generated_at": "<ISO8601 UTC>",
      "source_commit": "<git rev-parse HEAD，非 git 环境为 null>",
      "record_count": <主记录条数>
    }

为什么放这里而不是各 build_* 里各写一份：
    字段口径（版本号、时间格式、commit 容错）必须全仓一致，
    散在四份文件里迟早漂移。下游（前端 / API / 调试）只认这一个形状。

注意：meta 只加在产物顶层，不碰 parts / robots / items 数组内的字段结构。
"""
from __future__ import annotations

import pathlib
import subprocess
from datetime import datetime, timezone

SCHEMA_VERSION = 1

ROOT = pathlib.Path(__file__).resolve().parents[1]


def source_commit() -> str | None:
    """git rev-parse HEAD；非 git 环境（无 .git、无 git 可执行）返回 None。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        pass
    return None


def meta(record_count: int) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit(),
        "record_count": record_count,
    }

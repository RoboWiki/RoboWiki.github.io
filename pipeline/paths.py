"""数据与站点路径的唯一入口。

拆分前：data/、schema/ 与站点同仓，直接读 ROOT。
拆分后：本仓不再保存数据，由 `RoboWiki` 仓的发布物提供；本地开发可以指向
../RoboWiki/data，CI 可以指向解压后的 release。

只改这里，不在各 build_*.py 里散落 os.environ。
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _resolve(env_name: str, default: Path) -> Path:
    raw = os.environ.get(env_name)
    path = Path(raw) if raw else default
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


DATA_DIR = _resolve("ROBOWIKI_DATA_DIR", ROOT / "data")
SCHEMA_DIR = _resolve("ROBOWIKI_SCHEMA_DIR", ROOT / "schema")
# 单仓模式图片在 console/public/parts；拆分后由 `RoboWiki` 仓的 assets/parts 提供。
ASSETS_DIR = _resolve("ROBOWIKI_ASSETS_DIR", ROOT / "console" / "public" / "parts")

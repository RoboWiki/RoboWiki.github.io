"""pytest 配置：把临时目录放到仓库内。

为什么：
    这台机器上 pytest 的默认临时根（%LOCALAPPDATA%\\Temp\\pytest-of-<user>）
    对当前用户不可写，任何用 tmp_path 的用例都会 PermissionError。
    与其让每个用例各自 workaround，不如在 conftest 里统一改掉。
"""
from __future__ import annotations

import os
import pathlib
import shutil
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_TMP = ROOT / ".pytest-tmp"

# 站点仓不再保存 data/schema/assets；测试指向 .data（CI 下载）或同级核心仓。
_CORE = ROOT.parent / "robowiki-core"
_DATA = ROOT / ".data" / "data"
if not _DATA.exists() and (_CORE / "data").exists():
    _DATA = _CORE / "data"
_SCHEMA = ROOT / ".data" / "schema"
if not _SCHEMA.exists() and (_CORE / "schema").exists():
    _SCHEMA = _CORE / "schema"
_ASSETS = ROOT / ".data" / "assets" / "parts"
if not _ASSETS.exists() and (_CORE / "assets" / "parts").exists():
    _ASSETS = _CORE / "assets" / "parts"

os.environ.setdefault("ROBOWIKI_DATA_DIR", str(_DATA))
os.environ.setdefault("ROBOWIKI_SCHEMA_DIR", str(_SCHEMA))
os.environ.setdefault("ROBOWIKI_ASSETS_DIR", str(_ASSETS))


@pytest.fixture()
def tmp_path():
    _TMP.mkdir(exist_ok=True)
    d = tempfile.mkdtemp(prefix="t-", dir=_TMP)
    try:
        yield pathlib.Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)

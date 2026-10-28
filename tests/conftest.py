"""pytest 配置：把临时目录放到仓库内。

为什么：
    这台机器上 pytest 的默认临时根（%LOCALAPPDATA%\\Temp\\pytest-of-<user>）
    对当前用户不可写，任何用 tmp_path 的用例都会 PermissionError。
    与其让每个用例各自 workaround，不如在 conftest 里统一改掉。
"""
from __future__ import annotations

import pathlib
import shutil
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_TMP = ROOT / ".pytest-tmp"


@pytest.fixture()
def tmp_path():
    _TMP.mkdir(exist_ok=True)
    d = tempfile.mkdtemp(prefix="t-", dir=_TMP)
    try:
        yield pathlib.Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)

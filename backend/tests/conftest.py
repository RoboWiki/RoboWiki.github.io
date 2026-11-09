"""测试公共设置。

1. 数据/schema 目录：`app/api/routes/semantics.py` 在 import 时就要找到
   `schema/semantics.json`，否则整个应用起不来。仓库根的报告 `tests/conftest.py`
   会设置这三个变量，但单独跑 `pytest backend/tests` 时那份 conftest 不在
   rootdir 里，收集阶段直接 RuntimeError。这里补一份同口径的定位逻辑，
   让「只跑后端测试」也能起步。
2. 限流器是**进程内全局**的（多副本部署才需要换成 Redis），而测试会反复登录，
   所以每个用例前清一次桶 —— 否则不同模块之间会互相「喂」到 429，
   表现为莫名其妙的 test_only_author_or_staff_can_delete 失败。
"""
from __future__ import annotations

import os
import pathlib

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: 测试不验证真实邮箱；邮箱必填与只读门禁由专门用例开启后覆盖。
os.environ.setdefault("ROBOWIKI_REQUIRE_REGISTER_EMAIL", "false")

#: 每个变量按「下载到 .data 的 release 产物」→「同级 RoboWiki 仓」的顺序找，
#: 找到就 setdefault；找不到就留空，让 semantics.py 自己给出可执行的报错。
_DIR_CANDIDATES = {
    "ROBOWIKI_DATA_DIR": (_ROOT / ".data" / "data",
                          _ROOT.parent / "RoboWiki" / "data"),
    "ROBOWIKI_SCHEMA_DIR": (_ROOT / ".data" / "schema",
                            _ROOT.parent / "RoboWiki" / "schema"),
    "ROBOWIKI_ASSETS_DIR": (_ROOT / ".data" / "assets" / "parts",
                            _ROOT.parent / "RoboWiki" / "assets" / "parts"),
}
for _key, _paths in _DIR_CANDIDATES.items():
    if os.environ.get(_key):
        continue
    for _p in _paths:
        if _p.is_dir():
            os.environ[_key] = str(_p)
            break


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    try:
        from app.api.deps import reset_rate_limits
        reset_rate_limits()
    except Exception:
        pass
    yield

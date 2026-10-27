"""测试公共设置。

限流器是**进程内全局**的（多副本部署才需要换成 Redis），而测试会反复登录，
所以每个用例前清一次桶 —— 否则不同模块之间会互相「喂」到 429，
表现为莫名其妙的 test_only_author_or_staff_can_delete 失败。
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    try:
        from app.api.deps import reset_rate_limits
        reset_rate_limits()
    except Exception:
        pass
    yield

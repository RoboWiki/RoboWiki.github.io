"""迁移完整性：模型里的每张表都必须有对应 Alembic 建表语句，且只有一个 head。

生产库用 `auto_create_tables=false`，只跑 `alembic upgrade head`；漏迁一张表
不会在本地测试里暴露（那里走 SQLModel.create_all），却会在线上直接 500。
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
MODELS = BACKEND / 'app' / 'models.py'
VERSIONS = BACKEND / 'alembic' / 'versions'


def _model_tables() -> set[str]:
    text = MODELS.read_text(encoding='utf-8')
    return set(re.findall(r'__tablename__ = "([^"]+)"', text))


def _migrated_tables() -> set[str]:
    tables: set[str] = set()
    for path in VERSIONS.glob('*.py'):
        text = path.read_text(encoding='utf-8')
        tables |= set(re.findall(r"create_table\(\s*['\"]([^'\"]+)['\"]", text))
    return tables


def _migration_heads() -> set[str]:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in VERSIONS.glob('*.py'):
        text = path.read_text(encoding='utf-8')
        rev = re.search(r"^revision: str = '([^']+)'", text, re.MULTILINE)
        down = re.search(r"^down_revision: [^=]+= (?:'([^']+)'|None)",
                         text, re.MULTILINE)
        if rev:
            revisions.add(rev.group(1))
        if down and down.group(1):
            parents.add(down.group(1))
    return revisions - parents


def test_every_model_table_has_migration():
    missing = sorted(_model_tables() - _migrated_tables())
    assert not missing, f'模型表缺少 Alembic 迁移：{missing}'


def test_single_migration_head():
    heads = _migration_heads()
    assert len(heads) == 1, f'alembic 存在多个 head：{sorted(heads)}'

"""handle provisional flag for provider-first signups

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-11-09 21:00:00.000000

第三方首登（微信 / GitHub）自动生成 `wx-*` / `gh-*` 账号名；标记为临时，
允许用户一次性改成自己的 handle。已有的这类账号回填为 true。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, Sequence[str], None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('handle_provisional', sa.Boolean(),
                                     nullable=False, server_default=sa.false()))
    op.execute("UPDATE users SET handle_provisional = true "
               "WHERE handle LIKE 'wx-%' OR handle LIKE 'gh-%'")


def downgrade() -> None:
    op.drop_column('users', 'handle_provisional')

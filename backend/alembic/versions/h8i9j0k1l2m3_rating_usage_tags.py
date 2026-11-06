"""rating usage level + reason tags

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-11-06 03:00:00.000000

1. `ratings.usage_level` —— 使用时长分档（long / short / unboxed）。
   own_hardware 只回答「装没装过」，回答不了「用了多久」；
   两者分开存，聚合时才能给不同权重。
2. `ratings.reason_tags` —— 逗号分隔的理由标签（最多 3 个）。
   只收白名单值：理由要能聚合、能搜索，不能是自由文本。

两列都给 server_default=''，老数据不需要回填：空串表示「没填」。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ratings', sa.Column('usage_level', sa.String(length=16),
                                       nullable=False, server_default=''))
    op.add_column('ratings', sa.Column('reason_tags', sa.String(length=128),
                                       nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('ratings', 'reason_tags')
    op.drop_column('ratings', 'usage_level')

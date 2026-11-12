"""comment withdrawn / edited_at

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-11-23 10:00:00.000000

软撤回：清正文但保留评论行与子回复；edited_at 记录最后一次编辑/撤回时间。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'n4o5p6q7r8s9'
down_revision: Union[str, Sequence[str], None] = 'm3n4o5p6q7r8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('comments', sa.Column('withdrawn', sa.Boolean(),
                                        nullable=False, server_default=sa.false()))
    op.create_index('ix_comments_withdrawn', 'comments', ['withdrawn'])
    op.add_column('comments', sa.Column(
        'edited_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('comments', 'edited_at')
    op.drop_index('ix_comments_withdrawn', table_name='comments')
    op.drop_column('comments', 'withdrawn')

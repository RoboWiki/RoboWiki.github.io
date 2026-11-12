"""comment quote reply

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-11-24 10:00:00.000000

引用回复：quote_id 指向被引用评论（**刻意不加外键**，与 posts.accepted_comment_id
同理 —— comments 自引用外键会让建表/删除形成循环依赖）；quote_author /
quote_excerpt 是创建时拍下的快照，被引用方撤回或隐藏时由服务端清空。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, Sequence[str], None] = 'n4o5p6q7r8s9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('comments', sa.Column('quote_id', sa.Integer(), nullable=True))
    op.create_index('ix_comments_quote_id', 'comments', ['quote_id'])
    op.add_column('comments', sa.Column(
        'quote_author', sqlmodel.sql.sqltypes.AutoString(),
        nullable=False, server_default=''))
    op.add_column('comments', sa.Column(
        'quote_excerpt', sqlmodel.sql.sqltypes.AutoString(),
        nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('comments', 'quote_excerpt')
    op.drop_column('comments', 'quote_author')
    op.drop_index('ix_comments_quote_id', table_name='comments')
    op.drop_column('comments', 'quote_id')

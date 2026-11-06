"""account avatar + accepted answer

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-11-06 16:30:00.000000

1. `users.avatar_url` —— 自定义头像地址（站内 /media/... 或 http(s)）。
   不设 server_default：NULL 表示「没设置」，前端回落 avatar_hue 底色。
2. `posts.accepted_comment_id` —— 问答闭环的采纳标记。非空即「已解决」。
   刻意不加外键：posts ↔ comments 互相引用会形成建表/删除的循环依赖；
   评论被删时是否清空采纳由业务决定，不能交给数据库级联。
   索引用于 `GET /posts?solved=true|false` 的过滤。

生产（auto_create_tables=false）跑 `alembic upgrade head`；
测试库由 SQLModel.create_all 直接建表。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500),
                                     nullable=True))
    op.add_column('posts', sa.Column('accepted_comment_id', sa.Integer(),
                                     nullable=True))
    op.create_index('ix_posts_accepted_comment_id', 'posts',
                    ['accepted_comment_id'])


def downgrade() -> None:
    op.drop_index('ix_posts_accepted_comment_id', table_name='posts')
    op.drop_column('posts', 'accepted_comment_id')
    op.drop_column('users', 'avatar_url')

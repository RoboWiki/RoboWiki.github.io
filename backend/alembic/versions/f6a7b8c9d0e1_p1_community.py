"""P1 互动：通知、媒体、文档页评论的嵌套/状态/软删

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-05 12:00:00.000000

三块内容：
1. `notifications` —— 回复/举报处置的站内提醒，只追加，按 read_at 判未读。
2. `media` —— 评论配图的元数据；文件落在 ROBOWIKI_MEDIA_DIR。
3. `wiki_comments` 新列：
   · root_id      —— 根讨论 id，回复（含多层）都绑到同一条根；
   · status       —— visible / pending / hidden；pending 仅作者与站务可见；
   · deleted_at / deleted_by —— 软删除，子节点保留。
   `hidden` 列保留（旧查询仍用它），hide/restore 会同时同步 status。

auto_create_tables=true 的开发/测试库由 SQLModel.create_all 建表；
生产（auto_create_tables=false）跑 `alembic upgrade head`。

说明：root_id / deleted_by 在 ORM 里声明了外键，但 SQLite 不支持给已有表
补外键约束，所以迁移里只建列与索引（代码层靠 id 引用保证）；Postgres 上
等价于同样的逻辑约束，避免迁移因数据库方言分叉。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 通知 ────────────────────────────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('link', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('read_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_read_at', 'notifications', ['read_at'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_user_read', 'notifications',
                    ['user_id', 'read_at'])
    op.create_index('ix_notifications_user_created', 'notifications',
                    ['user_id', 'created_at'])

    # ── 媒体 ────────────────────────────────────────────────────────────────
    op.create_table(
        'media',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('original_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('content_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_media_user_id', 'media', ['user_id'])
    op.create_index('ix_media_created_at', 'media', ['created_at'])

    # ── 文档页评论：嵌套 / 状态 / 软删 ───────────────────────────────────────
    op.add_column('wiki_comments', sa.Column('root_id', sa.Integer(), nullable=True))
    op.add_column('wiki_comments', sa.Column(
        'status', sqlmodel.sql.sqltypes.AutoString(), nullable=False,
        server_default='visible'))
    op.add_column('wiki_comments', sa.Column(
        'deleted_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True))
    op.add_column('wiki_comments', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_index('ix_wiki_comments_root_id', 'wiki_comments', ['root_id'])
    op.create_index('ix_wiki_comments_status', 'wiki_comments', ['status'])
    op.create_index('ix_wiki_comments_deleted_at', 'wiki_comments', ['deleted_at'])
    op.create_index('ix_wiki_root_created', 'wiki_comments', ['root_id', 'created_at'])
    op.create_index('ix_wiki_page_status', 'wiki_comments', ['page', 'status'])


def downgrade() -> None:
    op.drop_index('ix_wiki_page_status', table_name='wiki_comments')
    op.drop_index('ix_wiki_root_created', table_name='wiki_comments')
    op.drop_index('ix_wiki_comments_deleted_at', table_name='wiki_comments')
    op.drop_index('ix_wiki_comments_status', table_name='wiki_comments')
    op.drop_index('ix_wiki_comments_root_id', table_name='wiki_comments')
    op.drop_column('wiki_comments', 'deleted_by')
    op.drop_column('wiki_comments', 'deleted_at')
    op.drop_column('wiki_comments', 'status')
    op.drop_column('wiki_comments', 'root_id')

    op.drop_index('ix_media_created_at', table_name='media')
    op.drop_index('ix_media_user_id', table_name='media')
    op.drop_table('media')

    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_notifications_user_read', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_read_at', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')

"""email notifications + bind/change email

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-05 00:00:00.000000

1. `users.email_notify` —— 站内通知是否附带邮件副本。
2. `email_tokens.meta` —— 换绑邮箱时记录目标地址，确认后才写 users.email。
3. `email_outbox` —— 异步邮件队列；worker 发送、失败退避重试。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('email_notify', sa.Boolean(), nullable=False,
                  server_default=sa.text('false')),
    )
    op.add_column('email_tokens', sa.Column('meta', sa.JSON(), nullable=True))

    op.create_table(
        'email_outbox',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('to_addr', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('html', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('dedupe_key', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('next_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('last_error', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('sent_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_outbox_user_id', 'email_outbox', ['user_id'])
    op.create_index('ix_email_outbox_to_addr', 'email_outbox', ['to_addr'])
    op.create_index('ix_email_outbox_dedupe_key', 'email_outbox', ['dedupe_key'],
                    unique=True)
    op.create_index('ix_email_outbox_status', 'email_outbox', ['status'])
    op.create_index('ix_email_outbox_next_at', 'email_outbox', ['next_at'])
    op.create_index('ix_email_outbox_status_next', 'email_outbox',
                    ['status', 'next_at'])


def downgrade() -> None:
    op.drop_index('ix_email_outbox_status_next', table_name='email_outbox')
    op.drop_index('ix_email_outbox_next_at', table_name='email_outbox')
    op.drop_index('ix_email_outbox_status', table_name='email_outbox')
    op.drop_index('ix_email_outbox_dedupe_key', table_name='email_outbox')
    op.drop_index('ix_email_outbox_to_addr', table_name='email_outbox')
    op.drop_index('ix_email_outbox_user_id', table_name='email_outbox')
    op.drop_table('email_outbox')
    op.drop_column('email_tokens', 'meta')
    op.drop_column('users', 'email_notify')

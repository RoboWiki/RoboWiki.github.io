"""wechat qr login tickets + user bans

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-11-09 13:30:00.000000

1. `login_tickets` —— 网页扫码登录的一次性票据（scene 里只放 ticket；
   confirmed 后暂存 TokenOut 供网页取走，5 分钟过期）。
2. `user_bans` —— 封禁记录；存在 `lifted_at IS NULL` 的行即生效。
   不往 `users` 加 banned 列，保留「谁、为什么、何时解封」的历史。

这两张表此前只由 SQLModel.create_all 在开发/测试库建出；
生产（auto_create_tables=false）必须补迁移，否则扫码登录与封禁检查会 500。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, Sequence[str], None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'login_tickets',
        sa.Column('ticket', sqlmodel.sql.sqltypes.AutoString(length=64),
                  nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('session', sa.JSON(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(),
                  nullable=False),
        sa.Column('expires_at', sqlmodel.sql.sqltypes.UTCDateTime(),
                  nullable=False),
        sa.Column('confirmed_at', sqlmodel.sql.sqltypes.UTCDateTime(),
                  nullable=True),
        sa.PrimaryKeyConstraint('ticket'),
    )
    op.create_index('ix_login_tickets_status', 'login_tickets', ['status'])
    op.create_index('ix_login_tickets_expires', 'login_tickets', ['expires_at'])

    op.create_table(
        'user_bans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('banned_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(),
                  nullable=False),
        sa.Column('lifted_at', sqlmodel.sql.sqltypes.UTCDateTime(),
                  nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['banned_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_bans_user_id', 'user_bans', ['user_id'])
    op.create_index('ix_user_bans_user_active', 'user_bans',
                    ['user_id', 'lifted_at'])


def downgrade() -> None:
    op.drop_index('ix_user_bans_user_active', table_name='user_bans')
    op.drop_index('ix_user_bans_user_id', table_name='user_bans')
    op.drop_table('user_bans')
    op.drop_index('ix_login_tickets_expires', table_name='login_tickets')
    op.drop_index('ix_login_tickets_status', table_name='login_tickets')
    op.drop_table('login_tickets')

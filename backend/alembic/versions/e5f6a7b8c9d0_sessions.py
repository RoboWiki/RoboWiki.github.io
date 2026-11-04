"""refresh sessions + GitHub handoff codes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-05 00:00:00.000000

P0 跨域会话所需：
1. `users.session_epoch` —— logout-all 后让所有 access token 失效。
2. `refresh_tokens` —— 30 天轮换 refresh，一次登录一个 family；复用即撤销整链。
3. `auth_handoffs` —— GitHub OAuth 回跳的一次性 code；JWT 不进 Location。

auto_create_tables=true 的开发/测试库由 SQLModel.create_all 建表；
生产（auto_create_tables=false）跑 `alembic upgrade head`。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('session_epoch', sa.Integer(), nullable=False,
                                     server_default='0'))

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('family', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('client', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expires_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('used_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('revoked_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens',
                    ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_family', 'refresh_tokens', ['family'])
    op.create_index('ix_refresh_user_family', 'refresh_tokens',
                    ['user_id', 'family'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_expires', 'refresh_tokens', ['expires_at'])

    op.create_table(
        'auth_handoffs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('code_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('return_to', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expires_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('used_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auth_handoffs_user_id', 'auth_handoffs', ['user_id'])
    op.create_index('ix_auth_handoffs_code_hash', 'auth_handoffs',
                    ['code_hash'], unique=True)
    op.create_index('ix_handoff_expires', 'auth_handoffs', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_handoff_expires', table_name='auth_handoffs')
    op.drop_index('ix_auth_handoffs_code_hash', table_name='auth_handoffs')
    op.drop_index('ix_auth_handoffs_user_id', table_name='auth_handoffs')
    op.drop_table('auth_handoffs')

    op.drop_index('ix_refresh_expires', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_user_family', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_family', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_column('users', 'session_epoch')

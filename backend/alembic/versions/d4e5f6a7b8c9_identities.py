"""third-party identities (github / wechat mini)

Revision ID: d4e5f6a7b8c9
Revises: c7d8e9f0a1b2
Create Date: 2026-11-25 10:00:00.000000

新增两件事：

1. `identities` 表 —— 一个 user 可以绑多个第三方身份，
   `(provider, subject)` 唯一。subject 是提供方侧的稳定 ID
   （GitHub 数字 id / 微信 openid），换昵称换邮箱都不变。
2. `users.password_set` —— 第三方登录建出来的账号拿着一个没人知道的
   随机口令哈希，这一列记「能不能口令登录」，解绑最后一个身份前要用它
   判断会不会把账号锁死。已有账号默认 True。

`auto_create_tables=true`（开发/测试）走 SQLModel.metadata.create_all，
不需要这条迁移；生产（auto_create_tables=false）用 alembic upgrade head。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_set', sa.Boolean(), nullable=False,
                                     server_default=sa.true()))

    op.create_table(
        'identities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('raw', sa.JSON(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'subject',
                            name='uq_identity_provider_subject'),
    )
    op.create_index('ix_identities_user_id', 'identities', ['user_id'])
    op.create_index('ix_identities_provider', 'identities', ['provider'])
    op.create_index('ix_identities_subject', 'identities', ['subject'])
    op.create_index('ix_identities_email', 'identities', ['email'])
    op.create_index('ix_identities_user_provider', 'identities',
                    ['user_id', 'provider'])


def downgrade() -> None:
    op.drop_index('ix_identities_user_provider', table_name='identities')
    op.drop_index('ix_identities_email', table_name='identities')
    op.drop_index('ix_identities_subject', table_name='identities')
    op.drop_index('ix_identities_provider', table_name='identities')
    op.drop_index('ix_identities_user_id', table_name='identities')
    op.drop_table('identities')
    op.drop_column('users', 'password_set')

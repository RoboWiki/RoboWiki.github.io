"""reproduction reports for build recipes

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-11-06 14:50:00.000000

方案复现记录：一条 = 一次真实复现尝试的结果（success / partial / failed）。

为什么不复用 ratings：评分是「值不值」的主观分档，复现是「装不装得出来」
的事实判断，两者的口径、聚合方式和展示位置都不同。build_id 不加外键——
方案存在数据仓里，不在本站库里。

auto_create_tables=true 的开发/测试库由 SQLModel.create_all 建表；
生产（auto_create_tables=false）跑 `alembic upgrade head`。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reproductions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('build_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('outcome', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('changes', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('note', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('updated_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'build_id', name='uq_reproduction_once'),
    )
    op.create_index('ix_reproductions_build_id', 'reproductions', ['build_id'])
    op.create_index('ix_reproductions_user_id', 'reproductions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_reproductions_user_id', table_name='reproductions')
    op.drop_index('ix_reproductions_build_id', table_name='reproductions')
    op.drop_table('reproductions')

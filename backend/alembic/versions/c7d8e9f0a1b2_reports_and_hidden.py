"""content reports and moderation flags

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-11-03 15:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ('posts', 'comments', 'wiki_comments'):
        op.add_column(table, sa.Column('hidden', sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
        op.create_index(f'ix_{table}_hidden', table, ['hidden'])

    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('target_kind', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('detail', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('resolution_note', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('resolver_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('resolved_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id']),
        sa.ForeignKeyConstraint(['resolver_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reporter_id', 'target_kind', 'target_id',
                            name='uq_report_once'),
    )
    op.create_index('ix_reports_reporter_id', 'reports', ['reporter_id'])
    op.create_index('ix_reports_target_id', 'reports', ['target_id'])
    op.create_index('ix_reports_status', 'reports', ['status'])
    op.create_index('ix_reports_created_at', 'reports', ['created_at'])
    op.create_index('ix_reports_status_created', 'reports', ['status', 'created_at'])
    op.create_index('ix_reports_target', 'reports', ['target_kind', 'target_id'])


def downgrade() -> None:
    op.drop_index('ix_reports_target', table_name='reports')
    op.drop_index('ix_reports_status_created', table_name='reports')
    op.drop_index('ix_reports_created_at', table_name='reports')
    op.drop_index('ix_reports_status', table_name='reports')
    op.drop_index('ix_reports_target_id', table_name='reports')
    op.drop_index('ix_reports_reporter_id', table_name='reports')
    op.drop_table('reports')

    for table in ('wiki_comments', 'comments', 'posts'):
        op.drop_index(f'ix_{table}_hidden', table_name=table)
        op.drop_column(table, 'hidden')

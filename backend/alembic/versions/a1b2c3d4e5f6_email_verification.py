"""email verification and reset tokens

Revision ID: a1b2c3d4e5f6
Revises: 8f2c1a7d4e60
Create Date: 2026-11-03 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8f2c1a7d4e60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False,
                                     server_default=sa.false()))
    op.create_table(
        'email_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('purpose', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('token_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expires_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('used_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_tokens_user_id', 'email_tokens', ['user_id'])
    op.create_index('ix_email_tokens_purpose', 'email_tokens', ['purpose'])
    op.create_index('ix_email_tokens_token_hash', 'email_tokens', ['token_hash'],
                    unique=True)
    op.create_index('ix_email_tokens_expires_at', 'email_tokens', ['expires_at'])
    op.create_index('ix_email_tokens_user_purpose', 'email_tokens',
                    ['user_id', 'purpose'])


def downgrade() -> None:
    op.drop_index('ix_email_tokens_user_purpose', table_name='email_tokens')
    op.drop_index('ix_email_tokens_expires_at', table_name='email_tokens')
    op.drop_index('ix_email_tokens_token_hash', table_name='email_tokens')
    op.drop_index('ix_email_tokens_purpose', table_name='email_tokens')
    op.drop_index('ix_email_tokens_user_id', table_name='email_tokens')
    op.drop_table('email_tokens')
    op.drop_column('users', 'email_verified')

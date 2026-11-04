"""outbox result

Revision ID: 8f2c1a7d4e60
Revises: 5322131b71ab
Create Date: 2026-11-02 23:05:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f2c1a7d4e60'
down_revision: Union[str, Sequence[str], None] = '5322131b71ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('outbox', sa.Column('result', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('outbox', 'result')

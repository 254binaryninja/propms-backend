"""add admin_id to properties

Revision ID: b5c63eac8a8f
Revises: 32f36fdd9135
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b5c63eac8a8f'
down_revision: Union[str, Sequence[str], None] = '32f36fdd9135'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'properties',
        sa.Column('admin_id', sa.UUID(), sa.ForeignKey('admin_users.id'), nullable=False)
    )


def downgrade() -> None:
    op.drop_column('properties', 'admin_id')

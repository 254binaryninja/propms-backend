"""add_property_admin_relationship

Revision ID: b5c63eac8a8f
Revises: 32f36fdd9135
Create Date: 2026-04-30 02:21:57.345410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c63eac8a8f'
down_revision: Union[str, Sequence[str], None] = '32f36fdd9135'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add admin_id to properties table."""
    # Step 1: Add admin_id column as nullable
    op.add_column('properties', sa.Column('admin_id', sa.UUID(), nullable=True))

    # Step 2: Populate admin_id with first admin user
    connection = op.get_bind()
    from sqlalchemy import text

    # Get first admin (ordered by created_at)
    result = connection.execute(text("SELECT id FROM admin_users ORDER BY created_at LIMIT 1"))
    first_admin_id = result.scalar()

    if not first_admin_id:
        raise Exception(
            "Cannot migrate: No admin users found in database. "
            "Please run 'python scripts/seed_admin.py' first to create an admin user."
        )

    # Assign all existing properties to first admin
    connection.execute(
        text("UPDATE properties SET admin_id = :admin_id WHERE admin_id IS NULL"),
        {"admin_id": first_admin_id}
    )

    # Step 3: Make admin_id non-nullable and add constraints
    op.alter_column('properties', 'admin_id', nullable=False)
    op.create_foreign_key('fk_properties_admin_id', 'properties', 'admin_users', ['admin_id'], ['id'])
    op.create_index('ix_properties_admin_id', 'properties', ['admin_id'])


def downgrade() -> None:
    """Downgrade schema - Remove admin_id from properties table."""
    op.drop_index('ix_properties_admin_id', table_name='properties')
    op.drop_constraint('fk_properties_admin_id', 'properties', type_='foreignkey')
    op.drop_column('properties', 'admin_id')

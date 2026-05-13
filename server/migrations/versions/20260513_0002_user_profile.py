"""add user profile fields

Revision ID: 0002_user_profile
Revises: 0001_initial_schema
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_user_profile"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_object_key", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("avatar_content_type", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("signature", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "signature")
    op.drop_column("users", "avatar_content_type")
    op.drop_column("users", "avatar_object_key")

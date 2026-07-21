"""add user profile fields

Revision ID: ac12f8739a6b
Revises: f31a8c7d9b02
Create Date: 2026-07-20 22:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ac12f8739a6b"
down_revision: Union[str, Sequence[str], None] = "f31a8c7d9b02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("avatar_data_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_data_url")
    op.drop_column("users", "phone")

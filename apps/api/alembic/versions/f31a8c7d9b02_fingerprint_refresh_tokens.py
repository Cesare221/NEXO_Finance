"""fingerprint refresh tokens

Revision ID: f31a8c7d9b02
Revises: 54213976b4f9
Create Date: 2026-07-17 23:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f31a8c7d9b02"
down_revision: Union[str, Sequence[str], None] = "54213976b4f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing sessions contain reusable tokens and cannot be safely transformed
    # in a database-independent migration. Re-authentication is required once.
    op.execute("DELETE FROM user_sessions")
    op.drop_index("ix_user_sessions_refresh_token", table_name="user_sessions")
    op.alter_column(
        "user_sessions",
        "refresh_token",
        new_column_name="refresh_token_hash",
        existing_type=sa.String(length=512),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.create_index(
        "ix_user_sessions_refresh_token_hash",
        "user_sessions",
        ["refresh_token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.execute("DELETE FROM user_sessions")
    op.drop_index(
        "ix_user_sessions_refresh_token_hash",
        table_name="user_sessions",
    )
    op.alter_column(
        "user_sessions",
        "refresh_token_hash",
        new_column_name="refresh_token",
        existing_type=sa.String(length=64),
        type_=sa.String(length=512),
        existing_nullable=False,
    )
    op.create_index(
        "ix_user_sessions_refresh_token",
        "user_sessions",
        ["refresh_token"],
        unique=True,
    )

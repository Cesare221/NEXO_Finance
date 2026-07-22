"""add session families and privacy controls

Revision ID: c91d4e7a2f10
Revises: b81f4c6d2a10
"""

from collections.abc import Sequence
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "c91d4e7a2f10"
down_revision: str | Sequence[str] | None = "b81f4c6d2a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_sessions", sa.Column("family_id", sa.String(36), nullable=True))
    op.add_column("user_sessions", sa.Column("parent_refresh_token_hash", sa.String(64), nullable=True))
    op.add_column("user_sessions", sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("user_sessions", sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_sessions", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_sessions", sa.Column("revocation_reason", sa.String(50), nullable=True))
    op.add_column("user_sessions", sa.Column("device_name", sa.String(80), nullable=True))
    op.add_column("user_sessions", sa.Column("ip_hash", sa.String(64), nullable=True))

    sessions = sa.table(
        "user_sessions",
        sa.column("id", sa.Integer),
        sa.column("family_id", sa.String),
    )
    connection = op.get_bind()
    for session_id in connection.execute(sa.select(sessions.c.id)).scalars():
        connection.execute(
            sessions.update().where(sessions.c.id == session_id).values(family_id=str(uuid.uuid4()))
        )
    op.alter_column("user_sessions", "family_id", nullable=False)
    op.create_index("ix_user_sessions_family_id", "user_sessions", ["family_id"])

    op.add_column("users", sa.Column("privacy_policy_version", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("ai_data_processing_consent", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("users", sa.Column("ai_consent_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ai_consent_updated_at")
    op.drop_column("users", "ai_data_processing_consent")
    op.drop_column("users", "privacy_accepted_at")
    op.drop_column("users", "privacy_policy_version")
    op.drop_index("ix_user_sessions_family_id", table_name="user_sessions")
    op.drop_column("user_sessions", "revocation_reason")
    op.drop_column("user_sessions", "ip_hash")
    op.drop_column("user_sessions", "device_name")
    op.drop_column("user_sessions", "revoked_at")
    op.drop_column("user_sessions", "rotated_at")
    op.drop_column("user_sessions", "last_used_at")
    op.drop_column("user_sessions", "parent_refresh_token_hash")
    op.drop_column("user_sessions", "family_id")

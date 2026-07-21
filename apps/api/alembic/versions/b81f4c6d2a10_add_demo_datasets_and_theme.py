"""add demo datasets and theme

Revision ID: b81f4c6d2a10
Revises: ac12f8739a6b
Create Date: 2026-07-20 22:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b81f4c6d2a10"
down_revision: Union[str, Sequence[str], None] = "ac12f8739a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demo_datasets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_demo_datasets_user_id", "demo_datasets", ["user_id"])
    op.create_index(
        "uq_demo_datasets_active_user_version",
        "demo_datasets",
        ["user_id", "version"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

    op.add_column(
        "users",
        sa.Column(
            "theme_preference",
            sa.String(length=10),
            server_default="system",
            nullable=False,
        ),
    )

    for table_name in (
        "financial_accounts",
        "categories",
        "credit_cards",
        "billing_statements",
        "transactions",
        "recurring_rules",
    ):
        op.add_column(
            table_name,
            sa.Column(
                "demo_dataset_id",
                sa.Integer(),
                sa.ForeignKey("demo_datasets.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index(
            f"ix_{table_name}_demo_dataset_id",
            table_name,
            ["demo_dataset_id"],
        )


def downgrade() -> None:
    for table_name in (
        "recurring_rules",
        "transactions",
        "billing_statements",
        "credit_cards",
        "categories",
        "financial_accounts",
    ):
        op.drop_index(f"ix_{table_name}_demo_dataset_id", table_name=table_name)
        op.drop_column(table_name, "demo_dataset_id")

    op.drop_column("users", "theme_preference")
    op.drop_index("uq_demo_datasets_active_user_version", table_name="demo_datasets")
    op.drop_index("ix_demo_datasets_user_id", table_name="demo_datasets")
    op.drop_table("demo_datasets")

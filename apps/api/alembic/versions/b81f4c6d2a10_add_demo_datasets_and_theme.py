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
        sa.UniqueConstraint("id", "user_id", name="uq_demo_datasets_id_user_id"),
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

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "theme_preference",
                sa.String(length=10),
                server_default="system",
                nullable=False,
            )
        )

    for table_name in (
        "financial_accounts",
        "categories",
        "credit_cards",
        "billing_statements",
        "transactions",
        "recurring_rules",
    ):
        with op.batch_alter_table(table_name) as batch_op:
            if table_name == "categories":
                batch_op.create_unique_constraint(
                    "uq_categories_id_user_id", ["id", "user_id"]
                )
            elif table_name in ("transactions", "recurring_rules"):
                batch_op.create_foreign_key(
                    f"fk_{table_name}_category_user",
                    "categories",
                    ["category_id", "user_id"],
                    ["id", "user_id"],
                )
            batch_op.add_column(
                sa.Column("demo_dataset_id", sa.Integer(), nullable=True)
            )
            batch_op.create_index(
                f"ix_{table_name}_demo_dataset_id", ["demo_dataset_id"]
            )
            batch_op.create_foreign_key(
                f"fk_{table_name}_demo_dataset",
                "demo_datasets",
                ["demo_dataset_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_foreign_key(
                f"fk_{table_name}_demo_dataset_user",
                "demo_datasets",
                ["demo_dataset_id", "user_id"],
                ["id", "user_id"],
            )
        if table_name == "categories":
            with op.batch_alter_table("categories") as batch_op:
                batch_op.create_foreign_key(
                    "fk_categories_parent_user",
                    "categories",
                    ["parent_id", "user_id"],
                    ["id", "user_id"],
                )

    with op.batch_alter_table("installment_plans") as batch_op:
        batch_op.create_foreign_key(
            "fk_installment_plans_category_user",
            "categories",
            ["category_id", "user_id"],
            ["id", "user_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("installment_plans") as batch_op:
        batch_op.drop_constraint(
            "fk_installment_plans_category_user", type_="foreignkey"
        )

    for table_name in (
        "recurring_rules",
        "transactions",
        "billing_statements",
        "credit_cards",
        "categories",
        "financial_accounts",
    ):
        with op.batch_alter_table(table_name) as batch_op:
            if table_name in ("transactions", "recurring_rules"):
                batch_op.drop_constraint(
                    f"fk_{table_name}_category_user", type_="foreignkey"
                )
            elif table_name == "categories":
                batch_op.drop_constraint(
                    "fk_categories_parent_user", type_="foreignkey"
                )
                batch_op.drop_constraint(
                    "uq_categories_id_user_id", type_="unique"
                )
            batch_op.drop_constraint(
                f"fk_{table_name}_demo_dataset_user", type_="foreignkey"
            )
            batch_op.drop_constraint(
                f"fk_{table_name}_demo_dataset", type_="foreignkey"
            )
            batch_op.drop_index(f"ix_{table_name}_demo_dataset_id")
            batch_op.drop_column("demo_dataset_id")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("theme_preference")
    op.drop_index("uq_demo_datasets_active_user_version", table_name="demo_datasets")
    op.drop_index("ix_demo_datasets_user_id", table_name="demo_datasets")
    op.drop_table("demo_datasets")

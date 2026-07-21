from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    Table,
    create_engine,
    event,
    inspect,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401
from app.core.database import Base


RESOURCE_TABLES = (
    "financial_accounts",
    "categories",
    "credit_cards",
    "billing_statements",
    "transactions",
    "recurring_rules",
)

CATEGORY_OWNERSHIP_TABLES = (
    "transactions",
    "installment_plans",
    "recurring_rules",
)


def _task_one_migration():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "b81f4c6d2a10_add_demo_datasets_and_theme.py"
    )
    spec = spec_from_file_location("task_one_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _run_migration(connection, migration, direction: str) -> None:
    migration_context = MigrationContext.configure(connection)
    with Operations.context(migration_context):
        getattr(migration, direction)()


def test_financial_foundation_metadata_contains_required_contracts() -> None:
    demo_datasets = Base.metadata.tables["demo_datasets"]

    assert {
        "id",
        "user_id",
        "version",
        "status",
        "manifest",
        "installed_at",
        "removed_at",
        "created_at",
        "updated_at",
    } <= set(demo_datasets.columns.keys())
    assert demo_datasets.c.user_id.nullable is False
    assert demo_datasets.c.status.default.arg == "installing"
    assert demo_datasets.c.manifest.default.is_callable
    assert demo_datasets.c.manifest.default.arg(None) == {}
    assert demo_datasets.c.installed_at.nullable is True
    assert demo_datasets.c.removed_at.nullable is True
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_demo_datasets_id_user_id"
        and tuple(constraint.columns.keys()) == ("id", "user_id")
        for constraint in demo_datasets.constraints
    )

    users = Base.metadata.tables["users"]
    assert users.c.theme_preference.nullable is False
    assert users.c.theme_preference.default.arg == "system"
    assert users.c.theme_preference.server_default.arg == "system"

    for table_name in RESOURCE_TABLES:
        table = Base.metadata.tables[table_name]
        assert table.c.demo_dataset_id.nullable is True
        assert f"ix_{table_name}_demo_dataset_id" in {index.name for index in table.indexes}

        constraints = {constraint.name: constraint for constraint in table.foreign_key_constraints}
        simple_constraint = constraints[f"fk_{table_name}_demo_dataset"]
        assert tuple(simple_constraint.column_keys) == ("demo_dataset_id",)
        assert tuple(element.target_fullname for element in simple_constraint.elements) == (
            "demo_datasets.id",
        )
        assert simple_constraint.elements[0].ondelete == "SET NULL"

        ownership_constraint = constraints[f"fk_{table_name}_demo_dataset_user"]
        assert tuple(ownership_constraint.column_keys) == ("demo_dataset_id", "user_id")
        assert tuple(element.target_fullname for element in ownership_constraint.elements) == (
            "demo_datasets.id",
            "demo_datasets.user_id",
        )

    categories = Base.metadata.tables["categories"]
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_categories_id_user_id"
        and tuple(constraint.columns.keys()) == ("id", "user_id")
        for constraint in categories.constraints
    )
    category_constraints = {
        constraint.name: constraint for constraint in categories.foreign_key_constraints
    }
    parent_constraint = category_constraints["fk_categories_parent_user"]
    assert tuple(parent_constraint.column_keys) == ("parent_id", "user_id")
    assert tuple(element.target_fullname for element in parent_constraint.elements) == (
        "categories.id",
        "categories.user_id",
    )

    for table_name in CATEGORY_OWNERSHIP_TABLES:
        constraints = {
            constraint.name: constraint
            for constraint in Base.metadata.tables[table_name].foreign_key_constraints
        }
        category_constraint = constraints[f"fk_{table_name}_category_user"]
        assert tuple(category_constraint.column_keys) == ("category_id", "user_id")
        assert tuple(element.target_fullname for element in category_constraint.elements) == (
            "categories.id",
            "categories.user_id",
        )


def test_alembic_migration_round_trips_sqlite_schema_and_dataset_ownership(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'financial-foundation.db').as_posix()}"
    engine = create_engine(database_url)
    event.listen(
        engine,
        "connect",
        lambda dbapi_connection, _: dbapi_connection.execute("PRAGMA foreign_keys=ON"),
    )
    migration = _task_one_migration()

    try:
        with engine.begin() as connection:
            metadata = MetaData()
            Table("users", metadata, Column("id", Integer, primary_key=True))
            for table_name in (*RESOURCE_TABLES, "installment_plans"):
                columns = [
                    Column("id", Integer, primary_key=True),
                    Column("user_id", Integer, nullable=False),
                ]
                if table_name == "categories":
                    columns.extend(
                        [
                            Column("parent_id", Integer, nullable=True),
                            ForeignKeyConstraint(
                                ["parent_id"], ["categories.id"], ondelete="SET NULL"
                            ),
                        ]
                    )
                elif table_name in CATEGORY_OWNERSHIP_TABLES:
                    columns.extend(
                        [
                            Column("category_id", Integer, nullable=True),
                            ForeignKeyConstraint(
                                ["category_id"],
                                ["categories.id"],
                                ondelete="SET NULL",
                            ),
                        ]
                    )
                Table(
                    table_name,
                    metadata,
                    *columns,
                )
            metadata.create_all(connection)

            _run_migration(connection, migration, "upgrade")
            inspector = inspect(connection)

            assert "demo_datasets" in inspector.get_table_names()
            assert {
                "id",
                "user_id",
                "version",
                "status",
                "manifest",
                "installed_at",
                "removed_at",
                "created_at",
                "updated_at",
            } <= {column["name"] for column in inspector.get_columns("demo_datasets")}

            theme_column = next(
                column
                for column in inspector.get_columns("users")
                if column["name"] == "theme_preference"
            )
            assert theme_column["nullable"] is False
            assert str(theme_column["default"]).strip("'") == "system"

            active_index = next(
                index
                for index in inspector.get_indexes("demo_datasets")
                if index["name"] == "uq_demo_datasets_active_user_version"
            )
            assert bool(active_index["unique"]) is True
            assert str(active_index["dialect_options"]["sqlite_where"]) == "status = 'active'"

            dataset_table_sql = connection.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'demo_datasets'"
                )
            ).scalar_one()
            assert "CONSTRAINT uq_demo_datasets_id_user_id UNIQUE (id, user_id)" in dataset_table_sql

            category_table_sql = connection.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'categories'"
                )
            ).scalar_one()
            assert "CONSTRAINT uq_categories_id_user_id UNIQUE (id, user_id)" in category_table_sql
            assert "CONSTRAINT fk_categories_parent_user " in category_table_sql
            assert "FOREIGN KEY(parent_id, user_id) REFERENCES categories (id, user_id)" in category_table_sql
            assert "FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL" in category_table_sql

            for table_name in RESOURCE_TABLES:
                assert "demo_dataset_id" in {
                    column["name"] for column in inspector.get_columns(table_name)
                }
                assert f"ix_{table_name}_demo_dataset_id" in {
                    index["name"] for index in inspector.get_indexes(table_name)
                }

                table_sql = connection.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type = 'table' AND name = :table_name"
                    ),
                    {"table_name": table_name},
                ).scalar_one()
                assert f"CONSTRAINT fk_{table_name}_demo_dataset " in table_sql
                assert "FOREIGN KEY(demo_dataset_id) REFERENCES demo_datasets (id) ON DELETE SET NULL" in table_sql
                assert f"CONSTRAINT fk_{table_name}_demo_dataset_user " in table_sql
                assert "FOREIGN KEY(demo_dataset_id, user_id) REFERENCES demo_datasets (id, user_id)" in table_sql

            for table_name in CATEGORY_OWNERSHIP_TABLES:
                table_sql = connection.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type = 'table' AND name = :table_name"
                    ),
                    {"table_name": table_name},
                ).scalar_one()
                assert f"CONSTRAINT fk_{table_name}_category_user " in table_sql
                assert "FOREIGN KEY(category_id, user_id) REFERENCES categories (id, user_id)" in table_sql
                assert "FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL" in table_sql

            connection.execute(text("INSERT INTO users (id) VALUES (1), (2)"))
            connection.execute(
                text(
                    "INSERT INTO demo_datasets (id, user_id, version, status, manifest) "
                    "VALUES (1, 1, 'v1', 'active', '{}')"
                )
            )

            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        "INSERT INTO categories (user_id, demo_dataset_id) "
                        "VALUES (2, 1)"
                    )
                )

            connection.execute(
                text(
                    "INSERT INTO categories (id, user_id, demo_dataset_id) "
                    "VALUES (2, 1, 1)"
                )
            )
            connection.execute(
                text("INSERT INTO categories (id, user_id) VALUES (3, 2)")
            )
            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        "INSERT INTO transactions (id, user_id, category_id) "
                        "VALUES (1, 2, 2)"
                    )
                )
            connection.execute(text("DELETE FROM demo_datasets WHERE id = 1"))
            assert connection.execute(
                text("SELECT demo_dataset_id FROM categories WHERE id = 2")
            ).scalar_one() is None

            _run_migration(connection, migration, "downgrade")

            inspector = inspect(connection)
            assert "demo_datasets" not in inspector.get_table_names()
            assert "theme_preference" not in {
                column["name"] for column in inspector.get_columns("users")
            }
            for table_name in RESOURCE_TABLES:
                assert "demo_dataset_id" not in {
                    column["name"] for column in inspector.get_columns(table_name)
                }

            category_table_sql = connection.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'categories'"
                )
            ).scalar_one()
            assert "uq_categories_id_user_id" not in category_table_sql
            assert "fk_categories_parent_user" not in category_table_sql
            assert "FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL" in category_table_sql

            for table_name in CATEGORY_OWNERSHIP_TABLES:
                table_sql = connection.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type = 'table' AND name = :table_name"
                    ),
                    {"table_name": table_name},
                ).scalar_one()
                assert f"fk_{table_name}_category_user" not in table_sql
                assert "FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE SET NULL" in table_sql
    finally:
        engine.dispose()

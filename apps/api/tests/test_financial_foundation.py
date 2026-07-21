import app.models  # noqa: F401

from app.core.database import Base


def test_financial_foundation_metadata_contains_dataset_ownership_and_theme() -> None:
    expected_columns = {
        "demo_datasets": {"id", "user_id", "version", "status", "manifest"},
        "users": {"theme_preference"},
        "financial_accounts": {"demo_dataset_id"},
        "categories": {"demo_dataset_id"},
        "credit_cards": {"demo_dataset_id"},
        "billing_statements": {"demo_dataset_id"},
        "transactions": {"demo_dataset_id"},
        "recurring_rules": {"demo_dataset_id"},
    }

    missing = {}
    for table_name, columns in expected_columns.items():
        table = Base.metadata.tables.get(table_name)
        absent_columns = sorted(
            columns if table is None else columns - set(table.columns.keys())
        )
        if absent_columns:
            missing[table_name] = absent_columns

    assert missing == {}

"""
Tests for verify-restored-database.py verifier.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add scripts to path (project root/scripts)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))

from verify_restored_database import (
    parse_args,
    validate_database_url,
    check_migration_head,
    check_tables,
    check_row_counts,
    check_foreign_key_orphans,
    main,
)


class TestValidateDatabaseUrl:
    """Test database URL validation."""

    def test_production_url_rejected(self):
        """Production URLs should be rejected."""
        urls = [
            "postgresql://user:pass@prod-db.nexo.example/db",
            "postgresql://user:pass@production.nexo-finance.com/db",
            "postgresql://user:pass@nexo-production.amazonaws.com/db",
        ]
        for url in urls:
            hostname, is_prod = validate_database_url(url)
            assert is_prod is True, f"Should reject {url}"

    def test_staging_url_accepted(self):
        """Staging/restored URLs should be accepted."""
        urls = [
            "postgresql://user:pass@staging-db.internal/db",
            "postgresql://user:pass@restored-db.staging/db",
            "postgresql://user:pass@localhost:5432/db",
            "postgresql://user:pass@127.0.0.1:5432/db",
            "postgresql://user:pass@db-staging.internal/db",
        ]
        for url in urls:
            hostname, is_prod = validate_database_url(url)
            assert is_prod is False, f"Should accept {url}"

    def test_parse_hostname(self):
        """Hostname should be extracted correctly."""
        hostname, _ = validate_database_url(
            "postgresql://user:pass@my-host.internal:5432/db"
        )
        assert hostname == "my-host.internal"


class TestCheckMigrationHead:
    """Test migration head checking."""

    @patch("verify_restored_database.subprocess.run")
    def test_single_head_ok(self, mock_run):
        """Single head should pass."""
        mock_run.return_value = Mock(
            stdout="c91d4e7a2f10 (head)\n",
            stderr="",
            returncode=0,
        )
        mock_cursor = Mock()
        head, ok = check_migration_head(mock_cursor)
        assert ok is True
        assert head == "c91d4e7a2f10"

    @patch("verify_restored_database.subprocess.run")
    def test_no_head_fails(self, mock_run):
        """No head should fail."""
        mock_run.return_value = Mock(
            stdout="",
            stderr="",
            returncode=0,
        )
        mock_cursor = Mock()
        head, ok = check_migration_head(mock_cursor)
        assert ok is False
        assert "No migration head" in head

    @patch("verify_restored_database.subprocess.run")
    def test_multiple_heads_fails(self, mock_run):
        """Multiple heads should fail."""
        mock_run.return_value = Mock(
            stdout="c91d4e7a2f10 (head)\nabc123def456 (head)\n",
            stderr="",
            returncode=0,
        )
        mock_cursor = Mock()
        head, ok = check_migration_head(mock_cursor)
        assert ok is False
        assert "Multiple migration heads" in head


class TestCheckTables:
    """Test table existence checking."""

    def test_all_tables_present(self):
        """All required tables present should pass."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"table_name": t} for t in [
                "users", "accounts", "categories", "transactions",
                "cards", "account_action_tokens", "mfa_methods",
                "mfa_recovery_codes", "mfa_challenges",
            ]
        ]
        missing, ok = check_tables(mock_cursor)
        assert missing == 0
        assert ok is True

    def test_missing_tables(self):
        """Missing tables should fail."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"table_name": t} for t in ["users", "accounts"]
        ]
        missing, ok = check_tables(mock_cursor)
        assert missing == 7  # 9 required - 2 present
        assert ok is False


class TestCheckRowCounts:
    """Test row count queries."""

    def test_counts_returned(self):
        """Counts should be returned for each table."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {"cnt": 10}, {"cnt": 5}, {"cnt": 20},
            {"cnt": 100}, {"cnt": 3}, {"cnt": 2},
            {"cnt": 1}, {"cnt": 1}, {"cnt": 0},
        ]
        counts = check_row_counts(mock_cursor)
        assert len(counts) == 9
        assert counts["users"] == 10
        assert counts["transactions"] == 100


class TestCheckForeignKeyOrphans:
    """Test foreign key orphan checking."""

    def test_no_orphans(self):
        """No orphans should return zero counts."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"cnt": 0}
        orphans = check_foreign_key_orphans(mock_cursor)
        assert all(v == 0 for v in orphans.values())
        assert len(orphans) == 9  # Number of FK checks

    def test_orphans_found(self):
        """Orphans should be reported."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {"cnt": 0}, {"cnt": 3}, {"cnt": 0},
            {"cnt": 0}, {"cnt": 0}, {"cnt": 0},
            {"cnt": 0}, {"cnt": 0}, {"cnt": 0},
        ]
        orphans = check_foreign_key_orphans(mock_cursor)
        assert orphans["mfa_methods.user_id -> users.id"] == 3


class TestMain:
    """Test main entry point."""

    @patch("verify_restored_database.psycopg2.connect")
    @patch("verify_restored_database.validate_database_url")
    @patch("verify_restored_database.check_migration_head")
    @patch("verify_restored_database.check_tables")
    @patch("verify_restored_database.check_row_counts")
    @patch("verify_restored_database.check_foreign_key_orphans")
    def test_main_success(
        self,
        mock_orphans,
        mock_counts,
        mock_tables,
        mock_head,
        mock_validate,
        mock_connect,
    ):
        """Successful verification should return 0."""
        # Setup mocks
        mock_validate.return_value = ("staging-host", False)
        mock_head.return_value = ("c91d4e7a2f10", True)
        mock_tables.return_value = (0, True)
        mock_counts.return_value = {t: 10 for t in [
            "users", "accounts", "categories", "transactions",
            "cards", "account_action_tokens", "mfa_methods",
            "mfa_recovery_codes", "mfa_challenges",
        ]}
        mock_orphans.return_value = {k: 0 for k in [
            "account_action_tokens.user_id -> users.id",
            "mfa_methods.user_id -> users.id",
            "mfa_recovery_codes.method_id -> mfa_methods.id",
            "mfa_challenges.user_id -> users.id",
            "user_sessions.user_id -> users.id",
            "accounts.user_id -> users.id",
            "transactions.account_id -> accounts.id",
            "categories.user_id -> users.id",
            "cards.user_id -> users.id",
        ]}

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(sys, "argv", [
            "verify-restored-database.py",
            "--database-url",
            "postgresql://user:pass@staging-host/db"
        ]):
            result = main()

        assert result == 0
        mock_conn.rollback.assert_called_once()

    @patch("verify_restored_database.validate_database_url")
    def test_main_rejects_production(self, mock_validate):
        """Production URL should be rejected."""
        mock_validate.return_value = ("prod.nexo.example", True)

        with patch.object(sys, "argv", [
            "verify-restored-database.py",
            "--database-url",
            "postgresql://user:pass@prod.nexo.example/db"
        ]):
            result = main()

        assert result == 1

    @patch("verify_restored_database.psycopg2.connect")
    @patch("verify_restored_database.validate_database_url")
    def test_main_connection_error(self, mock_validate, mock_connect):
        """Connection error should return 1."""
        mock_validate.return_value = ("staging-host", False)
        mock_connect.side_effect = Exception("Connection failed")

        with patch.object(sys, "argv", [
            "verify-restored-database.py",
            "--database-url",
            "postgresql://user:pass@staging-host/db"
        ]):
            result = main()

        assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
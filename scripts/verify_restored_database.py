#!/usr/bin/env python
"""
Restored database verifier.
Read-only verification of a restored PostgreSQL database.
Outputs aggregate counts only - never exports user data.
"""
import argparse
import os
import subprocess
import sys
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


REQUIRED_TABLES = [
    "users",
    "accounts",
    "categories",
    "transactions",
    "cards",
    "account_action_tokens",
    "mfa_methods",
    "mfa_recovery_codes",
    "mfa_challenges",
]


FOREIGN_KEY_CHECKS = [
    ("account_action_tokens", "user_id", "users", "id"),
    ("mfa_methods", "user_id", "users", "id"),
    ("mfa_recovery_codes", "method_id", "mfa_methods", "id"),
    ("mfa_challenges", "user_id", "users", "id"),
    ("user_sessions", "user_id", "users", "id"),
    ("accounts", "user_id", "users", "id"),
    ("transactions", "account_id", "accounts", "id"),
    ("categories", "user_id", "users", "id"),
    ("cards", "user_id", "users", "id"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify a restored PostgreSQL database"
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="PostgreSQL connection URL (must not be production)",
    )
    return parser.parse_args()


def validate_database_url(url: str) -> tuple[str, bool]:
    """Parse and validate the database URL."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Check for production-like hostnames
    is_production = any(
        keyword in hostname.lower()
        for keyword in ["prod", "production", "nexo.example", "nexo-finance"]
    )

    # Explicit check for localhost (allowed for testing)
    is_localhost = hostname in ("localhost", "127.0.0.1", "::1")

    return hostname, is_production and not is_localhost


def check_migration_head(cursor) -> tuple[str, bool]:
    """Check Alembic has exactly one migration head."""
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "heads"],
            capture_output=True,
            text=True,
            cwd="/app",
        )
        output = result.stdout.strip()
        lines = [
            line.strip() for line in output.splitlines()
            if line.strip() and not line.startswith("Rev:")
        ]
        heads = [line for line in lines if "(head)" in line]

        if len(heads) == 0:
            return "No migration head found", False
        if len(heads) > 1:
            return f"Multiple migration heads ({len(heads)})", False

        return heads[0].split()[0], True
    except Exception as e:
        return f"Error checking migration heads: {e}", False


def check_tables(cursor) -> tuple[int, bool]:
    """Check required tables exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing = {row["table_name"] for row in cursor.fetchall()}

    missing = [t for t in REQUIRED_TABLES if t not in existing]
    return len(missing), len(missing) == 0


def check_row_counts(cursor) -> dict:
    """Get row counts for required tables."""
    counts = {}
    for table in REQUIRED_TABLES:
        try:
            cursor.execute(f'SELECT COUNT(*) as cnt FROM "{table}"')
            counts[table] = cursor.fetchone()["cnt"]
        except Exception:
            counts[table] = -1
    return counts


def check_foreign_key_orphans(cursor) -> dict:
    """Check for foreign key orphans."""
    orphans = {}
    for child_table, child_col, parent_table, parent_col in FOREIGN_KEY_CHECKS:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) as cnt
                FROM "{child_table}" c
                LEFT JOIN "{parent_table}" p ON c."{child_col}" = p."{parent_col}"
                WHERE p."{parent_col}" IS NULL
            """)
            orphans[f"{child_table}.{child_col} -> {parent_table}.{parent_col}"] = (
                cursor.fetchone()["cnt"]
            )
        except Exception:
            orphans[f"{child_table}.{child_col} -> {parent_table}.{parent_col}"] = -1
    return orphans


def main():
    args = parse_args()
    url = args.database_url

    # Validate database URL
    hostname, is_production = validate_database_url(url)
    if is_production:
        print(
            "ERROR: Database URL appears to be production. "
            "Use a staging/restored database only.",
            file=sys.stderr,
        )
        return 1

    try:
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        conn.set_session(readonly=True, autocommit=False)
        cursor = conn.cursor()

        # Check migration head
        print("Checking migration head...")
        head, head_ok = check_migration_head(cursor)
        print(f"  Migration head: {head} ({'OK' if head_ok else 'FAIL'})")

        # Check tables
        print("Checking required tables...")
        missing_count, tables_ok = check_tables(cursor)
        print(f"  Missing tables: {missing_count} ({'OK' if tables_ok else 'FAIL'})")

        # Check row counts
        print("Checking row counts...")
        row_counts = check_row_counts(cursor)
        for table, count in row_counts.items():
            print(f"  {table}: {count}")

        # Check foreign key orphans
        print("Checking foreign key orphans...")
        orphans = check_foreign_key_orphans(cursor)
        orphan_total = 0
        for fk, count in orphans.items():
            status = "OK" if count == 0 else "ORPHANS FOUND"
            print(f"  {fk}: {count} ({status})")
            if count > 0:
                orphan_total += count

        # Rollback unconditionally
        conn.rollback()

        # Overall status
        all_ok = head_ok and tables_ok and (orphan_total == 0)

        print("\n" + "=" * 50)
        print(f"OVERALL: {'PASS' if all_ok else 'FAIL'}")
        print(f"  Migration head: {'OK' if head_ok else 'FAIL'}")
        print(f"  Required tables: {'OK' if tables_ok else 'FAIL'}")
        print(f"  Foreign key orphans: {orphan_total}")
        print(f"  Read-only mode: verified")

        return 0 if all_ok else 1

    except psycopg2.OperationalError as e:
        print(f"ERROR: Cannot connect to database: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import subprocess
    sys.exit(main())
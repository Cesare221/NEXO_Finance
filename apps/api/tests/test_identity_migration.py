import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models import MfaMethod, MfaRecoveryCode, User
from tests.conftest import TestingSessionLocal

API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def db() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_identity_tables_are_registered() -> None:
    assert "account_action_tokens" in Base.metadata.tables
    assert "mfa_methods" in Base.metadata.tables
    assert "mfa_recovery_codes" in Base.metadata.tables
    assert "mfa_challenges" in Base.metadata.tables


def test_user_defaults_token_version(db: Session) -> None:
    user = User(name="A", email="a@example.com", password_hash="hash")
    db.add(user)
    db.commit()

    assert user.email_verified_at is None
    assert user.token_version == 0


def test_identity_metadata_has_required_lifecycle_contracts() -> None:
    action_tokens = Base.metadata.tables["account_action_tokens"]
    methods = Base.metadata.tables["mfa_methods"]
    recovery_codes = Base.metadata.tables["mfa_recovery_codes"]
    challenges = Base.metadata.tables["mfa_challenges"]

    assert action_tokens.c.token_hash.type.length == 64
    assert action_tokens.c.token_hash.unique is True
    assert action_tokens.c.request_ip_hash.type.length == 64
    assert action_tokens.c.expires_at.type.timezone is True
    assert methods.c.user_id.unique is True
    assert methods.c.activated_at.nullable is True
    assert methods.c.disabled_at.nullable is True
    assert recovery_codes.c.code_hash.type.length == 255
    assert recovery_codes.c.consumed_at.nullable is True
    assert challenges.c.challenge_hash.type.length == 64
    assert challenges.c.challenge_hash.unique is True
    assert challenges.c.attempts.default.arg == 0

    for table, column, target in (
        (action_tokens, "user_id", "users.id"),
        (methods, "user_id", "users.id"),
        (recovery_codes, "method_id", "mfa_methods.id"),
        (challenges, "user_id", "users.id"),
    ):
        foreign_key = next(iter(table.c[column].foreign_keys))
        assert foreign_key.target_fullname == target
        assert foreign_key.ondelete == "CASCADE"


def test_recovery_code_round_trips_argon2_hash(db: Session) -> None:
    user = User(name="Recovery", email="recovery@example.com", password_hash="hash")
    db.add(user)
    db.flush()
    method = MfaMethod(
        user_id=user.id,
        secret_ciphertext="ciphertext",
        key_version="v1",
    )
    db.add(method)
    db.flush()
    recovery_code = "ABCD-EFGH-IJKL"
    code_hash = hash_password(recovery_code)
    assert len(code_hash) > 64
    db.add(MfaRecoveryCode(method_id=method.id, code_hash=code_hash))
    db.commit()

    stored = db.query(MfaRecoveryCode).one()
    assert stored.code_hash == code_hash


@pytest.fixture()
def isolated_postgresql_database() -> Generator[str, None, None]:
    source_url = make_url(settings.database_url)
    if source_url.get_backend_name() != "postgresql":
        pytest.skip("The configured database is not PostgreSQL")

    database_name = f"identity_migration_{uuid.uuid4().hex}"
    isolated_url = source_url.set(database=database_name)
    admin_engine = sa.create_engine(
        source_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        with admin_engine.connect() as connection:
            connection.execute(sa.text(f'CREATE DATABASE "{database_name}"'))
    except (OperationalError, ProgrammingError) as exc:
        pytest.skip(f"Unable to create isolated PostgreSQL database: {exc.orig}")
    finally:
        admin_engine.dispose()

    try:
        yield isolated_url.render_as_string(hide_password=False)
    finally:
        cleanup_engine = sa.create_engine(
            source_url,
            isolation_level="AUTOCOMMIT",
            poolclass=NullPool,
        )
        try:
            with cleanup_engine.connect() as connection:
                connection.execute(
                    sa.text(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                    ),
                    {"database_name": database_name},
                )
                connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        finally:
            cleanup_engine.dispose()


def test_identity_migration_upgrades_and_downgrades_isolated_postgresql(
    isolated_postgresql_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration_config = Config(str(API_ROOT / "alembic.ini"))
    monkeypatch.setattr(settings, "database_url", isolated_postgresql_database)
    command.upgrade(migration_config, "c91d4e7a2f10")

    engine: Engine = sa.create_engine(isolated_postgresql_database, poolclass=NullPool)
    try:
        with engine.begin() as connection:
            connection.execute(
                sa.text(
                    "INSERT INTO users (name, email, password_hash) "
                    "VALUES ('Existing', 'existing@example.com', 'hash')"
                )
            )

        command.upgrade(migration_config, "e3b7a12c9d40")

        inspector = sa.inspect(engine)
        users = {column["name"]: column for column in inspector.get_columns("users")}
        recovery_codes = {
            column["name"]: column
            for column in inspector.get_columns("mfa_recovery_codes")
        }
        assert users["email_verified_at"]["nullable"] is True
        assert users["token_version"]["nullable"] is False
        assert "0" in str(users["token_version"]["default"])
        assert recovery_codes["code_hash"]["type"].length == 255

        with engine.begin() as connection:
            existing_user = connection.execute(
                sa.text(
                    "SELECT email_verified_at, token_version FROM users "
                    "WHERE email = 'existing@example.com'"
                )
            ).one()
            new_token_version = connection.execute(
                sa.text(
                    "INSERT INTO users (name, email, password_hash) "
                    "VALUES ('New', 'new@example.com', 'hash') "
                    "RETURNING token_version"
                )
            ).scalar_one()
        assert existing_user.email_verified_at is not None
        assert existing_user.token_version == 0
        assert new_token_version == 0

        recovery_foreign_keys = inspector.get_foreign_keys("mfa_recovery_codes")
        assert len(recovery_foreign_keys) == 1
        recovery_foreign_key = recovery_foreign_keys[0]
        assert recovery_foreign_key["constrained_columns"] == ["method_id"]
        assert recovery_foreign_key["referred_table"] == "mfa_methods"
        assert recovery_foreign_key["referred_columns"] == ["id"]
        assert recovery_foreign_key["options"] == {"ondelete": "CASCADE"}
        recovery_indexes = inspector.get_indexes("mfa_recovery_codes")
        assert any(
            index["name"] == "ix_mfa_recovery_codes_method_id"
            and index["column_names"] == ["method_id"]
            for index in recovery_indexes
        )
    finally:
        engine.dispose()

    command.downgrade(migration_config, "c91d4e7a2f10")
    downgraded_engine = sa.create_engine(isolated_postgresql_database, poolclass=NullPool)
    try:
        downgraded_inspector = sa.inspect(downgraded_engine)
        assert "mfa_recovery_codes" not in downgraded_inspector.get_table_names()
        assert "email_verified_at" not in {
            column["name"] for column in downgraded_inspector.get_columns("users")
        }
        assert "token_version" not in {
            column["name"] for column in downgraded_inspector.get_columns("users")
        }
    finally:
        downgraded_engine.dispose()

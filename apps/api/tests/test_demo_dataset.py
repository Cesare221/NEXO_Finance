from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.audit_event import AuditEvent
from app.models.billing_statement import BillingStatement
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.demo_dataset import DemoDataset
from app.models.financial_account import FinancialAccount
from app.models.recurring_rule import RecurringRule
from app.models.transaction import Transaction
from app.models.user import User
from app.services import demo_dataset_service
from app.services import financial_service
from tests.conftest import TestingSessionLocal


def _register(client, email: str) -> tuple[dict[str, str], int]:
    response = client.post(
        "/auth/register",
        json={"name": "Demo User", "email": email, "password": "FinSeguro123!"},
    )
    assert response.status_code == 201
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    with TestingSessionLocal() as db:
        user_id = db.query(User.id).filter(User.email == email).scalar()
    return headers, user_id


def _assert_public_state(state: dict) -> None:
    assert set(state) == {"active", "version", "installed_at", "summary"}
    assert set(state["summary"]) == {
        "accounts",
        "cards",
        "categories",
        "transactions",
        "recurring_rules",
    }


def test_get_returns_inactive_public_state(client):
    headers, _ = _register(client, "inactive@example.com")

    response = client.get("/financial/demo-dataset", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "active": False,
        "version": "2026.07.v1",
        "installed_at": None,
        "summary": {
            "accounts": 0,
            "cards": 0,
            "categories": 0,
            "transactions": 0,
            "recurring_rules": 0,
        },
    }


def test_install_creates_exact_complete_dataset(client):
    headers, user_id = _register(client, "complete@example.com")

    response = client.post("/financial/demo-dataset", headers=headers)

    assert response.status_code == 201
    state = response.json()
    _assert_public_state(state)
    assert state["active"] is True
    assert state["version"] == "2026.07.v1"
    assert state["installed_at"] is not None
    assert state["summary"] == {
        "accounts": 3,
        "cards": 1,
        "categories": 14,
        "transactions": 12,
        "recurring_rules": 1,
    }

    with TestingSessionLocal() as db:
        dataset = db.query(DemoDataset).filter_by(user_id=user_id, status="active").one()
        accounts = db.query(FinancialAccount).filter_by(demo_dataset_id=dataset.id).all()
        assert {account.name: (account.type, Decimal(account.initial_balance)) for account in accounts} == {
            "Conta principal": ("checking", Decimal("6450.80")),
            "Reserva": ("savings", Decimal("12000.00")),
            "Carteira": ("wallet", Decimal("180.00")),
        }
        categories = db.query(Category).filter_by(demo_dataset_id=dataset.id).all()
        assert {category.name for category in categories} == {
            "Renda",
            "Sal\u00e1rio",
            "Moradia",
            "Aluguel",
            "Alimenta\u00e7\u00e3o",
            "Supermercado",
            "Transporte",
            "Combust\u00edvel",
            "Sa\u00fade",
            "Farm\u00e1cia",
            "Lazer",
            "Entretenimento",
            "Assinaturas",
            "Streaming",
        }
        card = db.query(CreditCard).filter_by(demo_dataset_id=dataset.id).one()
        assert card.name == "Cart\u00e3o principal"
        assert Decimal(card.limit_amount) == Decimal("7000.00")
        assert (card.closing_day, card.due_day) == (10, 17)
        assert card.payment_account_id == next(
            account.id for account in accounts if account.name == "Conta principal"
        )
        assert db.query(Transaction).filter_by(demo_dataset_id=dataset.id).count() == 12
        assert db.query(RecurringRule).filter_by(demo_dataset_id=dataset.id).count() == 1
        assert dataset.manifest["summary"] == state["summary"]
        assert "resource_ids" in dataset.manifest


def test_install_uses_relative_dates_and_card_cycle_without_changing_bank_balance(client):
    _, user_id = _register(client, "dates@example.com")
    installed_on = date(2028, 2, 29)

    with TestingSessionLocal() as db:
        state, created = demo_dataset_service.install_demo_dataset(
            db, user_id, installed_on=installed_on
        )
        assert created is True
        assert state["active"] is True

    with TestingSessionLocal() as db:
        dataset = db.query(DemoDataset).filter_by(user_id=user_id, status="active").one()
        transactions = db.query(Transaction).filter_by(demo_dataset_id=dataset.id).all()
        statement = db.query(BillingStatement).filter_by(demo_dataset_id=dataset.id).one()
        card = db.query(CreditCard).filter_by(demo_dataset_id=dataset.id).one()
        account = db.query(FinancialAccount).filter_by(
            demo_dataset_id=dataset.id, name="Conta principal"
        ).one()
        rule = db.query(RecurringRule).filter_by(demo_dataset_id=dataset.id).one()

        assert any(tx.occurred_on.month == installed_on.month for tx in transactions)
        assert any(tx.occurred_on.month != installed_on.month for tx in transactions)
        assert max(tx.occurred_on for tx in transactions) <= installed_on
        assert statement.status == "open"
        card_total = sum(
            Decimal(tx.amount) for tx in transactions if tx.type == "card_purchase"
        )
        assert Decimal(statement.total_amount) == card_total > Decimal("0")
        assert statement.period_start <= installed_on <= statement.period_end
        assert rule.next_occurrence_on > installed_on

        current_balance = Decimal(account.initial_balance)
        for tx in transactions:
            if tx.account_id != account.id:
                continue
            if tx.type == "income":
                current_balance += Decimal(tx.amount)
            elif tx.type == "expense":
                current_balance -= Decimal(tx.amount)
        assert current_balance == financial_service.get_account_balance(
            db, user_id, account.id
        )
        assert Decimal(card.limit_amount) - Decimal(statement.total_amount) == Decimal("6264.20")


def test_second_post_is_stable_and_does_not_duplicate(client):
    headers, user_id = _register(client, "stable@example.com")
    first = client.post("/financial/demo-dataset", headers=headers)

    second = client.post("/financial/demo-dataset", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    with TestingSessionLocal() as db:
        assert db.query(DemoDataset).filter_by(user_id=user_id, status="active").count() == 1
        assert db.query(Transaction).filter_by(user_id=user_id).count() == 12


def test_status_install_and_cleanup_are_isolated_by_user(client):
    headers_a, user_a = _register(client, "a@example.com")
    headers_b, user_b = _register(client, "b@example.com")
    assert client.post("/financial/demo-dataset", headers=headers_a).status_code == 201

    assert client.get("/financial/demo-dataset", headers=headers_b).json()["active"] is False
    assert client.delete("/financial/demo-dataset", headers=headers_b).json()["active"] is False
    assert client.get("/financial/demo-dataset", headers=headers_a).json()["active"] is True

    with TestingSessionLocal() as db:
        assert db.query(DemoDataset).filter_by(user_id=user_a, status="active").count() == 1
        assert db.query(DemoDataset).filter_by(user_id=user_b).count() == 0


def test_builder_exception_rolls_back_every_resource_and_audit(client, monkeypatch):
    _, user_id = _register(client, "rollback@example.com")

    def explode(db, owner_id, dataset_id, installed_on):
        db.add(
            FinancialAccount(
                user_id=owner_id,
                demo_dataset_id=dataset_id,
                name="Partial",
                type="checking",
                initial_balance=Decimal("1.00"),
            )
        )
        db.flush()
        raise RuntimeError("forced builder failure")

    monkeypatch.setattr(demo_dataset_service, "_build_resources", explode)
    with TestingSessionLocal() as db:
        with pytest.raises(RuntimeError, match="forced builder failure"):
            demo_dataset_service.install_demo_dataset(db, user_id)

    with TestingSessionLocal() as db:
        assert db.query(DemoDataset).filter_by(user_id=user_id).count() == 0
        assert db.query(FinancialAccount).filter_by(user_id=user_id).count() == 0
        assert db.query(AuditEvent).filter_by(user_id=user_id).count() == 0


def test_cleanup_deletes_only_demo_resources_and_is_repeatable(client):
    headers, user_id = _register(client, "cleanup@example.com")
    with TestingSessionLocal() as db:
        real_account = FinancialAccount(
            user_id=user_id,
            name="Real account",
            type="checking",
            initial_balance=Decimal("50.00"),
        )
        real_category = Category(user_id=user_id, name="Real category")
        db.add_all([real_account, real_category])
        db.flush()
        db.add(
            Transaction(
                user_id=user_id,
                account_id=real_account.id,
                category_id=real_category.id,
                type="expense",
                amount=Decimal("10.00"),
                description="Real expense",
                occurred_on=date.today(),
                origin="manual",
            )
        )
        db.commit()

    assert client.post("/financial/demo-dataset", headers=headers).status_code == 201
    first = client.delete("/financial/demo-dataset", headers=headers)
    second = client.delete("/financial/demo-dataset", headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {
        "active": False,
        "version": "2026.07.v1",
        "installed_at": None,
        "summary": {
            "accounts": 0,
            "cards": 0,
            "categories": 0,
            "transactions": 0,
            "recurring_rules": 0,
        },
    }
    with TestingSessionLocal() as db:
        assert db.query(FinancialAccount).filter_by(user_id=user_id).count() == 1
        assert db.query(Category).filter_by(user_id=user_id).count() == 1
        assert db.query(Transaction).filter_by(user_id=user_id).count() == 1
        removed = db.query(DemoDataset).filter_by(user_id=user_id, status="removed").one()
        assert removed.manifest == {}
        assert removed.removed_at is not None


def test_cleanup_preserves_and_detaches_adopted_demo_graph(client):
    headers, user_id = _register(client, "adopted@example.com")
    assert client.post("/financial/demo-dataset", headers=headers).status_code == 201

    with TestingSessionLocal() as db:
        dataset = db.query(DemoDataset).filter_by(user_id=user_id, status="active").one()
        account = db.query(FinancialAccount).filter_by(
            demo_dataset_id=dataset.id, name="Conta principal"
        ).one()
        category = db.query(Category).filter_by(
            demo_dataset_id=dataset.id, name="Supermercado"
        ).one()
        card = db.query(CreditCard).filter_by(demo_dataset_id=dataset.id).one()
        statement = db.query(BillingStatement).filter_by(demo_dataset_id=dataset.id).one()
        adopted_ids = (account.id, category.id, card.id, statement.id)
        db.add(
            Transaction(
                user_id=user_id,
                account_id=account.id,
                category_id=category.id,
                credit_card_id=card.id,
                statement_id=statement.id,
                type="card_purchase",
                amount=Decimal("25.00"),
                description="User adopted purchase",
                occurred_on=date.today(),
                origin="manual",
            )
        )
        db.commit()

    assert client.delete("/financial/demo-dataset", headers=headers).status_code == 200

    with TestingSessionLocal() as db:
        account = db.get(FinancialAccount, adopted_ids[0])
        category = db.get(Category, adopted_ids[1])
        card = db.get(CreditCard, adopted_ids[2])
        statement = db.get(BillingStatement, adopted_ids[3])
        assert all(resource is not None for resource in (account, category, card, statement))
        assert all(
            resource.demo_dataset_id is None
            for resource in (account, category, card, statement)
        )
        real_tx = db.query(Transaction).filter_by(description="User adopted purchase").one()
        assert real_tx.demo_dataset_id is None


def test_install_and_cleanup_audits_are_sanitized(client):
    headers, user_id = _register(client, "audit@example.com")
    assert client.post("/financial/demo-dataset", headers=headers).status_code == 201
    assert client.delete("/financial/demo-dataset", headers=headers).status_code == 200

    with TestingSessionLocal() as db:
        events = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.user_id == user_id,
                AuditEvent.event_type.in_(
                    ("demo_dataset.installed", "demo_dataset.cleaned")
                ),
            )
            .order_by(AuditEvent.id)
            .all()
        )
        assert [event.event_type for event in events] == [
            "demo_dataset.installed",
            "demo_dataset.cleaned",
        ]
        serialized = repr([event.payload for event in events]).lower()
        for forbidden in (
            "amount",
            "balance",
            "description",
            "manifest",
            "resource_id",
            "account_id",
            "category_id",
            "card_id",
            "transaction_id",
        ):
            assert forbidden not in serialized
        assert events[0].payload == {
            "version": "2026.07.v1",
            "counts": {
                "accounts": 3,
                "cards": 1,
                "categories": 14,
                "transactions": 12,
                "recurring_rules": 1,
            },
        }
        assert set(events[1].payload) == {"removed", "preserved"}

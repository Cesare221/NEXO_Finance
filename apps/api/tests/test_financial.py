from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.action_proposal import ActionProposal
from app.models.audit_event import AuditEvent
from app.models.transaction import Transaction
from app.models.user import User
from app.services import financial_service
from tests.conftest import TestingSessionLocal


def _register_and_get_token(client, email="test@example.com", name="Test User") -> str:
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "FinSeguro123!"},
    )
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": "FinSeguro123!"},
    )
    return login_resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_account(client, token: str, **kwargs) -> dict:
    defaults = {"name": "My Account", "type": "checking", "initial_balance": "0.00"}
    defaults.update(kwargs)
    resp = client.post(
        "/financial/accounts",
        json=defaults,
        headers=_auth_header(token),
    )
    return resp.json()


def _create_category(client, token: str, **kwargs) -> dict:
    defaults = {"name": "General"}
    defaults.update(kwargs)
    resp = client.post(
        "/financial/categories",
        json=defaults,
        headers=_auth_header(token),
    )
    return resp.json()


def _create_credit_card(client, token: str, payment_account_id: int, **kwargs) -> dict:
    defaults = {
        "name": "Main Card",
        "limit_amount": "500.00",
        "closing_day": 10,
        "due_day": 17,
        "payment_account_id": payment_account_id,
    }
    defaults.update(kwargs)
    resp = client.post(
        "/financial/credit-cards",
        json=defaults,
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    return resp.json()


class TestAccounts:
    def test_create_account(self, client):
        token = _register_and_get_token(client)
        data = _create_account(client, token, name="Checking", type="checking")
        assert data["name"] == "Checking"
        assert data["type"] == "checking"
        assert Decimal(data["initial_balance"]) == Decimal("0.00")
        assert data["is_archived"] is False

    def test_list_accounts(self, client):
        token = _register_and_get_token(client)
        _create_account(client, token, name="Wallet")
        _create_account(client, token, name="Savings", type="savings", initial_balance="500.00")
        resp = client.get(
            "/financial/accounts", headers=_auth_header(token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_update_account(self, client):
        token = _register_and_get_token(client)
        account = _create_account(client, token, name="Old Name")
        resp = client.put(
            f"/financial/accounts/{account['id']}",
            json={"name": "New Name", "initial_balance": "100.50"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert Decimal(data["initial_balance"]) == Decimal("100.50")

    def test_archive_account(self, client):
        token = _register_and_get_token(client)
        account = _create_account(client, token)
        resp = client.delete(
            f"/financial/accounts/{account['id']}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_archived"] is True

    def test_account_not_found(self, client):
        token = _register_and_get_token(client)
        resp = client.put(
            "/financial/accounts/99999",
            json={"name": "Nope"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_account_not_found_delete(self, client):
        token = _register_and_get_token(client)
        resp = client.delete(
            "/financial/accounts/99999",
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_duplicate_account_name(self, client):
        token = _register_and_get_token(client)
        _create_account(client, token, name="Dupe")
        resp = client.post(
            "/financial/accounts",
            json={"name": "Dupe", "type": "checking"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 409

    def test_invalid_account_type(self, client):
        token = _register_and_get_token(client)
        resp = client.post(
            "/financial/accounts",
            json={"name": "Bad", "type": "invalid_type"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 422

    def test_balance_precision(self, client):
        token = _register_and_get_token(client)
        data = _create_account(
            client, token, name="Precise", initial_balance="12345.67"
        )
        assert Decimal(data["initial_balance"]) == Decimal("12345.67")

    def test_user_isolation_accounts(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        _create_account(client, token_a, name="A Account")
        _create_account(client, token_b, name="B Account")

        resp_a = client.get("/financial/accounts", headers=_auth_header(token_a))
        resp_b = client.get("/financial/accounts", headers=_auth_header(token_b))
        assert len(resp_a.json()) == 1
        assert len(resp_b.json()) == 1
        assert resp_a.json()[0]["name"] == "A Account"
        assert resp_b.json()[0]["name"] == "B Account"

    def test_user_b_cannot_update_user_a_account(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        account_a = _create_account(client, token_a, name="A Only")
        resp = client.put(
            f"/financial/accounts/{account_a['id']}",
            json={"name": "Hijacked"},
            headers=_auth_header(token_b),
        )
        assert resp.status_code == 404


class TestCategories:
    def test_create_category(self, client):
        token = _register_and_get_token(client)
        resp = client.post(
            "/financial/categories",
            json={"name": "Food", "color": "#FF0000"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Food"
        assert data["color"] == "#FF0000"
        assert data["parent_id"] is None
        assert data["is_archived"] is False

    def test_create_category_with_parent(self, client):
        token = _register_and_get_token(client)
        parent = client.post(
            "/financial/categories",
            json={"name": "Groceries"},
            headers=_auth_header(token),
        ).json()
        child = client.post(
            "/financial/categories",
            json={"name": "Fruits", "parent_id": parent["id"]},
            headers=_auth_header(token),
        )
        assert child.status_code == 201
        assert child.json()["parent_id"] == parent["id"]

    def test_category_tree(self, client):
        token = _register_and_get_token(client)
        food = client.post(
            "/financial/categories",
            json={"name": "Food"},
            headers=_auth_header(token),
        ).json()
        client.post(
            "/financial/categories",
            json={"name": "Fruits", "parent_id": food["id"]},
            headers=_auth_header(token),
        )
        client.post(
            "/financial/categories",
            json={"name": "Vegetables", "parent_id": food["id"]},
            headers=_auth_header(token),
        )
        client.post(
            "/financial/categories",
            json={"name": "Transport"},
            headers=_auth_header(token),
        )

        resp = client.get("/financial/categories", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        roots = [c for c in data if c["parent_id"] is None]
        assert len(roots) == 2

        food_node = next(c for c in roots if c["name"] == "Food")
        assert len(food_node["children"]) == 2
        child_names = {c["name"] for c in food_node["children"]}
        assert child_names == {"Fruits", "Vegetables"}

    def test_update_category(self, client):
        token = _register_and_get_token(client)
        cat = client.post(
            "/financial/categories",
            json={"name": "Old"},
            headers=_auth_header(token),
        ).json()
        resp = client.put(
            f"/financial/categories/{cat['id']}",
            json={"name": "Updated", "icon": "shopping-cart"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated"
        assert data["icon"] == "shopping-cart"

    def test_update_category_can_remove_parent(self, client):
        token = _register_and_get_token(client)
        parent = client.post(
            "/financial/categories",
            json={"name": "Parent"},
            headers=_auth_header(token),
        ).json()
        child = client.post(
            "/financial/categories",
            json={"name": "Child", "parent_id": parent["id"]},
            headers=_auth_header(token),
        ).json()

        response = client.put(
            f"/financial/categories/{child['id']}",
            json={"parent_id": None},
            headers=_auth_header(token),
        )

        assert response.status_code == 200
        assert response.json()["parent_id"] is None

    def test_delete_unused_category_permanently_removes_it_and_audits(self, client):
        token = _register_and_get_token(client)
        cat = client.post(
            "/financial/categories",
            json={"name": "Unused"},
            headers=_auth_header(token),
        ).json()
        resp = client.delete(
            f"/financial/categories/{cat['id']}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "action": "deleted",
            "category": {
                **cat,
                "children": [],
            },
        }
        assert client.get("/financial/categories", headers=_auth_header(token)).json() == []

        db = TestingSessionLocal()
        try:
            event = db.query(AuditEvent).filter(AuditEvent.entity_id == cat["id"]).one()
            assert event.event_type == "category.deleted"
            assert event.payload == {"action": "deleted", "category_ids": [cat["id"]]}
            assert "amount" not in str(event.payload).lower()
            assert "description" not in str(event.payload).lower()
        finally:
            db.close()

    @pytest.mark.parametrize(
        ("dependency", "expected_kind"),
        [
            ("transaction", "transactions"),
            ("soft_deleted_transaction", "transactions"),
            ("installment_plan", "installment_plans"),
            ("recurring_rule", "recurring_rules"),
            ("child", "child_categories"),
            ("proposed_proposal", "action_proposals"),
            ("confirmed_proposal", "action_proposals"),
        ],
    )
    def test_category_dependency_archives_historical_tree_and_audits(
        self, client, dependency, expected_kind
    ):
        token = _register_and_get_token(client)
        account = _create_account(client, token)
        category = _create_category(client, token, name=f"{dependency} category")

        if dependency in {"transaction", "soft_deleted_transaction"}:
            transaction = client.post(
                "/financial/transactions",
                json={
                    "type": "expense",
                    "account_id": account["id"],
                    "category_id": category["id"],
                    "amount": "13.50",
                    "description": "Historical purchase",
                    "occurred_on": "2026-01-15",
                },
                headers=_auth_header(token),
            ).json()
            if dependency == "soft_deleted_transaction":
                deleted = client.delete(
                    f"/financial/transactions/{transaction['id']}",
                    headers=_auth_header(token),
                )
                assert deleted.status_code == 200
        elif dependency == "installment_plan":
            response = client.post(
                "/financial/installment-plans",
                json={
                    "type": "expense",
                    "account_id": account["id"],
                    "category_id": category["id"],
                    "amount": "120.00",
                    "installments_count": 2,
                    "description": "Plan description",
                    "first_due_on": "2026-01-15",
                },
                headers=_auth_header(token),
            )
            assert response.status_code == 201
        elif dependency == "recurring_rule":
            response = client.post(
                "/financial/recurring-rules",
                json={
                    "type": "expense",
                    "account_id": account["id"],
                    "category_id": category["id"],
                    "amount": "45.00",
                    "description": "Rule description",
                    "frequency": "monthly",
                    "next_occurrence_on": "2026-02-01",
                },
                headers=_auth_header(token),
            )
            assert response.status_code == 201
        elif dependency == "child":
            child = _create_category(client, token, name="Required child", parent_id=category["id"])
        else:
            db = TestingSessionLocal()
            try:
                user = db.query(User).filter(User.email == "test@example.com").one()
                db.add(
                    ActionProposal(
                        user_id=user.id,
                        action_type="create_transaction",
                        payload={"category_id": category["id"], "amount": "99.99"},
                        human_summary="Pending proposal description",
                        previous_state_snapshot={},
                        status=dependency.removesuffix("_proposal"),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                        idempotency_key="category-delete-proposal",
                    )
                )
                db.commit()
            finally:
                db.close()

        response = client.delete(
            f"/financial/categories/{category['id']}", headers=_auth_header(token)
        )

        assert response.status_code == 200
        assert response.json()["action"] == "archived"
        assert response.json()["category"]["id"] == category["id"]
        assert response.json()["category"]["is_archived"] is True
        assert client.get("/financial/categories", headers=_auth_header(token)).json() == []

        db = TestingSessionLocal()
        try:
            event = db.query(AuditEvent).filter(AuditEvent.entity_id == category["id"]).one()
            assert event.event_type == "category.archived"
            assert event.payload["action"] == "archived"
            assert category["id"] in event.payload["category_ids"]
            assert event.payload[expected_kind] is True
            assert "amount" not in str(event.payload).lower()
            assert "description" not in str(event.payload).lower()
            if dependency == "child":
                assert child["id"] in event.payload["category_ids"]
        finally:
            db.close()

    def test_archived_parent_and_required_descendants_are_omitted_from_active_tree(self, client):
        token = _register_and_get_token(client)
        parent = client.post(
            "/financial/categories",
            json={"name": "Parent"},
            headers=_auth_header(token),
        ).json()
        child = client.post(
            "/financial/categories",
            json={"name": "Child", "parent_id": parent["id"]},
            headers=_auth_header(token),
        ).json()
        client.delete(
            f"/financial/categories/{parent['id']}",
            headers=_auth_header(token),
        )

        resp = client.get("/financial/categories", headers=_auth_header(token))
        assert resp.json() == []

    def test_archived_category_is_rejected_by_every_new_record_path(self, client):
        token = _register_and_get_token(client)
        account = _create_account(client, token)
        category = _create_category(client, token, name="Historical")
        card = _create_credit_card(client, token, account["id"])
        transaction = client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": account["id"],
                "category_id": category["id"],
                "amount": "1.00",
                "occurred_on": "2026-01-15",
            },
            headers=_auth_header(token),
        )
        assert transaction.status_code == 201
        assert client.delete(
            f"/financial/categories/{category['id']}", headers=_auth_header(token)
        ).json()["action"] == "archived"

        requests = [
            (
                "/financial/transactions",
                {
                    "type": "expense", "account_id": account["id"], "category_id": category["id"],
                    "amount": "2.00", "occurred_on": "2026-02-01",
                },
            ),
            (
                f"/financial/credit-cards/{card['id']}/purchases",
                {"category_id": category["id"], "amount": "2.00", "occurred_on": "2026-02-01"},
            ),
            (
                "/financial/installment-plans",
                {
                    "type": "expense", "account_id": account["id"], "category_id": category["id"],
                    "amount": "4.00", "installments_count": 2, "first_due_on": "2026-02-01",
                },
            ),
            (
                "/financial/recurring-rules",
                {
                    "type": "expense", "account_id": account["id"], "category_id": category["id"],
                    "amount": "2.00", "frequency": "monthly", "next_occurrence_on": "2026-02-01",
                },
            ),
        ]
        for path, body in requests:
            response = client.post(path, json=body, headers=_auth_header(token))
            assert response.status_code == 409
            assert "archived" in response.json()["detail"].lower()

    def test_other_users_dependencies_do_not_influence_category_lifecycle(self, client):
        token_a = _register_and_get_token(client, email="a-lifecycle@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b-lifecycle@test.com", name="User B")
        category_a = _create_category(client, token_a, name="A category")
        account_b = _create_account(client, token_b, name="B account")
        category_b = _create_category(client, token_b, name="B category")

        db = TestingSessionLocal()
        try:
            db.execute(text("PRAGMA foreign_keys=ON"))
            user_b = db.query(User).filter(User.email == "b-lifecycle@test.com").one()
            db.add(
                Transaction(
                    user_id=user_b.id,
                    account_id=account_b["id"],
                    category_id=category_a["id"],
                    type="expense",
                    amount="10.00",
                    description="B only",
                    occurred_on=date(2026, 1, 15),
                    origin="manual",
                )
            )
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
        finally:
            db.close()

        valid_b_transaction = client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": account_b["id"],
                "category_id": category_b["id"],
                "amount": "10.00",
                "occurred_on": "2026-01-15",
            },
            headers=_auth_header(token_b),
        )
        assert valid_b_transaction.status_code == 201

        response = client.delete(
            f"/financial/categories/{category_a['id']}", headers=_auth_header(token_a)
        )

        assert response.status_code == 200
        assert response.json()["action"] == "deleted"
        b_transactions = client.get(
            "/financial/transactions", headers=_auth_header(token_b)
        ).json()
        assert [transaction["id"] for transaction in b_transactions] == [
            valid_b_transaction.json()["id"]
        ]

    def test_duplicate_category_name(self, client):
        token = _register_and_get_token(client)
        client.post(
            "/financial/categories",
            json={"name": "Dupe"},
            headers=_auth_header(token),
        )
        resp = client.post(
            "/financial/categories",
            json={"name": "Dupe"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 409

    def test_category_not_found(self, client):
        token = _register_and_get_token(client)
        resp = client.put(
            "/financial/categories/99999",
            json={"name": "Nope"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404

    def test_cannot_set_self_as_parent(self, client):
        token = _register_and_get_token(client)
        cat = client.post(
            "/financial/categories",
            json={"name": "Self"},
            headers=_auth_header(token),
        ).json()
        resp = client.put(
            f"/financial/categories/{cat['id']}",
            json={"parent_id": cat["id"]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        assert "own parent" in resp.json()["detail"]

    def test_cannot_set_child_as_parent(self, client):
        token = _register_and_get_token(client)
        parent = client.post(
            "/financial/categories",
            json={"name": "Parent"},
            headers=_auth_header(token),
        ).json()
        child = client.post(
            "/financial/categories",
            json={"name": "Child", "parent_id": parent["id"]},
            headers=_auth_header(token),
        ).json()
        resp = client.put(
            f"/financial/categories/{parent['id']}",
            json={"parent_id": child["id"]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        assert "child category" in resp.json()["detail"].lower()

    def test_user_isolation_categories(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        client.post(
            "/financial/categories",
            json={"name": "A Cat"},
            headers=_auth_header(token_a),
        )
        client.post(
            "/financial/categories",
            json={"name": "B Cat"},
            headers=_auth_header(token_b),
        )
        resp_a = client.get("/financial/categories", headers=_auth_header(token_a))
        resp_b = client.get("/financial/categories", headers=_auth_header(token_b))
        names_a = [c["name"] for c in resp_a.json()]
        names_b = [c["name"] for c in resp_b.json()]
        assert "A Cat" in names_a
        assert "B Cat" not in names_a
        assert "B Cat" in names_b
        assert "A Cat" not in names_b

    def test_parent_not_found(self, client):
        token = _register_and_get_token(client)
        resp = client.post(
            "/financial/categories",
            json={"name": "Orphan", "parent_id": 99999},
            headers=_auth_header(token),
        )
        assert resp.status_code == 404
        assert "parent" in resp.json()["detail"].lower()

    def test_multi_level_tree(self, client):
        token = _register_and_get_token(client)
        root = client.post(
            "/financial/categories",
            json={"name": "Root"},
            headers=_auth_header(token),
        ).json()
        mid = client.post(
            "/financial/categories",
            json={"name": "Mid", "parent_id": root["id"]},
            headers=_auth_header(token),
        ).json()
        client.post(
            "/financial/categories",
            json={"name": "Leaf", "parent_id": mid["id"]},
            headers=_auth_header(token),
        )

        resp = client.get("/financial/categories", headers=_auth_header(token))
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Root"
        mid_children = data[0]["children"]
        assert len(mid_children) == 1
        assert mid_children[0]["name"] == "Mid"
        leaf_children = mid_children[0]["children"]
        assert len(leaf_children) == 1
        assert leaf_children[0]["name"] == "Leaf"

    def test_unauthenticated_access(self, client):
        resp = client.get("/financial/accounts")
        assert resp.status_code == 401
        resp = client.get("/financial/categories")
        assert resp.status_code == 401
        resp = client.post(
            "/financial/accounts",
            json={"name": "Test", "type": "checking"},
        )
        assert resp.status_code == 401


class TestTransactions:
    def test_create_income_and_expense_updates_account_balance(self, client):
        token = _register_and_get_token(client)
        account = _create_account(
            client, token, name="Checking", initial_balance="100.00"
        )
        category = _create_category(client, token, name="Food")

        income = client.post(
            "/financial/transactions",
            json={
                "type": "income",
                "account_id": account["id"],
                "amount": "250.00",
                "description": "Salary",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        expense = client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": account["id"],
                "category_id": category["id"],
                "amount": "45.50",
                "description": "Groceries",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        )

        assert income.status_code == 201
        assert expense.status_code == 201
        assert Decimal(balance.json()["current_balance"]) == Decimal("304.50")

    def test_list_transactions_with_filters(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        wallet = _create_account(client, token, name="Wallet", type="wallet")

        client.post(
            "/financial/transactions",
            json={
                "type": "income",
                "account_id": checking["id"],
                "amount": "100.00",
                "description": "Freelance",
                "occurred_on": "2026-07-16",
            },
            headers=_auth_header(token),
        )
        client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": checking["id"],
                "amount": "20.00",
                "description": "Coffee",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": wallet["id"],
                "amount": "15.00",
                "description": "Snack",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )

        resp = client.get(
            f"/financial/transactions?type=expense&account_id={checking['id']}",
            headers=_auth_header(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["description"] == "Coffee"

    def test_soft_delete_transaction_removes_it_from_balance(self, client):
        token = _register_and_get_token(client)
        account = _create_account(
            client, token, name="Checking", initial_balance="100.00"
        )
        tx = client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": account["id"],
                "amount": "30.00",
                "description": "Mistake",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        ).json()

        deleted = client.delete(
            f"/financial/transactions/{tx['id']}",
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        )

        assert deleted.status_code == 200
        assert deleted.json()["is_deleted"] is True
        assert Decimal(balance.json()["current_balance"]) == Decimal("100.00")

    def test_user_b_cannot_use_user_a_account_or_category(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        account_a = _create_account(client, token_a, name="A Account")
        category_a = _create_category(client, token_a, name="A Category")

        resp = client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": account_a["id"],
                "category_id": category_a["id"],
                "amount": "10.00",
                "description": "Should fail",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token_b),
        )

        assert resp.status_code == 404
        resp = client.post(
            "/financial/categories",
            json={"name": "Test"},
        )
        assert resp.status_code == 401


class TestTransfers:
    def test_transfer_moves_money_between_accounts_without_changing_net_worth(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(
            client, token, name="Checking", initial_balance="500.00"
        )
        wallet = _create_account(
            client, token, name="Wallet", type="wallet", initial_balance="50.00"
        )

        resp = client.post(
            "/financial/transfers",
            json={
                "from_account_id": checking["id"],
                "to_account_id": wallet["id"],
                "amount": "125.50",
                "description": "ATM cash",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )

        checking_balance = client.get(
            f"/financial/accounts/{checking['id']}/balance",
            headers=_auth_header(token),
        ).json()
        wallet_balance = client.get(
            f"/financial/accounts/{wallet['id']}/balance",
            headers=_auth_header(token),
        ).json()

        assert resp.status_code == 201
        data = resp.json()
        assert data["from_account_id"] == checking["id"]
        assert data["to_account_id"] == wallet["id"]
        assert Decimal(checking_balance["current_balance"]) == Decimal("374.50")
        assert Decimal(wallet_balance["current_balance"]) == Decimal("175.50")
        assert (
            Decimal(checking_balance["current_balance"])
            + Decimal(wallet_balance["current_balance"])
        ) == Decimal("550.00")

    def test_transfer_creates_linked_transactions_that_are_not_income_or_expense(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        wallet = _create_account(client, token, name="Wallet", type="wallet")

        transfer = client.post(
            "/financial/transfers",
            json={
                "from_account_id": checking["id"],
                "to_account_id": wallet["id"],
                "amount": "25.00",
                "description": "Pocket money",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        ).json()

        all_transactions = client.get(
            "/financial/transactions", headers=_auth_header(token)
        ).json()
        income_transactions = client.get(
            "/financial/transactions?type=income", headers=_auth_header(token)
        ).json()
        expense_transactions = client.get(
            "/financial/transactions?type=expense", headers=_auth_header(token)
        ).json()

        assert transfer["out_transaction_id"] is not None
        assert transfer["in_transaction_id"] is not None
        assert {tx["type"] for tx in all_transactions} == {
            "transfer_out",
            "transfer_in",
        }
        assert income_transactions == []
        assert expense_transactions == []

    def test_list_transfers_is_scoped_to_current_user(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        checking_a = _create_account(client, token_a, name="A Checking")
        wallet_a = _create_account(client, token_a, name="A Wallet", type="wallet")
        checking_b = _create_account(client, token_b, name="B Checking")
        wallet_b = _create_account(client, token_b, name="B Wallet", type="wallet")

        client.post(
            "/financial/transfers",
            json={
                "from_account_id": checking_a["id"],
                "to_account_id": wallet_a["id"],
                "amount": "10.00",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token_a),
        )
        client.post(
            "/financial/transfers",
            json={
                "from_account_id": checking_b["id"],
                "to_account_id": wallet_b["id"],
                "amount": "20.00",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token_b),
        )

        resp_a = client.get("/financial/transfers", headers=_auth_header(token_a))
        resp_b = client.get("/financial/transfers", headers=_auth_header(token_b))

        assert len(resp_a.json()) == 1
        assert Decimal(resp_a.json()[0]["amount"]) == Decimal("10.00")
        assert len(resp_b.json()) == 1
        assert Decimal(resp_b.json()[0]["amount"]) == Decimal("20.00")

    def test_user_cannot_transfer_from_another_users_account(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        account_a = _create_account(client, token_a, name="A Account")
        account_b = _create_account(client, token_b, name="B Account")

        resp = client.post(
            "/financial/transfers",
            json={
                "from_account_id": account_a["id"],
                "to_account_id": account_b["id"],
                "amount": "10.00",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token_b),
        )

        assert resp.status_code == 404


class TestCreditCards:
    def test_closing_cycle_includes_purchases_on_or_before_closing_day(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"])

        for occurred_on in ("2026-07-09", "2026-07-10"):
            purchase = client.post(
                f"/financial/credit-cards/{card['id']}/purchases",
                json={"amount": "10.00", "occurred_on": occurred_on},
                headers=_auth_header(token),
            )
            assert purchase.status_code == 201

        statements = client.get(
            "/financial/dashboard", headers=_auth_header(token)
        ).json()["open_statements"]

        assert len(statements) == 1
        assert statements[0]["period_start"] == "2026-06-11"
        assert statements[0]["period_end"] == "2026-07-10"
        assert statements[0]["due_on"] == "2026-07-17"

    def test_closing_cycle_moves_purchase_after_closing_to_next_cycle(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"])

        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={"amount": "10.00", "occurred_on": "2026-07-11"},
            headers=_auth_header(token),
        )
        statement = client.get(
            "/financial/dashboard", headers=_auth_header(token)
        ).json()["open_statements"][0]

        assert purchase.status_code == 201
        assert statement["period_start"] == "2026-07-11"
        assert statement["period_end"] == "2026-08-10"
        assert statement["due_on"] == "2026-08-17"

    def test_statement_cycle_rolls_over_year_boundary(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"])

        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={"amount": "10.00", "occurred_on": "2026-12-31"},
            headers=_auth_header(token),
        )
        statement = client.get(
            "/financial/dashboard", headers=_auth_header(token)
        ).json()["open_statements"][0]

        assert purchase.status_code == 201
        assert statement["period_start"] == "2026-12-11"
        assert statement["period_end"] == "2027-01-10"
        assert statement["due_on"] == "2027-01-17"

    def test_statement_cycle_clamps_short_months_and_moves_due_date(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(
            client, token, checking["id"], closing_day=31, due_day=30
        )

        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={"amount": "10.00", "occurred_on": "2026-02-28"},
            headers=_auth_header(token),
        )
        statement = client.get(
            "/financial/dashboard", headers=_auth_header(token)
        ).json()["open_statements"][0]

        assert purchase.status_code == 201
        assert statement["period_start"] == "2026-02-01"
        assert statement["period_end"] == "2026-02-28"
        assert statement["due_on"] == "2026-03-30"

    def test_duplicate_active_card_rejects_create_with_normalized_name(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        _create_credit_card(client, token, checking["id"], name="Main Card")

        response = client.post(
            "/financial/credit-cards",
            json={
                "name": "  MAIN CARD  ",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 17,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        )

        assert response.status_code == 409

    def test_duplicate_active_card_rejects_rename(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        _create_credit_card(client, token, checking["id"], name="Main Card")
        other = _create_credit_card(client, token, checking["id"], name="Backup")

        response = client.put(
            f"/financial/credit-cards/{other['id']}",
            json={"name": " main card "},
            headers=_auth_header(token),
        )

        assert response.status_code == 409

    def test_duplicate_active_card_allows_unchanged_name_on_update(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"])

        response = client.put(
            f"/financial/credit-cards/{card['id']}",
            json={"name": "Main Card", "due_day": 20},
            headers=_auth_header(token),
        )

        assert response.status_code == 200

    def test_duplicate_active_card_allows_same_name_for_another_user(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        checking_a = _create_account(client, token_a, name="A Checking")
        checking_b = _create_account(client, token_b, name="B Checking")
        _create_credit_card(client, token_a, checking_a["id"], name="Main Card")

        response = client.post(
            "/financial/credit-cards",
            json={
                "name": "main card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 17,
                "payment_account_id": checking_b["id"],
            },
            headers=_auth_header(token_b),
        )

        assert response.status_code == 201

    def test_duplicate_active_card_allows_archived_card_name_reuse(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"], name="Main Card")
        archived = client.delete(
            f"/financial/credit-cards/{card['id']}",
            headers=_auth_header(token),
        )

        replacement = client.post(
            "/financial/credit-cards",
            json={
                "name": "main card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 17,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        )

        assert archived.status_code == 200
        assert replacement.status_code == 201

    def test_duplicate_active_card_allows_archived_rename_but_rejects_reactivation(
        self, client
    ):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        _create_credit_card(client, token, checking["id"], name="Main Card")
        archived_card = _create_credit_card(client, token, checking["id"], name="Old")
        client.delete(
            f"/financial/credit-cards/{archived_card['id']}",
            headers=_auth_header(token),
        )

        renamed = client.put(
            f"/financial/credit-cards/{archived_card['id']}",
            json={"name": " main card "},
            headers=_auth_header(token),
        )
        db = TestingSessionLocal()
        try:
            with pytest.raises(HTTPException) as error:
                financial_service.update_credit_card(
                    db,
                    archived_card["user_id"],
                    archived_card["id"],
                    is_archived=False,
                )
        finally:
            db.close()

        assert renamed.status_code == 200
        assert error.value.status_code == 409

    def test_duplicate_active_card_lock_contract_uses_user_row_for_update(self):
        query = Mock()
        query.filter.return_value = query
        query.with_for_update.return_value = query
        query.first.return_value = object()
        db = Mock()
        db.query.return_value = query

        lock_namespace = getattr(
            financial_service, "_lock_card_name_namespace", None
        )

        assert lock_namespace is not None
        lock_namespace(db, user_id=42)
        db.query.assert_called_once_with(User)
        query.with_for_update.assert_called_once_with()

    def test_duplicate_active_card_locks_namespace_before_create_and_rename_checks(
        self, client, monkeypatch
    ):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        existing = _create_credit_card(client, token, checking["id"], name="Existing")
        events = []
        original_conflict_check = financial_service._has_active_card_name_conflict

        def record_lock(db, user_id):
            events.append(("lock", user_id))

        def record_conflict_check(db, user_id, name, card_id=None):
            events.append(("check", user_id))
            return original_conflict_check(db, user_id, name, card_id)

        monkeypatch.setattr(
            financial_service,
            "_lock_card_name_namespace",
            record_lock,
            raising=False,
        )
        monkeypatch.setattr(
            financial_service,
            "_has_active_card_name_conflict",
            record_conflict_check,
        )

        created = _create_credit_card(client, token, checking["id"], name="Second")
        renamed = client.put(
            f"/financial/credit-cards/{created['id']}",
            json={"name": "Renamed"},
            headers=_auth_header(token),
        )

        assert renamed.status_code == 200
        assert events == [
            ("lock", existing["user_id"]),
            ("check", existing["user_id"]),
            ("lock", existing["user_id"]),
            ("check", existing["user_id"]),
        ]

    def test_statement_cycle_preserves_existing_statement_after_card_edit(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = _create_credit_card(client, token, checking["id"])
        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={"amount": "10.00", "occurred_on": "2026-07-09"},
            headers=_auth_header(token),
        )

        update = client.put(
            f"/financial/credit-cards/{card['id']}",
            json={"closing_day": 20, "due_day": 25},
            headers=_auth_header(token),
        )
        statement = client.get(
            "/financial/dashboard", headers=_auth_header(token)
        ).json()["open_statements"][0]

        assert purchase.status_code == 201
        assert update.status_code == 200
        assert statement["period_start"] == "2026-06-11"
        assert statement["period_end"] == "2026-07-10"
        assert statement["due_on"] == "2026-07-17"

    def test_update_credit_card(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        savings = _create_account(client, token, name="Savings")
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        ).json()

        response = client.put(
            f"/financial/credit-cards/{card['id']}",
            json={
                "name": "Updated Card",
                "limit_amount": "750.00",
                "closing_day": 12,
                "due_day": 22,
                "payment_account_id": savings["id"],
            },
            headers=_auth_header(token),
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Card"
        assert Decimal(response.json()["limit_amount"]) == Decimal("750.00")
        assert response.json()["payment_account_id"] == savings["id"]

    def test_cannot_reduce_card_limit_below_used_amount(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        ).json()
        client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={
                "amount": "200.00",
                "description": "Phone",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )

        response = client.put(
            f"/financial/credit-cards/{card['id']}",
            json={"limit_amount": "100.00"},
            headers=_auth_header(token),
        )

        assert response.status_code == 409
        assert "used limit" in response.json()["detail"].lower()

    def test_archived_card_preserves_history_and_rejects_new_purchases(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(client, token, name="Checking")
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        ).json()

        archived = client.delete(
            f"/financial/credit-cards/{card['id']}",
            headers=_auth_header(token),
        )
        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={
                "amount": "10.00",
                "description": "Blocked purchase",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )

        assert archived.status_code == 200
        assert archived.json()["is_archived"] is True
        assert purchase.status_code == 409

    def test_card_purchase_reduces_available_limit_but_not_bank_balance(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )
        category = _create_category(client, token, name="Food")
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        )
        purchase = client.post(
            f"/financial/credit-cards/{card.json()['id']}/purchases",
            json={
                "amount": "123.45",
                "description": "Groceries on card",
                "category_id": category["id"],
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{checking['id']}/balance",
            headers=_auth_header(token),
        ).json()
        card_after = client.get(
            "/financial/credit-cards", headers=_auth_header(token)
        ).json()[0]

        assert card.status_code == 201
        assert purchase.status_code == 201
        assert Decimal(balance["current_balance"]) == Decimal("1000.00")
        assert Decimal(card_after["used_limit"]) == Decimal("123.45")
        assert Decimal(card_after["available_limit"]) == Decimal("376.55")

    def test_statement_payment_reduces_bank_balance_without_new_expense(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        ).json()
        purchase = client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={
                "amount": "200.00",
                "description": "Phone",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        ).json()

        payment = client.post(
            f"/financial/statements/{purchase['statement_id']}/pay",
            json={"paid_on": "2026-07-20"},
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{checking['id']}/balance",
            headers=_auth_header(token),
        ).json()
        expenses = client.get(
            "/financial/transactions?type=expense", headers=_auth_header(token)
        ).json()

        assert payment.status_code == 200
        assert payment.json()["status"] == "paid"
        assert Decimal(balance["current_balance"]) == Decimal("800.00")
        assert expenses == []

    def test_user_cannot_create_card_with_another_users_payment_account(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        account_a = _create_account(client, token_a, name="A Account")

        resp = client.post(
            "/financial/credit-cards",
            json={
                "name": "Bad Card",
                "limit_amount": "100.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": account_a["id"],
            },
            headers=_auth_header(token_b),
        )

        assert resp.status_code == 404


class TestInstallmentsAndRecurring:
    def test_installment_plan_creates_pending_installments_without_changing_balance(self, client):
        token = _register_and_get_token(client)
        account = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )

        plan = client.post(
            "/financial/installment-plans",
            json={
                "type": "expense",
                "account_id": account["id"],
                "amount": "300.00",
                "installments_count": 3,
                "description": "Appliance",
                "first_due_on": "2026-08-05",
            },
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        ).json()

        assert plan.status_code == 201
        data = plan.json()
        assert len(data["installments"]) == 3
        assert {item["status"] for item in data["installments"]} == {"pending"}
        assert Decimal(data["installments"][0]["amount"]) == Decimal("100.00")
        assert Decimal(balance["current_balance"]) == Decimal("1000.00")

    def test_confirm_installment_creates_effective_transaction_once(self, client):
        token = _register_and_get_token(client)
        account = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )
        plan = client.post(
            "/financial/installment-plans",
            json={
                "type": "expense",
                "account_id": account["id"],
                "amount": "300.00",
                "installments_count": 3,
                "description": "Appliance",
                "first_due_on": "2026-08-05",
            },
            headers=_auth_header(token),
        ).json()
        installment_id = plan["installments"][0]["id"]

        first = client.post(
            f"/financial/installments/{installment_id}/confirm",
            headers=_auth_header(token),
        )
        second = client.post(
            f"/financial/installments/{installment_id}/confirm",
            headers=_auth_header(token),
        )
        balance = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        ).json()

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["status"] == "confirmed"
        assert second.json()["transaction_id"] == first.json()["transaction_id"]
        assert Decimal(balance["current_balance"]) == Decimal("900.00")

    def test_recurring_rule_confirmation_creates_transaction_and_advances_rule(self, client):
        token = _register_and_get_token(client)
        account = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )

        rule = client.post(
            "/financial/recurring-rules",
            json={
                "type": "expense",
                "account_id": account["id"],
                "amount": "80.00",
                "description": "Internet",
                "frequency": "monthly",
                "next_occurrence_on": "2026-08-10",
            },
            headers=_auth_header(token),
        )
        before = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        ).json()
        confirmation = client.post(
            f"/financial/recurring-rules/{rule.json()['id']}/confirm",
            json={"amount": "75.00", "occurred_on": "2026-08-10"},
            headers=_auth_header(token),
        )
        after = client.get(
            f"/financial/accounts/{account['id']}/balance",
            headers=_auth_header(token),
        ).json()

        assert rule.status_code == 201
        assert Decimal(before["current_balance"]) == Decimal("1000.00")
        assert confirmation.status_code == 200
        assert confirmation.json()["last_transaction_id"] is not None
        assert confirmation.json()["next_occurrence_on"] == "2026-09-10"
        assert Decimal(after["current_balance"]) == Decimal("925.00")

    def test_user_cannot_confirm_another_users_recurring_rule(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        account_a = _create_account(client, token_a, name="A Account")
        rule = client.post(
            "/financial/recurring-rules",
            json={
                "type": "expense",
                "account_id": account_a["id"],
                "amount": "80.00",
                "description": "Internet",
                "frequency": "monthly",
                "next_occurrence_on": "2026-08-10",
            },
            headers=_auth_header(token_a),
        ).json()

        resp = client.post(
            f"/financial/recurring-rules/{rule['id']}/confirm",
            json={"amount": "75.00", "occurred_on": "2026-08-10"},
            headers=_auth_header(token_b),
        )

        assert resp.status_code == 404


class TestDashboard:
    def test_dashboard_returns_real_monthly_cash_flow_and_statement_total(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(
            client, token, name="Checking", initial_balance="1000.00"
        )
        for transaction_type, amount, occurred_on in [
            ("income", "500.00", "2026-05-10"),
            ("expense", "120.00", "2026-05-11"),
            ("income", "700.00", "2026-07-02"),
            ("expense", "80.00", "2026-07-03"),
        ]:
            client.post(
                "/financial/transactions",
                json={
                    "type": transaction_type,
                    "account_id": checking["id"],
                    "amount": amount,
                    "occurred_on": occurred_on,
                },
                headers=_auth_header(token),
            )

        response = client.get(
            "/financial/dashboard?start_date=2026-07-01&end_date=2026-07-31&months=3",
            headers=_auth_header(token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cash_flow"] == [
            {"month": "2026-05", "income": "500.00", "expense": "120.00"},
            {"month": "2026-06", "income": "0.00", "expense": "0.00"},
            {"month": "2026-07", "income": "700.00", "expense": "80.00"},
        ]
        assert Decimal(data["open_statement_total"]) == Decimal("0.00")

    def test_dashboard_summarizes_balance_spending_statements_and_recent_transactions(self, client):
        token = _register_and_get_token(client)
        checking = _create_account(
            client, token, name="Checking", initial_balance="500.00"
        )
        category = _create_category(client, token, name="General")
        card = client.post(
            "/financial/credit-cards",
            json={
                "name": "Main Card",
                "limit_amount": "500.00",
                "closing_day": 10,
                "due_day": 20,
                "payment_account_id": checking["id"],
            },
            headers=_auth_header(token),
        ).json()
        client.post(
            "/financial/transactions",
            json={
                "type": "income",
                "account_id": checking["id"],
                "amount": "100.00",
                "description": "Bonus",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        client.post(
            "/financial/transactions",
            json={
                "type": "expense",
                "account_id": checking["id"],
                "category_id": category["id"],
                "amount": "50.00",
                "description": "Groceries",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )
        client.post(
            f"/financial/credit-cards/{card['id']}/purchases",
            json={
                "amount": "25.00",
                "description": "Card lunch",
                "occurred_on": "2026-07-17",
            },
            headers=_auth_header(token),
        )

        resp = client.get(
            "/financial/dashboard?start_date=2026-07-01&end_date=2026-07-31",
            headers=_auth_header(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["total_balance"]) == Decimal("550.00")
        assert Decimal(data["period_income"]) == Decimal("100.00")
        assert Decimal(data["period_expenses"]) == Decimal("75.00")
        assert len(data["accounts"]) == 1
        assert len(data["open_statements"]) == 1
        assert Decimal(data["open_statements"][0]["total_amount"]) == Decimal("25.00")
        assert len(data["recent_transactions"]) == 3

    def test_dashboard_is_scoped_to_current_user(self, client):
        token_a = _register_and_get_token(client, email="a@test.com", name="User A")
        token_b = _register_and_get_token(client, email="b@test.com", name="User B")
        _create_account(client, token_a, name="A Checking", initial_balance="100.00")
        _create_account(client, token_b, name="B Checking", initial_balance="999.00")

        resp = client.get("/financial/dashboard", headers=_auth_header(token_a))

        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["total_balance"]) == Decimal("100.00")
        assert data["accounts"][0]["name"] == "A Checking"

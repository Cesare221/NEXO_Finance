from decimal import Decimal
from datetime import date, datetime, timezone

from app.core.config import settings
from app.models.user import User
from app.services.assistant_provider import ProviderResult, TransactionDraft
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
    defaults = {"name": "Checking", "type": "checking", "initial_balance": "100.00"}
    defaults.update(kwargs)
    return client.post(
        "/financial/accounts", json=defaults, headers=_auth_header(token)
    ).json()


def test_proposed_action_does_not_mutate_financial_data(client):
    token = _register_and_get_token(client)
    account = _create_account(client, token)

    proposal = client.post(
        "/assistant/proposals",
        json={
            "action_type": "create_transaction",
            "payload": {
                "type": "expense",
                "account_id": account["id"],
                "amount": "25.00",
                "description": "Pizza",
                "occurred_on": "2026-07-17",
            },
            "human_summary": "Criar despesa de 25.00 em Pizza",
            "idempotency_key": "pizza-1",
        },
        headers=_auth_header(token),
    )
    balance = client.get(
        f"/financial/accounts/{account['id']}/balance", headers=_auth_header(token)
    ).json()

    assert proposal.status_code == 201
    assert proposal.json()["status"] == "proposed"
    assert Decimal(balance["current_balance"]) == Decimal("100.00")


def test_confirm_proposal_executes_once_and_records_audit(client):
    token = _register_and_get_token(client)
    account = _create_account(client, token)
    proposal = client.post(
        "/assistant/proposals",
        json={
            "action_type": "create_transaction",
            "payload": {
                "type": "expense",
                "account_id": account["id"],
                "amount": "25.00",
                "description": "Pizza",
                "occurred_on": "2026-07-17",
            },
            "human_summary": "Criar despesa de 25.00 em Pizza",
            "idempotency_key": "pizza-2",
        },
        headers=_auth_header(token),
    ).json()

    first = client.post(
        f"/assistant/proposals/{proposal['id']}/confirm",
        headers=_auth_header(token),
    )
    second = client.post(
        f"/assistant/proposals/{proposal['id']}/confirm",
        headers=_auth_header(token),
    )
    balance = client.get(
        f"/financial/accounts/{account['id']}/balance", headers=_auth_header(token)
    ).json()
    audit = client.get("/assistant/audit-events", headers=_auth_header(token)).json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "executed"
    assert second.json()["execution"]["result"] == first.json()["execution"]["result"]
    assert Decimal(balance["current_balance"]) == Decimal("75.00")
    assert {event["event_type"] for event in audit} >= {
        "proposal_created",
        "proposal_executed",
    }


def test_cancel_proposal_does_not_execute(client):
    token = _register_and_get_token(client)
    account = _create_account(client, token)
    proposal = client.post(
        "/assistant/proposals",
        json={
            "action_type": "create_transaction",
            "payload": {
                "type": "expense",
                "account_id": account["id"],
                "amount": "25.00",
                "occurred_on": "2026-07-17",
            },
            "human_summary": "Criar despesa",
            "idempotency_key": "cancel-1",
        },
        headers=_auth_header(token),
    ).json()

    cancelled = client.post(
        f"/assistant/proposals/{proposal['id']}/cancel",
        headers=_auth_header(token),
    )
    confirm = client.post(
        f"/assistant/proposals/{proposal['id']}/confirm",
        headers=_auth_header(token),
    )
    balance = client.get(
        f"/financial/accounts/{account['id']}/balance", headers=_auth_header(token)
    ).json()

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert confirm.status_code == 400
    assert Decimal(balance["current_balance"]) == Decimal("100.00")


def test_expired_proposal_does_not_execute(client):
    token = _register_and_get_token(client)
    account = _create_account(client, token)
    proposal = client.post(
        "/assistant/proposals",
        json={
            "action_type": "create_transaction",
            "payload": {
                "type": "expense",
                "account_id": account["id"],
                "amount": "25.00",
                "occurred_on": "2026-07-17",
            },
            "human_summary": "Criar despesa",
            "idempotency_key": "expired-1",
            "expires_at": "2020-01-01T00:00:00+00:00",
        },
        headers=_auth_header(token),
    ).json()

    resp = client.post(
        f"/assistant/proposals/{proposal['id']}/confirm",
        headers=_auth_header(token),
    )

    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_user_cannot_confirm_another_users_proposal(client):
    token_a = _register_and_get_token(client, email="a@test.com", name="User A")
    token_b = _register_and_get_token(client, email="b@test.com", name="User B")
    account_a = _create_account(client, token_a)
    proposal = client.post(
        "/assistant/proposals",
        json={
            "action_type": "create_transaction",
            "payload": {
                "type": "expense",
                "account_id": account_a["id"],
                "amount": "25.00",
                "occurred_on": "2026-07-17",
            },
            "human_summary": "Criar despesa",
            "idempotency_key": "cross-user-1",
        },
        headers=_auth_header(token_a),
    ).json()

    resp = client.post(
        f"/assistant/proposals/{proposal['id']}/confirm",
        headers=_auth_header(token_b),
    )

    assert resp.status_code == 404


def test_list_proposals_filters_status_exposes_created_at_and_isolates_user(client):
    token_a = _register_and_get_token(client, email="a@test.com", name="User A")
    token_b = _register_and_get_token(client, email="b@test.com", name="User B")
    account_a = _create_account(client, token_a)
    account_b = _create_account(client, token_b)

    def create(token, account_id, key):
        return client.post(
            "/assistant/proposals",
            json={
                "action_type": "create_transaction",
                "payload": {
                    "type": "expense",
                    "account_id": account_id,
                    "amount": "10.00",
                    "occurred_on": "2026-07-17",
                    "origin": "recognized",
                },
                "human_summary": f"Movimentacao {key}",
                "idempotency_key": key,
            },
            headers=_auth_header(token),
        ).json()

    pending_a = create(token_a, account_a["id"], "pending-a")
    cancelled_a = create(token_a, account_a["id"], "cancelled-a")
    create(token_b, account_b["id"], "pending-b")
    client.post(
        f"/assistant/proposals/{cancelled_a['id']}/cancel",
        headers=_auth_header(token_a),
    )

    response = client.get(
        "/assistant/proposals?status=proposed",
        headers=_auth_header(token_a),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [pending_a["id"]]
    assert response.json()[0]["created_at"] is not None


def test_message_creates_proposal_without_mutating_balance(client):
    token = _register_and_get_token(client)
    account = _create_account(client, token)

    response = client.post(
        "/assistant/messages",
        json={
            "message": "gastei R$ 35,50 no mercado hoje",
            "conversation_id": "conversation-1",
            "client_message_id": "message-1",
        },
        headers=_auth_header(token),
    )
    balance = client.get(
        f"/financial/accounts/{account['id']}/balance", headers=_auth_header(token)
    ).json()

    assert response.status_code == 200
    assert response.json()["kind"] == "proposal"
    assert response.json()["proposal"]["status"] == "proposed"
    assert response.json()["proposal"]["payload"]["amount"] == "35.50"
    assert Decimal(balance["current_balance"]) == Decimal("100.00")


def test_read_only_message_returns_answer_without_proposal(client):
    token = _register_and_get_token(client)
    _create_account(client, token, initial_balance="321.45")

    response = client.post(
        "/assistant/messages",
        json={
            "message": "qual é o meu saldo?",
            "conversation_id": "conversation-2",
            "client_message_id": "message-2",
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "answer"
    assert response.json()["proposal"] is None
    assert "321,45" in response.json()["message"]


def test_transaction_message_without_account_requests_clarification(client):
    token = _register_and_get_token(client)

    response = client.post(
        "/assistant/messages",
        json={
            "message": "recebi 500 de um trabalho",
            "conversation_id": "conversation-3",
            "client_message_id": "message-3",
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "clarification"
    assert response.json()["proposal"] is None
    assert "conta" in response.json()["message"].lower()


def test_groq_provider_can_only_prepare_a_pending_proposal(client, monkeypatch):
    client.post(
        "/auth/register",
        json={
            "name": "AI User",
            "email": "ai-user@example.com",
            "password": "FinSeguro123!",
            "ai_data_processing_consent": True,
        },
    )
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "ai-user@example.com").one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()
    token = client.post("/auth/login", json={"email": "ai-user@example.com", "password": "FinSeguro123!"}).json()["access_token"]
    account = _create_account(client, token, name="Conta principal")
    monkeypatch.setattr(settings, "fin_ai_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    def fake_response(provider, db, user_id, message):
        return ProviderResult(
            message="Preparei a proposta para sua revisão.",
            draft=TransactionDraft(
                transaction_type="expense",
                account_id=account["id"],
                account_name="Conta principal",
                category_id=None,
                category_name=None,
                amount=Decimal("42.90"),
                description="Almoço",
                occurred_on=date(2026, 7, 21),
            ),
        )

    monkeypatch.setattr(
        "app.services.assistant_service.GroqAssistantProvider.respond",
        fake_response,
    )
    response = client.post(
        "/assistant/messages",
        json={
            "message": "Gastei 42,90 no almoço",
            "client_message_id": "groq-message-1",
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "proposal"
    assert response.json()["proposal"]["payload"]["origin"] == "fin_ai"
    assert response.json()["proposal"]["status"] == "proposed"
    transactions = client.get("/financial/transactions", headers=_auth_header(token))
    assert transactions.json() == []


def test_external_ai_is_not_called_without_user_consent(client, monkeypatch):
    token = _register_and_get_token(client, email="no-ai-consent@example.com")
    _create_account(client, token, initial_balance="250.00")
    monkeypatch.setattr(settings, "fin_ai_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    def forbidden(*args, **kwargs):
        raise AssertionError("Groq must not be called without consent")

    monkeypatch.setattr(
        "app.services.assistant_service.GroqAssistantProvider.respond",
        forbidden,
    )
    response = client.post(
        "/assistant/messages",
        json={"message": "qual meu saldo?", "client_message_id": "local-message-1"},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert "250,00" in response.json()["message"]


def test_public_proposal_endpoint_rejects_unknown_action_and_extra_payload(client):
    token = _register_and_get_token(client, email="strict-proposal@example.com")
    account = _create_account(client, token)
    response = client.post(
        "/assistant/proposals",
        json={
            "action_type": "delete_account",
            "payload": {
                "type": "expense",
                "account_id": account["id"],
                "amount": "10.00",
                "occurred_on": "2026-07-21",
                "admin": True,
            },
            "human_summary": "Operação inválida",
            "idempotency_key": "invalid-action",
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 422

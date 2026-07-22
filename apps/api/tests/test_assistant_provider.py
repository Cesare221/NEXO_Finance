from app.services.assistant_provider import GroqAssistantProvider
from app.models.user import User
from tests.conftest import TestingSessionLocal


def test_groq_tool_loop_prepares_draft_without_writing_transaction(client, monkeypatch):
    registration = client.post(
        "/auth/register",
        json={
            "name": "Provider User",
            "email": "provider@example.com",
            "password": "FinSeguro123!",
        },
    )
    token = registration.json()["access_token"]
    account = client.post(
        "/financial/accounts",
        json={"name": "Conta principal", "type": "checking", "initial_balance": "100.00"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    responses = iter(
        [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "tool-1",
                        "type": "function",
                        "function": {
                            "name": "prepare_transaction",
                            "arguments": (
                                '{"type":"expense","amount":35.5,'
                                '"description":"Mercado","account_name":"Conta principal"}'
                            ),
                        },
                    }
                ],
            },
            {"content": "Revise a proposta antes de confirmar."},
        ]
    )
    provider = object.__new__(GroqAssistantProvider)
    monkeypatch.setattr(provider, "_call", lambda messages: next(responses))

    with TestingSessionLocal() as db:
        user_id = db.query(User).filter(User.email == "provider@example.com").one().id
        result = provider.respond(db, user_id, "Gastei 35,50 no mercado")

    assert result.draft is not None
    assert result.draft.account_id == account["id"]
    assert str(result.draft.amount) == "35.50"
    transactions = client.get(
        "/financial/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transactions.json() == []

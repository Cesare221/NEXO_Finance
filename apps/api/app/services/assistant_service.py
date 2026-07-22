from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import re
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.action_execution import ActionExecution
from app.models.action_proposal import ActionProposal
from app.models.audit_event import AuditEvent
from app.models.category import Category
from app.services import financial_service as fs
from app.services.assistant_provider import AssistantProviderError, GroqAssistantProvider


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _audit(
    db: Session,
    user_id: int,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    payload: dict,
) -> None:
    db.add(
        AuditEvent(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
    )


def _get_proposal(db: Session, user_id: int, proposal_id: int) -> ActionProposal:
    proposal = (
        db.query(ActionProposal)
        .filter(ActionProposal.id == proposal_id, ActionProposal.user_id == user_id)
        .first()
    )
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found"
        )
    return proposal


def create_proposal(
    db: Session,
    user_id: int,
    conversation_id: str | None,
    action_type: str,
    payload: dict,
    human_summary: str,
    previous_state_snapshot: dict,
    expires_at: datetime | None,
    idempotency_key: str,
) -> ActionProposal:
    existing = (
        db.query(ActionProposal)
        .filter(
            ActionProposal.user_id == user_id,
            ActionProposal.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing:
        return existing
    proposal = ActionProposal(
        user_id=user_id,
        conversation_id=conversation_id,
        action_type=action_type,
        payload=payload,
        human_summary=human_summary,
        previous_state_snapshot=previous_state_snapshot,
        status="proposed",
        expires_at=expires_at or (_now() + timedelta(minutes=15)),
        idempotency_key=idempotency_key,
    )
    db.add(proposal)
    db.flush()
    _audit(
        db,
        user_id,
        "proposal_created",
        "ActionProposal",
        proposal.id,
        {"action_type": action_type, "human_summary": human_summary},
    )
    db.commit()
    db.refresh(proposal)
    return proposal


def list_proposals(
    db: Session, user_id: int, proposal_status: str | None = None
) -> list[ActionProposal]:
    query = db.query(ActionProposal).filter(ActionProposal.user_id == user_id)
    if proposal_status is not None:
        query = query.filter(ActionProposal.status == proposal_status)
    return query.order_by(ActionProposal.id.desc()).all()


def update_proposal(
    db: Session,
    user_id: int,
    proposal_id: int,
    payload: dict | None,
    human_summary: str | None,
) -> ActionProposal:
    proposal = _get_proposal(db, user_id, proposal_id)
    if proposal.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only proposed actions can be edited",
        )
    if payload is not None:
        proposal.payload = payload
    if human_summary is not None:
        proposal.human_summary = human_summary
    _audit(db, user_id, "proposal_edited", "ActionProposal", proposal.id, {})
    db.commit()
    db.refresh(proposal)
    return proposal


def cancel_proposal(db: Session, user_id: int, proposal_id: int) -> ActionProposal:
    proposal = _get_proposal(db, user_id, proposal_id)
    if proposal.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only proposed actions can be cancelled",
        )
    proposal.status = "cancelled"
    _audit(db, user_id, "proposal_cancelled", "ActionProposal", proposal.id, {})
    db.commit()
    db.refresh(proposal)
    return proposal


def _existing_execution(
    db: Session, user_id: int, proposal_id: int
) -> ActionExecution | None:
    return (
        db.query(ActionExecution)
        .filter(
            ActionExecution.user_id == user_id,
            ActionExecution.proposal_id == proposal_id,
        )
        .first()
    )


def _execute_create_transaction(
    db: Session, user_id: int, proposal: ActionProposal
) -> dict:
    payload = proposal.payload
    transaction = fs.create_transaction(
        db,
        user_id,
        payload["type"],
        int(payload["account_id"]),
        payload.get("category_id"),
        Decimal(str(payload["amount"])),
        payload.get("description"),
        datetime.fromisoformat(payload["occurred_on"]).date(),
        payload.get("origin", "fin"),
    )
    return {"transaction_id": transaction.id}


def confirm_proposal(
    db: Session, user_id: int, proposal_id: int
) -> tuple[ActionProposal, ActionExecution | None]:
    proposal = _get_proposal(db, user_id, proposal_id)
    existing = _existing_execution(db, user_id, proposal.id)
    if proposal.status == "executed":
        return proposal, existing
    if proposal.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm proposal in status {proposal.status}",
        )
    if _aware(proposal.expires_at) < _now():
        proposal.status = "expired"
        _audit(db, user_id, "proposal_expired", "ActionProposal", proposal.id, {})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal expired"
        )

    proposal.status = "confirmed"
    proposal.confirmed_at = _now()
    if proposal.action_type == "create_transaction":
        result = _execute_create_transaction(db, user_id, proposal)
    else:
        proposal.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported action type: {proposal.action_type}",
        )

    execution = ActionExecution(
        user_id=user_id,
        proposal_id=proposal.id,
        status="succeeded",
        result=result,
        idempotency_key=proposal.idempotency_key,
    )
    proposal.status = "executed"
    proposal.executed_at = _now()
    db.add(execution)
    db.flush()
    _audit(
        db,
        user_id,
        "proposal_executed",
        "ActionProposal",
        proposal.id,
        {"result": result},
    )
    db.commit()
    db.refresh(proposal)
    db.refresh(execution)
    return proposal, execution


def list_audit_events(db: Session, user_id: int) -> list[AuditEvent]:
    return (
        db.query(AuditEvent)
        .filter(AuditEvent.user_id == user_id)
        .order_by(AuditEvent.id.asc())
        .all()
    )


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _extract_amount(message: str) -> Decimal | None:
    match = re.search(
        r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+\.\d{1,2}|\d+(?:,\d{1,2})?)",
        message.casefold(),
    )
    if not match:
        return None
    raw = match.group(1)
    if "." in raw and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    amount = Decimal(raw).quantize(Decimal("0.01"))
    return amount if amount > 0 else None


def _format_currency(value: Decimal) -> str:
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def _read_only_answer(db: Session, user_id: int, normalized: str) -> str:
    today = date.today()
    dashboard = fs.get_dashboard(db, user_id, today.replace(day=1), today)
    if "saldo" in normalized:
        return f"Seu saldo total é {_format_currency(Decimal(dashboard['total_balance']))}."
    if any(word in normalized for word in ("gastei", "despesa", "gastos")):
        return f"Suas despesas neste mês somam {_format_currency(Decimal(dashboard['period_expenses']))}."
    if any(word in normalized for word in ("recebi", "receita", "renda")):
        return f"Suas receitas neste mês somam {_format_currency(Decimal(dashboard['period_income']))}."
    return (
        f"Seu saldo é {_format_currency(Decimal(dashboard['total_balance']))}, com "
        f"{_format_currency(Decimal(dashboard['period_income']))} em receitas e "
        f"{_format_currency(Decimal(dashboard['period_expenses']))} em despesas neste mês."
    )


def handle_message(
    db: Session,
    user_id: int,
    message: str,
    conversation_id: str | None,
    client_message_id: str,
    allow_external_ai: bool = False,
) -> dict:
    if allow_external_ai and settings.fin_ai_provider == "groq" and settings.groq_api_key:
        try:
            result = GroqAssistantProvider().respond(db, user_id, message)
            _audit(
                db,
                user_id,
                "assistant_response_generated",
                "AssistantProvider",
                None,
                {
                    "provider": result.provider,
                    "model": result.model,
                    "outcome": "proposal" if result.draft else "answer",
                },
            )
            if result.draft is None:
                db.commit()
                return {"kind": "answer", "message": result.message, "proposal": None}

            draft = result.draft
            type_label = "despesa" if draft.transaction_type == "expense" else "receita"
            category_label = f" em {draft.category_name}" if draft.category_name else ""
            summary = (
                f"Criar {type_label} de {_format_currency(draft.amount)}{category_label} "
                f"na conta {draft.account_name}."
            )
            idempotency_key = hashlib.sha256(
                f"{user_id}:{client_message_id}".encode("utf-8")
            ).hexdigest()
            proposal = create_proposal(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                action_type="create_transaction",
                payload={
                    "type": draft.transaction_type,
                    "account_id": draft.account_id,
                    "category_id": draft.category_id,
                    "amount": str(draft.amount),
                    "description": draft.description,
                    "occurred_on": draft.occurred_on.isoformat(),
                    "origin": "fin_ai",
                },
                human_summary=summary,
                previous_state_snapshot={},
                expires_at=None,
                idempotency_key=idempotency_key,
            )
            return {"kind": "proposal", "message": result.message, "proposal": proposal}
        except AssistantProviderError:
            db.rollback()
            _audit(
                db,
                user_id,
                "assistant_provider_fallback",
                "AssistantProvider",
                None,
                {"provider": "groq", "model": settings.fin_ai_model},
            )
            db.commit()

    normalized = _normalize_text(message)
    amount = _extract_amount(message)
    expense_words = ("gastei", "paguei", "comprei", "despesa", "debito")
    income_words = ("recebi", "ganhei", "salario", "renda", "receita", "entrou")
    is_expense = any(word in normalized for word in expense_words)
    is_income = any(word in normalized for word in income_words)
    asks_question = any(word in normalized for word in ("quanto", "qual", "total", "saldo"))

    if asks_question and amount is None:
        return {
            "kind": "answer",
            "message": _read_only_answer(db, user_id, normalized),
            "proposal": None,
        }

    if not is_expense and not is_income:
        return {
            "kind": "clarification",
            "message": (
                "Posso consultar saldo, receitas e despesas ou preparar um lançamento. "
                "Por exemplo: “gastei R$ 35 no mercado”."
            ),
            "proposal": None,
        }

    if amount is None:
        return {
            "kind": "clarification",
            "message": "Qual foi o valor? Inclua um número, por exemplo R$ 35,50.",
            "proposal": None,
        }

    accounts = [account for account in fs.list_accounts(db, user_id) if not account.is_archived]
    if not accounts:
        return {
            "kind": "clarification",
            "message": "Cadastre uma conta antes de registrar movimentações pelo Fin.",
            "proposal": None,
        }

    account = next(
        (item for item in accounts if _normalize_text(item.name) in normalized),
        accounts[0],
    )
    categories = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.is_archived.is_(False))
        .all()
    )
    category = next(
        (
            item
            for item in sorted(categories, key=lambda value: len(value.name), reverse=True)
            if _normalize_text(item.name) in normalized
        ),
        None,
    )
    transaction_type = "expense" if is_expense else "income"
    type_label = "despesa" if transaction_type == "expense" else "receita"
    category_label = f" em {category.name}" if category else ""
    summary = (
        f"Criar {type_label} de {_format_currency(amount)}{category_label} "
        f"na conta {account.name}."
    )
    idempotency_key = hashlib.sha256(
        f"{user_id}:{client_message_id}".encode("utf-8")
    ).hexdigest()
    proposal = create_proposal(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        action_type="create_transaction",
        payload={
            "type": transaction_type,
            "account_id": account.id,
            "category_id": category.id if category else None,
            "amount": str(amount),
            "description": message.strip(),
            "occurred_on": date.today().isoformat(),
            "origin": "fin",
        },
        human_summary=summary,
        previous_state_snapshot={},
        expires_at=None,
        idempotency_key=idempotency_key,
    )
    return {
        "kind": "proposal",
        "message": "Preparei a proposta abaixo. Revise os dados antes de confirmar.",
        "proposal": proposal,
    }

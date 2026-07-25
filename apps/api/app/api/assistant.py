from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_verified_user
from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import RateLimitExceeded, RateLimitUnavailable, auth_rate_limiter
from app.models.user import User
from app.schemas.assistant import (
    ActionProposalCreate,
    ActionProposalResponse,
    ActionProposalUpdate,
    AssistantMessageRequest,
    AssistantMessageResponse,
    AuditEventResponse,
    ConfirmProposalResponse,
)
from app.services import assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _limit(bucket: str, user_id: int, limit: int, window_seconds: int) -> None:
    try:
        auth_rate_limiter.check(bucket, str(user_id), limit, window_seconds)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Limite de uso do Fin atingido. Aguarde e tente novamente.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except RateLimitUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Protecao do Fin temporariamente indisponivel.",
            headers={"Retry-After": "30"},
        ) from exc


@router.post("/messages", response_model=AssistantMessageResponse)
def send_message(
    body: AssistantMessageRequest,
    request: Request,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    _limit("assistant-minute", current_user.id, settings.fin_ai_messages_per_minute, 60)
    _limit("assistant-day", current_user.id, settings.fin_ai_messages_per_day, 86400)
    return assistant_service.handle_message(
        db,
        current_user.id,
        body.message,
        body.conversation_id,
        body.client_message_id,
        current_user.ai_data_processing_consent,
    )


@router.get("/proposals", response_model=list[ActionProposalResponse])
def list_proposals(
    status: str | None = Query(
        default=None,
        pattern="^(proposed|executed|cancelled|expired|failed)$",
    ),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return assistant_service.list_proposals(db, current_user.id, status)


@router.post("/proposals", response_model=ActionProposalResponse, status_code=201)
def create_proposal(
    body: ActionProposalCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    _limit("assistant-proposal-create", current_user.id, 20, 60)
    return assistant_service.create_proposal(
        db,
        current_user.id,
        body.conversation_id,
        body.action_type,
        body.payload.model_dump(mode="json"),
        body.human_summary,
        body.previous_state_snapshot,
        body.expires_at,
        body.idempotency_key,
    )


@router.put("/proposals/{proposal_id}", response_model=ActionProposalResponse)
def update_proposal(
    proposal_id: int,
    body: ActionProposalUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    _limit("assistant-proposal-update", current_user.id, 30, 60)
    return assistant_service.update_proposal(
        db,
        current_user.id,
        proposal_id,
        body.payload.model_dump(mode="json") if body.payload else None,
        body.human_summary,
    )


@router.post("/proposals/{proposal_id}/cancel", response_model=ActionProposalResponse)
def cancel_proposal(
    proposal_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    _limit("assistant-proposal-cancel", current_user.id, 30, 60)
    return assistant_service.cancel_proposal(db, current_user.id, proposal_id)


@router.post("/proposals/{proposal_id}/confirm", response_model=ConfirmProposalResponse)
def confirm_proposal(
    proposal_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    _limit("assistant-proposal-confirm", current_user.id, 10, 60)
    proposal, execution = assistant_service.confirm_proposal(
        db, current_user.id, proposal_id
    )
    return {"status": proposal.status, "proposal": proposal, "execution": execution}


@router.get("/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return assistant_service.list_audit_events(db, current_user.id)

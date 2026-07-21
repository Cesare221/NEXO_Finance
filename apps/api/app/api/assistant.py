from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
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


@router.post("/messages", response_model=AssistantMessageResponse)
def send_message(
    body: AssistantMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.handle_message(
        db,
        current_user.id,
        body.message,
        body.conversation_id,
        body.client_message_id,
    )


@router.get("/proposals", response_model=list[ActionProposalResponse])
def list_proposals(
    status: str | None = Query(
        default=None,
        pattern="^(proposed|executed|cancelled|expired|failed)$",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.list_proposals(db, current_user.id, status)


@router.post("/proposals", response_model=ActionProposalResponse, status_code=201)
def create_proposal(
    body: ActionProposalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.create_proposal(
        db,
        current_user.id,
        body.conversation_id,
        body.action_type,
        body.payload,
        body.human_summary,
        body.previous_state_snapshot,
        body.expires_at,
        body.idempotency_key,
    )


@router.put("/proposals/{proposal_id}", response_model=ActionProposalResponse)
def update_proposal(
    proposal_id: int,
    body: ActionProposalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.update_proposal(
        db, current_user.id, proposal_id, body.payload, body.human_summary
    )


@router.post("/proposals/{proposal_id}/cancel", response_model=ActionProposalResponse)
def cancel_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.cancel_proposal(db, current_user.id, proposal_id)


@router.post("/proposals/{proposal_id}/confirm", response_model=ConfirmProposalResponse)
def confirm_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal, execution = assistant_service.confirm_proposal(
        db, current_user.id, proposal_id
    )
    return {"status": proposal.status, "proposal": proposal, "execution": execution}


@router.get("/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assistant_service.list_audit_events(db, current_user.id)

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class TransactionProposalPayload(BaseModel):
    type: Literal["income", "expense"]
    account_id: int = Field(..., gt=0)
    category_id: int | None = Field(None, gt=0)
    amount: Decimal = Field(..., gt=0, le=Decimal("9999999999999999.99"))
    description: str | None = Field(None, min_length=2, max_length=500)
    occurred_on: date
    origin: Literal["fin", "fin_ai", "recognized"] = "fin"

    model_config = {"extra": "forbid"}


class ActionProposalCreate(BaseModel):
    conversation_id: str | None = Field(None, max_length=100)
    action_type: Literal["create_transaction"]
    payload: TransactionProposalPayload
    human_summary: str = Field(..., min_length=1, max_length=1000)
    previous_state_snapshot: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None
    idempotency_key: str = Field(..., min_length=1, max_length=255)


class ActionProposalUpdate(BaseModel):
    payload: TransactionProposalPayload | None = None
    human_summary: str | None = Field(None, min_length=1, max_length=1000)


class ActionProposalResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: str | None
    action_type: str
    payload: dict[str, Any]
    human_summary: str
    previous_state_snapshot: dict[str, Any]
    status: str
    expires_at: datetime
    confirmed_at: datetime | None
    executed_at: datetime | None
    idempotency_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionExecutionResponse(BaseModel):
    id: int
    user_id: int
    proposal_id: int
    status: str
    result: dict[str, Any]
    idempotency_key: str

    model_config = {"from_attributes": True}


class ConfirmProposalResponse(BaseModel):
    status: str
    proposal: ActionProposalResponse
    execution: ActionExecutionResponse | None


class AuditEventResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    entity_type: str
    entity_id: int | None
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AssistantMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: str | None = Field(None, max_length=100)
    client_message_id: str = Field(..., min_length=1, max_length=100)


class AssistantMessageResponse(BaseModel):
    kind: Literal["answer", "proposal", "clarification"]
    message: str
    proposal: ActionProposalResponse | None = None

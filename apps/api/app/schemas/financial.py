from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ACCOUNT_TYPES = {"checking", "savings", "wallet", "investment"}
TRANSACTION_CREATE_TYPES = {"income", "expense"}


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1)
    initial_balance: Decimal = Field(default_factory=lambda: Decimal("0.00"))
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ACCOUNT_TYPES:
            raise ValueError(f"Type must be one of: {', '.join(sorted(ACCOUNT_TYPES))}")
        return v


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: str | None = None
    initial_balance: Decimal | None = None
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)
    is_archived: bool | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ACCOUNT_TYPES:
            raise ValueError(f"Type must be one of: {', '.join(sorted(ACCOUNT_TYPES))}")
        return v


class AccountResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    initial_balance: Decimal
    color: str | None
    icon: str | None
    is_archived: bool

    model_config = {"from_attributes": True}


class AccountBalanceResponse(BaseModel):
    account_id: int
    current_balance: Decimal


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int | None = None
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    parent_id: int | None = None
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)
    is_archived: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    parent_id: int | None
    color: str | None
    icon: str | None
    is_archived: bool
    children: list["CategoryResponse"] = []

    model_config = {"from_attributes": True}


class CategoryDeleteResponse(BaseModel):
    action: Literal["deleted", "archived"]
    category: CategoryResponse


class TransactionCreate(BaseModel):
    type: str = Field(..., min_length=1)
    account_id: int
    category_id: int | None = None
    amount: Decimal = Field(..., gt=Decimal("0"))
    description: str | None = Field(None, max_length=500)
    occurred_on: date
    origin: str = Field(default="manual", max_length=30)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in TRANSACTION_CREATE_TYPES:
            raise ValueError(
                f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}"
            )
        return v


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    description: str | None
    occurred_on: date
    origin: str
    is_deleted: bool

    model_config = {"from_attributes": True}


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(..., gt=Decimal("0"))
    description: str | None = Field(None, max_length=500)
    occurred_on: date


class TransferResponse(BaseModel):
    id: int
    user_id: int
    from_account_id: int
    to_account_id: int
    out_transaction_id: int
    in_transaction_id: int
    amount: Decimal
    description: str | None
    occurred_on: date

    model_config = {"from_attributes": True}


class CreditCardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    limit_amount: Decimal = Field(..., gt=Decimal("0"))
    closing_day: int = Field(..., ge=1, le=31)
    due_day: int = Field(..., ge=1, le=31)
    payment_account_id: int


class CreditCardUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    limit_amount: Decimal | None = Field(None, gt=Decimal("0"))
    closing_day: int | None = Field(None, ge=1, le=31)
    due_day: int | None = Field(None, ge=1, le=31)
    payment_account_id: int | None = None


class CreditCardResponse(BaseModel):
    id: int
    user_id: int
    payment_account_id: int
    name: str
    limit_amount: Decimal
    closing_day: int
    due_day: int
    is_archived: bool
    used_limit: Decimal
    available_limit: Decimal


class CardPurchaseCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"))
    description: str | None = Field(None, max_length=500)
    category_id: int | None = None
    occurred_on: date


class CardPurchaseResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: int | None
    credit_card_id: int
    statement_id: int
    type: str
    amount: Decimal
    description: str | None
    occurred_on: date
    origin: str
    is_deleted: bool

    model_config = {"from_attributes": True}


class StatementPaymentCreate(BaseModel):
    paid_on: date


class BillingStatementResponse(BaseModel):
    id: int
    user_id: int
    credit_card_id: int
    period_start: date
    period_end: date
    due_on: date
    total_amount: Decimal
    paid_amount: Decimal
    status: str
    paid_on: date | None

    model_config = {"from_attributes": True}


class InstallmentPlanCreate(BaseModel):
    type: str = Field(..., min_length=1)
    account_id: int
    category_id: int | None = None
    amount: Decimal = Field(..., gt=Decimal("0"))
    installments_count: int = Field(..., ge=2, le=120)
    description: str | None = Field(None, max_length=500)
    first_due_on: date

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in TRANSACTION_CREATE_TYPES:
            raise ValueError(
                f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}"
            )
        return v


class InstallmentResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    sequence: int
    amount: Decimal
    due_on: date
    status: str
    transaction_id: int | None

    model_config = {"from_attributes": True}


class InstallmentPlanResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    installments_count: int
    description: str | None
    installments: list[InstallmentResponse]

    model_config = {"from_attributes": True}


class RecurringRuleCreate(BaseModel):
    type: str = Field(..., min_length=1)
    account_id: int
    category_id: int | None = None
    amount: Decimal = Field(..., gt=Decimal("0"))
    description: str | None = Field(None, max_length=500)
    frequency: str = Field(..., pattern="^monthly$")
    next_occurrence_on: date

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in TRANSACTION_CREATE_TYPES:
            raise ValueError(
                f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}"
            )
        return v


class RecurringRuleConfirm(BaseModel):
    amount: Decimal | None = Field(None, gt=Decimal("0"))
    occurred_on: date | None = None


class RecurringRuleResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    description: str | None
    frequency: str
    next_occurrence_on: date
    last_transaction_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class DashboardAccountSummary(BaseModel):
    id: int
    name: str
    type: str
    current_balance: Decimal


class DashboardCashFlowPoint(BaseModel):
    month: str
    income: Decimal
    expense: Decimal


class DashboardResponse(BaseModel):
    total_balance: Decimal
    period_income: Decimal
    period_expenses: Decimal
    open_statement_total: Decimal
    accounts: list[DashboardAccountSummary]
    open_statements: list[BillingStatementResponse]
    upcoming_due: list[BillingStatementResponse]
    recent_transactions: list[TransactionResponse]
    cash_flow: list[DashboardCashFlowPoint]

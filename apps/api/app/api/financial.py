from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_verified_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.financial import (
    AccountCreate,
    AccountBalanceResponse,
    AccountResponse,
    AccountUpdate,
    BillingStatementResponse,
    CardPurchaseCreate,
    CardPurchaseResponse,
    CategoryCreate,
    CategoryDeleteResponse,
    CategoryResponse,
    CategoryUpdate,
    CreditCardCreate,
    CreditCardResponse,
    CreditCardUpdate,
    DashboardResponse,
    DemoDatasetResponse,
    InstallmentPlanCreate,
    InstallmentPlanResponse,
    InstallmentResponse,
    RecurringRuleConfirm,
    RecurringRuleCreate,
    RecurringRuleResponse,
    StatementPaymentCreate,
    TransactionCreate,
    TransactionResponse,
    TransferCreate,
    TransferResponse,
)
from app.services import financial_service as fs
from app.services import demo_dataset_service as demo_service

router = APIRouter(prefix="/financial", tags=["financial"])


@router.get("/demo-dataset", response_model=DemoDatasetResponse)
def get_demo_dataset(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return demo_service.get_demo_dataset_status(db, current_user.id)


@router.post("/demo-dataset", response_model=DemoDatasetResponse, status_code=201)
def install_demo_dataset(
    response: Response,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    state, created = demo_service.install_demo_dataset(db, current_user.id)
    response.status_code = 201 if created else 200
    return state


@router.delete("/demo-dataset", response_model=DemoDatasetResponse)
def clean_demo_dataset(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return demo_service.clean_demo_dataset(db, current_user.id)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    start_date: date | None = None,
    end_date: date | None = None,
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.get_dashboard(db, current_user.id, start_date, end_date, months)


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.list_accounts(db, current_user.id)


@router.post("/accounts", response_model=AccountResponse, status_code=201)
def create_account(
    body: AccountCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_account(
        db,
        current_user.id,
        body.name,
        body.type,
        str(body.initial_balance),
        body.color,
        body.icon,
    )


@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    body: AccountUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.update_account(
        db, current_user.id, account_id, **body.model_dump(exclude_none=True)
    )


@router.delete("/accounts/{account_id}", response_model=AccountResponse)
def archive_account(
    account_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.archive_account(db, current_user.id, account_id)


@router.get("/accounts/{account_id}/balance", response_model=AccountBalanceResponse)
def get_account_balance(
    account_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return {
        "account_id": account_id,
        "current_balance": fs.get_account_balance(db, current_user.id, account_id),
    }


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    tree = fs.get_category_tree(db, current_user.id)
    return tree


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CategoryCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_category(
        db, current_user.id, body.name, body.parent_id, body.color, body.icon
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.update_category(
        db, current_user.id, category_id, **body.model_dump(exclude_unset=True)
    )


@router.delete("/categories/{category_id}", response_model=CategoryDeleteResponse)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.delete_or_archive_category(db, current_user.id, category_id)


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    type: str | None = Query(default=None),
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.list_transactions(
        db,
        current_user.id,
        transaction_type=type,
        account_id=account_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_transaction(
        db,
        current_user.id,
        body.type,
        body.account_id,
        body.category_id,
        body.amount,
        body.description,
        body.occurred_on,
        body.origin,
    )


@router.delete("/transactions/{transaction_id}", response_model=TransactionResponse)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.delete_transaction(db, current_user.id, transaction_id)


@router.get("/transfers", response_model=list[TransferResponse])
def list_transfers(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.list_transfers(db, current_user.id)


@router.post("/transfers", response_model=TransferResponse, status_code=201)
def create_transfer(
    body: TransferCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_transfer(
        db,
        current_user.id,
        body.from_account_id,
        body.to_account_id,
        body.amount,
        body.description,
        body.occurred_on,
    )


@router.get("/credit-cards", response_model=list[CreditCardResponse])
def list_credit_cards(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.list_credit_cards(db, current_user.id)


@router.post("/credit-cards", response_model=CreditCardResponse, status_code=201)
def create_credit_card(
    body: CreditCardCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_credit_card(
        db,
        current_user.id,
        body.name,
        body.limit_amount,
        body.closing_day,
        body.due_day,
        body.payment_account_id,
    )


@router.put("/credit-cards/{card_id}", response_model=CreditCardResponse)
def update_credit_card(
    card_id: int,
    body: CreditCardUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.update_credit_card(
        db, current_user.id, card_id, **body.model_dump(exclude_unset=True)
    )


@router.delete("/credit-cards/{card_id}", response_model=CreditCardResponse)
def archive_credit_card(
    card_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.archive_credit_card(db, current_user.id, card_id)


@router.post(
    "/credit-cards/{card_id}/purchases",
    response_model=CardPurchaseResponse,
    status_code=201,
)
def create_card_purchase(
    card_id: int,
    body: CardPurchaseCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_card_purchase(
        db,
        current_user.id,
        card_id,
        body.amount,
        body.description,
        body.category_id,
        body.occurred_on,
    )


@router.post("/statements/{statement_id}/pay", response_model=BillingStatementResponse)
def pay_statement(
    statement_id: int,
    body: StatementPaymentCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.pay_statement(db, current_user.id, statement_id, body.paid_on)


@router.get("/installment-plans", response_model=list[InstallmentPlanResponse])
def list_installment_plans(
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.list_installment_plans(db, current_user.id)


@router.post(
    "/installment-plans", response_model=InstallmentPlanResponse, status_code=201
)
def create_installment_plan(
    body: InstallmentPlanCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_installment_plan(
        db,
        current_user.id,
        body.type,
        body.account_id,
        body.category_id,
        body.amount,
        body.installments_count,
        body.description,
        body.first_due_on,
    )


@router.post("/installments/{installment_id}/confirm", response_model=InstallmentResponse)
def confirm_installment(
    installment_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.confirm_installment(db, current_user.id, installment_id)


@router.post("/recurring-rules", response_model=RecurringRuleResponse, status_code=201)
def create_recurring_rule(
    body: RecurringRuleCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.create_recurring_rule(
        db,
        current_user.id,
        body.type,
        body.account_id,
        body.category_id,
        body.amount,
        body.description,
        body.frequency,
        body.next_occurrence_on,
    )


@router.post(
    "/recurring-rules/{rule_id}/confirm", response_model=RecurringRuleResponse
)
def confirm_recurring_rule(
    rule_id: int,
    body: RecurringRuleConfirm,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    return fs.confirm_recurring_rule(
        db, current_user.id, rule_id, body.amount, body.occurred_on
    )

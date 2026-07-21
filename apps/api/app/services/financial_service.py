from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from app.models.action_proposal import ActionProposal
from app.models.audit_event import AuditEvent
from app.models.billing_statement import BillingStatement
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.financial_account import FinancialAccount
from app.models.installment import Installment
from app.models.installment_plan import InstallmentPlan
from app.models.recurring_rule import RecurringRule
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.models.user import User

ACCOUNT_TYPES = {"checking", "savings", "wallet", "investment"}
TRANSACTION_TYPES = {
    "income",
    "expense",
    "transfer_out",
    "transfer_in",
    "card_purchase",
    "statement_payment",
}
TRANSACTION_CREATE_TYPES = {"income", "expense"}


def _not_found(entity: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} not found",
    )


def _conflict(entity: str, name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"A {entity.lower()} with the name '{name}' already exists",
    )


def create_account(
    db: Session, user_id: int, name: str, account_type: str, initial_balance: str, color: str | None, icon: str | None
) -> FinancialAccount:
    if account_type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type must be one of: {', '.join(sorted(ACCOUNT_TYPES))}",
        )
    existing = (
        db.query(FinancialAccount)
        .filter(FinancialAccount.user_id == user_id, FinancialAccount.name == name)
        .first()
    )
    if existing:
        raise _conflict("account", name)
    account = FinancialAccount(
        user_id=user_id,
        name=name,
        type=account_type,
        initial_balance=initial_balance,
        color=color,
        icon=icon,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(
    db: Session, user_id: int, account_id: int, **kwargs
) -> FinancialAccount:
    account = (
        db.query(FinancialAccount)
        .filter(FinancialAccount.id == account_id, FinancialAccount.user_id == user_id)
        .first()
    )
    if not account:
        raise _not_found("Account")

    if "type" in kwargs and kwargs["type"] is not None:
        if kwargs["type"] not in ACCOUNT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type must be one of: {', '.join(sorted(ACCOUNT_TYPES))}",
            )

    if "name" in kwargs and kwargs["name"] is not None:
        existing = (
            db.query(FinancialAccount)
            .filter(
                FinancialAccount.user_id == user_id,
                FinancialAccount.name == kwargs["name"],
                FinancialAccount.id != account_id,
            )
            .first()
        )
        if existing:
            raise _conflict("Account", kwargs["name"])

    for field, value in kwargs.items():
        if value is not None:
            setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


def archive_account(db: Session, user_id: int, account_id: int) -> FinancialAccount:
    return update_account(db, user_id, account_id, is_archived=True)


def list_accounts(db: Session, user_id: int) -> list[FinancialAccount]:
    return (
        db.query(FinancialAccount)
        .filter(FinancialAccount.user_id == user_id)
        .all()
    )


def get_dashboard(
    db: Session,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    months: int = 6,
) -> dict:
    accounts = list_accounts(db, user_id)
    account_summaries = []
    total_balance = Decimal("0.00")
    for account in accounts:
        balance = get_account_balance(db, user_id, account.id)
        total_balance += balance
        account_summaries.append(
            {
                "id": account.id,
                "name": account.name,
                "type": account.type,
                "current_balance": balance,
            }
        )

    period_query = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_deleted.is_(False),
    )
    if start_date is not None:
        period_query = period_query.filter(Transaction.occurred_on >= start_date)
    if end_date is not None:
        period_query = period_query.filter(Transaction.occurred_on <= end_date)
    period_transactions = period_query.all()

    period_income = sum(
        Decimal(tx.amount) for tx in period_transactions if tx.type == "income"
    )
    period_expenses = sum(
        Decimal(tx.amount)
        for tx in period_transactions
        if tx.type in {"expense", "card_purchase"}
    )

    open_statements = (
        db.query(BillingStatement)
        .filter(
            BillingStatement.user_id == user_id,
            BillingStatement.status != "paid",
        )
        .order_by(BillingStatement.due_on.asc())
        .all()
    )
    recent_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
        )
        .order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
        .limit(10)
        .all()
    )

    series_end = end_date or date.today()
    month_index = series_end.year * 12 + series_end.month - 1 - (months - 1)
    series_start = date(month_index // 12, month_index % 12 + 1, 1)
    series_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            Transaction.occurred_on >= series_start,
            Transaction.occurred_on <= series_end,
        )
        .all()
    )
    cash_flow_by_month: dict[str, dict[str, Decimal]] = {}
    for offset in range(months):
        current_index = month_index + offset
        key = f"{current_index // 12:04d}-{current_index % 12 + 1:02d}"
        cash_flow_by_month[key] = {
            "income": Decimal("0.00"),
            "expense": Decimal("0.00"),
        }
    for transaction in series_transactions:
        key = transaction.occurred_on.strftime("%Y-%m")
        if transaction.type == "income":
            cash_flow_by_month[key]["income"] += Decimal(transaction.amount)
        elif transaction.type in {"expense", "card_purchase"}:
            cash_flow_by_month[key]["expense"] += Decimal(transaction.amount)

    open_statement_total = sum(
        (
            Decimal(statement.total_amount) - Decimal(statement.paid_amount)
            for statement in open_statements
        ),
        Decimal("0.00"),
    )

    return {
        "total_balance": total_balance,
        "period_income": period_income,
        "period_expenses": period_expenses,
        "open_statement_total": open_statement_total,
        "accounts": account_summaries,
        "open_statements": open_statements,
        "upcoming_due": open_statements[:5],
        "recent_transactions": recent_transactions,
        "cash_flow": [
            {"month": month, **values}
            for month, values in cash_flow_by_month.items()
        ],
    }


def get_account(db: Session, user_id: int, account_id: int) -> FinancialAccount:
    account = (
        db.query(FinancialAccount)
        .filter(FinancialAccount.id == account_id, FinancialAccount.user_id == user_id)
        .first()
    )
    if not account:
        raise _not_found("Account")
    return account


def create_category(
    db: Session, user_id: int, name: str, parent_id: int | None, color: str | None, icon: str | None
) -> Category:
    existing = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.name == name)
        .first()
    )
    if existing:
        raise _conflict("Category", name)
    if parent_id is not None:
        parent = (
            db.query(Category)
            .filter(Category.id == parent_id, Category.user_id == user_id)
            .first()
        )
        if not parent:
            raise _not_found("Parent category")
    category = Category(
        user_id=user_id,
        name=name,
        parent_id=parent_id,
        color=color,
        icon=icon,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, user_id: int, category_id: int, **kwargs
) -> Category:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise _not_found("Category")

    if "name" in kwargs and kwargs["name"] is not None:
        existing = (
            db.query(Category)
            .filter(
                Category.user_id == user_id,
                Category.name == kwargs["name"],
                Category.id != category_id,
            )
            .first()
        )
        if existing:
            raise _conflict("Category", kwargs["name"])

    if "parent_id" in kwargs and kwargs["parent_id"] is not None:
        if kwargs["parent_id"] == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category cannot be its own parent",
            )
        parent = (
            db.query(Category)
            .filter(Category.id == kwargs["parent_id"], Category.user_id == user_id)
            .first()
        )
        if not parent:
            raise _not_found("Parent category")
        descendant_ids = _get_descendant_ids(db, user_id, category_id)
        if kwargs["parent_id"] in descendant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set a child category as parent",
            )

    nullable_fields = {"parent_id", "color", "icon"}
    for field, value in kwargs.items():
        if value is not None or field in nullable_fields:
            setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def _get_descendant_ids(db: Session, user_id: int, category_id: int) -> set[int]:
    children = (
        db.query(Category)
        .filter(Category.parent_id == category_id, Category.user_id == user_id)
        .all()
    )
    ids = set()
    for child in children:
        ids.add(child.id)
        ids |= _get_descendant_ids(db, user_id, child.id)
    return ids


def _category_snapshot(categories: list[Category], category_id: int) -> dict:
    snapshots = {
        category.id: {
            "id": category.id,
            "user_id": category.user_id,
            "name": category.name,
            "parent_id": category.parent_id,
            "color": category.color,
            "icon": category.icon,
            "is_archived": category.is_archived,
            "children": [],
        }
        for category in categories
    }
    for category in categories:
        if category.parent_id in snapshots:
            snapshots[category.parent_id]["children"].append(snapshots[category.id])
    return snapshots[category_id]


def _proposal_references_categories(value: object, category_ids: set[int], key: str = "") -> bool:
    if isinstance(value, dict):
        return any(
            _proposal_references_categories(child, category_ids, child_key)
            for child_key, child in value.items()
        )
    if isinstance(value, list):
        return any(_proposal_references_categories(child, category_ids, key) for child in value)
    normalized_key = key.lower().replace("_", "")
    if not (
        normalized_key.endswith("categoryid")
        or normalized_key.endswith("categoryids")
    ):
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value in category_ids
    return isinstance(value, str) and value.isdigit() and int(value) in category_ids


def delete_or_archive_category(db: Session, user_id: int, category_id: int) -> dict:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise _not_found("Category")

    descendant_ids = _get_descendant_ids(db, user_id, category.id)
    category_ids = {category.id, *descendant_ids}
    categories = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.id.in_(category_ids))
        .all()
    )
    dependency_kinds: set[str] = set()
    if descendant_ids:
        dependency_kinds.add("child_categories")
    if (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.category_id.in_(category_ids))
        .first()
    ):
        dependency_kinds.add("transactions")
    if (
        db.query(InstallmentPlan)
        .filter(InstallmentPlan.user_id == user_id, InstallmentPlan.category_id.in_(category_ids))
        .first()
    ):
        dependency_kinds.add("installment_plans")
    if (
        db.query(RecurringRule)
        .filter(RecurringRule.user_id == user_id, RecurringRule.category_id.in_(category_ids))
        .first()
    ):
        dependency_kinds.add("recurring_rules")
    proposals = (
        db.query(ActionProposal)
        .filter(ActionProposal.user_id == user_id, ActionProposal.status.in_(("proposed", "confirmed")))
        .all()
    )
    if any(_proposal_references_categories(proposal.payload, category_ids) for proposal in proposals):
        dependency_kinds.add("action_proposals")

    if dependency_kinds:
        for item in categories:
            item.is_archived = True
        action = "archived"
        event_type = "category.archived"
    else:
        action = "deleted"
        event_type = "category.deleted"

    snapshot = _category_snapshot(categories, category.id)
    payload = {"action": action, "category_ids": sorted(category_ids)}
    payload.update({kind: True for kind in sorted(dependency_kinds)})
    db.add(
        AuditEvent(
            user_id=user_id,
            event_type=event_type,
            entity_type="category",
            entity_id=category.id,
            payload=payload,
        )
    )
    if action == "deleted":
        db.delete(category)
    db.commit()
    return {"action": action, "category": snapshot}


def get_category_tree(db: Session, user_id: int) -> list[Category]:
    all_categories = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.is_archived.is_(False))
        .all()
    )
    for category in all_categories:
        set_committed_value(
            category,
            "children",
            [child for child in all_categories if child.parent_id == category.id],
        )
    roots = [category for category in all_categories if category.parent_id is None]
    return roots


def create_transaction(
    db: Session,
    user_id: int,
    transaction_type: str,
    account_id: int,
    category_id: int | None,
    amount: Decimal,
    description: str | None,
    occurred_on: date,
    origin: str,
) -> Transaction:
    if transaction_type not in TRANSACTION_CREATE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}",
        )
    get_account(db, user_id, account_id)
    _validate_category(db, user_id, category_id)
    transaction = Transaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=transaction_type,
        amount=amount,
        description=description,
        occurred_on=occurred_on,
        origin=origin,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def list_transactions(
    db: Session,
    user_id: int,
    transaction_type: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Transaction]:
    query = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_deleted.is_(False),
    )
    if transaction_type is not None:
        if transaction_type not in TRANSACTION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type must be one of: {', '.join(sorted(TRANSACTION_TYPES))}",
            )
        query = query.filter(Transaction.type == transaction_type)
    if account_id is not None:
        get_account(db, user_id, account_id)
        query = query.filter(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if start_date is not None:
        query = query.filter(Transaction.occurred_on >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.occurred_on <= end_date)
    return query.order_by(Transaction.occurred_on.desc(), Transaction.id.desc()).all()


def delete_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
        .first()
    )
    if not transaction:
        raise _not_found("Transaction")
    transaction.is_deleted = True
    db.commit()
    db.refresh(transaction)
    return transaction


def get_account_balance(db: Session, user_id: int, account_id: int) -> Decimal:
    account = get_account(db, user_id, account_id)
    balance = Decimal(account.initial_balance)
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.account_id == account_id,
            Transaction.is_deleted.is_(False),
        )
        .all()
    )
    for transaction in transactions:
        amount = Decimal(transaction.amount)
        if transaction.type == "income":
            balance += amount
        elif transaction.type in {"expense", "transfer_out", "statement_payment"}:
            balance -= amount
        elif transaction.type == "transfer_in":
            balance += amount
    return balance


def create_transfer(
    db: Session,
    user_id: int,
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    description: str | None,
    occurred_on: date,
) -> Transfer:
    if from_account_id == to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer accounts must be different",
        )
    get_account(db, user_id, from_account_id)
    get_account(db, user_id, to_account_id)

    out_transaction = Transaction(
        user_id=user_id,
        account_id=from_account_id,
        category_id=None,
        type="transfer_out",
        amount=amount,
        description=description,
        occurred_on=occurred_on,
        origin="transfer",
    )
    in_transaction = Transaction(
        user_id=user_id,
        account_id=to_account_id,
        category_id=None,
        type="transfer_in",
        amount=amount,
        description=description,
        occurred_on=occurred_on,
        origin="transfer",
    )
    db.add_all([out_transaction, in_transaction])
    db.flush()

    transfer = Transfer(
        user_id=user_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        out_transaction_id=out_transaction.id,
        in_transaction_id=in_transaction.id,
        amount=amount,
        description=description,
        occurred_on=occurred_on,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


def list_transfers(db: Session, user_id: int) -> list[Transfer]:
    return (
        db.query(Transfer)
        .filter(Transfer.user_id == user_id)
        .order_by(Transfer.occurred_on.desc(), Transfer.id.desc())
        .all()
    )


def _valid_day(year: int, month: int, requested_day: int) -> date:
    return date(year, month, min(requested_day, monthrange(year, month)[1]))


def _month_shift(day: date, months: int) -> date:
    index = day.year * 12 + day.month - 1 + months
    return _valid_day(index // 12, index % 12 + 1, day.day)


def _statement_cycle(
    occurred_on: date, closing_day: int, due_day: int
) -> tuple[date, date, date]:
    current_close = _valid_day(occurred_on.year, occurred_on.month, closing_day)
    next_month = _month_shift(current_close, 1)
    period_end = (
        current_close
        if occurred_on <= current_close
        else _valid_day(next_month.year, next_month.month, closing_day)
    )
    previous_month = _month_shift(period_end, -1)
    period_start = (
        _valid_day(previous_month.year, previous_month.month, closing_day)
        + timedelta(days=1)
    )
    same_month_due = _valid_day(period_end.year, period_end.month, due_day)
    if same_month_due > period_end:
        due_on = same_month_due
    else:
        following_month = _month_shift(period_end, 1)
        due_on = _valid_day(following_month.year, following_month.month, due_day)
    return period_start, period_end, due_on


def _get_card(db: Session, user_id: int, card_id: int) -> CreditCard:
    card = (
        db.query(CreditCard)
        .filter(CreditCard.id == card_id, CreditCard.user_id == user_id)
        .first()
    )
    if not card:
        raise _not_found("Credit card")
    return card


def _card_used_limit(db: Session, user_id: int, card_id: int) -> Decimal:
    statements = (
        db.query(BillingStatement)
        .filter(
            BillingStatement.user_id == user_id,
            BillingStatement.credit_card_id == card_id,
            BillingStatement.status != "paid",
        )
        .all()
    )
    return sum(
        (Decimal(statement.total_amount) - Decimal(statement.paid_amount))
        for statement in statements
    )


def _card_response(db: Session, card: CreditCard) -> dict:
    used_limit = _card_used_limit(db, card.user_id, card.id)
    limit_amount = Decimal(card.limit_amount)
    return {
        "id": card.id,
        "user_id": card.user_id,
        "payment_account_id": card.payment_account_id,
        "name": card.name,
        "limit_amount": limit_amount,
        "closing_day": card.closing_day,
        "due_day": card.due_day,
        "is_archived": card.is_archived,
        "used_limit": used_limit,
        "available_limit": limit_amount - used_limit,
    }


def _has_active_card_name_conflict(
    db: Session, user_id: int, name: str, card_id: int | None = None
) -> bool:
    cards = (
        db.query(CreditCard)
        .filter(
            CreditCard.user_id == user_id,
            CreditCard.is_archived.is_(False),
        )
        .all()
    )
    normalized_name = name.strip().casefold()
    return any(
        card.id != card_id and card.name.strip().casefold() == normalized_name
        for card in cards
    )


def _lock_card_name_namespace(db: Session, user_id: int) -> None:
    (
        db.query(User)
        .filter(User.id == user_id)
        .with_for_update()
        .first()
    )


def create_credit_card(
    db: Session,
    user_id: int,
    name: str,
    limit_amount: Decimal,
    closing_day: int,
    due_day: int,
    payment_account_id: int,
) -> dict:
    get_account(db, user_id, payment_account_id)
    _lock_card_name_namespace(db, user_id)
    if _has_active_card_name_conflict(db, user_id, name):
        raise _conflict("Credit card", name)
    card = CreditCard(
        user_id=user_id,
        payment_account_id=payment_account_id,
        name=name,
        limit_amount=limit_amount,
        closing_day=closing_day,
        due_day=due_day,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return _card_response(db, card)


def list_credit_cards(db: Session, user_id: int) -> list[dict]:
    cards = (
        db.query(CreditCard)
        .filter(CreditCard.user_id == user_id)
        .order_by(CreditCard.id.asc())
        .all()
    )
    return [_card_response(db, card) for card in cards]


def update_credit_card(
    db: Session, user_id: int, card_id: int, **kwargs
) -> dict:
    card = _get_card(db, user_id, card_id)
    resulting_is_archived = kwargs.get("is_archived", card.is_archived)
    if not resulting_is_archived and ("name" in kwargs or card.is_archived):
        resulting_name = kwargs.get("name") or card.name
        _lock_card_name_namespace(db, user_id)
        if _has_active_card_name_conflict(db, user_id, resulting_name, card_id):
            raise _conflict("Credit card", resulting_name)
    if "payment_account_id" in kwargs:
        get_account(db, user_id, kwargs["payment_account_id"])
    if "limit_amount" in kwargs:
        used_limit = _card_used_limit(db, user_id, card_id)
        if Decimal(kwargs["limit_amount"]) < used_limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Card limit cannot be lower than used limit",
            )
    for field, value in kwargs.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    return _card_response(db, card)


def archive_credit_card(db: Session, user_id: int, card_id: int) -> dict:
    return update_credit_card(db, user_id, card_id, is_archived=True)


def _get_or_create_statement(
    db: Session, user_id: int, card: CreditCard, occurred_on: date
) -> BillingStatement:
    period_start, period_end, due_on = _statement_cycle(
        occurred_on, card.closing_day, card.due_day
    )
    statement = (
        db.query(BillingStatement)
        .filter(
            BillingStatement.user_id == user_id,
            BillingStatement.credit_card_id == card.id,
            BillingStatement.period_start == period_start,
            BillingStatement.period_end == period_end,
        )
        .first()
    )
    if statement:
        return statement
    statement = BillingStatement(
        user_id=user_id,
        credit_card_id=card.id,
        period_start=period_start,
        period_end=period_end,
        due_on=due_on,
        total_amount=Decimal("0.00"),
        paid_amount=Decimal("0.00"),
        status="open",
    )
    db.add(statement)
    db.flush()
    return statement


def create_card_purchase(
    db: Session,
    user_id: int,
    card_id: int,
    amount: Decimal,
    description: str | None,
    category_id: int | None,
    occurred_on: date,
) -> Transaction:
    card = _get_card(db, user_id, card_id)
    if card.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived cards cannot receive new purchases",
        )
    _validate_category(db, user_id, category_id)
    statement = _get_or_create_statement(db, user_id, card, occurred_on)
    transaction = Transaction(
        user_id=user_id,
        account_id=card.payment_account_id,
        category_id=category_id,
        credit_card_id=card.id,
        statement_id=statement.id,
        type="card_purchase",
        amount=amount,
        description=description,
        occurred_on=occurred_on,
        origin="credit_card",
    )
    statement.total_amount = Decimal(statement.total_amount) + amount
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def pay_statement(
    db: Session, user_id: int, statement_id: int, paid_on: date
) -> BillingStatement:
    statement = (
        db.query(BillingStatement)
        .filter(BillingStatement.id == statement_id, BillingStatement.user_id == user_id)
        .first()
    )
    if not statement:
        raise _not_found("Billing statement")
    if statement.status == "paid":
        return statement
    card = _get_card(db, user_id, statement.credit_card_id)
    outstanding = Decimal(statement.total_amount) - Decimal(statement.paid_amount)
    if outstanding > Decimal("0.00"):
        payment = Transaction(
            user_id=user_id,
            account_id=card.payment_account_id,
            category_id=None,
            credit_card_id=card.id,
            statement_id=statement.id,
            type="statement_payment",
            amount=outstanding,
            description=f"Payment for statement {statement.id}",
            occurred_on=paid_on,
            origin="credit_card_payment",
        )
        db.add(payment)
    statement.paid_amount = Decimal(statement.total_amount)
    statement.status = "paid"
    statement.paid_on = paid_on
    db.commit()
    db.refresh(statement)
    return statement


def _add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def _validate_category(db: Session, user_id: int, category_id: int | None) -> None:
    if category_id is None:
        return
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise _not_found("Category")
    if category.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived categories cannot receive new records",
        )


def create_installment_plan(
    db: Session,
    user_id: int,
    transaction_type: str,
    account_id: int,
    category_id: int | None,
    amount: Decimal,
    installments_count: int,
    description: str | None,
    first_due_on: date,
) -> InstallmentPlan:
    if transaction_type not in TRANSACTION_CREATE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}",
        )
    get_account(db, user_id, account_id)
    _validate_category(db, user_id, category_id)
    plan = InstallmentPlan(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=transaction_type,
        amount=amount,
        installments_count=installments_count,
        description=description,
    )
    db.add(plan)
    db.flush()

    installment_amount = (amount / Decimal(installments_count)).quantize(
        Decimal("0.01")
    )
    remaining = amount
    for sequence in range(1, installments_count + 1):
        current_amount = installment_amount
        if sequence == installments_count:
            current_amount = remaining
        installment = Installment(
            user_id=user_id,
            plan_id=plan.id,
            sequence=sequence,
            amount=current_amount,
            due_on=_add_months(first_due_on, sequence - 1),
            status="pending",
        )
        remaining -= current_amount
        db.add(installment)
    db.commit()
    db.refresh(plan)
    return plan


def list_installment_plans(db: Session, user_id: int) -> list[InstallmentPlan]:
    return (
        db.query(InstallmentPlan)
        .filter(InstallmentPlan.user_id == user_id)
        .order_by(InstallmentPlan.id.desc())
        .all()
    )


def confirm_installment(
    db: Session, user_id: int, installment_id: int
) -> Installment:
    installment = (
        db.query(Installment)
        .filter(Installment.id == installment_id, Installment.user_id == user_id)
        .first()
    )
    if not installment:
        raise _not_found("Installment")
    if installment.status == "confirmed":
        return installment
    plan = (
        db.query(InstallmentPlan)
        .filter(
            InstallmentPlan.id == installment.plan_id,
            InstallmentPlan.user_id == user_id,
        )
        .first()
    )
    if not plan:
        raise _not_found("Installment plan")
    transaction = Transaction(
        user_id=user_id,
        account_id=plan.account_id,
        category_id=plan.category_id,
        type=plan.type,
        amount=installment.amount,
        description=plan.description,
        occurred_on=installment.due_on,
        origin="installment",
    )
    db.add(transaction)
    db.flush()
    installment.status = "confirmed"
    installment.transaction_id = transaction.id
    db.commit()
    db.refresh(installment)
    return installment


def create_recurring_rule(
    db: Session,
    user_id: int,
    transaction_type: str,
    account_id: int,
    category_id: int | None,
    amount: Decimal,
    description: str | None,
    frequency: str,
    next_occurrence_on: date,
) -> RecurringRule:
    if transaction_type not in TRANSACTION_CREATE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type must be one of: {', '.join(sorted(TRANSACTION_CREATE_TYPES))}",
        )
    if frequency != "monthly":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only monthly recurrence is supported",
        )
    get_account(db, user_id, account_id)
    _validate_category(db, user_id, category_id)
    rule = RecurringRule(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=transaction_type,
        amount=amount,
        description=description,
        frequency=frequency,
        next_occurrence_on=next_occurrence_on,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def confirm_recurring_rule(
    db: Session,
    user_id: int,
    rule_id: int,
    amount: Decimal | None,
    occurred_on: date | None,
) -> RecurringRule:
    rule = (
        db.query(RecurringRule)
        .filter(RecurringRule.id == rule_id, RecurringRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise _not_found("Recurring rule")
    effective_amount = amount if amount is not None else Decimal(rule.amount)
    effective_date = occurred_on if occurred_on is not None else rule.next_occurrence_on
    transaction = Transaction(
        user_id=user_id,
        account_id=rule.account_id,
        category_id=rule.category_id,
        type=rule.type,
        amount=effective_amount,
        description=rule.description,
        occurred_on=effective_date,
        origin="recurring",
    )
    db.add(transaction)
    db.flush()
    rule.last_transaction_id = transaction.id
    rule.next_occurrence_on = _add_months(rule.next_occurrence_on, 1)
    db.commit()
    db.refresh(rule)
    return rule

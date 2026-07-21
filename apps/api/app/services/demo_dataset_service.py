from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.action_proposal import ActionProposal
from app.models.audit_event import AuditEvent
from app.models.billing_statement import BillingStatement
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.demo_dataset import DemoDataset
from app.models.financial_account import FinancialAccount
from app.models.installment_plan import InstallmentPlan
from app.models.recurring_rule import RecurringRule
from app.models.transaction import Transaction
from app.models.user import User
from app.services import financial_service as fs

DEMO_VERSION = "2026.07.v1"

_EMPTY_SUMMARY = {
    "accounts": 0,
    "cards": 0,
    "categories": 0,
    "transactions": 0,
    "recurring_rules": 0,
}


def _public_state(dataset: DemoDataset | None) -> dict:
    if dataset is None:
        return {
            "active": False,
            "version": DEMO_VERSION,
            "installed_at": None,
            "summary": dict(_EMPTY_SUMMARY),
        }
    return {
        "active": dataset.status == "active",
        "version": dataset.version,
        "installed_at": dataset.installed_at,
        "summary": dict(dataset.manifest.get("summary", _EMPTY_SUMMARY)),
    }


def _active_dataset(db: Session, user_id: int) -> DemoDataset | None:
    return (
        db.query(DemoDataset)
        .filter(
            DemoDataset.user_id == user_id,
            DemoDataset.version == DEMO_VERSION,
            DemoDataset.status == "active",
        )
        .order_by(DemoDataset.id.desc())
        .first()
    )


def _lock_namespace(db: Session, user_id: int) -> None:
    db.query(User).filter(User.id == user_id).with_for_update().one()


def _shift_month(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(index, 12)
    month = month_index + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def _audit(
    db: Session,
    user_id: int,
    event_type: str,
    dataset_id: int,
    payload: dict,
) -> None:
    db.add(
        AuditEvent(
            user_id=user_id,
            event_type=event_type,
            entity_type="DemoDataset",
            entity_id=dataset_id,
            payload=payload,
        )
    )


def _build_resources(
    db: Session, user_id: int, dataset_id: int, installed_on: date
) -> dict:
    accounts = {
        account.name: account
        for account in (
            FinancialAccount(
                user_id=user_id,
                demo_dataset_id=dataset_id,
                name="Conta principal",
                type="checking",
                initial_balance=Decimal("6450.80"),
                color="#10b981",
                icon="landmark",
            ),
            FinancialAccount(
                user_id=user_id,
                demo_dataset_id=dataset_id,
                name="Reserva",
                type="savings",
                initial_balance=Decimal("12000.00"),
                color="#0ea5e9",
                icon="piggy-bank",
            ),
            FinancialAccount(
                user_id=user_id,
                demo_dataset_id=dataset_id,
                name="Carteira",
                type="wallet",
                initial_balance=Decimal("180.00"),
                color="#f59e0b",
                icon="wallet",
            ),
        )
    }
    db.add_all(list(accounts.values()))
    db.flush()

    category_specs = (
        ("Renda", "Sal\u00e1rio", "#10b981", "badge-dollar-sign"),
        ("Moradia", "Aluguel", "#6366f1", "house"),
        ("Alimenta\u00e7\u00e3o", "Supermercado", "#f59e0b", "shopping-basket"),
        ("Transporte", "Combust\u00edvel", "#0ea5e9", "car"),
        ("Sa\u00fade", "Farm\u00e1cia", "#ef4444", "heart-pulse"),
        ("Lazer", "Entretenimento", "#ec4899", "clapperboard"),
        ("Assinaturas", "Streaming", "#8b5cf6", "repeat-2"),
    )
    categories: dict[str, Category] = {}
    roots = []
    for root_name, _, color, icon in category_specs:
        root = Category(
            user_id=user_id,
            demo_dataset_id=dataset_id,
            name=root_name,
            color=color,
            icon=icon,
        )
        roots.append(root)
        categories[root_name] = root
    db.add_all(roots)
    db.flush()
    children = []
    for root_name, child_name, color, icon in category_specs:
        child = Category(
            user_id=user_id,
            demo_dataset_id=dataset_id,
            name=child_name,
            parent_id=categories[root_name].id,
            color=color,
            icon=icon,
        )
        children.append(child)
        categories[child_name] = child
    db.add_all(children)
    db.flush()

    primary = accounts["Conta principal"]
    card = CreditCard(
        user_id=user_id,
        demo_dataset_id=dataset_id,
        payment_account_id=primary.id,
        name="Cart\u00e3o principal",
        limit_amount=Decimal("7000.00"),
        closing_day=10,
        due_day=17,
        is_archived=False,
    )
    db.add(card)
    db.flush()

    period_start, period_end, due_on = fs._statement_cycle(
        installed_on, card.closing_day, card.due_day
    )
    statement = BillingStatement(
        user_id=user_id,
        demo_dataset_id=dataset_id,
        credit_card_id=card.id,
        period_start=period_start,
        period_end=period_end,
        due_on=due_on,
        total_amount=Decimal("735.80"),
        paid_amount=Decimal("0.00"),
        status="open",
    )
    db.add(statement)
    db.flush()

    previous_month = _shift_month(installed_on, -1)
    regular_specs = (
        ("income", "8200.00", "Sal\u00e1rio", "Sal\u00e1rio mensal", previous_month),
        ("income", "950.00", "Renda", "Renda extra", installed_on),
        ("expense", "1800.00", "Aluguel", "Aluguel", previous_month),
        ("expense", "420.30", "Supermercado", "Compras do m\u00eas", installed_on),
        ("expense", "280.00", "Combust\u00edvel", "Combust\u00edvel", previous_month),
        ("expense", "89.90", "Farm\u00e1cia", "Farm\u00e1cia", installed_on),
        ("expense", "120.00", "Entretenimento", "Cinema e lazer", installed_on),
        ("expense", "49.90", "Streaming", "Streaming", previous_month),
    )
    transactions = [
        Transaction(
            user_id=user_id,
            demo_dataset_id=dataset_id,
            account_id=primary.id,
            category_id=categories[category_name].id,
            type=transaction_type,
            amount=Decimal(amount),
            description=description,
            occurred_on=occurred_on,
            origin="demo",
        )
        for transaction_type, amount, category_name, description, occurred_on in regular_specs
    ]
    card_specs = (
        ("360.40", "Supermercado", "Compra no cart\u00e3o"),
        ("210.00", "Combust\u00edvel", "Abastecimento no cart\u00e3o"),
        ("89.90", "Farm\u00e1cia", "Farm\u00e1cia no cart\u00e3o"),
        ("75.50", "Entretenimento", "Lazer no cart\u00e3o"),
    )
    transactions.extend(
        Transaction(
            user_id=user_id,
            demo_dataset_id=dataset_id,
            account_id=primary.id,
            category_id=categories[category_name].id,
            credit_card_id=card.id,
            statement_id=statement.id,
            type="card_purchase",
            amount=Decimal(amount),
            description=description,
            occurred_on=installed_on,
            origin="demo",
        )
        for amount, category_name, description in card_specs
    )
    db.add_all(transactions)
    db.flush()

    recurring_rule = RecurringRule(
        user_id=user_id,
        demo_dataset_id=dataset_id,
        account_id=primary.id,
        category_id=categories["Streaming"].id,
        type="expense",
        amount=Decimal("49.90"),
        description="Assinatura de streaming",
        frequency="monthly",
        next_occurrence_on=_shift_month(installed_on, 1),
        is_active=True,
    )
    db.add(recurring_rule)
    db.flush()

    summary = {
        "accounts": len(accounts),
        "cards": 1,
        "categories": len(categories),
        "transactions": len(transactions),
        "recurring_rules": 1,
    }
    return {
        "summary": summary,
        "resource_ids": {
            "accounts": [account.id for account in accounts.values()],
            "cards": [card.id],
            "categories": [category.id for category in categories.values()],
            "statements": [statement.id],
            "transactions": [transaction.id for transaction in transactions],
            "recurring_rules": [recurring_rule.id],
        },
    }


def get_demo_dataset_status(db: Session, user_id: int) -> dict:
    return _public_state(_active_dataset(db, user_id))


def install_demo_dataset(
    db: Session, user_id: int, installed_on: date | None = None
) -> tuple[dict, bool]:
    try:
        _lock_namespace(db, user_id)
        existing = _active_dataset(db, user_id)
        if existing is not None:
            return _public_state(existing), False

        dataset = DemoDataset(
            user_id=user_id,
            version=DEMO_VERSION,
            status="installing",
            manifest={},
        )
        db.add(dataset)
        db.flush()
        manifest = _build_resources(
            db, user_id, dataset.id, installed_on or date.today()
        )
        dataset.status = "active"
        dataset.installed_at = datetime.now(timezone.utc)
        dataset.manifest = manifest
        _audit(
            db,
            user_id,
            "demo_dataset.installed",
            dataset.id,
            {"version": DEMO_VERSION, "counts": manifest["summary"]},
        )
        db.commit()
        return _public_state(dataset), True
    except IntegrityError:
        db.rollback()
        existing = _active_dataset(db, user_id)
        if existing is not None:
            return _public_state(existing), False
        raise
    except Exception:
        db.rollback()
        raise


def _has_row(query) -> bool:
    return query.first() is not None


def _not_owned(column, dataset_id: int):
    return or_(column.is_(None), column != dataset_id)


def clean_demo_dataset(db: Session, user_id: int) -> dict:
    try:
        _lock_namespace(db, user_id)
        dataset = (
            db.query(DemoDataset)
            .filter(
                DemoDataset.user_id == user_id,
                DemoDataset.version == DEMO_VERSION,
                DemoDataset.status == "active",
            )
            .with_for_update()
            .first()
        )
        if dataset is None:
            return _public_state(None)

        dataset.status = "cleaning"
        db.flush()
        removed = {
            "transactions": 0,
            "recurring_rules": 0,
            "statements": 0,
            "cards": 0,
            "accounts": 0,
            "categories": 0,
        }
        preserved = dict.fromkeys(removed, 0)

        demo_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.demo_dataset_id == dataset.id,
            )
            .all()
        )
        for transaction in demo_transactions:
            db.delete(transaction)
        removed["transactions"] = len(demo_transactions)

        demo_rules = (
            db.query(RecurringRule)
            .filter(
                RecurringRule.user_id == user_id,
                RecurringRule.demo_dataset_id == dataset.id,
            )
            .all()
        )
        for rule in demo_rules:
            db.delete(rule)
        removed["recurring_rules"] = len(demo_rules)
        db.flush()

        demo_statements = (
            db.query(BillingStatement)
            .filter(
                BillingStatement.user_id == user_id,
                BillingStatement.demo_dataset_id == dataset.id,
            )
            .all()
        )
        for statement in demo_statements:
            adopted = _has_row(
                db.query(Transaction.id).filter(
                    Transaction.user_id == user_id,
                    Transaction.statement_id == statement.id,
                    _not_owned(Transaction.demo_dataset_id, dataset.id),
                )
            )
            if adopted:
                statement.demo_dataset_id = None
                preserved["statements"] += 1
            else:
                db.delete(statement)
                removed["statements"] += 1
        db.flush()

        demo_cards = (
            db.query(CreditCard)
            .filter(
                CreditCard.user_id == user_id,
                CreditCard.demo_dataset_id == dataset.id,
            )
            .all()
        )
        for card in demo_cards:
            adopted = _has_row(
                db.query(Transaction.id).filter(
                    Transaction.user_id == user_id,
                    Transaction.credit_card_id == card.id,
                    _not_owned(Transaction.demo_dataset_id, dataset.id),
                )
            ) or _has_row(
                db.query(BillingStatement.id).filter(
                    BillingStatement.user_id == user_id,
                    BillingStatement.credit_card_id == card.id,
                    _not_owned(BillingStatement.demo_dataset_id, dataset.id),
                )
            )
            if adopted:
                card.demo_dataset_id = None
                preserved["cards"] += 1
            else:
                db.delete(card)
                removed["cards"] += 1
        db.flush()

        demo_accounts = (
            db.query(FinancialAccount)
            .filter(
                FinancialAccount.user_id == user_id,
                FinancialAccount.demo_dataset_id == dataset.id,
            )
            .all()
        )
        for account in demo_accounts:
            adopted = any(
                (
                    _has_row(
                        db.query(model.id).filter(
                            model.user_id == user_id,
                            account_column == account.id,
                        )
                    )
                    for model, account_column in (
                        (Transaction, Transaction.account_id),
                        (CreditCard, CreditCard.payment_account_id),
                        (RecurringRule, RecurringRule.account_id),
                        (InstallmentPlan, InstallmentPlan.account_id),
                    )
                )
            )
            if adopted:
                account.demo_dataset_id = None
                preserved["accounts"] += 1
            else:
                db.delete(account)
                removed["accounts"] += 1
        db.flush()

        demo_categories = (
            db.query(Category)
            .filter(
                Category.user_id == user_id,
                Category.demo_dataset_id == dataset.id,
            )
            .all()
        )
        original_parent = {category.id: category.parent_id for category in demo_categories}
        by_id = {category.id: category for category in demo_categories}

        def depth(category: Category) -> int:
            value = 0
            parent_id = category.parent_id
            while parent_id in by_id:
                value += 1
                parent_id = by_id[parent_id].parent_id
            return value

        pending_proposals = (
            db.query(ActionProposal)
            .filter(
                ActionProposal.user_id == user_id,
                ActionProposal.status.in_(("proposed", "confirmed")),
            )
            .all()
        )
        preserved_category_ids: set[int] = set()
        for category in sorted(demo_categories, key=depth, reverse=True):
            adopted = (
                _has_row(
                    db.query(Transaction.id).filter(
                        Transaction.user_id == user_id,
                        Transaction.category_id == category.id,
                    )
                )
                or _has_row(
                    db.query(InstallmentPlan.id).filter(
                        InstallmentPlan.user_id == user_id,
                        InstallmentPlan.category_id == category.id,
                    )
                )
                or _has_row(
                    db.query(RecurringRule.id).filter(
                        RecurringRule.user_id == user_id,
                        RecurringRule.category_id == category.id,
                    )
                )
                or any(
                    fs._proposal_references_categories(proposal.payload, {category.id})
                    for proposal in pending_proposals
                )
                or any(
                    original_parent.get(child_id) == category.id
                    for child_id in preserved_category_ids
                )
            )
            if adopted:
                category.demo_dataset_id = None
                preserved_category_ids.add(category.id)
                preserved["categories"] += 1
            else:
                db.delete(category)
                removed["categories"] += 1
        db.flush()

        dataset.status = "removed"
        dataset.removed_at = datetime.now(timezone.utc)
        dataset.manifest = {}
        _audit(
            db,
            user_id,
            "demo_dataset.cleaned",
            dataset.id,
            {"removed": removed, "preserved": preserved},
        )
        db.commit()
        return _public_state(None)
    except Exception:
        db.rollback()
        raise

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BillingStatement(Base):
    __tablename__ = "billing_statements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["demo_dataset_id"],
            ["demo_datasets.id"],
            name="fk_billing_statements_demo_dataset",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["demo_dataset_id", "user_id"],
            ["demo_datasets.id", "demo_datasets.user_id"],
            name="fk_billing_statements_demo_dataset_user",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    demo_dataset_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    credit_card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    paid_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    demo_dataset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("demo_datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    credit_card_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("credit_cards.id", ondelete="SET NULL"), nullable=True
    )
    statement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("billing_statements.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["FinancialAccount"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")

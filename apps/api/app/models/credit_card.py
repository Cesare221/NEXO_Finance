from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CreditCard(Base):
    __tablename__ = "credit_cards"

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
    payment_account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

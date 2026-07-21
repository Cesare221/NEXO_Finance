from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DemoDataset(Base):
    __tablename__ = "demo_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="installing")
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    installed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

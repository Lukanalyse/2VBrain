from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class ObjectConnection(Base):
    __tablename__ = "object_connections"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "target_id",
            "relation_type",
            name="uq_object_connection",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

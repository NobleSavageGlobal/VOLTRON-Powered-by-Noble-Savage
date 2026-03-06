from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    """Use JSONB on PostgreSQL, JSON on other DBs (e.g. SQLite for tests)."""
    return sa.JSON().with_variant(JSONB(), "postgresql")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
    settings: Mapped[dict] = mapped_column(_json_col(), nullable=False, default=dict)

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="organization")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="organization")  # noqa: F821

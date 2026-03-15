from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    filename: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(sa.Text, nullable=False)
    file_size: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="pending", index=True)
    doc_type: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="other", index=True)
    extracted_data: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    key_dates: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    risks: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    opportunities: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="documents")  # noqa: F821
    uploader: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="documents", foreign_keys=[uploaded_by]
    )
    client: Mapped["Client"] = relationship("Client", back_populates="documents")  # noqa: F821

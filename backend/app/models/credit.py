from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class CreditReport(Base):
    __tablename__ = "credit_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="upload")
    report_date: Mapped[str | None] = mapped_column(sa.Date, nullable=True)
    raw_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    bureaus: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship("Client", back_populates="credit_reports")  # noqa: F821
    tradelines: Mapped[list["Tradeline"]] = relationship(  # noqa: F821
        "Tradeline", back_populates="credit_report"
    )
    collections: Mapped[list["Collection"]] = relationship(  # noqa: F821
        "Collection", back_populates="credit_report"
    )


class Tradeline(Base):
    __tablename__ = "tradelines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    credit_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("credit_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creditor_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    balance: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    credit_limit: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    payment_status: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    opened_at: Mapped[str | None] = mapped_column(sa.Date, nullable=True)
    closed_at: Mapped[str | None] = mapped_column(sa.Date, nullable=True)
    utilization: Mapped[float | None] = mapped_column(sa.Numeric(6, 4), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    credit_report: Mapped["CreditReport"] = relationship(  # noqa: F821
        "CreditReport", back_populates="tradelines"
    )


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    credit_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("credit_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collector_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    original_creditor: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    amount: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    opened_at: Mapped[str | None] = mapped_column(sa.Date, nullable=True)
    status: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    credit_report: Mapped["CreditReport"] = relationship(  # noqa: F821
        "CreditReport", back_populates="collections"
    )


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bureau: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    furnisher: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    issue_type: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    expected_response_by: Mapped[str | None] = mapped_column(sa.Date, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    notes_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="disputes")  # noqa: F821
    dispute_letters: Mapped[list["DisputeLetter"]] = relationship(  # noqa: F821
        "DisputeLetter", back_populates="dispute"
    )


class DisputeLetter(Base):
    __tablename__ = "dispute_letters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dispute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("disputes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_version: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    pdf_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    dispute: Mapped["Dispute"] = relationship("Dispute", back_populates="dispute_letters")  # noqa: F821

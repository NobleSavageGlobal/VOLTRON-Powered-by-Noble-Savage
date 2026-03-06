from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class FinancialConnection(Base):
    __tablename__ = "financial_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    encrypted_token: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    account_mask: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="active")
    last_synced_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship("Client", back_populates="financial_connections")  # noqa: F821
    accounts: Mapped[list["FinancialAccount"]] = relationship(  # noqa: F821
        "FinancialAccount", back_populates="connection"
    )


class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("financial_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_mask: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    account_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(10), nullable=False, default="USD")
    current_balance: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    provider_account_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    connection: Mapped["FinancialConnection"] = relationship(  # noqa: F821
        "FinancialConnection", back_populates="accounts"
    )
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", back_populates="account"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("financial_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    posted_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    amount: Mapped[float] = mapped_column(sa.Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    merchant: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    transaction_type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    raw_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    hash_dedupe: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    account: Mapped["FinancialAccount"] = relationship(  # noqa: F821
        "FinancialAccount", back_populates="transactions"
    )


class MonthlyRollup(Base):
    __tablename__ = "monthly_rollups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_month: Mapped[str] = mapped_column(sa.Date, nullable=False)
    income_total: Mapped[float] = mapped_column(sa.Numeric(15, 2), nullable=False, default=0)
    expense_total: Mapped[float] = mapped_column(sa.Numeric(15, 2), nullable=False, default=0)
    net_total: Mapped[float] = mapped_column(sa.Numeric(15, 2), nullable=False, default=0)
    category_breakdown: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint("client_id", "period_month", name="uq_monthly_rollup_client_month"),
    )

    client: Mapped["Client"] = relationship("Client", back_populates="monthly_rollups")  # noqa: F821


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    obligation_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    creditor_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    principal: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    monthly_payment: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    apr: Mapped[float | None] = mapped_column(sa.Numeric(6, 4), nullable=True)
    balance: Mapped[float | None] = mapped_column(sa.Numeric(15, 2), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="current")
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    client: Mapped["Client"] = relationship("Client", back_populates="obligations")  # noqa: F821

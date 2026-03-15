from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="person")
    ein: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    ssn_last4: Mapped[str | None] = mapped_column(sa.String(4), nullable=True)
    industry: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    annual_revenue_range: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    profile_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    org: Mapped["Organization"] = relationship("Organization", back_populates="clients")  # noqa: F821
    financial_connections: Mapped[list["FinancialConnection"]] = relationship(  # noqa: F821
        "FinancialConnection", back_populates="client"
    )
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="client"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="client")  # noqa: F821
    decision_plans: Mapped[list["DecisionPlan"]] = relationship(  # noqa: F821
        "DecisionPlan", back_populates="client"
    )
    credit_reports: Mapped[list["CreditReport"]] = relationship(  # noqa: F821
        "CreditReport", back_populates="client"
    )
    monthly_rollups: Mapped[list["MonthlyRollup"]] = relationship(  # noqa: F821
        "MonthlyRollup", back_populates="client"
    )
    obligations: Mapped[list["Obligation"]] = relationship(  # noqa: F821
        "Obligation", back_populates="client"
    )
    disputes: Mapped[list["Dispute"]] = relationship("Dispute", back_populates="client")  # noqa: F821
    scoring_snapshots: Mapped[list["ScoringSnapshot"]] = relationship(  # noqa: F821
        "ScoringSnapshot", back_populates="client"
    )

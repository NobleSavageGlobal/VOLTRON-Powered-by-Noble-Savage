from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class DecisionPlan(Base):
    __tablename__ = "decision_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    plan_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="draft")
    generated_by: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="system")
    goal: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    time_horizon_days: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="decision_plans")  # noqa: F821
    plan_actions: Mapped[list["PlanAction"]] = relationship("PlanAction", back_populates="plan")  # noqa: F821


class PlanAction(Base):
    __tablename__ = "plan_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("decision_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    action_code: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    why: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    depends_on: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    due_in_days: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    success_metric: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    evidence_refs: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    risk_flags: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="pending")
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    plan: Mapped["DecisionPlan"] = relationship("DecisionPlan", back_populates="plan_actions")  # noqa: F821


class ScoringSnapshot(Base):
    __tablename__ = "scoring_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    score: Mapped[float] = mapped_column(sa.Numeric(5, 2), nullable=False)
    factors_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    inputs_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="scoring_snapshots")  # noqa: F821


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    version: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    rule_json: Mapped[dict] = mapped_column(_json_col(), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    effective_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    deprecated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    version: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    template_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    schema_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("name", "version", name="uq_prompt_template_name_version"),
    )

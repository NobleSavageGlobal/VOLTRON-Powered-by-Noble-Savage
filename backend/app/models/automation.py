from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    trigger_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    trigger_config: Mapped[dict] = mapped_column(_json_col(), nullable=False, default=dict)
    actions: Mapped[list] = mapped_column(_json_col(), nullable=False, default=list)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="draft")
    run_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    last_triggered_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    runs: Mapped[list["WorkflowRun"]] = relationship("WorkflowRun", back_populates="workflow")  # noqa: F821


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="pending")
    trigger_event: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    steps_log: Mapped[list | None] = mapped_column(_json_col(), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(sa.String(255), unique=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    error_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="runs")  # noqa: F821


class AutomationEvent(Base):
    __tablename__ = "automation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(_json_col(), nullable=True)
    processed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

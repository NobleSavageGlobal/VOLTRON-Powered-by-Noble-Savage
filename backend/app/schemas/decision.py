from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PlanActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action_code: str
    action_type: str
    title: str
    description: str | None
    why: str | None
    depends_on: list | None
    due_in_days: int | None
    success_metric: str | None
    evidence_refs: list | None
    risk_flags: list | None
    status: str
    created_at: datetime


class PlanActionUpdate(BaseModel):
    status: str | None = None
    approved_by: uuid.UUID | None = None


class DecisionPlanCreate(BaseModel):
    client_id: uuid.UUID
    goal: str | None = None
    time_horizon_days: int | None = None


class DecisionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    plan_title: str
    plan_version: int
    status: str
    goal: str | None
    time_horizon_days: int | None
    created_at: datetime
    published_at: datetime | None
    actions: list[PlanActionResponse] = []


class ScoringSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    score_type: str
    score: Any
    factors_json: dict | None
    computed_at: datetime

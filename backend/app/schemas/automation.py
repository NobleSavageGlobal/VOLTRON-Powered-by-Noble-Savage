from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkflowCreate(BaseModel):
    name: str
    trigger_type: str
    trigger_config: dict
    actions: list[dict]


class WorkflowUpdate(BaseModel):
    name: str | None = None
    trigger_type: str | None = None
    trigger_config: dict | None = None
    actions: list[dict] | None = None
    status: str | None = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    trigger_type: str
    trigger_config: Any
    actions: Any
    status: str
    run_count: int
    last_triggered_at: datetime | None
    created_at: datetime


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_event: dict | None
    started_at: datetime
    completed_at: datetime | None
    error_json: dict | None


class AutomationEventCreate(BaseModel):
    event_type: str
    payload_json: dict | None = None
    client_id: uuid.UUID | None = None


class AutomationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    client_id: uuid.UUID | None
    event_type: str
    payload_json: dict | None
    processed: bool
    created_at: datetime

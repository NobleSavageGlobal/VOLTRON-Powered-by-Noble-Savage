from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


TaskStatus = Literal["todo", "in_progress", "blocked", "review", "done"]
TaskPriority = Literal["critical", "high", "medium", "low"]
TaskSource = Literal["manual", "ai_generated", "automation"]


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: datetime | None = None
    assigned_to: uuid.UUID | None = None
    source: TaskSource = "manual"
    metadata_: dict[str, Any] | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assigned_to: uuid.UUID | None = None
    metadata_: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    created_by: uuid.UUID | None
    assigned_to: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    completed_at: datetime | None
    source: TaskSource
    metadata_: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int

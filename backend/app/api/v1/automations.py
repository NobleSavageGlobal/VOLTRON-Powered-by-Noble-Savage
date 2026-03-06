from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.automation import WorkflowCreate, WorkflowResponse, WorkflowRunResponse
from app.services.automation_service import automation_service

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await automation_service.list_workflows(db, current_user.org_id)


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await automation_service.create_workflow(db, current_user.org_id, data.model_dump())


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    updates: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await automation_service.update_workflow(db, workflow_id, current_user.org_id, updates)


@router.post("/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await automation_service.run_workflow(db, workflow_id, current_user.org_id)


@router.get("/runs", response_model=list[WorkflowRunResponse])
async def list_runs(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await automation_service.get_workflow_runs(db, current_user.org_id, limit)


@router.get("/events")
async def list_events(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    events = await automation_service.get_events(db, current_user.org_id, limit)
    return [
        {
            "id": str(e.id),
            "org_id": str(e.org_id),
            "event_type": e.event_type,
            "payload_json": e.payload_json,
            "processed": e.processed,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]

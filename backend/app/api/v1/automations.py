from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DB
from app.core.exceptions import ForbiddenError
from app.schemas.automation import WorkflowCreate, WorkflowResponse, WorkflowRunResponse, WorkflowUpdate
from app.services.automation_service import automation_service

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    current_user: CurrentUser,
    db: DB,
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await automation_service.list_workflows(db, current_user.org_id)


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await automation_service.create_workflow(db, current_user.org_id, data.model_dump())


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    updates: WorkflowUpdate,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await automation_service.update_workflow(db, workflow_id, current_user.org_id, updates.model_dump(exclude_unset=True))


@router.post("/workflows/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await automation_service.run_workflow(db, workflow_id, current_user.org_id)


@router.get("/runs", response_model=list[WorkflowRunResponse])
async def list_runs(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(50, le=200),
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await automation_service.get_workflow_runs(db, current_user.org_id, limit)


@router.get("/events")
async def list_events(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(50, le=200),
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
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

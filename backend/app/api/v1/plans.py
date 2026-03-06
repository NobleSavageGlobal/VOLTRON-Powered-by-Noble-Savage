from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.decision import (
    DecisionPlanCreate,
    DecisionPlanResponse,
    PlanActionUpdate,
    ScoringSnapshotResponse,
)
from app.services.decision_service import decision_service

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[DecisionPlanResponse])
async def list_plans(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await decision_service.get_plans(db, client_id)


@router.post("/generate", response_model=DecisionPlanResponse, status_code=201)
async def generate_plan(
    data: DecisionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await decision_service.generate_plan(
        db,
        data.client_id,
        current_user.org_id,
        data.goal,
        data.time_horizon_days or 90,
    )


@router.get("/{plan_id}", response_model=DecisionPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await decision_service.get_plan(db, plan_id, current_user.org_id)


@router.post("/{plan_id}/publish", response_model=DecisionPlanResponse)
async def publish_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await decision_service.publish_plan(db, plan_id, current_user.org_id)


@router.patch("/{plan_id}/actions/{action_id}")
async def update_action(
    plan_id: uuid.UUID,
    action_id: uuid.UUID,
    data: PlanActionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await decision_service.update_action_status(db, action_id, data.status, current_user.id)


@router.get("/scores/latest", response_model=list[ScoringSnapshotResponse])
async def get_scores(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await decision_service.get_latest_scores(db, client_id)


@router.post("/scores/compute", response_model=list[ScoringSnapshotResponse])
async def compute_scores(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await decision_service.compute_scores(db, client_id)

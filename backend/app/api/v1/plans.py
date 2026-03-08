from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.client import Client
from app.schemas.decision import (
    DecisionPlanCreate,
    DecisionPlanResponse,
    PlanActionUpdate,
    ScoringSnapshotResponse,
)
from app.services.decision_service import decision_service

router = APIRouter(prefix="/plans", tags=["plans"])


async def _verify_client_access(
    db: DB, client_id: uuid.UUID, current_user: CurrentUser
) -> None:
    result = await db.execute(
        select(Client).where(
            Client.id == client_id, Client.org_id == current_user.org_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Client", str(client_id))


@router.get("/", response_model=list[DecisionPlanResponse])
async def list_plans(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await decision_service.get_plans(db, client_id)


@router.post("/generate", response_model=DecisionPlanResponse, status_code=201)
async def generate_plan(
    data: DecisionPlanCreate,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, data.client_id, current_user)
    return await decision_service.generate_plan(
        db,
        data.client_id,
        current_user.org_id,
        data.goal or "Improve financial position",
        data.time_horizon_days or 90,
    )


@router.get("/{plan_id}", response_model=DecisionPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await decision_service.get_plan(db, plan_id, current_user.org_id)


@router.post("/{plan_id}/publish", response_model=DecisionPlanResponse)
async def publish_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await decision_service.publish_plan(db, plan_id, current_user.org_id)


@router.patch("/{plan_id}/actions/{action_id}")
async def update_action(
    plan_id: uuid.UUID,
    action_id: uuid.UUID,
    data: PlanActionUpdate,
    current_user: CurrentUser,
    db: DB,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await decision_service.update_action_status(
        db, action_id, data.status, current_user.id
    )


@router.get("/scores/latest", response_model=list[ScoringSnapshotResponse])
async def get_scores(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await decision_service.get_latest_scores(db, client_id)


@router.post("/scores/compute", response_model=list[ScoringSnapshotResponse])
async def compute_scores(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list:
    return await decision_service.compute_scores(db, client_id)

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.client import Client
from app.models.financial import (
    FinancialConnection,
    MonthlyRollup,
    Obligation,
    Transaction,
)
from app.schemas.financial import (
    FinancialConnectionCreate,
    FinancialConnectionResponse,
    MonthlyRollupResponse,
    ObligationCreate,
    ObligationResponse,
    TransactionResponse,
)
from app.services.financial_service import financial_service

router = APIRouter(prefix="/financial", tags=["financial"])


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


@router.get("/connections", response_model=list[FinancialConnectionResponse])
async def list_connections(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID | None = None,
) -> list[FinancialConnection]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    if client_id:
        await _verify_client_access(db, client_id, current_user)
    stmt = select(FinancialConnection).where(
        FinancialConnection.org_id == current_user.org_id
    )
    if client_id:
        stmt = stmt.where(FinancialConnection.client_id == client_id)
    result = await db.execute(stmt.order_by(FinancialConnection.created_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/connections", response_model=FinancialConnectionResponse, status_code=201
)
async def create_connection(
    data: FinancialConnectionCreate,
    current_user: CurrentUser,
    db: DB,
) -> FinancialConnection:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, data.client_id, current_user)
    conn = await financial_service.create_connection(
        db, current_user.org_id, data.client_id, data.provider, data.account_mask
    )
    return conn


@router.post("/connections/{connection_id}/sync")
async def sync_connection(
    connection_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> dict:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    result = await db.execute(
        select(FinancialConnection).where(
            FinancialConnection.id == connection_id,
            FinancialConnection.org_id == current_user.org_id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise NotFoundError("Connection", str(connection_id))
    sync_result = await financial_service.simulate_plaid_sync(db, connection_id)
    return sync_result


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> list[Transaction]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    if client_id:
        await _verify_client_access(db, client_id, current_user)
    return await financial_service.get_transactions(db, client_id, limit, offset)


@router.get("/rollups", response_model=list[MonthlyRollupResponse])
async def list_rollups(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list[MonthlyRollup]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await financial_service.compute_monthly_rollups(db, client_id)


@router.get("/summary")
async def financial_summary(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> dict:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await financial_service.get_financial_summary(db, client_id)


@router.get("/obligations", response_model=list[ObligationResponse])
async def list_obligations(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list[Obligation]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await financial_service.list_obligations(db, client_id)


@router.post("/obligations", response_model=ObligationResponse, status_code=201)
async def create_obligation(
    data: ObligationCreate,
    current_user: CurrentUser,
    db: DB,
) -> Obligation:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, data.client_id, current_user)
    return await financial_service.create_obligation(
        db, data.client_id, data.model_dump()
    )

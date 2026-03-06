from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException
from app.models.financial import FinancialConnection, MonthlyRollup, Obligation, Transaction
from app.models.user import User
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


@router.get("/connections", response_model=list[FinancialConnectionResponse])
async def list_connections(
    client_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FinancialConnection]:
    stmt = select(FinancialConnection).where(FinancialConnection.org_id == current_user.org_id)
    if client_id:
        stmt = stmt.where(FinancialConnection.client_id == client_id)
    result = await db.execute(stmt.order_by(FinancialConnection.created_at.desc()))
    return list(result.scalars().all())


@router.post("/connections", response_model=FinancialConnectionResponse, status_code=201)
async def create_connection(
    data: FinancialConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinancialConnection:
    conn = await financial_service.create_connection(
        db, current_user.org_id, data.client_id, data.provider, data.account_mask
    )
    return conn


@router.post("/connections/{connection_id}/sync")
async def sync_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(FinancialConnection).where(
            FinancialConnection.id == connection_id,
            FinancialConnection.org_id == current_user.org_id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise AppException(404, "Connection not found")
    sync_result = await financial_service.simulate_plaid_sync(db, connection_id)
    return sync_result


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    client_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Transaction]:
    return await financial_service.get_transactions(db, client_id, limit, offset)


@router.get("/rollups", response_model=list[MonthlyRollupResponse])
async def list_rollups(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MonthlyRollup]:
    return await financial_service.compute_monthly_rollups(db, client_id)


@router.get("/summary")
async def financial_summary(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return await financial_service.get_financial_summary(db, client_id)


@router.get("/obligations", response_model=list[ObligationResponse])
async def list_obligations(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Obligation]:
    return await financial_service.list_obligations(db, client_id)


@router.post("/obligations", response_model=ObligationResponse, status_code=201)
async def create_obligation(
    data: ObligationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Obligation:
    return await financial_service.create_obligation(db, data.client_id, data.model_dump())

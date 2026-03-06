from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException
from app.models.credit import Collection, CreditReport, Dispute, DisputeLetter, Tradeline
from app.models.user import User
from app.schemas.credit import (
    CreditReportResponse,
    DisputeCreate,
    DisputeLetterResponse,
    DisputeResponse,
    DisputeUpdate,
)
from app.services.credit_service import credit_service

router = APIRouter(prefix="/credit", tags=["credit"])


@router.get("/reports", response_model=list[CreditReportResponse])
async def list_reports(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CreditReport]:
    return await credit_service.get_credit_reports(db, client_id)


@router.post("/reports", response_model=CreditReportResponse, status_code=201)
async def create_report(
    client_id: uuid.UUID,
    document_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return await credit_service.process_credit_report(db, client_id, document_id)


@router.get("/reports/{report_id}/tradelines", response_model=None)
async def get_tradelines(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    result = await db.execute(select(Tradeline).where(Tradeline.credit_report_id == report_id))
    rows = result.scalars().all()
    return [{"id": str(r.id), "creditor_name": r.creditor_name, "account_type": r.account_type, "balance": str(r.balance) if r.balance else None, "payment_status": r.payment_status} for r in rows]


@router.get("/reports/{report_id}/collections", response_model=None)
async def get_collections(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    result = await db.execute(select(Collection).where(Collection.credit_report_id == report_id))
    rows = result.scalars().all()
    return [{"id": str(r.id), "collector_name": r.collector_name, "amount": str(r.amount) if r.amount else None, "status": r.status} for r in rows]


@router.get("/disputes", response_model=list[DisputeResponse])
async def list_disputes(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Dispute]:
    return await credit_service.list_disputes(db, client_id)


@router.post("/disputes", response_model=DisputeResponse, status_code=201)
async def create_dispute(
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dispute:
    return await credit_service.create_dispute(db, data.client_id, data.model_dump())


@router.patch("/disputes/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: uuid.UUID,
    data: DisputeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dispute:
    return await credit_service.update_dispute(db, dispute_id, data.model_dump(exclude_unset=True))


@router.post("/disputes/{dispute_id}/letters", response_model=DisputeLetterResponse, status_code=201)
async def generate_letter(
    dispute_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DisputeLetter:
    return await credit_service.generate_dispute_letter(db, dispute_id, current_user.id)


@router.get("/disputes/{dispute_id}/letters", response_model=list[DisputeLetterResponse])
async def list_letters(
    dispute_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DisputeLetter]:
    result = await db.execute(
        select(DisputeLetter).where(DisputeLetter.dispute_id == dispute_id).order_by(DisputeLetter.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/health")
async def credit_health(
    client_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return await credit_service.get_credit_health_factors(db, client_id)

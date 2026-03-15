from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.client import Client
from app.models.credit import (
    Collection,
    CreditReport,
    Dispute,
    DisputeLetter,
    Tradeline,
)
from app.schemas.credit import (
    CreditReportResponse,
    DisputeCreate,
    DisputeLetterResponse,
    DisputeResponse,
    DisputeUpdate,
)
from app.services.credit_service import credit_service

router = APIRouter(prefix="/credit", tags=["credit"])


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


@router.get("/reports", response_model=list[CreditReportResponse])
async def list_reports(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list[CreditReport]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await credit_service.get_credit_reports(db, client_id)


@router.post("/reports", response_model=CreditReportResponse, status_code=201)
async def create_report(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
    document_id: uuid.UUID | None = None,
) -> object:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await credit_service.process_credit_report(db, client_id, document_id)


@router.get("/reports/{report_id}/tradelines")
async def get_tradelines(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    result = await db.execute(
        select(Tradeline).where(Tradeline.credit_report_id == report_id)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "creditor_name": r.creditor_name,
            "account_type": r.account_type,
            "balance": str(r.balance) if r.balance else None,
            "payment_status": r.payment_status,
        }
        for r in rows
    ]


@router.get("/reports/{report_id}/collections")
async def get_collections(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> list:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    result = await db.execute(
        select(Collection).where(Collection.credit_report_id == report_id)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "collector_name": r.collector_name,
            "amount": str(r.amount) if r.amount else None,
            "status": r.status,
        }
        for r in rows
    ]


@router.get("/disputes", response_model=list[DisputeResponse])
async def list_disputes(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> list[Dispute]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await credit_service.list_disputes(db, client_id)


@router.post("/disputes", response_model=DisputeResponse, status_code=201)
async def create_dispute(
    data: DisputeCreate,
    current_user: CurrentUser,
    db: DB,
) -> Dispute:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, data.client_id, current_user)
    return await credit_service.create_dispute(db, data.client_id, data.model_dump())


@router.patch("/disputes/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: uuid.UUID,
    data: DisputeUpdate,
    current_user: CurrentUser,
    db: DB,
) -> Dispute:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await credit_service.update_dispute(
        db, dispute_id, data.model_dump(exclude_unset=True)
    )


@router.post(
    "/disputes/{dispute_id}/letters",
    response_model=DisputeLetterResponse,
    status_code=201,
)
async def generate_letter(
    dispute_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> DisputeLetter:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    return await credit_service.generate_dispute_letter(db, dispute_id, current_user.id)


@router.get(
    "/disputes/{dispute_id}/letters", response_model=list[DisputeLetterResponse]
)
async def list_letters(
    dispute_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> list[DisputeLetter]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    result = await db.execute(
        select(DisputeLetter)
        .where(DisputeLetter.dispute_id == dispute_id)
        .order_by(DisputeLetter.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/health")
async def credit_health(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID = Query(...),
) -> dict:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    await _verify_client_access(db, client_id, current_user)
    return await credit_service.get_credit_health_factors(db, client_id)

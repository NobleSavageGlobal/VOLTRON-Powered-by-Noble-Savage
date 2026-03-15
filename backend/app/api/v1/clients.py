from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Client]:
    stmt = select(Client).where(Client.org_id == current_user.org_id)
    if status:
        stmt = stmt.where(Client.status == status)
    result = await db.execute(stmt.order_by(Client.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all())


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    client = Client(org_id=current_user.org_id, **data.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.org_id == current_user.org_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise AppException(404, "Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.org_id == current_user.org_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise AppException(404, "Client not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(client, k, v)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.org_id == current_user.org_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise AppException(404, "Client not found")
    client.status = "inactive"
    await db.commit()

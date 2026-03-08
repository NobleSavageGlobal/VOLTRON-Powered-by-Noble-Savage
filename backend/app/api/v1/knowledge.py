from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.client import Client
from app.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


async def _verify_client_access(db: DB, client_id: uuid.UUID, current_user: CurrentUser) -> None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.org_id == current_user.org_id)
    )
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Client", str(client_id))


@router.get("/search")
async def search(
    current_user: CurrentUser,
    db: DB,
    q: str = Query(..., min_length=1),
    client_id: uuid.UUID | None = None,
    limit: int = Query(10, le=50),
) -> list[dict]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    if client_id:
        await _verify_client_access(db, client_id, current_user)
    return await knowledge_service.search(db, current_user.org_id, q, client_id, limit)


@router.post("/index")
async def index_document(
    current_user: CurrentUser,
    db: DB,
    document_id: uuid.UUID = Query(...),
    client_id: uuid.UUID | None = None,
) -> dict:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    if client_id:
        await _verify_client_access(db, client_id, current_user)
    chunks = await knowledge_service.index_document(db, document_id, current_user.org_id, client_id)
    return {"indexed_chunks": len(chunks), "document_id": str(document_id)}


@router.get("/chunks")
async def list_chunks(
    current_user: CurrentUser,
    db: DB,
    client_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
) -> list[dict]:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization")
    if client_id:
        await _verify_client_access(db, client_id, current_user)
    chunks = await knowledge_service.get_chunks(db, current_user.org_id, client_id, limit)
    return [
        {
            "id": str(c.id),
            "document_id": str(c.document_id) if c.document_id else None,
            "chunk_text": c.chunk_text[:200],
            "chunk_index": c.chunk_index,
            "created_at": c.created_at.isoformat(),
        }
        for c in chunks
    ]

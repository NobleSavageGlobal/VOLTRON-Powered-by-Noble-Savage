from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    client_id: uuid.UUID | None = None,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    return await knowledge_service.search(db, current_user.org_id, q, client_id, limit)


@router.post("/index")
async def index_document(
    document_id: uuid.UUID = Query(...),
    client_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    chunks = await knowledge_service.index_document(db, document_id, current_user.org_id, client_id)
    return {"indexed_chunks": len(chunks), "document_id": str(document_id)}


@router.get("/chunks")
async def list_chunks(
    client_id: uuid.UUID | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
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

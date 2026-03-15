from __future__ import annotations

import hashlib
import json
import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document
from app.models.knowledge import KnowledgeChunk, KnowledgeEmbedding
from app.services.ai_service import AIService

logger = get_logger(__name__)
_ai = AIService()

_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def _cosine_sim(a: list[float], b_str: str) -> float:
    try:
        b: list[float] = json.loads(b_str)
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)
    except Exception:
        return 0.0


def _split_chunks(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + _CHUNK_SIZE])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


class KnowledgeService:
    async def index_document(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        org_id: uuid.UUID,
        client_id: uuid.UUID | None = None,
    ) -> list[KnowledgeChunk]:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return []

        parts: list[str] = []
        if doc.ai_summary:
            parts.append(doc.ai_summary)
        if doc.extracted_data:
            parts.append(json.dumps(doc.extracted_data))
        full_text = " ".join(parts).strip()
        if not full_text:
            return []

        chunks_text = _split_chunks(full_text)
        try:
            embeddings = await _ai.compute_embeddings(chunks_text)
        except Exception as exc:
            logger.warning("embedding computation failed", error=str(exc))
            embeddings = [[] for _ in chunks_text]

        created: list[KnowledgeChunk] = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            chunk_hash = hashlib.sha256(f"{document_id}:{i}:{chunk_text}".encode()).hexdigest()[:64]
            existing = await db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.chunk_hash == chunk_hash)
            )
            if existing.scalar_one_or_none():
                continue

            chunk = KnowledgeChunk(
                org_id=org_id,
                client_id=client_id,
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_hash=chunk_hash,
                chunk_index=i,
            )
            db.add(chunk)
            await db.flush()

            if embedding:
                db.add(
                    KnowledgeEmbedding(
                        chunk_id=chunk.id,
                        embedding_vector=json.dumps(embedding),
                        model_name="text-embedding-3-small",
                    )
                )
            created.append(chunk)

        await db.commit()
        return created

    async def search(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        query: str,
        client_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[dict]:
        try:
            query_vecs = await _ai.compute_embeddings([query])
            query_vec = query_vecs[0] if query_vecs else []
        except Exception:
            query_vec = []

        stmt = select(KnowledgeChunk).where(KnowledgeChunk.org_id == org_id)
        if client_id:
            stmt = stmt.where(KnowledgeChunk.client_id == client_id)
        result = await db.execute(stmt.limit(200))
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        if not query_vec:
            q_lower = query.lower()
            matched = [c for c in chunks if q_lower in c.chunk_text.lower()]
            return [
                {
                    "chunk_id": str(c.id),
                    "document_id": str(c.document_id) if c.document_id else None,
                    "text": c.chunk_text,
                    "score": 1.0,
                    "page": c.page_number,
                }
                for c in matched[:limit]
            ]

        chunk_ids = [c.id for c in chunks]
        emb_result = await db.execute(
            select(KnowledgeEmbedding).where(KnowledgeEmbedding.chunk_id.in_(chunk_ids))
        )
        emb_map = {e.chunk_id: e.embedding_vector for e in emb_result.scalars().all()}

        scored = sorted(
            [(_cosine_sim(query_vec, emb_map.get(c.id, "[]") or "[]"), c) for c in chunks],
            reverse=True,
        )
        return [
            {
                "chunk_id": str(c.id),
                "document_id": str(c.document_id) if c.document_id else None,
                "text": c.chunk_text,
                "score": round(score, 4),
                "page": c.page_number,
            }
            for score, c in scored[:limit]
        ]

    async def get_chunks(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        client_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.org_id == org_id)
        if client_id:
            stmt = stmt.where(KnowledgeChunk.client_id == client_id)
        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())


knowledge_service = KnowledgeService()

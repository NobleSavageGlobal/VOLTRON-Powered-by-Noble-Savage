from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _json_col():
    return sa.JSON().with_variant(JSONB(), "postgresql")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    page_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    chunk_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    chunk_index: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


class KnowledgeEmbedding(Base):
    """Vector embedding for a knowledge chunk.

    NOTE: In production PostgreSQL with pgvector, replace `embedding_vector` (Text)
    with a VECTOR(1536) column using pgvector. For now we store as a JSON array string
    for SQLite/portability compatibility.
    Migration example:
        ALTER TABLE knowledge_embeddings ADD COLUMN embedding_vector vector(1536);
    """

    __tablename__ = "knowledge_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), unique=True, nullable=False)
    # Store as JSON array string; use pgvector VECTOR(1536) in production
    embedding_vector: Mapped[str] = mapped_column(sa.Text, nullable=False)
    model_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

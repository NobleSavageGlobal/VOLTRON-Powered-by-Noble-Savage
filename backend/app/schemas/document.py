from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


DocumentStatus = Literal["pending", "processing", "processed", "failed", "review_required"]
DocumentType = Literal[
    "bank_statement", "tax_return", "contract", "invoice",
    "credit_report", "government", "other"
]


class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str


class DocumentUpdate(BaseModel):
    status: DocumentStatus | None = None
    notes: str | None = None
    doc_type: DocumentType | None = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    uploaded_by: uuid.UUID | None
    status: DocumentStatus
    doc_type: DocumentType
    confidence_score: float | None
    ai_summary: str | None
    key_dates: list[Any] | None
    risks: list[Any] | None
    opportunities: list[Any] | None
    extracted_data: dict[str, Any] | None
    notes: str | None
    created_at: datetime
    processed_at: datetime | None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import StorageError
from app.models.document import Document
from app.models.user import User
from app.services.ai_service import AIService
from app.services.storage_service import get_storage_service


MIME_TO_DOC_TYPE: dict[str, str] = {
    "application/pdf": "other",
    "image/jpeg": "other",
    "image/png": "other",
    "image/tiff": "other",
}

FILENAME_PATTERNS: list[tuple[str, str]] = [
    (r"bank.?statement|statement.?of.?account", "bank_statement"),
    (r"tax.?return|1040|w-?2|1099|schedule", "tax_return"),
    (r"contract|agreement|deed|lease", "contract"),
    (r"invoice|bill|receipt", "invoice"),
    (r"credit.?report|credit.?score|fico", "credit_report"),
    (r"passport|driver.?licen|license|id.?card|government", "government"),
]


def classify_by_filename(filename: str) -> str:
    lower = filename.lower()
    for pattern, doc_type in FILENAME_PATTERNS:
        if re.search(pattern, lower):
            return doc_type
    return "other"


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.storage = get_storage_service()
        self.ai_service = AIService()

    async def create_document(self, file: UploadFile, user: User) -> Document:
        content = await file.read()
        file_size = len(content)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise StorageError(f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB")

        unique_name = f"{uuid.uuid4()}{Path(file.filename or 'upload').suffix}"
        file_path = await self.storage.save(unique_name, content)

        doc_type = classify_by_filename(file.filename or "")
        doc = Document(
            org_id=user.org_id,
            uploaded_by=user.id,
            filename=unique_name,
            original_filename=file.filename or unique_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            status="pending",
            doc_type=doc_type,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Process asynchronously (in a real system, push to a task queue)
        try:
            doc = await self._process_document(doc, content)
        except Exception:
            doc.status = "failed"
            await self.db.commit()
            await self.db.refresh(doc)

        return doc

    async def _process_document(self, doc: Document, content: bytes) -> Document:
        doc.status = "processing"
        await self.db.commit()

        text = self._extract_text(content, doc.mime_type)

        if settings.OPENAI_API_KEY:
            result = await self.ai_service.analyze_document(
                text=text,
                filename=doc.original_filename,
                doc_type=doc.doc_type,
            )
            doc.doc_type = result.get("doc_type", doc.doc_type)
            doc.confidence_score = result.get("confidence_score", 0.5)
            doc.ai_summary = result.get("summary")
            doc.key_dates = result.get("key_dates", [])
            doc.risks = result.get("risks", [])
            doc.opportunities = result.get("opportunities", [])
            doc.extracted_data = result.get("extracted_data", {})
        else:
            doc.confidence_score = 0.5
            doc.ai_summary = "AI analysis not configured (no API key)"
            doc.key_dates = []
            doc.risks = []
            doc.opportunities = []
            doc.extracted_data = {}

        doc.status = "processed"
        doc.processed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    def _extract_text(self, content: bytes, mime_type: str) -> str:
        try:
            if mime_type == "application/pdf":
                from pdfminer.high_level import extract_text_to_fp
                from pdfminer.layout import LAParams
                import io
                output = io.StringIO()
                extract_text_to_fp(io.BytesIO(content), output, laparams=LAParams())
                return output.getvalue()
        except Exception:
            pass

        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    async def reprocess_document(self, doc: Document) -> Document:
        content = await self.storage.load(doc.filename)
        return await self._process_document(doc, content)

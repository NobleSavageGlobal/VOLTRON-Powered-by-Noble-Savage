from __future__ import annotations

import io
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError, StorageError
from app.models.client import Client
from app.models.document import Document
from app.models.user import User
from app.services.ai_service import AIService
from app.services.storage_service import get_storage_service

MIME_TO_DOC_TYPE: dict[str, str] = {
    "application/pdf": "other",
    "image/jpeg": "other",
    "image/png": "other",
    "image/tiff": "other",
    "image/webp": "other",
    "image/bmp": "other",
    "application/msword": "other",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "other",
    "text/plain": "other",
    "text/csv": "other",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp", ".gif"}
DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

REVENUE_RANGES = [
    (50_000, "Under $50K"),
    (100_000, "$50K-$100K"),
    (250_000, "$100K-$250K"),
    (500_000, "$250K-$500K"),
    (1_000_000, "$500K-$1M"),
    (float("inf"), "Over $1M"),
]

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


def _clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _fallback_client_name(filename: str) -> str:
    stem = Path(filename or "Uploaded Document").stem
    stem = re.sub(r"[_\-.]+", " ", stem)
    stem = re.sub(
        r"\b(bank|statement|invoice|contract|tax|return|report|document|upload)\b",
        "",
        stem,
        flags=re.I,
    )
    stem = _clean_text(stem)
    return stem.title() if len(stem) >= 3 else "New Client"


def _merge_dict(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dict(merged[key], value)
            continue
        if value not in (None, "", [], {}):
            merged[key] = value
    return merged


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.storage = get_storage_service()
        self.ai_service = AIService()

    async def create_document(
        self,
        file: UploadFile,
        user: User,
        client_id: uuid.UUID | None = None,
        auto_onboard: bool = False,
    ) -> Document:
        if client_id:
            existing_client = await self.db.execute(
                select(Client).where(
                    Client.id == client_id, Client.org_id == user.org_id
                )
            )
            if existing_client.scalar_one_or_none() is None:
                raise NotFoundError("Client", str(client_id))

        content = await file.read()
        file_size = len(content)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise StorageError(
                f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        unique_name = f"{uuid.uuid4()}{Path(file.filename or 'upload').suffix}"
        file_path = await self.storage.save(unique_name, content)

        mime_doc_type = MIME_TO_DOC_TYPE.get(file.content_type or "")
        doc_type = mime_doc_type or classify_by_filename(file.filename or "")
        doc = Document(
            org_id=user.org_id,
            client_id=client_id,
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

        if auto_onboard and doc.status in {"processed", "review_required"}:
            try:
                client = await self.auto_onboard_document(
                    doc=doc, user=user, client_id=client_id
                )
                doc.client_id = client.id
                current_data = (
                    dict(doc.extracted_data)
                    if isinstance(doc.extracted_data, dict)
                    else {}
                )
                current_data["onboarding"] = {
                    "auto_onboarded": True,
                    "client_id": str(client.id),
                    "client_name": client.display_name,
                }
                doc.extracted_data = current_data
                await self.db.commit()
                await self.db.refresh(doc)
            except Exception as exc:
                current_data = (
                    dict(doc.extracted_data)
                    if isinstance(doc.extracted_data, dict)
                    else {}
                )
                current_data["onboarding"] = {
                    "auto_onboarded": False,
                    "error": str(exc),
                }
                doc.extracted_data = current_data
                doc.status = "review_required"
                await self.db.commit()
                await self.db.refresh(doc)

        return doc

    async def _process_document(self, doc: Document, content: bytes) -> Document:
        doc.status = "processing"
        await self.db.commit()

        text, extraction_meta = self._extract_text(
            content=content,
            mime_type=doc.mime_type,
            filename=doc.original_filename,
        )

        structured_data = self._extract_structured_data(
            text=text, filename=doc.original_filename
        )
        analysis_error = None

        if settings.OPENAI_API_KEY and text:
            try:
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
                ai_data = result.get("extracted_data", {})
                doc.extracted_data = _merge_dict(
                    structured_data, ai_data if isinstance(ai_data, dict) else {}
                )
            except Exception as exc:
                analysis_error = str(exc)
                doc.confidence_score = 0.35 if text else 0.0
                doc.ai_summary = "AI analysis unavailable; fallback extraction used"
                doc.key_dates = []
                doc.risks = ["AI analysis failed. Review extracted fields before use."]
                doc.opportunities = [
                    "Reprocess this document after AI connectivity is restored."
                ]
                doc.extracted_data = structured_data
        else:
            doc.confidence_score = 0.35 if text else 0.0
            doc.ai_summary = (
                "AI analysis not configured (no API key). Fallback extraction used."
            )
            doc.key_dates = []
            doc.risks = []
            doc.opportunities = []
            doc.extracted_data = structured_data

        current_data = (
            dict(doc.extracted_data) if isinstance(doc.extracted_data, dict) else {}
        )
        current_data["_extraction"] = extraction_meta
        if analysis_error:
            current_data["_analysis_error"] = analysis_error

        onboarding_hint = self._build_onboarding_hint(
            extracted_data=current_data,
            text=text,
            filename=doc.original_filename,
        )
        if onboarding_hint:
            current_data["onboarding_hint"] = onboarding_hint
        doc.extracted_data = current_data

        if extraction_meta.get("text_length", 0) < 40:
            doc.status = "review_required"
            doc.risks = list(
                {
                    *(doc.risks or []),
                    "Low text extraction quality; manual review recommended.",
                }
            )
        else:
            doc.status = "processed"

        doc.processed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    def _extract_text(
        self, content: bytes, mime_type: str, filename: str
    ) -> tuple[str, dict[str, Any]]:
        extension = Path(filename or "").suffix.lower()
        methods: list[str] = []
        text = ""

        if mime_type == "application/pdf" or extension == ".pdf":
            methods.append("pdfminer")
            text = self._extract_pdf_text(content)

        if not text and (mime_type in DOCX_MIME_TYPES or extension == ".docx"):
            methods.append("docx_xml")
            text = self._extract_docx_text(content)

        if not text and (
            mime_type.startswith("image/") or extension in IMAGE_EXTENSIONS
        ):
            methods.append("ocr")
            text = self._extract_image_text(content)

        if not text:
            methods.append("text_decode")
            text = self._decode_text(content)

        cleaned = _clean_text(text)
        meta = {
            "methods": methods,
            "mime_type": mime_type,
            "text_length": len(cleaned),
            "looks_low_quality": self._is_low_quality_text(cleaned),
        }
        return cleaned, meta

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams

            output = io.StringIO()
            extract_text_to_fp(io.BytesIO(content), output, laparams=LAParams())
            return output.getvalue()
        except Exception:
            return ""

    def _extract_docx_text(self, content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                xml_bytes = zf.read("word/document.xml")
            root = ElementTree.fromstring(xml_bytes)
            texts = [
                node.text
                for node in root.iter()
                if node.tag.endswith("}t") and node.text
            ]
            return "\n".join(texts)
        except Exception:
            return ""

    def _extract_image_text(self, content: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image, ImageOps

            image = Image.open(io.BytesIO(content))
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            grayscale = ImageOps.grayscale(image)
            return pytesseract.image_to_string(grayscale, config="--oem 3 --psm 6")
        except Exception:
            return ""

    def _decode_text(self, content: bytes) -> str:
        encodings = ("utf-8", "utf-16", "latin-1", "cp1252")
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except Exception:
                continue
        return ""

    def _is_low_quality_text(self, text: str) -> bool:
        if not text or len(text) < 40:
            return True
        alpha = sum(ch.isalnum() for ch in text)
        return (alpha / max(len(text), 1)) < 0.35

    def _extract_structured_data(self, text: str, filename: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if not text:
            return data

        data["candidate_client_name"] = self._extract_candidate_name(text, filename)
        entity_type = self._infer_entity_type(text, filename)
        if entity_type:
            data["entity_type"] = entity_type

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text
        )
        if email_match:
            data["contact_email"] = email_match.group(0)

        phone_match = re.search(
            r"(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
        )
        if phone_match:
            data["contact_phone"] = re.sub(r"\s+", "", phone_match.group(0))

        ein_match = re.search(r"\b\d{2}-\d{7}\b", text)
        if ein_match:
            data["ein"] = ein_match.group(0)

        ssn_match = re.search(r"\b\d{3}-\d{2}-(\d{4})\b", text)
        if ssn_match:
            data["ssn_last4"] = ssn_match.group(1)

        data["annual_revenue_range"] = self._infer_revenue_range(text)

        industry = self._infer_industry(text)
        if industry:
            data["industry"] = industry

        return {k: v for k, v in data.items() if v not in (None, "")}

    def _extract_candidate_name(self, text: str, filename: str) -> str:
        label_patterns = [
            r"(?:Business Name|Company Name|Client Name|Borrower Name|Account Holder)\s*[:\-]\s*([^\n\r]{3,80})",
            r"\bName\s*[:\-]\s*([^\n\r]{3,80})",
        ]
        for pattern in label_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = _clean_text(match.group(1))
                if len(value) >= 3 and not value.isdigit():
                    return value
        return _fallback_client_name(filename)

    def _infer_entity_type(self, text: str, filename: str) -> str:
        source = f"{filename}\n{text}".lower()
        if re.search(r"\b(llc|inc|corp|corporation|company|ltd|pllc|gmbh)\b", source):
            return "business"
        if "trust" in source:
            return "trust"
        return "person"

    def _infer_revenue_range(self, text: str) -> str | None:
        amounts = []
        for raw in re.findall(r"\$\s*([\d,]+(?:\.\d{2})?)", text):
            clean = raw.replace(",", "")
            try:
                amounts.append(float(clean))
            except ValueError:
                continue
        if not amounts:
            return None

        max_amount = max(amounts)
        for threshold, label in REVENUE_RANGES:
            if max_amount <= threshold:
                return label
        return None

    def _infer_industry(self, text: str) -> str | None:
        industry_hints = {
            "Real Estate": ["property", "tenant", "lease", "real estate"],
            "Healthcare": ["patient", "clinic", "medical", "health"],
            "Technology": ["software", "saas", "technology", "api", "cloud"],
            "Retail": ["retail", "inventory", "store", "sku"],
            "Hospitality": ["hotel", "hospitality", "restaurant", "booking"],
            "Construction": ["construction", "contractor", "project site", "materials"],
        }
        lower = text.lower()
        for industry, hints in industry_hints.items():
            if any(hint in lower for hint in hints):
                return industry
        return None

    def _build_onboarding_hint(
        self,
        extracted_data: dict[str, Any],
        text: str,
        filename: str,
    ) -> dict[str, Any]:
        display_name = extracted_data.get(
            "candidate_client_name"
        ) or _fallback_client_name(filename)
        if not display_name:
            return {}

        hint: dict[str, Any] = {
            "display_name": display_name,
            "entity_type": extracted_data.get("entity_type")
            or self._infer_entity_type(text, filename),
            "industry": extracted_data.get("industry"),
            "annual_revenue_range": extracted_data.get("annual_revenue_range"),
            "profile_json": {
                "ein": extracted_data.get("ein"),
                "ssn_last4": extracted_data.get("ssn_last4"),
                "contact_email": extracted_data.get("contact_email"),
                "contact_phone": extracted_data.get("contact_phone"),
            },
        }
        profile = hint["profile_json"]
        if isinstance(profile, dict):
            hint["profile_json"] = {k: v for k, v in profile.items() if v}
        return hint

    async def auto_onboard_document(
        self,
        doc: Document,
        user: User,
        client_id: uuid.UUID | None = None,
    ) -> Client:
        extracted_data = (
            doc.extracted_data if isinstance(doc.extracted_data, dict) else {}
        )
        hint = (
            extracted_data.get("onboarding_hint")
            if isinstance(extracted_data.get("onboarding_hint"), dict)
            else {}
        )

        display_name = hint.get("display_name") or _fallback_client_name(
            doc.original_filename
        )
        entity_type = hint.get("entity_type") or "person"
        industry = hint.get("industry")
        annual_revenue_range = hint.get("annual_revenue_range")
        profile_json = (
            hint.get("profile_json")
            if isinstance(hint.get("profile_json"), dict)
            else {}
        )

        if client_id:
            result = await self.db.execute(
                select(Client).where(
                    Client.id == client_id, Client.org_id == user.org_id
                )
            )
            client = result.scalar_one_or_none()
            if not client:
                raise NotFoundError("Client", str(client_id))

            if not client.industry and industry:
                client.industry = industry
            if not client.annual_revenue_range and annual_revenue_range:
                client.annual_revenue_range = annual_revenue_range
            if profile_json:
                existing_profile = (
                    client.profile_json if isinstance(client.profile_json, dict) else {}
                )
                client.profile_json = _merge_dict(existing_profile, profile_json)
            doc.client_id = client.id
            await self.db.commit()
            await self.db.refresh(client)
            return client

        client = Client(
            org_id=user.org_id,
            display_name=display_name,
            entity_type=entity_type,
            industry=industry,
            annual_revenue_range=annual_revenue_range,
            profile_json=profile_json or None,
        )
        self.db.add(client)
        await self.db.flush()
        doc.client_id = client.id
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def reprocess_document(self, doc: Document) -> Document:
        content = await self.storage.load(doc.filename)
        return await self._process_document(doc, content)

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

CONTENT_CLASSIFICATION_PATTERNS: list[tuple[str, str, float]] = [
    (
        r"(beginning balance|ending balance|account summary|deposits? and|withdrawals?|checking|savings)",
        "bank_statement",
        0.75,
    ),
    (
        r"(form 1040|adjusted gross income|taxable income|filing status|schedule [a-e]|w-?2 wage|1099-)",
        "tax_return",
        0.80,
    ),
    (
        r"(agreement|whereas|hereby|covenant|binding|term of|indemnif|arbitration|governing law)",
        "contract",
        0.70,
    ),
    (
        r"(invoice number|invoice date|bill to|amount due|subtotal|total due|payment terms|qty|unit price)",
        "invoice",
        0.80,
    ),
    (
        r"(credit score|fico|equifax|experian|transunion|credit bureau|payment history|credit utilization)",
        "credit_report",
        0.80,
    ),
    (
        r"(driver.?s? licen|passport number|date of birth|issuing authority|social security|government.?issued)",
        "government",
        0.70,
    ),
]


def classify_by_filename(filename: str) -> str:
    lower = filename.lower()
    for pattern, doc_type in FILENAME_PATTERNS:
        if re.search(pattern, lower):
            return doc_type
    return "other"


def classify_by_content(text: str) -> tuple[str, float]:
    """Classify document type by analyzing text content. Returns (doc_type, confidence)."""
    if not text or len(text) < 20:
        return "other", 0.1

    lower = text.lower()
    best_type = "other"
    best_score = 0.0

    for pattern, doc_type, base_confidence in CONTENT_CLASSIFICATION_PATTERNS:
        matches = re.findall(pattern, lower)
        if matches:
            score = min(base_confidence + (len(matches) - 1) * 0.05, 0.95)
            if score > best_score:
                best_score = score
                best_type = doc_type

    if best_score == 0.0 and len(text) >= 40:
        best_score = 0.2

    return best_type, round(best_score, 2)


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

        # Content-based classification (always runs — improves on filename-only guess)
        content_type, content_confidence = classify_by_content(text)
        if content_type != "other":
            doc.doc_type = content_type
        elif doc.doc_type == "other":
            doc.doc_type = classify_by_filename(doc.original_filename)

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
            doc.confidence_score = content_confidence if text else 0.0
            fallback = self._build_fallback_analysis(
                text=text,
                filename=doc.original_filename,
                doc_type=doc.doc_type,
                structured_data=structured_data,
            )
            doc.ai_summary = fallback["summary"]
            doc.key_dates = fallback["key_dates"]
            doc.risks = fallback["risks"]
            doc.opportunities = fallback["opportunities"]
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

    def _build_fallback_analysis(
        self,
        text: str,
        filename: str,
        doc_type: str,
        structured_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build rich analysis output without AI — uses pattern matching and heuristics."""
        summary_parts: list[str] = []
        risks: list[str] = []
        opportunities: list[str] = []

        # Document type insight
        doc_type_labels = {
            "bank_statement": "Bank Statement",
            "tax_return": "Tax Return",
            "contract": "Contract / Agreement",
            "invoice": "Invoice / Bill",
            "credit_report": "Credit Report",
            "government": "Government ID Document",
            "other": "Document",
        }
        type_label = doc_type_labels.get(doc_type, "Document")
        client_name = structured_data.get("candidate_client_name", "")

        if client_name and client_name != "New Client":
            summary_parts.append(f"{type_label} associated with {client_name}.")
        else:
            summary_parts.append(f"Uploaded {type_label} ({filename}).")

        # Extract monetary values for reporting
        monetary = self._extract_monetary_values(text)
        if monetary:
            structured_data["monetary_values"] = monetary
            amounts = list(monetary.values())
            if amounts:
                total = sum(amounts)
                summary_parts.append(
                    f"Contains {len(amounts)} monetary value(s) totaling ${total:,.2f}."
                )

        # Extract dates
        key_dates = self._extract_dates_from_text(text)
        if key_dates:
            summary_parts.append(f"Found {len(key_dates)} key date(s) in document.")

        # Doc-type-specific insights
        type_insights = self._generate_doc_type_insights(text, doc_type)
        risks.extend(type_insights.get("risks", []))
        opportunities.extend(type_insights.get("opportunities", []))
        if type_insights.get("summary_extra"):
            summary_parts.append(type_insights["summary_extra"])

        # Contact / entity info
        entity_type = structured_data.get("entity_type", "")
        industry = structured_data.get("industry", "")
        if entity_type:
            summary_parts.append(f"Entity type: {entity_type}.")
        if industry:
            summary_parts.append(f"Industry: {industry}.")
        if structured_data.get("contact_email"):
            summary_parts.append(f"Contact: {structured_data['contact_email']}.")

        # Revenue range
        rev = structured_data.get("annual_revenue_range")
        if rev:
            summary_parts.append(f"Estimated revenue range: {rev}.")

        # General risk/opportunity for unclassified
        if doc_type == "other":
            risks.append(
                "Document type could not be auto-classified. Manual review recommended."
            )
            opportunities.append(
                "Reprocess with AI analysis enabled for deeper insights."
            )

        if not risks and text:
            risks.append(
                "Review extracted fields to confirm accuracy of automated extraction."
            )

        if not opportunities:
            opportunities.append(
                "Link this document to a client to enrich their profile with extracted data."
            )

        return {
            "summary": " ".join(summary_parts),
            "key_dates": key_dates,
            "risks": risks,
            "opportunities": opportunities,
        }

    def _extract_dates_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract dates with context descriptions from document text."""
        if not text:
            return []

        date_patterns = [
            # Labeled dates: "Date: Jan 15, 2024" or "Due Date: 01/15/2024"
            (
                r"((?:due|invoice|statement|effective|expiration|start|end|closing|opening|filing|issued?)\s*date)\s*[:\-]\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                None,
            ),
            (
                r"((?:due|invoice|statement|effective|expiration|start|end|closing|opening|filing|issued?)\s*date)\s*[:\-]\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\.?\s+\d{1,2},?\s+\d{4})",
                None,
            ),
            # Period: "Period: 01/01/2024 - 01/31/2024" or "for the period ending"
            (
                r"(?:period|from)\s*[:\-]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|through|\-)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                "period",
            ),
        ]

        results: list[dict[str, str]] = []
        seen: set[str] = set()

        for pattern, fixed_label in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if fixed_label == "period":
                    date_str = f"{match.group(1)} to {match.group(2)}"
                    desc = "Statement/reporting period"
                else:
                    label = _clean_text(match.group(1))
                    date_str = _clean_text(match.group(2))
                    desc = label.title()

                if date_str not in seen:
                    seen.add(date_str)
                    results.append({"date": date_str, "description": desc})

            if len(results) >= 10:
                break

        # Fallback: find standalone dates with some context
        if not results:
            for match in re.finditer(
                r"(\b\w{2,20}\b)\s*[:\-]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
                text[:3000],
            ):
                label = match.group(1).strip()
                date_str = match.group(2).strip()
                if date_str not in seen and label.isalpha():
                    seen.add(date_str)
                    results.append({"date": date_str, "description": label.title()})
                if len(results) >= 5:
                    break

        return results

    def _extract_monetary_values(self, text: str) -> dict[str, float]:
        """Extract labeled monetary values from text."""
        if not text:
            return {}

        money_patterns = [
            (
                r"(total|balance|amount due|subtotal|gross|net|payment|deposit|withdrawal|income|revenue|debit|credit)\s*[:\-]?\s*\$\s*([\d,]+(?:\.\d{2})?)",
                None,
            ),
            (r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:total|balance|due)", "reversed"),
        ]

        values: dict[str, float] = {}
        for pattern, mode in money_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if mode == "reversed":
                    label = "total"
                    raw_amount = match.group(1)
                else:
                    label = _clean_text(match.group(1)).lower()
                    raw_amount = match.group(2)

                clean = raw_amount.replace(",", "")
                try:
                    amount = float(clean)
                except ValueError:
                    continue

                # Use the largest value for each label
                key = label.replace(" ", "_")
                if key not in values or amount > values[key]:
                    values[key] = amount

            if len(values) >= 15:
                break

        return values

    def _generate_doc_type_insights(self, text: str, doc_type: str) -> dict[str, Any]:
        """Generate type-specific risks, opportunities, and extra summary text."""
        lower = text.lower() if text else ""
        result: dict[str, Any] = {"risks": [], "opportunities": [], "summary_extra": ""}

        if doc_type == "bank_statement":
            # Look for overdrafts, NSF, low balances
            if re.search(r"(overdraft|nsf|insufficient|negative balance)", lower):
                result["risks"].append(
                    "Overdraft or NSF fees detected — review account health."
                )
            if re.search(r"(recurring|automatic|autopay|subscription)", lower):
                result["summary_extra"] = "Recurring transactions detected."
            result["opportunities"].append(
                "Use bank statement data to verify cash flow and support lending applications."
            )

        elif doc_type == "tax_return":
            if re.search(r"(loss|negative|deficit|carryforward)", lower):
                result["risks"].append(
                    "Document indicates losses or deficit — verify current financial health."
                )
            result["opportunities"].append(
                "Tax return data can pre-populate financial assessments and lending profiles."
            )
            result["opportunities"].append(
                "Cross-reference with bank statements for income verification."
            )

        elif doc_type == "contract":
            if re.search(
                r"(termination|penalty|breach|default|liquidated damages)", lower
            ):
                result["risks"].append(
                    "Contract contains termination clauses or penalty terms that need review."
                )
            if re.search(r"(renewal|auto.?renew|option to extend)", lower):
                result["opportunities"].append(
                    "Contract has renewal/extension options — set reminder for review dates."
                )
            result["opportunities"].append(
                "Extract key terms and deadlines for task automation."
            )

        elif doc_type == "invoice":
            if re.search(r"(overdue|past due|late fee|collection)", lower):
                result["risks"].append("Invoice shows overdue status or late fees.")
            result["opportunities"].append(
                "Track invoice for accounts receivable/payable management."
            )

        elif doc_type == "credit_report":
            if re.search(
                r"(delinquent|collections?|charge.?off|late payment|negative)", lower
            ):
                result["risks"].append(
                    "Negative items found on credit report — may affect lending eligibility."
                )
            if re.search(r"(excellent|good standing|no derog)", lower):
                result["opportunities"].append(
                    "Credit report shows positive standing — leverage for better rates."
                )
            result["opportunities"].append(
                "Use credit data to build dispute strategies or improvement plans."
            )

        elif doc_type == "government":
            if re.search(r"(expired|expir)", lower):
                result["risks"].append(
                    "Government document may be expired — verify validity dates."
                )
            result["opportunities"].append(
                "Use identity document for KYC/compliance verification."
            )

        return result

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

        # Extract labeled monetary values
        monetary = self._extract_monetary_values(text)
        if monetary:
            data["monetary_values"] = monetary

        # Extract address
        address = self._extract_address(text)
        if address:
            data["address"] = address

        return {k: v for k, v in data.items() if v not in (None, "", {})}

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
            "Financial Services": [
                "banking",
                "loan",
                "mortgage",
                "investment",
                "insurance",
            ],
            "Legal": ["attorney", "law firm", "counsel", "litigation", "plaintiff"],
            "Education": ["school", "university", "student", "tuition", "academic"],
            "Transportation": ["freight", "shipping", "logistics", "fleet", "carrier"],
        }
        lower = text.lower()
        for industry, hints in industry_hints.items():
            if any(hint in lower for hint in hints):
                return industry
        return None

    def _extract_address(self, text: str) -> str | None:
        """Extract a US-style mailing address from text."""
        # Look for state+zip pattern which anchors an address
        match = re.search(
            r"([\w\s.#]+(?:st(?:reet)?|ave(?:nue)?|blvd|dr(?:ive)?|rd|ln|way|ct|pl|pkwy|hwy|suite|ste|unit|apt)[\w\s.,#]*\b[A-Z]{2}\s+\d{5}(?:-\d{4})?)",
            text,
            re.IGNORECASE,
        )
        if match:
            addr = _clean_text(match.group(1))
            if 15 < len(addr) < 200:
                return addr
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

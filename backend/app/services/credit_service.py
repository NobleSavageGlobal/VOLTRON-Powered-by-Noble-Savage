from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.credit import Collection, CreditReport, Dispute, DisputeLetter, Tradeline

logger = get_logger(__name__)


class CreditService:
    async def process_credit_report(
        self,
        db: AsyncSession,
        client_id: uuid.UUID,
        document_id: uuid.UUID | None = None,
    ) -> CreditReport:
        report = CreditReport(
            client_id=client_id,
            raw_document_id=document_id,
            source="upload" if document_id else "provider",
            status="processed",
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        return report

    async def get_credit_reports(self, db: AsyncSession, client_id: uuid.UUID) -> list[CreditReport]:
        result = await db.execute(
            select(CreditReport).where(CreditReport.client_id == client_id).order_by(CreditReport.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_dispute(self, db: AsyncSession, client_id: uuid.UUID, data: dict) -> Dispute:
        dispute = Dispute(client_id=client_id, **data)
        db.add(dispute)
        await db.flush()
        await db.refresh(dispute)
        return dispute

    async def update_dispute(self, db: AsyncSession, dispute_id: uuid.UUID, data: dict) -> Dispute:
        result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
        dispute = result.scalar_one_or_none()
        if not dispute:
            raise NotFoundError("Dispute", str(dispute_id))
        for k, v in data.items():
            if v is not None:
                setattr(dispute, k, v)
        await db.flush()
        await db.refresh(dispute)
        return dispute

    async def list_disputes(self, db: AsyncSession, client_id: uuid.UUID) -> list[Dispute]:
        result = await db.execute(
            select(Dispute).where(Dispute.client_id == client_id).order_by(Dispute.created_at.desc())
        )
        return list(result.scalars().all())

    async def generate_dispute_letter(
        self, db: AsyncSession, dispute_id: uuid.UUID, user_id: uuid.UUID
    ) -> DisputeLetter:
        result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
        dispute = result.scalar_one_or_none()
        if not dispute:
            raise NotFoundError("Dispute", str(dispute_id))

        content = (
            f"To Whom It May Concern,\n\n"
            f"I am writing to dispute the following item with {dispute.bureau}.\n"
            f"Issue: {dispute.issue_type}\n"
            f"Furnisher: {dispute.furnisher or 'Unknown'}\n\n"
            f"Please investigate and correct this information.\n\nSincerely,\n[Client Name]"
        )
        letter = DisputeLetter(
            dispute_id=dispute_id,
            template_version="1.0",
            content_text=content,
            created_by=user_id,
        )
        db.add(letter)
        await db.flush()
        await db.refresh(letter)
        return letter

    async def get_credit_health_factors(self, db: AsyncSession, client_id: uuid.UUID) -> dict:
        reports = await self.get_credit_reports(db, client_id)
        if not reports:
            return {"derogatory_count": 0, "utilization_avg": 0.0, "collection_total": 0.0}

        latest = reports[0]
        tl_result = await db.execute(
            select(Tradeline).where(Tradeline.credit_report_id == latest.id)
        )
        tradelines = list(tl_result.scalars().all())
        coll_result = await db.execute(
            select(Collection).where(Collection.credit_report_id == latest.id)
        )
        collections = list(coll_result.scalars().all())

        derogatory = sum(1 for t in tradelines if t.payment_status and "derog" in t.payment_status.lower())
        utils = [float(t.utilization) for t in tradelines if t.utilization is not None]
        utilization_avg = sum(utils) / len(utils) if utils else 0.0
        collection_total = float(sum(Decimal(str(c.amount or 0)) for c in collections))

        return {
            "derogatory_count": derogatory,
            "utilization_avg": utilization_avg,
            "collection_total": collection_total,
        }

credit_service = CreditService()

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.decision import DecisionPlan, PlanAction, ScoringSnapshot
from app.services.ai_service import AIService

logger = get_logger(__name__)
_ai = AIService()


class DecisionService:
    async def generate_plan(
        self,
        db: AsyncSession,
        client_id: uuid.UUID,
        org_id: uuid.UUID,
        goal: str,
        time_horizon_days: int,
    ) -> DecisionPlan:
        snapshot = {"client_id": str(client_id), "goal": goal, "time_horizon_days": time_horizon_days}
        try:
            plan_data = await _ai.generate_decision_plan(snapshot, [], goal)
        except Exception as exc:
            logger.warning("AI plan generation failed, using default", error=str(exc))
            plan_data = {
                "plan_title": f"Action Plan: {goal}",
                "actions": [
                    {
                        "id": "A1",
                        "type": "request_info",
                        "title": "Complete financial profile",
                        "why": "Full data required to generate a precise plan",
                        "depends_on": [],
                        "due_in_days": 7,
                        "success_metric": "All required documents uploaded",
                        "evidence_refs": [],
                        "risk_flags": ["low_confidence"],
                    }
                ],
            }

        plan = DecisionPlan(
            client_id=client_id,
            org_id=org_id,
            plan_title=plan_data.get("plan_title", f"Plan: {goal}"),
            plan_version=1,
            status="draft",
            generated_by="system",
            goal=goal,
            time_horizon_days=time_horizon_days,
        )
        db.add(plan)
        await db.flush()

        for i, ad in enumerate(plan_data.get("actions", [])):
            action = PlanAction(
                plan_id=plan.id,
                action_code=ad.get("id", f"A{i + 1}"),
                action_type=ad.get("type", "other"),
                title=ad.get("title", "Action"),
                description=ad.get("why"),
                why=ad.get("why"),
                depends_on=ad.get("depends_on", []),
                due_in_days=ad.get("due_in_days"),
                success_metric=ad.get("success_metric"),
                evidence_refs=ad.get("evidence_refs", []),
                risk_flags=ad.get("risk_flags", []),
                status="pending",
            )
            db.add(action)

        await db.commit()
        await db.refresh(plan)
        return plan

    async def get_plans(self, db: AsyncSession, client_id: uuid.UUID) -> list[DecisionPlan]:
        result = await db.execute(
            select(DecisionPlan)
            .where(DecisionPlan.client_id == client_id)
            .order_by(DecisionPlan.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_plan(self, db: AsyncSession, plan_id: uuid.UUID, org_id: uuid.UUID) -> DecisionPlan:
        result = await db.execute(
            select(DecisionPlan).where(DecisionPlan.id == plan_id, DecisionPlan.org_id == org_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise AppException(404, "Plan not found")
        return plan

    async def get_plan_actions(self, db: AsyncSession, plan_id: uuid.UUID) -> list[PlanAction]:
        result = await db.execute(
            select(PlanAction).where(PlanAction.plan_id == plan_id).order_by(PlanAction.action_code)
        )
        return list(result.scalars().all())

    async def publish_plan(self, db: AsyncSession, plan_id: uuid.UUID, org_id: uuid.UUID) -> DecisionPlan:
        plan = await self.get_plan(db, plan_id, org_id)
        plan.status = "published"
        plan.published_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(plan)
        return plan

    async def update_action_status(
        self, db: AsyncSession, action_id: uuid.UUID, status: str, user_id: uuid.UUID | None = None
    ) -> PlanAction:
        result = await db.execute(select(PlanAction).where(PlanAction.id == action_id))
        action = result.scalar_one_or_none()
        if not action:
            raise AppException(404, "Action not found")
        action.status = status
        if status == "approved" and user_id:
            action.approved_by = user_id
            action.approved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(action)
        return action

    async def compute_scores(self, db: AsyncSession, client_id: uuid.UUID) -> list[ScoringSnapshot]:
        inputs = {"client_id": str(client_id), "ts": datetime.now(timezone.utc).isoformat()}
        inputs_hash = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:64]

        score_defs = [
            ("financial_health", Decimal("65.00"), {"status": "partial", "note": "Based on available data"}),
            ("funding_readiness", Decimal("55.00"), {"status": "partial", "note": "Complete profile to improve score"}),
        ]
        snapshots = []
        for score_type, score_val, factors in score_defs:
            snap = ScoringSnapshot(
                client_id=client_id,
                score_type=score_type,
                score=score_val,
                factors_json=factors,
                inputs_hash=inputs_hash,
            )
            db.add(snap)
            snapshots.append(snap)

        await db.commit()
        return snapshots

    async def get_latest_scores(self, db: AsyncSession, client_id: uuid.UUID) -> list[ScoringSnapshot]:
        result = await db.execute(
            select(ScoringSnapshot)
            .where(ScoringSnapshot.client_id == client_id)
            .order_by(ScoringSnapshot.computed_at.desc())
        )
        all_scores = list(result.scalars().all())
        seen: set[str] = set()
        latest = []
        for s in all_scores:
            if s.score_type not in seen:
                seen.add(s.score_type)
                latest.append(s)
        return latest


decision_service = DecisionService()

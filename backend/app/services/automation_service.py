from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.automation import AutomationEvent, Workflow, WorkflowRun

logger = get_logger(__name__)


class AutomationService:
    async def create_workflow(self, db: AsyncSession, org_id: uuid.UUID, data: dict) -> Workflow:
        workflow = Workflow(
            org_id=org_id,
            name=data["name"],
            trigger_type=data["trigger_type"],
            trigger_config=data.get("trigger_config", {}),
            actions=data.get("actions", []),
            status="active",
        )
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        return workflow

    async def list_workflows(self, db: AsyncSession, org_id: uuid.UUID) -> list[Workflow]:
        result = await db.execute(
            select(Workflow).where(Workflow.org_id == org_id).order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_workflow(
        self, db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID, updates: dict
    ) -> Workflow:
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.org_id == org_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise AppException(404, "Workflow not found")
        for k, v in updates.items():
            if hasattr(workflow, k) and k not in ("id", "org_id", "created_at"):
                setattr(workflow, k, v)
        await db.commit()
        await db.refresh(workflow)
        return workflow

    async def emit_event(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        event_type: str,
        payload: dict,
        client_id: uuid.UUID | None = None,
    ) -> AutomationEvent:
        event = AutomationEvent(
            org_id=org_id, event_type=event_type, payload_json=payload, client_id=client_id
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: uuid.UUID,
        org_id: uuid.UUID,
        trigger_event: dict | None = None,
    ) -> WorkflowRun:
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id, Workflow.org_id == org_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise AppException(404, "Workflow not found")

        run = WorkflowRun(
            workflow_id=workflow_id,
            status="running",
            trigger_event=trigger_event or {"manual": True},
            steps_log=[],
            idempotency_key=f"{workflow_id}:{datetime.now(timezone.utc).isoformat()}",
        )
        db.add(run)
        await db.flush()

        steps: list[dict] = []
        success = True
        for i, action in enumerate(workflow.actions or []):
            atype = action.get("type", "unknown")
            step: dict = {"step": i + 1, "type": atype}
            try:
                step["status"] = "completed"
                step["result"] = f"Action '{atype}' executed (stub)"
            except Exception as exc:
                step["status"] = "failed"
                step["error"] = str(exc)
                success = False
            steps.append(step)

        run.steps_log = steps
        run.status = "completed" if success else "failed"
        run.completed_at = datetime.now(timezone.utc)
        workflow.run_count = (workflow.run_count or 0) + 1
        workflow.last_triggered_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(run)
        return run

    async def get_workflow_runs(self, db: AsyncSession, org_id: uuid.UUID, limit: int = 50) -> list[WorkflowRun]:
        result = await db.execute(
            select(WorkflowRun)
            .join(Workflow, WorkflowRun.workflow_id == Workflow.id)
            .where(Workflow.org_id == org_id)
            .order_by(WorkflowRun.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_events(self, db: AsyncSession, org_id: uuid.UUID, limit: int = 50) -> list[AutomationEvent]:
        result = await db.execute(
            select(AutomationEvent)
            .where(AutomationEvent.org_id == org_id)
            .order_by(AutomationEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


automation_service = AutomationService()

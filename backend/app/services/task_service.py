from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_tasks_by_org(
        self,
        org_id: str,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[Task]:
        query = select(Task).where(Task.org_id == org_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_from_ai(
        self,
        org_id: str,
        created_by: str,
        task_data: list[dict[str, Any]],
    ) -> list[Task]:
        tasks: list[Task] = []
        for item in task_data:
            task = Task(
                org_id=org_id,
                created_by=created_by,
                title=item.get("title", "Untitled Task"),
                description=item.get("description"),
                priority=item.get("priority", "medium"),
                source="ai_generated",
            )
            self.db.add(task)
            tasks.append(task)
        await self.db.commit()
        return tasks

    async def mark_complete(self, task: Task) -> Task:
        task.status = "done"
        task.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(task)
        return task

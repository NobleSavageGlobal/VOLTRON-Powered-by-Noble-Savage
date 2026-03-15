from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DB
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    db: DB,
) -> Task:
    if not current_user.org_id:
        raise ForbiddenError("You must belong to an organization to create tasks")

    task = Task(
        org_id=current_user.org_id,
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        assigned_to=payload.assigned_to,
        source=payload.source,
        metadata_=payload.metadata_,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    current_user: CurrentUser,
    db: DB,
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TaskListResponse:
    if not current_user.org_id:
        return TaskListResponse(items=[], total=0, page=page, page_size=page_size)

    query = select(Task).where(Task.org_id == current_user.org_id)
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return TaskListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.org_id == current_user.org_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", str(task_id))
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: CurrentUser,
    db: DB,
) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.org_id == current_user.org_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", str(task_id))

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    if payload.status == "done" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.org_id == current_user.org_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", str(task_id))
    await db.delete(task)
    await db.commit()

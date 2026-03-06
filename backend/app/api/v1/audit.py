from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DB
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: CurrentUser,
    db: DB,
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> AuditLogListResponse:
    if not current_user.org_id:
        return AuditLogListResponse(items=[], total=0, page=page, page_size=page_size)

    query = select(AuditLog).where(AuditLog.org_id == current_user.org_id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)

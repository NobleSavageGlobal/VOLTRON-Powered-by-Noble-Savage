from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=OrganizationResponse)
async def get_my_org(current_user: CurrentUser, db: DB) -> Organization:
    if not current_user.org_id:
        raise NotFoundError("Organization")

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", str(current_user.org_id))
    return org


@router.patch("/me", response_model=OrganizationResponse)
async def update_my_org(
    payload: OrganizationUpdate,
    current_user: CurrentUser,
    db: DB,
) -> Organization:
    if current_user.role not in ("admin",):
        raise ForbiddenError("Only admins can update organization settings")

    if not current_user.org_id:
        raise NotFoundError("Organization")

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", str(current_user.org_id))

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org


@router.get("/me/members", response_model=list[UserResponse])
async def list_members(current_user: CurrentUser, db: DB) -> list[User]:
    if not current_user.org_id:
        return []

    result = await db.execute(
        select(User).where(User.org_id == current_user.org_id)
    )
    return list(result.scalars().all())

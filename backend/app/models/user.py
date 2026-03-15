from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="entrepreneur")
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="uploader", foreign_keys="Document.uploaded_by"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="assignee", foreign_keys="Task.assigned_to"
    )
    created_tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="creator", foreign_keys="Task.created_by"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")  # noqa: F821

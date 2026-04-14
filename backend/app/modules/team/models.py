"""Role & TeamInvitation models for the RBAC system."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseModel


class Role(BaseModel):
    """A permission role scoped to an organization.

    ``is_system`` distinguishes the six built-in roles (Owner, Admin, Editor,
    Designer, Viewer, VA) from user-created custom roles.
    """

    __tablename__ = "roles"

    org_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    __table_args__ = (
        Index("ix_roles_org_name_unique", "org_id", "name", unique=True),
    )


class TeamInvitation(BaseModel):
    __tablename__ = "team_invitations"

    org_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

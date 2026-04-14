"""Pydantic schemas for team management & roles."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ModulePermissions(BaseModel):
    view: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False
    publish: bool = False


PermissionsMap = dict[str, dict[str, bool]]


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: PermissionsMap = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[PermissionsMap] = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    description: Optional[str] = None
    permissions: PermissionsMap = Field(default_factory=dict)
    is_system: bool = False
    created_at: datetime


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    name: Optional[str] = None
    role_id: Optional[UUID] = None
    role_name: Optional[str] = None
    status: str = "active"
    joined_at: Optional[datetime] = None


class InviteCreate(BaseModel):
    email: EmailStr
    role_id: UUID
    message: Optional[str] = None


class RoleAssign(BaseModel):
    role_id: UUID


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    email: str
    role_id: UUID
    role_name: Optional[str] = None
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime

"""User, ApiKey, and UserSession models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    WRITER = "writer"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.VIEWER,
        server_default="viewer",
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Platform administration is not an organization role. Every /admin
    # endpoint is platform-wide — list_users does `select(User)` with no org
    # filter, and the feature flags are global — so guarding them with
    # require_role("admin", "owner") let any org owner read every tenant's
    # users and flip flags for all of them. This bit is the real guard, and it
    # is granted deliberately: nobody has it by default.
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    onboarding_state: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Auth-specific columns (registration, password reset, MFA)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verify_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    email_verify_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    password_reset_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    mfa_backup_codes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user", lazy="selectin", foreign_keys="[ApiKey.created_by]")
    sessions = relationship("UserSession", back_populates="user", lazy="selectin")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", lazy="selectin")
    writing_sessions = relationship("WritingSession", back_populates="user", lazy="selectin")
    book_versions = relationship("BookVersion", back_populates="created_by_user", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("email", name="users_email_key"),
        Index("ix_users_role", "role"),
        Index("ix_users_preferences_gin", "preferences", postgresql_using="gin"),
        Index("ix_users_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_users_org_id_created_at", "org_id", "created_at"),
    )


class OAuthAccount(BaseModel):
    """Stores linked OAuth provider accounts for a user."""

    __tablename__ = "oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # "google" | "github"
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(320), nullable=True, default=None)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        Index("ix_oauth_accounts_provider_user", "provider", "provider_user_id", unique=True),
        Index("ix_oauth_accounts_user_provider", "user_id", "provider", unique=True),
        Index("ix_oauth_accounts_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ApiKey(BaseModel):
    __tablename__ = "api_keys"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    organization = relationship("Organization", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys", foreign_keys=[created_by])

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    # NOT NULL in the database with no default, and nothing writes it — so
    # every insert into this table against the migrated schema failed. It
    # is superseded by `created_by`; relaxed rather than dropped.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, default=None
    )

    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_scopes_gin", "scopes", postgresql_using="gin"),
        Index("ix_api_keys_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_api_keys_is_active", "is_active"),
    )


class UserSession(BaseModel):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, default=None)
    refresh_token_hash: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True, default=None)
    device_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_user_sessions_device_info_gin", "device_info", postgresql_using="gin"),
        Index("ix_user_sessions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_user_sessions_revoked_at", "revoked_at"),
    )


class RefreshToken(BaseModel):
    """A persisted refresh token, for revocation.

    Migration 002 created this table and nothing has ever read it — refresh
    tokens are signed JWTs and are not looked up anywhere. It is declared here
    so the schema is visible in the model layer rather than existing only in
    the database, and so `alembic check` compares like with like. Session
    revocation (T-004) is what would use it.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        UniqueConstraint("token_hash", name="refresh_tokens_token_hash_key"),
        Index("ix_refresh_tokens_user_active", "user_id", "revoked"),
        Index("ix_refresh_tokens_active", "id", postgresql_where=text("deleted_at IS NULL")),
    )

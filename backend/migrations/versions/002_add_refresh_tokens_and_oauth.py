"""Add refresh_tokens and oauth_accounts tables.

Revision ID: 002_refresh_tokens_oauth
Revises: 001_initial_schema
Create Date: 2025-01-15 12:00:00.000000
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "002_refresh_tokens_oauth"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # -- refresh_tokens --------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])
    op.create_index(
        "ix_refresh_tokens_active",
        "refresh_tokens",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_refresh_tokens_user_active",
        "refresh_tokens",
        ["user_id", "revoked"],
    )

    # -- oauth_accounts --------------------------------------------------------
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])
    op.create_index("ix_oauth_accounts_provider", "oauth_accounts", ["provider"])
    op.create_index(
        "uq_oauth_accounts_provider_user",
        "oauth_accounts",
        ["provider", "provider_user_id"],
        unique=True,
    )
    op.create_index("ix_oauth_accounts_email", "oauth_accounts", ["email"])
    op.create_index(
        "ix_oauth_accounts_active",
        "oauth_accounts",
        ["id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_oauth_accounts_user_provider",
        "oauth_accounts",
        ["user_id", "provider"],
    )


def downgrade() -> None:
    op.drop_table("oauth_accounts")
    op.drop_table("refresh_tokens")

"""Add missing user auth columns to the users table.

The User model defines several auth-related columns (is_active, avatar_url,
email verification, password reset, and MFA fields) that were never added
in a migration.  This migration brings the database schema in line with the
ORM model.

Revision ID: a3b4c5d6e7f8
Revises: 005_add_billing_and_auth_columns
Create Date: 2026-02-10
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "a3b4c5d6e7f8"
down_revision: str | None = "005_add_billing_and_auth_columns"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Add auth-related columns to the users table.
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("email_verify_token", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verify_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("mfa_secret", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("mfa_backup_codes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Drop auth-related columns from the users table (reverse order).
    # ------------------------------------------------------------------
    op.drop_column("users", "mfa_backup_codes")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "email_verify_expires")
    op.drop_column("users", "email_verify_token")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "is_active")

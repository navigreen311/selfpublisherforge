"""Add users.is_platform_admin.

Platform administration is not an organization role. Every endpoint under
/admin is platform-wide — `list_users` selects from `users` with no org
filter, the feature flags carry no org_id — yet they were guarded with
`require_role("admin", "owner")`, which any organization's owner satisfies.
An org owner could therefore read every tenant's users and flip feature flags
for the whole platform.

The column is the guard. It defaults to false for everyone, including existing
rows: the first platform admin is granted deliberately, not inherited.

Revision ID: 024_platform_admin
Revises: 023_reconcile_schema_with_models
Create Date: 2026-09-11
"""

import sqlalchemy as sa
from alembic import op

revision = "024_platform_admin"
down_revision = "023_reconcile_schema_with_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_platform_admin", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_platform_admin")

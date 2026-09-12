"""Allow org-less system rows in dictation_commands.

`list_commands` selects `is_system IS TRUE OR org_id = :org`, so the built-in
commands are meant to be visible to every tenant and to belong to none. But
DictationCommand inherits TenantModel, which makes org_id NOT NULL, and the
seeder passed org_id=None — so the twelve built-in commands could never be
inserted. Widened for those rows; a custom command still carries its org, and
no org-scoped query can match NULL.

Revision ID: 025_dictation_system_commands
Revises: 024_platform_admin
Create Date: 2026-09-11
"""

import sqlalchemy as sa
from alembic import op

revision = "025_dictation_system_commands"
down_revision = "024_platform_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("dictation_commands", "org_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM dictation_commands WHERE org_id IS NULL")
    op.alter_column("dictation_commands", "org_id", existing_type=sa.Uuid(), nullable=False)

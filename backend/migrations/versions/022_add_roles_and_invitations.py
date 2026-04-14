"""Add roles & team_invitations tables, seed system roles (Final Gaps Stream 1 / RBAC).

Revision ID: 022_add_roles_and_invitations
Revises: 021_add_pen_names
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "022_add_roles_and_invitations"
down_revision = "021_add_pen_names"
branch_labels = None
depends_on = None


# ─── System role permission payloads ─────────────────────────────────────────
# Modules covered here are a representative subset of the real module list —
# the full list can be seeded via app code when new modules register, but this
# covers every module referenced by the Custom Role Builder mockup in the spec.
MODULES = [
    "dashboard",
    "projects",
    "market",
    "competitors",
    "reviews",
    "writing",
    "cover_design",
    "audiobook",
    "childrens_books",
    "coloring_books",
    "puzzle_books",
    "comic_books",
    "cookbooks",
    "style_profiles",
    "pipeline",
    "marketing",
    "publishing",
    "advertising",
    "analytics",
    "analytics_revenue",
    "pricing",
    "agents",
    "admin",
    "settings",
    "team",
    "billing",
    "pen_names",
]

ALL = {"view": True, "create": True, "edit": True, "delete": True, "publish": True}
VIEW = {"view": True, "create": False, "edit": False, "delete": False, "publish": False}
NONE = {"view": False, "create": False, "edit": False, "delete": False, "publish": False}
EDIT = {"view": True, "create": True, "edit": True, "delete": False, "publish": False}


def _owner() -> dict:
    return {m: dict(ALL) for m in MODULES}


def _admin() -> dict:
    perms = {m: dict(ALL) for m in MODULES}
    # Admin cannot delete the org (captured as delete on 'settings') or change billing
    perms["settings"] = {**ALL, "delete": False}
    perms["billing"] = dict(VIEW)
    return perms


def _editor() -> dict:
    perms = {m: dict(NONE) for m in MODULES}
    for m in (
        "dashboard", "projects", "market", "reviews", "competitors",
        "writing", "cover_design", "childrens_books", "coloring_books",
        "puzzle_books", "comic_books", "cookbooks", "pipeline",
        "style_profiles", "agents", "pen_names",
    ):
        perms[m] = dict(EDIT)
    perms["settings"] = dict(VIEW)
    perms["analytics"] = dict(VIEW)
    return perms


def _designer() -> dict:
    perms = {m: dict(NONE) for m in MODULES}
    for m in ("dashboard", "cover_design", "style_profiles"):
        perms[m] = dict(EDIT)
    for m in ("childrens_books", "coloring_books", "puzzle_books",
              "comic_books", "cookbooks", "projects"):
        perms[m] = dict(VIEW)
    perms["settings"] = dict(VIEW)
    return perms


def _viewer() -> dict:
    return {m: dict(VIEW) for m in MODULES}


def _va() -> dict:
    perms = {m: dict(NONE) for m in MODULES}
    for m in ("dashboard", "projects", "pipeline"):
        perms[m] = dict(EDIT)
    for m in ("writing", "childrens_books", "coloring_books",
              "puzzle_books", "cookbooks", "comic_books"):
        perms[m] = dict(EDIT)
    perms["settings"] = dict(VIEW)
    return perms


SYSTEM_ROLES = [
    ("Owner", "Full access to everything. Can delete organization. Cannot be removed.", _owner()),
    ("Admin", "Full access except org deletion and billing changes.", _admin()),
    ("Editor", "Create/edit content. No publish, team or financial access.", _editor()),
    ("Designer", "Cover design and illustration features only.", _designer()),
    ("Viewer", "Read-only access to all modules.", _viewer()),
    ("VA", "Task-focused access for virtual assistants.", _va()),
]


def upgrade() -> None:
    # ── roles ────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permissions", JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_system", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_roles_org", "roles", ["org_id"])
    op.create_index("ix_roles_org_name", "roles", ["org_id", "name"], unique=True)

    # ── team_invitations ─────────────────────────────────────────────────
    op.create_table(
        "team_invitations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True),
                  sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by", UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False,
                  server_default=sa.text("'pending'")),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_team_invitations_org", "team_invitations", ["org_id"])
    op.create_index("ix_team_invitations_email", "team_invitations", ["email"])
    op.create_index("ix_team_invitations_status", "team_invitations", ["status"])

    # ── users extensions ─────────────────────────────────────────────────
    bind = op.get_bind()
    insp = sa.inspect(bind)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "role_id" not in user_cols:
        op.add_column(
            "users",
            sa.Column("role_id", UUID(as_uuid=True),
                      sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
        )
    if "org_role" not in user_cols:
        op.add_column(
            "users",
            sa.Column("org_role", sa.String(length=50),
                      nullable=True, server_default=sa.text("'owner'")),
        )

    # ── Seed system roles for every existing org ────────────────────────
    import json as _json

    orgs = bind.execute(sa.text("SELECT id FROM organizations")).fetchall()
    for (org_id,) in orgs:
        for role_name, role_desc, role_perms in SYSTEM_ROLES:
            # Skip if already seeded (rerun safety)
            already = bind.execute(
                sa.text(
                    "SELECT id FROM roles WHERE org_id = :oid AND name = :n"
                ),
                {"oid": org_id, "n": role_name},
            ).first()
            if already:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO roles (org_id, name, description, permissions, is_system) "
                    "VALUES (:oid, :n, :d, CAST(:p AS JSONB), true)"
                ),
                {"oid": org_id, "n": role_name, "d": role_desc,
                 "p": _json.dumps(role_perms)},
            )

        # Assign Owner role to existing users based on legacy role column
        owner_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE org_id = :oid AND name = 'Owner'"),
            {"oid": org_id},
        ).first()
        if owner_row:
            bind.execute(
                sa.text(
                    "UPDATE users SET role_id = :rid WHERE org_id = :oid "
                    "AND role_id IS NULL"
                ),
                {"rid": owner_row[0], "oid": org_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "role_id" in user_cols:
        op.drop_column("users", "role_id")
    if "org_role" in user_cols:
        op.drop_column("users", "org_role")

    op.drop_index("ix_team_invitations_status", table_name="team_invitations")
    op.drop_index("ix_team_invitations_email", table_name="team_invitations")
    op.drop_index("ix_team_invitations_org", table_name="team_invitations")
    op.drop_table("team_invitations")

    op.drop_index("ix_roles_org_name", table_name="roles")
    op.drop_index("ix_roles_org", table_name="roles")
    op.drop_table("roles")

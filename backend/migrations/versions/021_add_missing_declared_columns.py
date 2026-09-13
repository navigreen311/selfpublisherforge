"""Add columns the services and API schemas have always read but no model declared.

Each column here was already being read or written by live code, or declared on
a Pydantic response model, while the table had no such column — so the endpoint
raised AttributeError (or, for the setattr paths, silently discarded the value)
on every call. mypy's [attr-defined] bucket surfaced the whole set.

Every column is nullable and additive, so this is safe to apply to a populated
database and needs no backfill.

  organizations.description        OrganizationResponse.description; the
                                   settings screen reads and writes it.
  dictation_sessions.title         SessionResponse / SessionListItem, and the
  dictation_sessions.project_id    frontend's dictation types.
  dictation_commands.description   CommandResponse.description.
  childrens_books.story_prompt     Fed to the AI story generator and scanned by
  childrens_books.theme_moral      the trademark check; carried by the create
  childrens_books.tone             and update payloads all along.
  childrens_book_pages.metadata_json  Illustration provenance (model, prompt
                                   hash, date) and upload details.
  coloring_book_pages.qa_issues    Per-issue detail behind quality_score.

Revision ID: 021_add_missing_declared_columns
Revises: 020_add_activity_log
Create Date: 2026-09-10
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "021_add_missing_declared_columns"
down_revision = "020_add_activity_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))

    op.add_column("dictation_sessions", sa.Column("title", sa.String(length=500), nullable=True))
    op.add_column("dictation_sessions", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_dictation_sessions_project_id",
        "dictation_sessions",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_dictation_sessions_project_id",
        "dictation_sessions",
        ["project_id"],
    )

    op.add_column("dictation_commands", sa.Column("description", sa.Text(), nullable=True))

    op.add_column("childrens_books", sa.Column("story_prompt", sa.Text(), nullable=True))
    op.add_column("childrens_books", sa.Column("theme_moral", sa.String(length=200), nullable=True))
    op.add_column("childrens_books", sa.Column("tone", sa.String(length=50), nullable=True))

    op.add_column("childrens_book_pages", sa.Column("metadata_json", sa.JSON(), nullable=True))

    op.add_column("coloring_book_pages", sa.Column("qa_issues", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("coloring_book_pages", "qa_issues")

    op.drop_column("childrens_book_pages", "metadata_json")

    op.drop_column("childrens_books", "tone")
    op.drop_column("childrens_books", "theme_moral")
    op.drop_column("childrens_books", "story_prompt")

    op.drop_column("dictation_commands", "description")

    op.drop_index("ix_dictation_sessions_project_id", table_name="dictation_sessions")
    op.drop_constraint(
        "fk_dictation_sessions_project_id",
        "dictation_sessions",
        type_="foreignkey",
    )
    op.drop_column("dictation_sessions", "project_id")
    op.drop_column("dictation_sessions", "title")

    op.drop_column("organizations", "description")

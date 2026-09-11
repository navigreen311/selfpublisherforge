"""Add pipeline stages, activity, and automation tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # `pipelines` and `pipeline_tasks` are the tables this migration was
    # written to extend, but no migration has ever created them — the module
    # has only ever existed in Base.metadata, so it worked under
    # `create_all` in tests and was absent from every migrated database.
    # They are created here, in the shape they would have had before this
    # migration's own additions below.
    pipeline_status = postgresql.ENUM(
        "draft", "active", "paused", "completed", "cancelled", name="pipeline_status", create_type=False
    )
    task_type = postgresql.ENUM(
        "writing", "editing", "proofreading", "formatting", "review", name="task_type", create_type=False
    )
    task_status = postgresql.ENUM(
        "pending", "in_progress", "blocked", "completed", "cancelled", name="task_status", create_type=False
    )
    for enum_type in (pipeline_status, task_type, task_status):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "pipelines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", pipeline_status, server_default="draft", nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pipelines_org_id", "pipelines", ["org_id"])
    op.create_index("ix_pipelines_book_id", "pipelines", ["book_id"])
    op.create_index("ix_pipelines_org_book", "pipelines", ["org_id", "book_id"])
    op.create_index("ix_pipelines_status", "pipelines", ["status"])

    op.create_table(
        "pipeline_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("pipeline_id", UUID(as_uuid=True), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", task_type, nullable=False),
        sa.Column("status", task_status, server_default="pending", nullable=False),
        sa.Column("assignee_id", UUID(as_uuid=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("depends_on", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pipeline_tasks_org_id", "pipeline_tasks", ["org_id"])
    op.create_index("ix_pipeline_tasks_pipeline_id", "pipeline_tasks", ["pipeline_id"])
    op.create_index("ix_pipeline_tasks_pipeline_status", "pipeline_tasks", ["pipeline_id", "status"])
    op.create_index("ix_pipeline_tasks_assignee", "pipeline_tasks", ["assignee_id"])
    op.create_index("ix_pipeline_tasks_due_date", "pipeline_tasks", ["due_date"])

    # Add columns to existing pipelines table
    op.add_column("pipelines", sa.Column("template", sa.String(100), nullable=True))
    op.add_column("pipelines", sa.Column("target_launch_date", sa.Date(), nullable=True))
    op.add_column("pipelines", sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=True))

    # Add stage_id column to pipeline_tasks (nullable for now, existing tasks won't have it)
    op.add_column("pipeline_tasks", sa.Column("stage_id", UUID(as_uuid=True), nullable=True))
    op.add_column("pipeline_tasks", sa.Column("priority", sa.String(20), server_default="medium", nullable=True))
    op.add_column("pipeline_tasks", sa.Column("checklist", JSONB(), server_default="[]", nullable=True))
    op.add_column("pipeline_tasks", sa.Column("links", JSONB(), server_default="[]", nullable=True))
    op.add_column(
        "pipeline_tasks", sa.Column("blocked_by", ARRAY(UUID(as_uuid=True)), server_default="{}", nullable=True)
    )
    op.add_column("pipeline_tasks", sa.Column("metadata_json", JSONB(), server_default="{}", nullable=True))
    op.add_column("pipeline_tasks", sa.Column("order_index", sa.Integer(), server_default="0", nullable=True))

    # Create pipeline_stages table
    op.create_table(
        "pipeline_stages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("pipeline_id", UUID(as_uuid=True), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_pipeline_stages_pipeline", "pipeline_stages", ["pipeline_id"])

    # Add FK from pipeline_tasks.stage_id -> pipeline_stages.id
    op.create_foreign_key(
        "fk_pipeline_tasks_stage", "pipeline_tasks", "pipeline_stages", ["stage_id"], ["id"], ondelete="SET NULL"
    )

    # Create pipeline_activity table
    op.create_table(
        "pipeline_activity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("pipeline_id", UUID(as_uuid=True), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("pipeline_tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_pipeline_activity_pipeline", "pipeline_activity", ["pipeline_id"])

    # Create pipeline_automations table
    op.create_table(
        "pipeline_automations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("pipeline_id", UUID(as_uuid=True), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_config", JSONB(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_config", JSONB(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pipeline_automations")
    op.drop_table("pipeline_activity")
    op.drop_constraint("fk_pipeline_tasks_stage", "pipeline_tasks", type_="foreignkey")
    op.drop_index("idx_pipeline_stages_pipeline")
    op.drop_table("pipeline_stages")
    op.drop_column("pipeline_tasks", "order_index")
    op.drop_column("pipeline_tasks", "metadata_json")
    op.drop_column("pipeline_tasks", "blocked_by")
    op.drop_column("pipeline_tasks", "links")
    op.drop_column("pipeline_tasks", "checklist")
    op.drop_column("pipeline_tasks", "priority")
    op.drop_column("pipeline_tasks", "stage_id")
    op.drop_column("pipelines", "progress_pct")
    op.drop_column("pipelines", "target_launch_date")
    op.drop_column("pipelines", "template")

    op.drop_table("pipeline_tasks")
    op.drop_table("pipelines")
    for enum_name in ("task_status", "task_type", "pipeline_status"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

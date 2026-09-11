"""Add AI Agents, Admin, and Settings enhancements."""

from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new tables and columns for AI Agents, Admin, and Settings features."""

    # ─────────────────────────────────────────────────────────────────────
    # 1. CREATE NEW TABLES
    # ─────────────────────────────────────────────────────────────────────

    # activity_log is created by migration 020, in the shape the ActivityLog
    # model actually declares (description + metadata, org_id NOT NULL). The
    # version that used to be created here had a different shape — details and
    # ip_address, nullable org_id — and nothing maps to it.

    # invoices table
    op.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            description VARCHAR(255),
            status VARCHAR(50) DEFAULT 'paid',
            period_start DATE,
            period_end DATE,
            pdf_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # webhooks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            events TEXT[] NOT NULL,
            secret VARCHAR(255),
            status VARCHAR(50) DEFAULT 'active',
            last_delivery_at TIMESTAMPTZ,
            last_response_code INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # notification_preferences table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
            preferences JSONB NOT NULL DEFAULT '{}',
            quiet_hours_start TIME,
            quiet_hours_end TIME,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ─────────────────────────────────────────────────────────────────────
    # 2. ADD COLUMNS TO EXISTING agents TABLE
    # ─────────────────────────────────────────────────────────────────────

    # Check and add each column only if it doesn't exist
    columns_to_add_agents = [
        ("icon", "VARCHAR(10)"),
        ("system_prompt", "TEXT"),
        ("temperature", "FLOAT DEFAULT 0.7"),
        ("default_execution_mode", "VARCHAR(50) DEFAULT 'draft'"),
        ("task_types", "JSONB DEFAULT '[]'"),
        ("context_sources", "TEXT[] DEFAULT '{}'"),
        ("budget_per_task", "DECIMAL(10,2)"),
        ("monthly_budget", "DECIMAL(10,2)"),
        ("is_system", "BOOLEAN DEFAULT FALSE"),
    ]

    for col_name, col_def in columns_to_add_agents:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='agents' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE agents ADD COLUMN {col_name} {col_def};
                END IF;
            END $$;
        """)

    # ─────────────────────────────────────────────────────────────────────
    # 3. ADD COLUMNS TO EXISTING agent_tasks TABLE
    # ─────────────────────────────────────────────────────────────────────

    columns_to_add_agent_tasks = [
        ("book_id", "UUID REFERENCES books(id) ON DELETE SET NULL"),
        ("task_type", "VARCHAR(100)"),
        ("instructions", "TEXT"),
        ("execution_mode", "VARCHAR(50)"),
        ("max_tokens", "INTEGER"),
        ("output", "TEXT"),
        ("output_format", "VARCHAR(50) DEFAULT 'markdown'"),
        ("steps", "JSONB DEFAULT '[]'"),
        ("tokens_used", "INTEGER DEFAULT 0"),
        ("cost", "DECIMAL(10,4) DEFAULT 0"),
        ("execution_time_seconds", "INTEGER"),
        ("rating", "INTEGER"),
        ("error_message", "TEXT"),
        ("approved_at", "TIMESTAMPTZ"),
        ("applied_to", "VARCHAR(255)"),
        ("started_at", "TIMESTAMPTZ"),
        ("completed_at", "TIMESTAMPTZ"),
    ]

    for col_name, col_def in columns_to_add_agent_tasks:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='agent_tasks' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE agent_tasks ADD COLUMN {col_name} {col_def};
                END IF;
            END $$;
        """)

    # ─────────────────────────────────────────────────────────────────────
    # 4. CREATE INDEXES
    # ─────────────────────────────────────────────────────────────────────

    # Indexes for agent_tasks (org_id needs to exist first)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='agent_tasks' AND column_name='org_id'
            ) THEN
                CREATE INDEX IF NOT EXISTS idx_agent_tasks_org
                ON agent_tasks(org_id, created_at DESC);
            END IF;
        END $$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent
        ON agent_tasks(agent_id, status)
    """)


def downgrade() -> None:
    """Remove AI Agents, Admin, and Settings enhancements."""

    # ─────────────────────────────────────────────────────────────────────
    # 1. DROP INDEXES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("DROP INDEX IF EXISTS idx_agent_tasks_agent")
    op.execute("DROP INDEX IF EXISTS idx_agent_tasks_org")
    op.execute("DROP INDEX IF EXISTS idx_activity_log_user")
    op.execute("DROP INDEX IF EXISTS idx_activity_log_org")

    # ─────────────────────────────────────────────────────────────────────
    # 2. DROP COLUMNS FROM agent_tasks
    # ─────────────────────────────────────────────────────────────────────

    columns_to_drop_agent_tasks = [
        "book_id",
        "task_type",
        "instructions",
        "execution_mode",
        "max_tokens",
        "output",
        "output_format",
        "steps",
        "tokens_used",
        "cost",
        "execution_time_seconds",
        "rating",
        "error_message",
        "approved_at",
        "applied_to",
        "started_at",
        "completed_at",
    ]

    for col_name in columns_to_drop_agent_tasks:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='agent_tasks' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE agent_tasks DROP COLUMN {col_name};
                END IF;
            END $$;
        """)

    # ─────────────────────────────────────────────────────────────────────
    # 3. DROP COLUMNS FROM agents
    # ─────────────────────────────────────────────────────────────────────

    columns_to_drop_agents = [
        "icon",
        "system_prompt",
        "temperature",
        "default_execution_mode",
        "task_types",
        "context_sources",
        "budget_per_task",
        "monthly_budget",
        "is_system",
    ]

    for col_name in columns_to_drop_agents:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='agents' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE agents DROP COLUMN {col_name};
                END IF;
            END $$;
        """)

    # ─────────────────────────────────────────────────────────────────────
    # 4. DROP TABLES
    # ─────────────────────────────────────────────────────────────────────

    op.execute("DROP TABLE IF EXISTS notification_preferences")
    op.execute("DROP TABLE IF EXISTS webhooks")
    op.execute("DROP TABLE IF EXISTS invoices")
    op.execute("DROP TABLE IF EXISTS activity_log")

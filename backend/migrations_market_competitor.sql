-- Market Research tables
CREATE TABLE IF NOT EXISTS market_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    query_keywords TEXT[] NOT NULL,
    marketplace VARCHAR(20) DEFAULT 'amazon_com',
    opportunity_score INTEGER,
    demand_score INTEGER,
    supply_score INTEGER,
    avg_revenue DECIMAL(10,2),
    verdict TEXT,
    ai_summary TEXT,
    results_data JSONB DEFAULT '{}',
    charts_data JSONB DEFAULT '{}',
    top_books JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS keyword_research_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seed_keywords TEXT[] NOT NULL,
    marketplace VARCHAR(20) DEFAULT 'amazon_com',
    results JSONB NOT NULL,
    suggested_kdp_keywords TEXT[],
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255),
    search_type VARCHAR(50) NOT NULL,
    query_params JSONB NOT NULL,
    analysis_id UUID REFERENCES market_analyses(id),
    project_id UUID REFERENCES projects(id),
    pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Competitor Finder tables
CREATE TABLE IF NOT EXISTS gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    competitor_ids UUID[] NOT NULL,
    project_id UUID REFERENCES projects(id),
    status VARCHAR(50) DEFAULT 'pending',
    weakness_signals JSONB DEFAULT '[]',
    opportunity_blueprint JSONB DEFAULT '{}',
    differentiation_score INTEGER,
    total_signals INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS competitor_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    alert_type VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    config JSONB NOT NULL,
    delivery_channels TEXT[] DEFAULT '{in_app}',
    check_frequency VARCHAR(20) DEFAULT 'daily',
    active BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMPTZ,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES competitor_alerts(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(id),
    event_data JSONB NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    delivered_channels TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_analyses_org ON market_analyses(org_id);
CREATE INDEX IF NOT EXISTS idx_market_analyses_keywords ON market_analyses USING GIN(query_keywords);
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_keyword_cache_expires ON keyword_research_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_gap_analyses_org ON gap_analyses(org_id);
CREATE INDEX IF NOT EXISTS idx_competitor_alerts_org ON competitor_alerts(org_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_org ON alert_events(org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_events_unread ON alert_events(org_id) WHERE read = FALSE;

-- Extend competitor_books table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'competitor_books') THEN
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id);
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS tracked BOOLEAN DEFAULT TRUE;
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS description TEXT;
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS page_count INTEGER;
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS publish_date DATE;
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS cover_image_url TEXT;
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS estimated_monthly_revenue DECIMAL(10,2);
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS keywords_extracted TEXT[];
        ALTER TABLE competitor_books ADD COLUMN IF NOT EXISTS last_data_refresh TIMESTAMPTZ;
    END IF;
END $$;

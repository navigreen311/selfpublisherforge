-- Migration: Review Intelligence & Writing Studio enhancements
-- New tables for review insights, ARC campaigns, alerts, writing sessions, and chapter versions.

-- Review insights cache
CREATE TABLE IF NOT EXISTS review_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    book_id UUID,
    positive_themes JSONB DEFAULT '[]',
    negative_themes JSONB DEFAULT '[]',
    keyword_cloud JSONB DEFAULT '[]',
    ai_summary TEXT,
    action_items JSONB DEFAULT '[]',
    sentiment_score FLOAT,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ARC campaigns
CREATE TABLE IF NOT EXISTS arc_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    book_id UUID,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    copies_sent INTEGER DEFAULT 0,
    reviews_received INTEGER DEFAULT 0,
    deadline DATE,
    recipients JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Review alerts (enhanced - only create if not exists, don't conflict with existing)
CREATE TABLE IF NOT EXISTS review_alerts_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    book_id UUID,
    config JSONB NOT NULL DEFAULT '{}',
    delivery_channels TEXT[] DEFAULT '{in_app}',
    active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert notification history
CREATE TABLE IF NOT EXISTS review_alert_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    alert_type VARCHAR(50),
    message TEXT,
    book_title VARCHAR(255),
    severity VARCHAR(20),
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Writing sessions (enhanced)
CREATE TABLE IF NOT EXISTS writing_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    user_id UUID NOT NULL,
    manuscript_id UUID,
    chapter_id UUID,
    words_written INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Chapter versions
CREATE TABLE IF NOT EXISTS chapter_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL,
    content TEXT,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_review_insights_org ON review_insights(org_id);
CREATE INDEX IF NOT EXISTS idx_review_insights_book ON review_insights(book_id);
CREATE INDEX IF NOT EXISTS idx_arc_campaigns_org ON arc_campaigns(org_id);
CREATE INDEX IF NOT EXISTS idx_review_alerts_config_org ON review_alerts_config(org_id);
CREATE INDEX IF NOT EXISTS idx_review_alert_notif_org ON review_alert_notifications(org_id);
CREATE INDEX IF NOT EXISTS idx_writing_sessions_org ON writing_sessions(org_id);
CREATE INDEX IF NOT EXISTS idx_writing_sessions_manuscript ON writing_sessions(manuscript_id);
CREATE INDEX IF NOT EXISTS idx_chapter_versions_chapter ON chapter_versions(chapter_id);

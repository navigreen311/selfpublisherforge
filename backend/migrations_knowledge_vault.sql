-- Enhance knowledge_entries table
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'notes';
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS project_id UUID;
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS content_plain TEXT;
ALTER TABLE knowledge_entries ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category);

-- Create knowledge_attachments table
CREATE TABLE IF NOT EXISTS knowledge_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id UUID NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    file_name VARCHAR(500),
    file_url TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_attachments_entry ON knowledge_attachments(entry_id);

-- Publishing Migration: New tables for ISBN management, book pricing, and pricing history
-- Created: 2026-02-13

-- ISBNs table
CREATE TABLE IF NOT EXISTS isbns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    isbn VARCHAR(17) NOT NULL UNIQUE,
    format VARCHAR(50),
    book_id UUID,
    status VARCHAR(50) DEFAULT 'available',
    barcode_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_isbns_org ON isbns(org_id);

-- Book pricing
CREATE TABLE IF NOT EXISTS book_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    book_id UUID NOT NULL,
    kindle_price DECIMAL(10,2),
    paperback_price DECIMAL(10,2),
    hardcover_price DECIMAL(10,2),
    audiobook_price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_book_pricing_book ON book_pricing(book_id);

-- Pricing history
CREATE TABLE IF NOT EXISTS pricing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL,
    format VARCHAR(50),
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Manuscript exports enhancement
ALTER TABLE manuscript_exports ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';
ALTER TABLE manuscript_exports ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Enhance publishing_accounts
ALTER TABLE publishing_accounts ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE publishing_accounts ADD COLUMN IF NOT EXISTS api_key_encrypted TEXT;

-- Enhance book_listings
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS format VARCHAR(50);
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS avg_rating FLOAT;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS bsr INTEGER;
ALTER TABLE book_listings ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_book_listings_book ON book_listings(book_id);

-- Add columns to existing style_profiles table if they don't exist
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS preset VARCHAR(100);
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS voice_description TEXT;
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS tuning_adjustments JSONB DEFAULT '{}';
ALTER TABLE style_profiles ADD COLUMN IF NOT EXISTS total_sample_words INTEGER DEFAULT 0;

-- Create style_profile_samples table
CREATE TABLE IF NOT EXISTS style_profile_samples (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
profile_id UUID NOT NULL REFERENCES style_profiles(id) ON DELETE CASCADE,
label VARCHAR(255),
source_type VARCHAR(50),
source_reference UUID,
content TEXT NOT NULL,
word_count INTEGER DEFAULT 0,
file_name VARCHAR(255),
created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_style_profile_samples_profile ON style_profile_samples(profile_id);

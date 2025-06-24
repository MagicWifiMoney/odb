-- Enhanced RFP Integration Schema - PostgreSQL Compatible
-- Extends existing opportunities table with advanced features

-- Add new columns to existing opportunities table (PostgreSQL compatible)
DO $$
BEGIN
    -- Add source_url column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='source_url') THEN
        ALTER TABLE opportunities ADD COLUMN source_url TEXT;
    END IF;
    
    -- Add categories column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='categories') THEN
        ALTER TABLE opportunities ADD COLUMN categories JSONB DEFAULT '[]'::jsonb;
    END IF;
    
    -- Add naics_codes column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='naics_codes') THEN
        ALTER TABLE opportunities ADD COLUMN naics_codes JSONB DEFAULT '[]'::jsonb;
    END IF;
    
    -- Add set_asides column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='set_asides') THEN
        ALTER TABLE opportunities ADD COLUMN set_asides JSONB DEFAULT '[]'::jsonb;
    END IF;
    
    -- Add attachments column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='attachments') THEN
        ALTER TABLE opportunities ADD COLUMN attachments JSONB DEFAULT '[]'::jsonb;
    END IF;
    
    -- Add contacts column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='contacts') THEN
        ALTER TABLE opportunities ADD COLUMN contacts JSONB DEFAULT '[]'::jsonb;
    END IF;
    
    -- Add intelligence column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='intelligence') THEN
        ALTER TABLE opportunities ADD COLUMN intelligence JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    -- Add relevance_score column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='relevance_score') THEN
        ALTER TABLE opportunities ADD COLUMN relevance_score FLOAT DEFAULT 0.5;
    END IF;
    
    -- Add data_quality_score column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='opportunities' AND column_name='data_quality_score') THEN
        ALTER TABLE opportunities ADD COLUMN data_quality_score FLOAT DEFAULT 0.5;
    END IF;
END $$;

-- Rate limits table for API management
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    api_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Saved searches table for user notifications
CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    search_params JSONB NOT NULL,
    notification_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunity tracking table for user workflow
CREATE TABLE IF NOT EXISTS opportunity_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'reviewing' CHECK (status IN ('reviewing', 'pursuing', 'passed', 'submitted', 'awarded', 'lost')),
    notes TEXT,
    bid_decision BOOLEAN,
    team_members JSONB DEFAULT '[]'::jsonb,
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    deadline_reminder TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create performance indexes (only if they don't exist)
DO $$
BEGIN
    -- Index for relevance score
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_opportunities_relevance') THEN
        CREATE INDEX idx_opportunities_relevance ON opportunities(relevance_score DESC);
    END IF;
    
    -- Index for data quality score
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_opportunities_quality') THEN
        CREATE INDEX idx_opportunities_quality ON opportunities(data_quality_score DESC);
    END IF;
    
    -- GIN index for categories
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_opportunities_categories') THEN
        CREATE INDEX idx_opportunities_categories ON opportunities USING GIN(categories);
    END IF;
    
    -- GIN index for NAICS codes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_opportunities_naics') THEN
        CREATE INDEX idx_opportunities_naics ON opportunities USING GIN(naics_codes);
    END IF;
    
    -- Index for source URL
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_opportunities_source_url') THEN
        CREATE INDEX idx_opportunities_source_url ON opportunities(source_url);
    END IF;
    
    -- Indexes for new tables
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_saved_searches_user') THEN
        CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tracking_user') THEN
        CREATE INDEX idx_tracking_user ON opportunity_tracking(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tracking_opportunity') THEN
        CREATE INDEX idx_tracking_opportunity ON opportunity_tracking(opportunity_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tracking_status') THEN
        CREATE INDEX idx_tracking_status ON opportunity_tracking(status);
    END IF;
END $$;

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns (only if they don't exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_saved_searches_updated_at') THEN
        CREATE TRIGGER update_saved_searches_updated_at 
            BEFORE UPDATE ON saved_searches
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_tracking_updated_at') THEN
        CREATE TRIGGER update_tracking_updated_at 
            BEFORE UPDATE ON opportunity_tracking
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Function to calculate opportunity score
CREATE OR REPLACE FUNCTION calculate_opportunity_score(
    relevance_score FLOAT,
    data_quality_score FLOAT,
    estimated_value DECIMAL,
    days_until_due INTEGER
)
RETURNS INTEGER AS $$
DECLARE
    base_score INTEGER;
    value_bonus INTEGER;
    urgency_bonus INTEGER;
BEGIN
    -- Base score from relevance and quality (0-70 points)
    base_score := ROUND((relevance_score * 0.6 + data_quality_score * 0.4) * 70);
    
    -- Value bonus (0-20 points)
    value_bonus := CASE 
        WHEN estimated_value >= 10000000 THEN 20  -- $10M+
        WHEN estimated_value >= 1000000 THEN 15   -- $1M+
        WHEN estimated_value >= 100000 THEN 10    -- $100K+
        WHEN estimated_value >= 10000 THEN 5      -- $10K+
        ELSE 0
    END;
    
    -- Urgency bonus (0-10 points)
    urgency_bonus := CASE 
        WHEN days_until_due <= 7 THEN 10   -- Due within a week
        WHEN days_until_due <= 14 THEN 7   -- Due within two weeks
        WHEN days_until_due <= 30 THEN 5   -- Due within a month
        ELSE 0
    END;
    
    RETURN LEAST(100, base_score + value_bonus + urgency_bonus);
END;
$$ language 'plpgsql';

-- Update existing opportunities with default values for new columns
UPDATE opportunities 
SET 
    categories = '[]'::jsonb,
    naics_codes = '[]'::jsonb,
    set_asides = '[]'::jsonb,
    attachments = '[]'::jsonb,
    contacts = '[]'::jsonb,
    intelligence = '{}'::jsonb,
    relevance_score = 0.8,  -- Set higher for existing real data
    data_quality_score = 0.9  -- High quality for USASpending.gov data
WHERE 
    categories IS NULL 
    OR relevance_score IS NULL;

-- Update total_score for existing opportunities using new calculation
UPDATE opportunities 
SET total_score = calculate_opportunity_score(
    COALESCE(relevance_score, 0.8),
    COALESCE(data_quality_score, 0.9),
    COALESCE(estimated_value, 0),
    COALESCE(EXTRACT(days FROM (due_date - CURRENT_DATE))::INTEGER, 30)
)
WHERE source_name = 'USASpending.gov';

-- Enable real-time subscriptions for new tables
DO $$
BEGIN
    -- Add tables to realtime publication if not already added
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE saved_searches;
    EXCEPTION WHEN duplicate_object THEN
        -- Table already in publication, ignore
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE opportunity_tracking;
    EXCEPTION WHEN duplicate_object THEN
        -- Table already in publication, ignore
    END;
END $$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Enhanced RFP schema applied successfully!';
    RAISE NOTICE 'Added % new columns to opportunities table', 9;
    RAISE NOTICE 'Created % new tables for advanced features', 3;
    RAISE NOTICE 'Enhanced existing % opportunities with new scoring', (SELECT COUNT(*) FROM opportunities);
END $$;
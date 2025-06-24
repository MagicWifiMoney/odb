-- Enhanced RFP Integration Schema
-- Extends existing opportunities table with advanced features

-- Add new columns to existing opportunities table
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS categories JSONB DEFAULT '[]'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS naics_codes JSONB DEFAULT '[]'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS set_asides JSONB DEFAULT '[]'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS attachments JSONB DEFAULT '[]'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS contacts JSONB DEFAULT '[]'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS intelligence JSONB DEFAULT '{}'::jsonb;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS relevance_score FLOAT DEFAULT 0.5;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS data_quality_score FLOAT DEFAULT 0.5;

-- Rate limits table for API management
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    api_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique constraint for rate limiting
CREATE UNIQUE INDEX IF NOT EXISTS idx_rate_limits_api_timestamp ON rate_limits(api_name, timestamp);

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

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_relevance ON opportunities(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_quality ON opportunities(data_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_categories ON opportunities USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_opportunities_naics ON opportunities USING GIN(naics_codes);
CREATE INDEX IF NOT EXISTS idx_opportunities_source_url ON opportunities(source_url);

-- Indexes for search performance
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_tracking_user ON opportunity_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_tracking_opportunity ON opportunity_tracking(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_tracking_status ON opportunity_tracking(status);

-- Enable real-time subscriptions for new tables
ALTER PUBLICATION supabase_realtime ADD TABLE saved_searches;
ALTER PUBLICATION supabase_realtime ADD TABLE opportunity_tracking;

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER IF NOT EXISTS update_saved_searches_updated_at 
    BEFORE UPDATE ON saved_searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_tracking_updated_at 
    BEFORE UPDATE ON opportunity_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean old rate limit entries
CREATE OR REPLACE FUNCTION clean_old_rate_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM rate_limits 
    WHERE timestamp < NOW() - INTERVAL '1 hour';
END;
$$ language 'plpgsql';

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

-- Update total_score for existing opportunities
UPDATE opportunities 
SET total_score = calculate_opportunity_score(
    COALESCE(relevance_score, 0.5),
    COALESCE(data_quality_score, 0.5),
    COALESCE(estimated_value, 0),
    COALESCE(EXTRACT(days FROM (due_date - CURRENT_DATE)), 30)
)
WHERE total_score IS NULL OR total_score = 0;

-- View for high-priority opportunities
CREATE OR REPLACE VIEW high_priority_opportunities AS
SELECT 
    o.*,
    EXTRACT(days FROM (due_date - CURRENT_DATE)) as days_until_due,
    CASE 
        WHEN due_date < CURRENT_DATE THEN 'expired'
        WHEN due_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'urgent'
        WHEN due_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'upcoming'
        ELSE 'future'
    END as urgency_level
FROM opportunities o
WHERE 
    (relevance_score >= 0.7 OR total_score >= 80)
    AND (due_date IS NULL OR due_date >= CURRENT_DATE)
ORDER BY total_score DESC, due_date ASC;

-- View for user dashboard
CREATE OR REPLACE VIEW user_opportunity_dashboard AS
SELECT 
    u.user_id,
    COUNT(*) as total_tracked,
    COUNT(*) FILTER (WHERE u.status = 'reviewing') as reviewing_count,
    COUNT(*) FILTER (WHERE u.status = 'pursuing') as pursuing_count,
    COUNT(*) FILTER (WHERE u.status = 'submitted') as submitted_count,
    SUM(o.estimated_value) FILTER (WHERE u.status IN ('pursuing', 'submitted')) as total_pursuing_value,
    MAX(u.updated_at) as last_activity
FROM opportunity_tracking u
JOIN opportunities o ON u.opportunity_id = o.id
GROUP BY u.user_id;

-- Function to get opportunity recommendations
CREATE OR REPLACE FUNCTION get_opportunity_recommendations(
    p_user_id TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    title TEXT,
    agency_name TEXT,
    estimated_value DECIMAL,
    relevance_score FLOAT,
    total_score INTEGER,
    recommendation_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_preferences AS (
        -- Get user's tracked opportunity patterns
        SELECT 
            array_agg(DISTINCT o.agency_name) as preferred_agencies,
            array_agg(DISTINCT o.source_type) as preferred_types,
            AVG(o.estimated_value) as avg_value_preference
        FROM opportunity_tracking t
        JOIN opportunities o ON t.opportunity_id = o.id
        WHERE t.user_id = p_user_id
          AND t.status IN ('pursuing', 'submitted', 'awarded')
    )
    SELECT 
        o.id,
        o.title,
        o.agency_name,
        o.estimated_value,
        o.relevance_score,
        o.total_score,
        CASE 
            WHEN o.agency_name = ANY(up.preferred_agencies) THEN 'Matches your preferred agencies'
            WHEN o.source_type = ANY(up.preferred_types) THEN 'Similar to your tracked opportunities'
            WHEN o.estimated_value BETWEEN up.avg_value_preference * 0.5 AND up.avg_value_preference * 2 THEN 'Matches your value range'
            WHEN o.relevance_score >= 0.8 THEN 'High relevance score'
            ELSE 'High overall score'
        END as recommendation_reason
    FROM opportunities o
    CROSS JOIN user_preferences up
    WHERE o.id NOT IN (
        SELECT opportunity_id 
        FROM opportunity_tracking 
        WHERE user_id = p_user_id
    )
    AND (
        o.agency_name = ANY(up.preferred_agencies)
        OR o.source_type = ANY(up.preferred_types)
        OR o.estimated_value BETWEEN up.avg_value_preference * 0.5 AND up.avg_value_preference * 2
        OR o.relevance_score >= 0.8
        OR o.total_score >= 85
    )
    AND (o.due_date IS NULL OR o.due_date >= CURRENT_DATE)
    ORDER BY 
        CASE WHEN o.agency_name = ANY(up.preferred_agencies) THEN 1 ELSE 2 END,
        o.total_score DESC,
        o.relevance_score DESC
    LIMIT p_limit;
END;
$$ language 'plpgsql';

-- Insert sample rate limit and search configurations
INSERT INTO rate_limits (api_name, timestamp) VALUES 
('sam_gov', NOW() - INTERVAL '2 hours'),
('usaspending', NOW() - INTERVAL '30 minutes')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE opportunities IS 'Enhanced opportunities table with RFP-specific fields and intelligence';
COMMENT ON TABLE saved_searches IS 'User-saved searches for automated notifications';
COMMENT ON TABLE opportunity_tracking IS 'User workflow tracking for opportunities';
COMMENT ON TABLE rate_limits IS 'API rate limiting tracking';

COMMENT ON COLUMN opportunities.relevance_score IS 'AI-calculated relevance score (0.0-1.0)';
COMMENT ON COLUMN opportunities.data_quality_score IS 'Data completeness and quality score (0.0-1.0)';
COMMENT ON COLUMN opportunities.intelligence IS 'AI-generated insights and analysis';
COMMENT ON COLUMN opportunities.categories IS 'Categorization tags for the opportunity';
COMMENT ON COLUMN opportunities.naics_codes IS 'NAICS industry classification codes';
COMMENT ON COLUMN opportunities.set_asides IS 'Set-aside designations (small business, etc.)';

-- Ensure all users can read opportunities
GRANT SELECT ON opportunities TO authenticated, anon;
GRANT SELECT ON high_priority_opportunities TO authenticated, anon;

-- Users can manage their own saved searches and tracking
GRANT ALL ON saved_searches TO authenticated;
GRANT ALL ON opportunity_tracking TO authenticated;
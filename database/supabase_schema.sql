-- Opportunity Dashboard - Supabase Database Schema
-- Created for PostgreSQL/Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Data Sources table
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opportunities table (main data)
CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE, -- Original ID from source
    title VARCHAR(500) NOT NULL,
    description TEXT,
    agency_name VARCHAR(200),
    opportunity_number VARCHAR(100),
    estimated_value DECIMAL(15,2),
    posted_date TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'open',
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_url VARCHAR(500),
    location VARCHAR(200),
    contact_info TEXT,
    keywords JSONB,
    
    -- Scoring fields
    relevance_score INTEGER DEFAULT 0,
    urgency_score INTEGER DEFAULT 0,
    value_score INTEGER DEFAULT 0,
    competition_score INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    
    -- Metadata
    data_source_id INTEGER REFERENCES data_sources(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sync Logs table
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_duration_ms INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- User Preferences table (for future user system)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID DEFAULT uuid_generate_v4(),
    keywords JSONB,
    notification_settings JSONB,
    scoring_weights JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_opportunities_source_type ON opportunities(source_type);
CREATE INDEX idx_opportunities_total_score ON opportunities(total_score DESC);
CREATE INDEX idx_opportunities_due_date ON opportunities(due_date);
CREATE INDEX idx_opportunities_posted_date ON opportunities(posted_date DESC);
CREATE INDEX idx_opportunities_external_id ON opportunities(external_id);
CREATE INDEX idx_opportunities_keywords ON opportunities USING GIN(keywords);
CREATE INDEX idx_sync_logs_source_name ON sync_logs(source_name);

-- RLS (Row Level Security) policies - Optional for multi-user
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Allow public read access for now (can be restricted later)
CREATE POLICY "Allow public read on opportunities" ON opportunities FOR SELECT USING (true);
CREATE POLICY "Allow public read on data_sources" ON data_sources FOR SELECT USING (true);
CREATE POLICY "Allow public read on sync_logs" ON sync_logs FOR SELECT USING (true);

-- Insert initial data sources
INSERT INTO data_sources (name, type, base_url, api_key_required, rate_limit_per_hour) VALUES
('USASpending.gov', 'federal_contract', 'https://api.usaspending.gov/api/v2/', FALSE, 1000),
('Grants.gov', 'federal_grant', 'https://www.grants.gov/web/grants/search-grants.html', FALSE, 1000),
('SAM.gov', 'federal_contract', 'https://api.sam.gov/prod/opportunities/v1/', TRUE, 450),
('Firecrawl', 'web_scraping', 'https://api.firecrawl.dev/', TRUE, 100);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
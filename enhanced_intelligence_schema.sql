-- Enhanced Intelligence Schema Migration
-- Extends existing Supabase schema for Perplexity Intelligence Hub
-- Migration Version: 002
-- Created: 2025-06-22

-- =====================================================================
-- TABLE 1: TREND_ANALYSIS
-- Stores time-series analysis data for RFP trends and anomaly detection
-- =====================================================================
CREATE TABLE trend_analysis (
    id SERIAL PRIMARY KEY,
    analysis_date DATE NOT NULL,
    analysis_type VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'industry', 'regional'
    
    -- Trend Metrics
    opportunity_count INTEGER NOT NULL DEFAULT 0,
    total_value DECIMAL(15,2) DEFAULT 0,
    avg_value DECIMAL(15,2) DEFAULT 0,
    
    -- Category Breakdowns (JSONB for flexibility)
    industry_breakdown JSONB, -- {"defense": 45, "healthcare": 30, "it": 25}
    region_breakdown JSONB,   -- {"federal": 60, "state": 25, "local": 15}
    agency_breakdown JSONB,   -- {"dod": 40, "hhs": 30, "gsa": 20}
    
    -- Anomaly Detection
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(5,2), -- 0.00 to 10.00
    anomaly_type VARCHAR(100), -- 'volume_spike', 'value_outlier', 'new_pattern'
    anomaly_description TEXT,
    
    -- Keywords & Trends
    trending_keywords JSONB, -- ["cloud", "cybersecurity", "ai"]
    declining_keywords JSONB, -- ["legacy", "mainframe"]
    
    -- Time Series Data
    rolling_7_day_avg DECIMAL(10,2),
    rolling_30_day_avg DECIMAL(10,2),
    year_over_year_change DECIMAL(5,2), -- percentage change
    
    -- Metadata
    data_quality_score DECIMAL(3,2), -- 0.00 to 1.00
    confidence_interval DECIMAL(5,2), -- statistical confidence
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- TABLE 2: WIN_PREDICTIONS  
-- Stores ML model predictions for win probability
-- =====================================================================
CREATE TABLE win_predictions (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    
    -- Core Prediction
    win_probability DECIMAL(5,2) NOT NULL, -- 0.00 to 100.00
    confidence_score DECIMAL(5,2) NOT NULL, -- 0.00 to 100.00
    
    -- Model Information
    model_version VARCHAR(50) NOT NULL,
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    features_used JSONB, -- {"budget_match": 0.8, "past_wins": 0.6, "capability_match": 0.9}
    
    -- Key Factors (what drives the prediction)
    positive_factors JSONB, -- ["strong_capability_match", "competitive_pricing", "past_performance"]
    negative_factors JSONB, -- ["budget_constraints", "competition_level", "timeline_mismatch"]
    
    -- Competitive Analysis
    estimated_competitors INTEGER,
    competition_level VARCHAR(20), -- 'low', 'medium', 'high', 'very_high'
    market_positioning VARCHAR(50), -- 'leader', 'challenger', 'follower', 'niche'
    
    -- Recommendation
    bid_recommendation VARCHAR(20), -- 'strongly_recommend', 'recommend', 'consider', 'avoid'
    effort_estimate VARCHAR(20), -- 'low', 'medium', 'high', 'very_high'
    
    -- Historical Context
    similar_rfps_won INTEGER DEFAULT 0,
    similar_rfps_lost INTEGER DEFAULT 0,
    agency_relationship_score DECIMAL(3,2), -- 0.00 to 1.00
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- TABLE 3: COMPLIANCE_MATRICES
-- Stores parsed requirements and compliance mapping
-- =====================================================================
CREATE TABLE compliance_matrices (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    
    -- Matrix Overview
    matrix_name VARCHAR(200) NOT NULL,
    total_requirements INTEGER NOT NULL DEFAULT 0,
    compliance_percentage DECIMAL(5,2) DEFAULT 0, -- 0.00 to 100.00
    
    -- Requirements Data
    requirements JSONB NOT NULL, -- [{"id": 1, "text": "Must have ISO 27001", "type": "mandatory", "section": "3.1"}]
    compliance_status JSONB, -- [{"req_id": 1, "status": "compliant", "evidence": "cert_link", "notes": "Current cert"}]
    
    -- Risk Assessment
    high_risk_requirements JSONB, -- Requirements that pose compliance risk
    missing_capabilities JSONB, -- Capabilities we don't have
    compliance_gaps JSONB, -- Detailed gap analysis
    
    -- AI Parsing Metadata
    parsing_confidence DECIMAL(5,2), -- AI confidence in requirement extraction
    manual_review_needed BOOLEAN DEFAULT FALSE,
    parsed_by VARCHAR(50), -- 'gpt-4', 'claude-3', 'manual'
    parsing_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Matrix Generation
    matrix_format VARCHAR(20) DEFAULT 'standard', -- 'standard', 'government', 'custom'
    export_formats JSONB, -- ["pdf", "excel", "word"]
    
    -- Compliance Scoring
    mandatory_compliance DECIMAL(5,2), -- % of mandatory requirements met
    desired_compliance DECIMAL(5,2), -- % of desired requirements met
    overall_risk_score VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- TABLE 4: FILTER_RULES
-- Stores user-defined filtering rules for fast-fail filtering
-- =====================================================================
CREATE TABLE filter_rules (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_preferences(user_id) ON DELETE CASCADE,
    
    -- Rule Definition
    rule_name VARCHAR(100) NOT NULL,
    rule_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1, -- Higher number = higher priority
    
    -- Rule Logic
    rule_type VARCHAR(30) NOT NULL, -- 'include', 'exclude', 'score_boost', 'score_penalty'
    conditions JSONB NOT NULL, -- {"field": "estimated_value", "operator": ">=", "value": 100000}
    action JSONB, -- {"type": "exclude", "reason": "Budget too low"} or {"type": "boost", "points": 10}
    
    -- Advanced Filtering
    keywords_required JSONB, -- ["cloud", "cybersecurity"] - ALL must be present
    keywords_excluded JSONB, -- ["legacy", "mainframe"] - NONE can be present
    industries_included JSONB, -- ["defense", "healthcare"] - opportunity must be in these
    agencies_included JSONB, -- ["dod", "va"] - only these agencies
    
    -- Value & Date Filters
    min_value DECIMAL(15,2),
    max_value DECIMAL(15,2),
    max_days_until_due INTEGER, -- Don't show RFPs due within X days
    min_days_until_due INTEGER, -- Don't show RFPs due after X days
    
    -- Performance Tracking
    opportunities_filtered INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0, -- Manually overridden
    false_negatives INTEGER DEFAULT 0, -- Should have been filtered
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- TABLE 5: AMENDMENT_HISTORY
-- Tracks RFP amendments and calculates volatility scores
-- =====================================================================
CREATE TABLE amendment_history (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    
    -- Amendment Details
    amendment_number INTEGER NOT NULL, -- 1, 2, 3, etc.
    amendment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    amendment_type VARCHAR(50), -- 'due_date_change', 'scope_change', 'requirements_change', 'budget_change'
    
    -- Change Impact
    impact_severity VARCHAR(20) NOT NULL, -- 'minor', 'moderate', 'major', 'critical'
    impact_score DECIMAL(3,2) NOT NULL, -- 1.0 to 10.0
    
    -- Specific Changes
    changes_description TEXT,
    old_values JSONB, -- {"due_date": "2025-01-15", "budget": 500000}
    new_values JSONB, -- {"due_date": "2025-02-15", "budget": 750000}
    
    -- Due Date Changes
    due_date_extended_days INTEGER, -- positive = extension, negative = acceleration
    
    -- Budget Changes  
    budget_change_amount DECIMAL(15,2),
    budget_change_percentage DECIMAL(5,2),
    
    -- Scope & Requirements
    requirements_added JSONB, -- New requirements
    requirements_removed JSONB, -- Removed requirements
    requirements_modified JSONB, -- Changed requirements
    
    -- Volatility Calculation
    contributes_to_volatility BOOLEAN DEFAULT TRUE,
    volatility_weight DECIMAL(3,2) DEFAULT 1.0, -- How much this amendment affects overall volatility
    
    -- Detection Method
    detected_by VARCHAR(50), -- 'perplexity_api', 'manual_entry', 'web_scraping'
    detection_confidence DECIMAL(5,2), -- AI confidence in change detection
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- TABLE 6: KEYWORD_SUGGESTIONS
-- AI-powered keyword suggestions and relationship mapping
-- =====================================================================
CREATE TABLE keyword_suggestions (
    id SERIAL PRIMARY KEY,
    base_keyword VARCHAR(100) NOT NULL,
    
    -- Suggestion Details
    suggested_keyword VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(30), -- 'synonym', 'related', 'broader', 'narrower', 'trending'
    relevance_score DECIMAL(5,2) NOT NULL, -- 0.00 to 100.00
    
    -- Trend Data
    search_volume_trend VARCHAR(20), -- 'rising', 'stable', 'declining'
    industry_relevance JSONB, -- {"defense": 0.9, "healthcare": 0.3, "it": 0.8}
    geographic_relevance JSONB, -- {"federal": 0.8, "state": 0.6, "local": 0.4}
    
    -- Performance Metrics
    opportunities_found INTEGER DEFAULT 0, -- How many RFPs contain this keyword
    user_adoption_rate DECIMAL(5,2), -- % of users who accepted this suggestion
    success_rate DECIMAL(5,2), -- % of opportunities with this keyword that were won
    
    -- AI Analysis
    generated_by VARCHAR(50), -- 'perplexity', 'openai', 'google', 'manual'
    generation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score DECIMAL(5,2), -- AI confidence in the suggestion
    
    -- User Interaction
    times_suggested INTEGER DEFAULT 0,
    times_accepted INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,
    
    -- Keyword Network
    co_occurring_keywords JSONB, -- Keywords that often appear together
    keyword_category VARCHAR(50), -- 'technology', 'industry', 'service_type', 'compliance'
    
    is_trending BOOLEAN DEFAULT FALSE,
    trend_start_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================================

-- Trend Analysis Indexes
CREATE INDEX idx_trend_analysis_date ON trend_analysis(analysis_date DESC);
CREATE INDEX idx_trend_analysis_type ON trend_analysis(analysis_type);
CREATE INDEX idx_trend_analysis_anomaly ON trend_analysis(is_anomaly, anomaly_score DESC);
CREATE INDEX idx_trend_analysis_keywords ON trend_analysis USING GIN(trending_keywords);

-- Win Predictions Indexes  
CREATE INDEX idx_win_predictions_opportunity ON win_predictions(opportunity_id);
CREATE INDEX idx_win_predictions_probability ON win_predictions(win_probability DESC);
CREATE INDEX idx_win_predictions_confidence ON win_predictions(confidence_score DESC);
CREATE INDEX idx_win_predictions_date ON win_predictions(prediction_date DESC);
CREATE INDEX idx_win_predictions_recommendation ON win_predictions(bid_recommendation);

-- Compliance Matrices Indexes
CREATE INDEX idx_compliance_matrices_opportunity ON compliance_matrices(opportunity_id);
CREATE INDEX idx_compliance_matrices_compliance ON compliance_matrices(compliance_percentage DESC);
CREATE INDEX idx_compliance_matrices_risk ON compliance_matrices(overall_risk_score);
CREATE INDEX idx_compliance_requirements ON compliance_matrices USING GIN(requirements);

-- Filter Rules Indexes
CREATE INDEX idx_filter_rules_user ON filter_rules(user_id);
CREATE INDEX idx_filter_rules_active ON filter_rules(is_active, priority DESC);
CREATE INDEX idx_filter_rules_type ON filter_rules(rule_type);
CREATE INDEX idx_filter_keywords_required ON filter_rules USING GIN(keywords_required);
CREATE INDEX idx_filter_keywords_excluded ON filter_rules USING GIN(keywords_excluded);

-- Amendment History Indexes
CREATE INDEX idx_amendment_history_opportunity ON amendment_history(opportunity_id);
CREATE INDEX idx_amendment_history_date ON amendment_history(amendment_date DESC);
CREATE INDEX idx_amendment_history_type ON amendment_history(amendment_type);
CREATE INDEX idx_amendment_history_impact ON amendment_history(impact_severity, impact_score DESC);
CREATE INDEX idx_amendment_volatility ON amendment_history(contributes_to_volatility, volatility_weight);

-- Keyword Suggestions Indexes
CREATE INDEX idx_keyword_suggestions_base ON keyword_suggestions(base_keyword);
CREATE INDEX idx_keyword_suggestions_suggested ON keyword_suggestions(suggested_keyword);
CREATE INDEX idx_keyword_suggestions_relevance ON keyword_suggestions(relevance_score DESC);
CREATE INDEX idx_keyword_suggestions_trending ON keyword_suggestions(is_trending, trend_start_date DESC);
CREATE INDEX idx_keyword_suggestions_category ON keyword_suggestions(keyword_category);
CREATE INDEX idx_keyword_co_occurring ON keyword_suggestions USING GIN(co_occurring_keywords);

-- =====================================================================
-- FULL-TEXT SEARCH INDEXES
-- =====================================================================

-- Add full-text search to compliance requirements
CREATE INDEX idx_compliance_requirements_fulltext ON compliance_matrices USING GIN(to_tsvector('english', requirements::text));

-- Add full-text search to amendment descriptions
CREATE INDEX idx_amendment_description_fulltext ON amendment_history USING GIN(to_tsvector('english', changes_description));

-- Add full-text search to keyword suggestions
CREATE INDEX idx_keyword_suggestions_fulltext ON keyword_suggestions USING GIN(to_tsvector('english', base_keyword || ' ' || suggested_keyword));

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

-- Enable RLS on new tables
ALTER TABLE trend_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE win_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_matrices ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE amendment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_suggestions ENABLE ROW LEVEL SECURITY;

-- Public read policies (can be restricted later)
CREATE POLICY "Allow public read on trend_analysis" ON trend_analysis FOR SELECT USING (true);
CREATE POLICY "Allow public read on win_predictions" ON win_predictions FOR SELECT USING (true);
CREATE POLICY "Allow public read on compliance_matrices" ON compliance_matrices FOR SELECT USING (true);
CREATE POLICY "Allow public read on amendment_history" ON amendment_history FOR SELECT USING (true);
CREATE POLICY "Allow public read on keyword_suggestions" ON keyword_suggestions FOR SELECT USING (true);

-- User-specific policies for filter_rules
CREATE POLICY "Users can manage their own filter rules" ON filter_rules FOR ALL USING (auth.uid() = user_id);

-- =====================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- =====================================================================

-- Apply updated_at triggers to new tables
CREATE TRIGGER update_trend_analysis_updated_at BEFORE UPDATE ON trend_analysis FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_win_predictions_updated_at BEFORE UPDATE ON win_predictions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_compliance_matrices_updated_at BEFORE UPDATE ON compliance_matrices FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_filter_rules_updated_at BEFORE UPDATE ON filter_rules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_keyword_suggestions_updated_at BEFORE UPDATE ON keyword_suggestions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- =====================================================================
-- COMPUTED COLUMNS & VIEWS (For easy access to complex data)
-- =====================================================================

-- Create a view for opportunity intelligence summary
CREATE VIEW opportunity_intelligence AS
SELECT 
    o.id,
    o.title,
    o.agency_name,
    o.estimated_value,
    o.due_date,
    o.total_score,
    
    -- Win Prediction Data
    wp.win_probability,
    wp.confidence_score,
    wp.bid_recommendation,
    wp.competition_level,
    
    -- Compliance Data
    cm.compliance_percentage,
    cm.overall_risk_score,
    cm.total_requirements,
    
    -- Amendment Volatility (calculated)
    COALESCE(amendment_stats.amendment_count, 0) as amendment_count,
    COALESCE(amendment_stats.avg_impact_score, 0) as volatility_score,
    
    -- Trend Context
    ta.is_anomaly,
    ta.anomaly_type

FROM opportunities o
LEFT JOIN win_predictions wp ON o.id = wp.opportunity_id
LEFT JOIN compliance_matrices cm ON o.id = cm.opportunity_id
LEFT JOIN trend_analysis ta ON DATE(o.posted_date) = ta.analysis_date AND ta.analysis_type = 'daily'
LEFT JOIN (
    SELECT 
        opportunity_id,
        COUNT(*) as amendment_count,
        AVG(impact_score) as avg_impact_score
    FROM amendment_history 
    WHERE contributes_to_volatility = true
    GROUP BY opportunity_id
) amendment_stats ON o.id = amendment_stats.opportunity_id;

-- =====================================================================
-- SAMPLE DATA FOR TESTING (Optional - uncomment to insert)
-- =====================================================================

/*
-- Sample trend analysis data
INSERT INTO trend_analysis (analysis_date, analysis_type, opportunity_count, total_value, industry_breakdown) VALUES
('2025-06-22', 'daily', 45, 12500000.00, '{"defense": 25, "healthcare": 15, "it": 5}'),
('2025-06-21', 'daily', 38, 9800000.00, '{"defense": 20, "healthcare": 12, "it": 6}'),
('2025-06-20', 'daily', 52, 15200000.00, '{"defense": 30, "healthcare": 18, "it": 4}');

-- Sample keyword suggestions
INSERT INTO keyword_suggestions (base_keyword, suggested_keyword, relationship_type, relevance_score) VALUES
('cybersecurity', 'zero-trust', 'related', 85.5),
('cloud', 'multi-cloud', 'narrower', 78.2),
('ai', 'machine-learning', 'broader', 92.1),
('compliance', 'sox-compliance', 'narrower', 68.7);
*/

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================
-- This migration adds 6 new tables for enhanced intelligence features:
-- 1. trend_analysis - Time-series analysis and anomaly detection
-- 2. win_predictions - ML-powered win probability predictions  
-- 3. compliance_matrices - AI-parsed requirements and compliance mapping
-- 4. filter_rules - User-defined fast-fail filtering rules
-- 5. amendment_history - RFP amendment tracking and volatility scoring
-- 6. keyword_suggestions - AI-powered keyword recommendations
--
-- All tables include proper indexing, full-text search, RLS policies,
-- and are integrated with the existing opportunities table.
-- =====================================================================
-- Win Probability ML Pipeline Database Schema
-- Tables for storing predictions, model performance, and training data

-- Win Predictions Table
CREATE TABLE IF NOT EXISTS win_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL,
    win_probability DECIMAL(5,4) NOT NULL CHECK (win_probability >= 0 AND win_probability <= 1),
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    risk_factors JSONB DEFAULT '[]'::jsonb,
    success_factors JSONB DEFAULT '[]'::jsonb,
    competitive_analysis JSONB DEFAULT '{}'::jsonb,
    feature_importance JSONB DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL,
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model Training Results Table
CREATE TABLE IF NOT EXISTS model_training_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    accuracy DECIMAL(5,4) NOT NULL,
    precision_score DECIMAL(5,4) NOT NULL,
    recall_score DECIMAL(5,4) NOT NULL,
    f1_score DECIMAL(5,4) NOT NULL,
    auc_roc DECIMAL(5,4) NOT NULL,
    feature_importance JSONB DEFAULT '{}'::jsonb,
    cross_val_scores JSONB DEFAULT '[]'::jsonb,
    confusion_matrix JSONB DEFAULT '[]'::jsonb,
    training_samples INTEGER NOT NULL,
    feature_count INTEGER NOT NULL,
    training_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Company Bidding History Table
CREATE TABLE IF NOT EXISTS company_bidding_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    agency_name TEXT NOT NULL,
    contract_value DECIMAL(15,2),
    estimated_value DECIMAL(15,2),
    won BOOLEAN NOT NULL DEFAULT false,
    bid_date TIMESTAMP WITH TIME ZONE NOT NULL,
    decision_date TIMESTAMP WITH TIME ZONE,
    timeline_days INTEGER,
    competitor_count INTEGER,
    keywords JSONB DEFAULT '[]'::jsonb,
    risk_factors JSONB DEFAULT '[]'::jsonb,
    success_factors JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market Intelligence Table
CREATE TABLE IF NOT EXISTS market_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_date DATE NOT NULL,
    agency_name TEXT NOT NULL,
    avg_competitors DECIMAL(4,2),
    win_rate_variance DECIMAL(4,3),
    contracts_per_month DECIMAL(6,2),
    avg_contract_value DECIMAL(15,2),
    total_opportunities INTEGER,
    market_trends JSONB DEFAULT '{}'::jsonb,
    seasonal_patterns JSONB DEFAULT '{}'::jsonb,
    keyword_competition JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Win Probability Analytics View
CREATE OR REPLACE VIEW win_probability_analytics AS
SELECT 
    wp.company_id,
    wp.opportunity_id,
    o.title,
    o.agency_name,
    o.estimated_value,
    o.posted_date,
    wp.win_probability,
    wp.confidence_score,
    wp.risk_factors,
    wp.success_factors,
    wp.competitive_analysis,
    wp.prediction_date,
    CASE 
        WHEN wp.win_probability >= 0.7 THEN 'High'
        WHEN wp.win_probability >= 0.4 THEN 'Medium'
        ELSE 'Low'
    END as probability_category,
    CASE
        WHEN wp.confidence_score >= 0.8 THEN 'High'
        WHEN wp.confidence_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as confidence_category
FROM win_predictions wp
JOIN opportunities o ON wp.opportunity_id = o.id
WHERE wp.prediction_date >= NOW() - INTERVAL '90 days';

-- Company Performance Summary View
CREATE OR REPLACE VIEW company_performance_summary AS
SELECT 
    cbh.company_id,
    COUNT(*) as total_bids,
    SUM(CASE WHEN cbh.won THEN 1 ELSE 0 END) as total_wins,
    ROUND(AVG(CASE WHEN cbh.won THEN 1.0 ELSE 0.0 END), 3) as overall_win_rate,
    COUNT(DISTINCT cbh.agency_name) as agencies_worked_with,
    AVG(cbh.contract_value) as avg_contract_value,
    MAX(cbh.contract_value) as max_contract_value,
    AVG(cbh.timeline_days) as avg_timeline_days,
    -- Recent performance (last 2 years)
    COUNT(CASE WHEN cbh.bid_date >= NOW() - INTERVAL '2 years' THEN 1 END) as recent_bids,
    SUM(CASE WHEN cbh.won AND cbh.bid_date >= NOW() - INTERVAL '2 years' THEN 1 ELSE 0 END) as recent_wins,
    ROUND(AVG(CASE WHEN cbh.bid_date >= NOW() - INTERVAL '2 years' AND cbh.won THEN 1.0 
                   WHEN cbh.bid_date >= NOW() - INTERVAL '2 years' THEN 0.0 END), 3) as recent_win_rate,
    -- Agency-specific performance
    MODE() WITHIN GROUP (ORDER BY cbh.agency_name) as most_frequent_agency,
    MAX(cbh.bid_date) as last_bid_date
FROM company_bidding_history cbh
GROUP BY cbh.company_id;

-- Opportunity Competitiveness View
CREATE OR REPLACE VIEW opportunity_competitiveness AS
SELECT 
    o.id,
    o.title,
    o.agency_name,
    o.estimated_value,
    o.posted_date,
    mi.avg_competitors,
    mi.win_rate_variance,
    CASE 
        WHEN mi.avg_competitors >= 10 THEN 'Very High'
        WHEN mi.avg_competitors >= 7 THEN 'High'
        WHEN mi.avg_competitors >= 5 THEN 'Medium'
        ELSE 'Low'
    END as competition_level,
    CASE
        WHEN o.estimated_value >= 5000000 THEN 'Mega'
        WHEN o.estimated_value >= 750000 THEN 'Large'
        WHEN o.estimated_value >= 150000 THEN 'Medium'
        WHEN o.estimated_value >= 25000 THEN 'Small'
        ELSE 'Micro'
    END as value_category,
    EXTRACT(EPOCH FROM (o.due_date - o.posted_date)) / 86400 as response_days
FROM opportunities o
LEFT JOIN market_intelligence mi ON o.agency_name = mi.agency_name 
    AND mi.analysis_date = (
        SELECT MAX(analysis_date) 
        FROM market_intelligence mi2 
        WHERE mi2.agency_name = o.agency_name
    );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_win_predictions_opportunity ON win_predictions(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_win_predictions_company ON win_predictions(company_id);
CREATE INDEX IF NOT EXISTS idx_win_predictions_date ON win_predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_win_predictions_probability ON win_predictions(win_probability DESC);

CREATE INDEX IF NOT EXISTS idx_company_bidding_history_company ON company_bidding_history(company_id);
CREATE INDEX IF NOT EXISTS idx_company_bidding_history_agency ON company_bidding_history(agency_name);
CREATE INDEX IF NOT EXISTS idx_company_bidding_history_date ON company_bidding_history(bid_date);
CREATE INDEX IF NOT EXISTS idx_company_bidding_history_won ON company_bidding_history(won);

CREATE INDEX IF NOT EXISTS idx_market_intelligence_agency ON market_intelligence(agency_name);
CREATE INDEX IF NOT EXISTS idx_market_intelligence_date ON market_intelligence(analysis_date);

CREATE INDEX IF NOT EXISTS idx_model_training_date ON model_training_results(training_date);
CREATE INDEX IF NOT EXISTS idx_model_training_version ON model_training_results(model_version);

-- Row Level Security (RLS) policies
ALTER TABLE win_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_bidding_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_training_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_intelligence ENABLE ROW LEVEL SECURITY;

-- Policies for authenticated users
CREATE POLICY "Users can read win predictions" ON win_predictions
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert win predictions" ON win_predictions
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update their company's predictions" ON win_predictions
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Users can read company bidding history" ON company_bidding_history
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert company bidding history" ON company_bidding_history
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update their company's bidding history" ON company_bidding_history
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Users can read model training results" ON model_training_results
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert model training results" ON model_training_results
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can read market intelligence" ON market_intelligence
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert market intelligence" ON market_intelligence
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_win_predictions_updated_at 
    BEFORE UPDATE ON win_predictions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_bidding_history_updated_at 
    BEFORE UPDATE ON company_bidding_history 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO market_intelligence (analysis_date, agency_name, avg_competitors, win_rate_variance, contracts_per_month, avg_contract_value, total_opportunities) VALUES
('2025-06-01', 'Department of Defense', 8.5, 0.30, 45.2, 850000, 136),
('2025-06-01', 'Department of Veterans Affairs', 6.2, 0.25, 25.1, 620000, 75),
('2025-06-01', 'Department of Health and Human Services', 5.8, 0.20, 30.4, 480000, 91),
('2025-06-01', 'Department of Homeland Security', 7.1, 0.28, 20.3, 720000, 61),
('2025-06-01', 'General Services Administration', 9.2, 0.35, 35.7, 380000, 107),
('2025-06-01', 'Department of Energy', 6.8, 0.24, 15.2, 950000, 46),
('2025-06-01', 'Department of Transportation', 5.5, 0.22, 18.9, 560000, 57),
('2025-06-01', 'Environmental Protection Agency', 4.3, 0.18, 12.6, 320000, 38);

-- Sample company bidding history
INSERT INTO company_bidding_history (company_id, agency_name, contract_value, estimated_value, won, bid_date, timeline_days, competitor_count, keywords) VALUES
('company_001', 'Department of Defense', 750000, 800000, true, '2025-01-15', 35, 8, '["software", "security", "development"]'),
('company_001', 'Department of Defense', 450000, 500000, false, '2024-11-20', 28, 12, '["consulting", "analysis"]'),
('company_001', 'Department of Veterans Affairs', 320000, 350000, true, '2024-09-10', 42, 5, '["healthcare", "IT", "software"]'),
('company_001', 'Department of Health and Human Services', 180000, 200000, false, '2024-07-05', 21, 7, '["research", "data"]'),
('company_001', 'Department of Defense', 920000, 1000000, true, '2024-05-12', 45, 9, '["cybersecurity", "infrastructure"]'),

('company_002', 'General Services Administration', 250000, 275000, false, '2025-02-01', 30, 11, '["facilities", "management"]'),
('company_002', 'Department of Transportation', 380000, 400000, true, '2024-12-15', 38, 6, '["logistics", "software"]'),
('company_002', 'Department of Energy', 650000, 700000, false, '2024-10-08', 25, 8, '["renewable", "consulting"]'),
('company_002', 'Environmental Protection Agency', 190000, 220000, true, '2024-08-22', 35, 4, '["environmental", "monitoring"]');

-- Comments for documentation
COMMENT ON TABLE win_predictions IS 'Stores ML-generated win probability predictions for opportunities';
COMMENT ON TABLE company_bidding_history IS 'Historical record of company bidding activities and outcomes';
COMMENT ON TABLE model_training_results IS 'Performance metrics and metadata from ML model training sessions';
COMMENT ON TABLE market_intelligence IS 'Market analysis data including competition levels and trends by agency';

COMMENT ON COLUMN win_predictions.win_probability IS 'Predicted probability of winning the contract (0.0-1.0)';
COMMENT ON COLUMN win_predictions.confidence_score IS 'Model confidence in the prediction (0.0-1.0)';
COMMENT ON COLUMN win_predictions.risk_factors IS 'JSON array of identified risk factors';
COMMENT ON COLUMN win_predictions.success_factors IS 'JSON array of identified success factors';
COMMENT ON COLUMN win_predictions.competitive_analysis IS 'JSON object with competitive landscape analysis';
COMMENT ON COLUMN win_predictions.feature_importance IS 'JSON object with feature importance scores from the model';

COMMENT ON VIEW win_probability_analytics IS 'Comprehensive view of recent win probability predictions with categorization';
COMMENT ON VIEW company_performance_summary IS 'Aggregated performance metrics by company including historical win rates';
COMMENT ON VIEW opportunity_competitiveness IS 'Analysis of opportunity competitiveness based on market intelligence';
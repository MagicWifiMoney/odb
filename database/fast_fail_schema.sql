-- Fast-Fail Filter Database Schema
-- Tables for storing filter rules, assessments, and optimization data

-- Fast-Fail Assessments Table (Main assessment results)
CREATE TABLE IF NOT EXISTS fast_fail_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL,
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    overall_recommendation TEXT NOT NULL CHECK (overall_recommendation IN ('exclude', 'flag', 'deprioritize', 'warn')),
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    triggered_rules JSONB DEFAULT '[]'::jsonb,
    exclusion_reasons JSONB DEFAULT '[]'::jsonb,
    warning_flags JSONB DEFAULT '[]'::jsonb,
    business_rationale TEXT,
    estimated_time_saved INTEGER DEFAULT 0, -- Hours
    ai_insights JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(opportunity_id, company_id, assessment_date::date)
);

-- Filter Rules Configuration Table
CREATE TABLE IF NOT EXISTS filter_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('exclusion', 'requirement', 'threshold', 'pattern', 'business_logic')),
    priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    action TEXT NOT NULL CHECK (action IN ('exclude', 'flag', 'deprioritize', 'warn')),
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_applied TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    total_applications INTEGER DEFAULT 0,
    created_by TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rule Application History Table
CREATE TABLE IF NOT EXISTS rule_application_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id TEXT REFERENCES filter_rules(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES fast_fail_assessments(id) ON DELETE CASCADE,
    triggered BOOLEAN NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    matched_criteria JSONB DEFAULT '[]'::jsonb,
    extracted_values JSONB DEFAULT '{}'::jsonb,
    execution_time_ms INTEGER,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Filter Performance Metrics Table
CREATE TABLE IF NOT EXISTS filter_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id TEXT REFERENCES filter_rules(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    applications_count INTEGER DEFAULT 0,
    triggers_count INTEGER DEFAULT 0,
    true_positives INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    false_negatives INTEGER DEFAULT 0,
    avg_confidence_score DECIMAL(5,4),
    avg_execution_time_ms DECIMAL(8,2),
    time_saved_hours INTEGER DEFAULT 0,
    cost_saved_estimate DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(rule_id, metric_date)
);

-- Filter Optimization Recommendations Table
CREATE TABLE IF NOT EXISTS filter_optimization_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN ('rule_adjustment', 'new_rule', 'rule_removal', 'threshold_tuning')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    affected_rule_ids JSONB DEFAULT '[]'::jsonb,
    suggested_changes JSONB DEFAULT '{}'::jsonb,
    expected_impact TEXT,
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'implemented', 'rejected', 'expired')),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),
    implemented_at TIMESTAMP WITH TIME ZONE,
    implemented_by TEXT
);

-- Exclusion Patterns Analysis Table
CREATE TABLE IF NOT EXISTS exclusion_patterns_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    pattern_type TEXT NOT NULL, -- 'keyword', 'value_range', 'category', 'combination'
    pattern_description TEXT NOT NULL,
    frequency_count INTEGER DEFAULT 0,
    exclusion_rate DECIMAL(5,4) CHECK (exclusion_rate >= 0 AND exclusion_rate <= 1),
    avg_opportunity_value DECIMAL(15,2),
    time_saved_hours INTEGER DEFAULT 0,
    pattern_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, analysis_date, pattern_type, pattern_description)
);

-- Filter Dashboard Cache Table
CREATE TABLE IF NOT EXISTS filter_dashboard_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    dashboard_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour'),
    UNIQUE(company_id, cache_key)
);

-- Analytics Views

-- Filter Rule Performance View
CREATE OR REPLACE VIEW filter_rule_performance AS
SELECT 
    fr.id as rule_id,
    fr.name as rule_name,
    fr.rule_type,
    fr.priority,
    fr.action,
    fr.enabled,
    COALESCE(fr.total_applications, 0) as total_applications,
    COALESCE(fr.success_count, 0) as success_count,
    CASE 
        WHEN fr.total_applications > 0 THEN fr.success_count::decimal / fr.total_applications
        ELSE 0 
    END as success_rate,
    COALESCE(SUM(fpm.time_saved_hours), 0) as total_time_saved,
    COALESCE(AVG(fpm.avg_confidence_score), 0) as avg_confidence,
    COALESCE(AVG(fpm.avg_execution_time_ms), 0) as avg_execution_time,
    fr.last_applied,
    COUNT(DISTINCT fpm.metric_date) as days_with_activity
FROM filter_rules fr
LEFT JOIN filter_performance_metrics fpm ON fr.id = fpm.rule_id
WHERE fpm.metric_date >= CURRENT_DATE - INTERVAL '30 days' OR fpm.metric_date IS NULL
GROUP BY fr.id, fr.name, fr.rule_type, fr.priority, fr.action, fr.enabled, 
         fr.total_applications, fr.success_count, fr.last_applied;

-- Fast-Fail Assessment Summary View
CREATE OR REPLACE VIEW fast_fail_assessment_summary AS
SELECT 
    ffa.company_id,
    DATE_TRUNC('week', ffa.assessment_date) as assessment_week,
    COUNT(*) as total_assessments,
    COUNT(CASE WHEN ffa.overall_recommendation = 'exclude' THEN 1 END) as exclusions,
    COUNT(CASE WHEN ffa.overall_recommendation = 'flag' THEN 1 END) as flags,
    COUNT(CASE WHEN ffa.overall_recommendation = 'warn' THEN 1 END) as warnings,
    AVG(ffa.confidence_score) as avg_confidence,
    SUM(ffa.estimated_time_saved) as total_time_saved,
    AVG(ffa.estimated_time_saved) as avg_time_saved_per_assessment,
    
    -- Exclusion rate calculation
    CASE 
        WHEN COUNT(*) > 0 THEN COUNT(CASE WHEN ffa.overall_recommendation = 'exclude' THEN 1 END)::decimal / COUNT(*)
        ELSE 0 
    END as exclusion_rate,
    
    -- Most common exclusion reasons
    MODE() WITHIN GROUP (ORDER BY jsonb_array_elements_text(ffa.exclusion_reasons)) as most_common_exclusion_reason
FROM fast_fail_assessments ffa
WHERE ffa.assessment_date >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY ffa.company_id, DATE_TRUNC('week', ffa.assessment_date)
ORDER BY assessment_week DESC;

-- Filter Efficiency Metrics View
CREATE OR REPLACE VIEW filter_efficiency_metrics AS
SELECT 
    ffa.company_id,
    COUNT(*) as total_opportunities_assessed,
    COUNT(CASE WHEN ffa.overall_recommendation = 'exclude' THEN 1 END) as opportunities_excluded,
    SUM(ffa.estimated_time_saved) as total_time_saved_hours,
    SUM(ffa.estimated_time_saved) * 150 as estimated_cost_saved, -- $150/hour rate
    
    -- Efficiency ratios
    CASE 
        WHEN COUNT(*) > 0 THEN COUNT(CASE WHEN ffa.overall_recommendation = 'exclude' THEN 1 END)::decimal / COUNT(*)
        ELSE 0 
    END as exclusion_efficiency_rate,
    
    CASE 
        WHEN COUNT(*) > 0 THEN SUM(ffa.estimated_time_saved)::decimal / COUNT(*)
        ELSE 0 
    END as avg_time_saved_per_opportunity,
    
    -- Confidence metrics
    AVG(ffa.confidence_score) as avg_assessment_confidence,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ffa.confidence_score) as median_confidence,
    
    -- Time period analysis
    MAX(ffa.assessment_date) as last_assessment_date,
    COUNT(DISTINCT ffa.assessment_date::date) as active_assessment_days
FROM fast_fail_assessments ffa
WHERE ffa.assessment_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY ffa.company_id;

-- Rule Trigger Frequency View
CREATE OR REPLACE VIEW rule_trigger_frequency AS
SELECT 
    rah.rule_id,
    fr.name as rule_name,
    fr.rule_type,
    fr.priority,
    fr.action,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN rah.triggered THEN 1 END) as trigger_count,
    CASE 
        WHEN COUNT(*) > 0 THEN COUNT(CASE WHEN rah.triggered THEN 1 END)::decimal / COUNT(*)
        ELSE 0 
    END as trigger_rate,
    AVG(rah.confidence_score) as avg_confidence_when_triggered,
    AVG(rah.execution_time_ms) as avg_execution_time,
    
    -- Recent activity
    MAX(rah.applied_at) as last_triggered,
    COUNT(CASE WHEN rah.applied_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as triggers_last_week,
    COUNT(CASE WHEN rah.applied_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as triggers_last_month
FROM rule_application_history rah
JOIN filter_rules fr ON rah.rule_id = fr.id
WHERE rah.applied_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY rah.rule_id, fr.name, fr.rule_type, fr.priority, fr.action
ORDER BY trigger_count DESC;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_opportunity ON fast_fail_assessments(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_company ON fast_fail_assessments(company_id);
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_date ON fast_fail_assessments(assessment_date);
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_recommendation ON fast_fail_assessments(overall_recommendation);

CREATE INDEX IF NOT EXISTS idx_filter_rules_enabled ON filter_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_filter_rules_type ON filter_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_filter_rules_priority ON filter_rules(priority);

CREATE INDEX IF NOT EXISTS idx_rule_application_history_rule ON rule_application_history(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_application_history_opportunity ON rule_application_history(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_rule_application_history_triggered ON rule_application_history(triggered);
CREATE INDEX IF NOT EXISTS idx_rule_application_history_date ON rule_application_history(applied_at);

CREATE INDEX IF NOT EXISTS idx_filter_performance_metrics_rule ON filter_performance_metrics(rule_id);
CREATE INDEX IF NOT EXISTS idx_filter_performance_metrics_date ON filter_performance_metrics(metric_date);

CREATE INDEX IF NOT EXISTS idx_filter_optimization_recommendations_company ON filter_optimization_recommendations(company_id);
CREATE INDEX IF NOT EXISTS idx_filter_optimization_recommendations_status ON filter_optimization_recommendations(status);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_triggered_rules_gin ON fast_fail_assessments USING GIN(triggered_rules);
CREATE INDEX IF NOT EXISTS idx_fast_fail_assessments_exclusion_reasons_gin ON fast_fail_assessments USING GIN(exclusion_reasons);
CREATE INDEX IF NOT EXISTS idx_filter_rules_conditions_gin ON filter_rules USING GIN(conditions);
CREATE INDEX IF NOT EXISTS idx_rule_application_history_matched_criteria_gin ON rule_application_history USING GIN(matched_criteria);

-- Row Level Security (RLS) policies
ALTER TABLE fast_fail_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE rule_application_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE filter_optimization_recommendations ENABLE ROW LEVEL SECURITY;

-- Policies for authenticated users
CREATE POLICY "Users can read fast-fail assessments" ON fast_fail_assessments
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert fast-fail assessments" ON fast_fail_assessments
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can read filter rules" ON filter_rules
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage filter rules" ON filter_rules
    FOR ALL USING (auth.role() = 'authenticated'); -- TODO: Add admin role check

CREATE POLICY "Users can read rule application history" ON rule_application_history
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert rule application history" ON rule_application_history
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can read filter performance metrics" ON filter_performance_metrics
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage optimization recommendations" ON filter_optimization_recommendations
    FOR ALL USING (auth.role() = 'authenticated');

-- Triggers for updated_at timestamps
CREATE TRIGGER update_fast_fail_assessments_updated_at 
    BEFORE UPDATE ON fast_fail_assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_filter_rules_updated_at 
    BEFORE UPDATE ON filter_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default filter rules
INSERT INTO filter_rules (id, name, description, rule_type, priority, action, conditions, enabled) VALUES

-- Business Size Filters
('min_contract_value', 'Minimum Contract Value', 'Exclude contracts below minimum viable value', 'threshold', 'high', 'exclude', 
 '{"field": "estimated_value", "operator": "lt", "threshold": 50000, "currency": "USD"}'::jsonb, true),

('max_contract_value', 'Maximum Contract Value Capacity', 'Flag contracts above company capacity', 'threshold', 'medium', 'flag', 
 '{"field": "estimated_value", "operator": "gt", "threshold": 10000000, "currency": "USD"}'::jsonb, true),

-- Geographic Restrictions
('international_restriction', 'International Work Restriction', 'Exclude international contracts if not capable', 'pattern', 'critical', 'exclude', 
 '{"fields": ["description", "requirements", "location"], "exclude_patterns": ["international", "overseas", "outside\\s+united\\s+states", "oconus", "foreign", "embassy", "consulate"], "case_sensitive": false}'::jsonb, true),

-- Security Clearance Requirements
('clearance_mismatch', 'Security Clearance Mismatch', 'Exclude if security clearance requirements not met', 'requirement', 'critical', 'exclude', 
 '{"required_clearances": ["top_secret", "ts_sci"], "company_clearances": ["secret", "public_trust"], "fields": ["description", "requirements"], "clearance_patterns": ["top\\s+secret", "ts/sci", "polygraph", "special\\s+access"]}'::jsonb, true),

-- Industry/Domain Exclusions
('excluded_industries', 'Excluded Industry Sectors', 'Exclude contracts in industries we do not serve', 'exclusion', 'high', 'exclude', 
 '{"excluded_keywords": ["weapons", "munitions", "military hardware", "tobacco", "gambling", "adult entertainment"], "fields": ["description", "agency_name", "title"], "threshold": 0.7}'::jsonb, true),

-- Technical Capability Filters
('technology_mismatch', 'Technology Stack Mismatch', 'Flag contracts requiring technologies we do not support', 'pattern', 'medium', 'flag', 
 '{"unsupported_tech": ["cobol", "fortran", "mainframe", "as400", "legacy system", "proprietary platform"], "fields": ["description", "requirements", "technical_specs"], "match_threshold": 2}'::jsonb, true),

-- Timeline Filters
('insufficient_timeline', 'Insufficient Response Timeline', 'Exclude if insufficient time to prepare quality response', 'threshold', 'high', 'exclude', 
 '{"field": "days_until_due", "operator": "lt", "threshold": 7, "exceptions": ["incumbent", "existing_relationship"]}'::jsonb, true),

-- Set-Aside Restrictions
('set_aside_eligibility', 'Set-Aside Eligibility Check', 'Exclude set-asides we are not eligible for', 'business_logic', 'critical', 'exclude', 
 '{"company_certifications": ["small_business"], "excluded_set_asides": ["8a_only", "hubzone_only", "wosb_only"], "fields": ["set_aside_type", "description", "requirements"]}'::jsonb, true),

-- Competition Level Filters
('high_competition_warning', 'High Competition Warning', 'Flag opportunities with extremely high competition', 'threshold', 'low', 'warn', 
 '{"competition_indicators": ["broad_market_research", "industry_day", "multiple_awards", "unrestricted_competition"], "estimated_bidders": 20}'::jsonb, true);

-- Insert sample performance metrics
INSERT INTO filter_performance_metrics (rule_id, metric_date, applications_count, triggers_count, true_positives, false_positives, avg_confidence_score, avg_execution_time_ms, time_saved_hours) VALUES
('min_contract_value', CURRENT_DATE - INTERVAL '1 day', 25, 8, 8, 0, 0.95, 2.5, 320),
('clearance_mismatch', CURRENT_DATE - INTERVAL '1 day', 25, 5, 5, 0, 0.90, 15.2, 200),
('international_restriction', CURRENT_DATE - INTERVAL '1 day', 25, 3, 3, 0, 0.88, 8.7, 120),
('set_aside_eligibility', CURRENT_DATE - INTERVAL '1 day', 25, 4, 4, 0, 0.92, 12.1, 160),
('technology_mismatch', CURRENT_DATE - INTERVAL '1 day', 25, 2, 1, 1, 0.65, 25.8, 40);

-- Comments for documentation
COMMENT ON TABLE fast_fail_assessments IS 'Results of fast-fail filter assessments for opportunities';
COMMENT ON TABLE filter_rules IS 'Configuration and definitions of filter rules';
COMMENT ON TABLE rule_application_history IS 'History of rule applications and results';
COMMENT ON TABLE filter_performance_metrics IS 'Performance metrics and statistics for filter rules';
COMMENT ON TABLE filter_optimization_recommendations IS 'AI-generated recommendations for filter optimization';
COMMENT ON TABLE exclusion_patterns_analysis IS 'Analysis of common exclusion patterns and trends';

COMMENT ON COLUMN fast_fail_assessments.overall_recommendation IS 'Final recommendation: exclude, flag, deprioritize, warn';
COMMENT ON COLUMN fast_fail_assessments.confidence_score IS 'Confidence in the assessment (0.0-1.0)';
COMMENT ON COLUMN fast_fail_assessments.estimated_time_saved IS 'Estimated time saved in hours by applying filters';

COMMENT ON COLUMN filter_rules.rule_type IS 'Type of rule: exclusion, requirement, threshold, pattern, business_logic';
COMMENT ON COLUMN filter_rules.priority IS 'Rule priority: critical, high, medium, low';
COMMENT ON COLUMN filter_rules.action IS 'Action to take when rule triggers: exclude, flag, deprioritize, warn';

COMMENT ON VIEW filter_rule_performance IS 'Performance analysis of filter rules over the last 30 days';
COMMENT ON VIEW fast_fail_assessment_summary IS 'Weekly summary of fast-fail assessments by company';
COMMENT ON VIEW filter_efficiency_metrics IS 'Overall efficiency metrics for the filter system';
COMMENT ON VIEW rule_trigger_frequency IS 'Frequency analysis of rule triggers over the last 90 days';
-- Compliance Matrix Engine Database Schema
-- Tables for storing compliance requirements, assessments, and company profiles

-- Company Compliance Profiles Table
CREATE TABLE IF NOT EXISTS company_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL UNIQUE,
    profile_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance Matrices Table (Main analysis results)
CREATE TABLE IF NOT EXISTS compliance_matrices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    overall_compliance_score DECIMAL(5,4) NOT NULL CHECK (overall_compliance_score >= 0 AND overall_compliance_score <= 1),
    total_effort_estimate INTEGER DEFAULT 0,
    total_cost_estimate DECIMAL(15,2) DEFAULT 0,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('Very Low', 'Low', 'Medium', 'High', 'Very High')),
    critical_gaps JSONB DEFAULT '[]'::jsonb,
    quick_wins JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    next_actions JSONB DEFAULT '[]'::jsonb,
    requirements_count INTEGER DEFAULT 0,
    assessments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(opportunity_id, company_id)
);

-- Compliance Requirements Table (Extracted requirements)
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'security_clearance', 'certifications', 'experience', 'financial', 
        'technical', 'legal', 'small_business', 'performance', 'insurance', 'geographic'
    )),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    mandatory BOOLEAN DEFAULT false,
    source_section TEXT,
    keywords JSONB DEFAULT '[]'::jsonb,
    sub_requirements JSONB DEFAULT '[]'::jsonb,
    verification_method TEXT,
    timeline_days INTEGER,
    cost_estimate DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(opportunity_id, requirement_id)
);

-- Compliance Assessments Table (Assessment results)
CREATE TABLE IF NOT EXISTS compliance_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('compliant', 'partial', 'non_compliant', 'unknown', 'not_applicable')),
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    evidence JSONB DEFAULT '[]'::jsonb,
    gaps JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    effort_estimate INTEGER, -- Hours
    cost_estimate DECIMAL(15,2),
    notes TEXT,
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(opportunity_id, requirement_id, company_id)
);

-- Compliance Categories Reference Table
CREATE TABLE IF NOT EXISTS compliance_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code TEXT NOT NULL UNIQUE,
    category_name TEXT NOT NULL,
    description TEXT,
    typical_requirements JSONB DEFAULT '[]'::jsonb,
    verification_methods JSONB DEFAULT '[]'::jsonb,
    average_timeline_days INTEGER,
    average_cost_estimate DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Requirement Templates Table (Common requirements patterns)
CREATE TABLE IF NOT EXISTS requirement_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name TEXT NOT NULL,
    category TEXT NOT NULL,
    template_text TEXT NOT NULL,
    keywords JSONB DEFAULT '[]'::jsonb,
    priority TEXT NOT NULL,
    mandatory BOOLEAN DEFAULT false,
    verification_method TEXT,
    typical_timeline_days INTEGER,
    typical_cost_estimate DECIMAL(15,2),
    usage_frequency INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance Analytics Views

-- Compliance Score Trends View
CREATE OR REPLACE VIEW compliance_score_trends AS
SELECT 
    cm.company_id,
    DATE_TRUNC('week', cm.analysis_date) as analysis_week,
    AVG(cm.overall_compliance_score) as avg_compliance_score,
    COUNT(*) as opportunities_analyzed,
    AVG(cm.total_effort_estimate) as avg_effort,
    AVG(cm.total_cost_estimate) as avg_cost,
    MODE() WITHIN GROUP (ORDER BY cm.risk_level) as most_common_risk_level
FROM compliance_matrices cm
WHERE cm.analysis_date >= NOW() - INTERVAL '12 weeks'
GROUP BY cm.company_id, DATE_TRUNC('week', cm.analysis_date)
ORDER BY analysis_week DESC;

-- Compliance Category Performance View
CREATE OR REPLACE VIEW compliance_category_performance AS
SELECT 
    cr.category,
    COUNT(*) as total_requirements,
    AVG(CASE 
        WHEN ca.status = 'compliant' THEN 1.0
        WHEN ca.status = 'partial' THEN 0.6
        WHEN ca.status = 'non_compliant' THEN 0.0
        ELSE 0.3
    END) as avg_compliance_rate,
    COUNT(CASE WHEN ca.status = 'compliant' THEN 1 END) as compliant_count,
    COUNT(CASE WHEN ca.status = 'non_compliant' THEN 1 END) as non_compliant_count,
    AVG(ca.effort_estimate) as avg_effort_to_comply,
    AVG(ca.cost_estimate) as avg_cost_to_comply,
    AVG(ca.confidence_score) as avg_assessment_confidence
FROM compliance_requirements cr
LEFT JOIN compliance_assessments ca ON cr.opportunity_id = ca.opportunity_id 
    AND cr.requirement_id = ca.requirement_id
WHERE cr.created_at >= NOW() - INTERVAL '90 days'
GROUP BY cr.category;

-- Gap Analysis Summary View
CREATE OR REPLACE VIEW compliance_gap_analysis AS
SELECT 
    cr.category,
    cr.priority,
    COUNT(*) as total_gaps,
    AVG(ca.effort_estimate) as avg_effort_to_close,
    AVG(ca.cost_estimate) as avg_cost_to_close,
    COUNT(CASE WHEN cr.mandatory = true THEN 1 END) as mandatory_gaps,
    ARRAY_AGG(DISTINCT cr.title ORDER BY cr.title) as common_gap_titles
FROM compliance_requirements cr
JOIN compliance_assessments ca ON cr.opportunity_id = ca.opportunity_id 
    AND cr.requirement_id = ca.requirement_id
WHERE ca.status IN ('non_compliant', 'partial')
    AND ca.assessment_date >= NOW() - INTERVAL '90 days'
GROUP BY cr.category, cr.priority
ORDER BY 
    CASE cr.priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END,
    total_gaps DESC;

-- Company Readiness Dashboard View
CREATE OR REPLACE VIEW company_readiness_dashboard AS
SELECT 
    cm.company_id,
    COUNT(DISTINCT cm.opportunity_id) as opportunities_analyzed,
    AVG(cm.overall_compliance_score) as avg_compliance_score,
    MODE() WITHIN GROUP (ORDER BY cm.risk_level) as typical_risk_level,
    SUM(cm.total_effort_estimate) as total_effort_needed,
    SUM(cm.total_cost_estimate) as total_cost_needed,
    
    -- Category breakdown
    COUNT(CASE WHEN 'security_clearance' = ANY(
        SELECT jsonb_array_elements_text(cm.critical_gaps)
    ) THEN 1 END) as security_clearance_gaps,
    
    COUNT(CASE WHEN 'certifications' = ANY(
        SELECT jsonb_array_elements_text(cm.critical_gaps)
    ) THEN 1 END) as certification_gaps,
    
    COUNT(CASE WHEN 'experience' = ANY(
        SELECT jsonb_array_elements_text(cm.critical_gaps)
    ) THEN 1 END) as experience_gaps,
    
    -- Recent trend
    AVG(CASE WHEN cm.analysis_date >= NOW() - INTERVAL '30 days' 
        THEN cm.overall_compliance_score END) as recent_compliance_score,
    
    MAX(cm.analysis_date) as last_analysis_date
FROM compliance_matrices cm
WHERE cm.analysis_date >= NOW() - INTERVAL '180 days'
GROUP BY cm.company_id;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_compliance_matrices_opportunity ON compliance_matrices(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_compliance_matrices_company ON compliance_matrices(company_id);
CREATE INDEX IF NOT EXISTS idx_compliance_matrices_date ON compliance_matrices(analysis_date);
CREATE INDEX IF NOT EXISTS idx_compliance_matrices_score ON compliance_matrices(overall_compliance_score);

CREATE INDEX IF NOT EXISTS idx_compliance_requirements_opportunity ON compliance_requirements(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_compliance_requirements_category ON compliance_requirements(category);
CREATE INDEX IF NOT EXISTS idx_compliance_requirements_priority ON compliance_requirements(priority);
CREATE INDEX IF NOT EXISTS idx_compliance_requirements_mandatory ON compliance_requirements(mandatory);

CREATE INDEX IF NOT EXISTS idx_compliance_assessments_opportunity ON compliance_assessments(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_compliance_assessments_company ON compliance_assessments(company_id);
CREATE INDEX IF NOT EXISTS idx_compliance_assessments_status ON compliance_assessments(status);
CREATE INDEX IF NOT EXISTS idx_compliance_assessments_date ON compliance_assessments(assessment_date);

CREATE INDEX IF NOT EXISTS idx_company_profiles_company ON company_profiles(company_id);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_compliance_matrices_gaps_gin ON compliance_matrices USING GIN(critical_gaps);
CREATE INDEX IF NOT EXISTS idx_compliance_requirements_keywords_gin ON compliance_requirements USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_compliance_assessments_evidence_gin ON compliance_assessments USING GIN(evidence);
CREATE INDEX IF NOT EXISTS idx_company_profiles_data_gin ON company_profiles USING GIN(profile_data);

-- Row Level Security (RLS) policies
ALTER TABLE compliance_matrices ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_profiles ENABLE ROW LEVEL SECURITY;

-- Policies for authenticated users
CREATE POLICY "Users can read compliance matrices" ON compliance_matrices
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert compliance matrices" ON compliance_matrices
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update their company's compliance matrices" ON compliance_matrices
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Users can read compliance requirements" ON compliance_requirements
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert compliance requirements" ON compliance_requirements
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can read compliance assessments" ON compliance_assessments
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert compliance assessments" ON compliance_assessments
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Users can update their company's assessments" ON compliance_assessments
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Users can read company profiles" ON company_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can update company profiles" ON company_profiles
    FOR ALL USING (auth.role() = 'authenticated');

-- Triggers for updated_at timestamps
CREATE TRIGGER update_compliance_matrices_updated_at 
    BEFORE UPDATE ON compliance_matrices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_profiles_updated_at 
    BEFORE UPDATE ON company_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_requirement_templates_updated_at 
    BEFORE UPDATE ON requirement_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert compliance categories reference data
INSERT INTO compliance_categories (category_code, category_name, description, typical_requirements, average_timeline_days, average_cost_estimate) VALUES
('security_clearance', 'Security Clearance', 'Personnel security clearance requirements', 
 '["Secret clearance", "Top Secret clearance", "Public Trust", "Background investigation"]'::jsonb, 180, 25000),

('certifications', 'Certifications & Accreditations', 'Company and individual certifications', 
 '["ISO 9001", "CMMI Level 3", "SOC 2", "FedRAMP", "Professional certifications"]'::jsonb, 90, 15000),

('experience', 'Experience Requirements', 'Relevant experience and past performance', 
 '["Years of experience", "Similar project experience", "Domain expertise", "Past performance"]'::jsonb, 30, 8000),

('financial', 'Financial Requirements', 'Financial capacity and bonding', 
 '["Annual revenue", "Bonding capacity", "Financial statements", "Credit rating"]'::jsonb, 45, 12000),

('technical', 'Technical Capabilities', 'Technical skills and infrastructure', 
 '["Technology expertise", "Infrastructure", "Technical team", "Tools and platforms"]'::jsonb, 60, 20000),

('legal', 'Legal & Regulatory', 'Legal compliance and regulatory requirements', 
 '["Regulatory compliance", "Legal structure", "Compliance frameworks", "Audit requirements"]'::jsonb, 75, 18000),

('small_business', 'Small Business Status', 'Small business and socioeconomic requirements', 
 '["Small business certification", "8(a) status", "HUBZone", "WOSB", "VOSB", "SDVOSB"]'::jsonb, 60, 8000),

('performance', 'Performance Standards', 'Performance metrics and SLA requirements', 
 '["Uptime requirements", "Performance metrics", "SLA compliance", "Quality standards"]'::jsonb, 45, 10000),

('insurance', 'Insurance Requirements', 'Insurance coverage requirements', 
 '["General liability", "Professional liability", "Cyber insurance", "Workers compensation"]'::jsonb, 14, 5000),

('geographic', 'Geographic Requirements', 'Location and facility requirements', 
 '["Domestic presence", "Facility requirements", "Geographic restrictions", "On-site capability"]'::jsonb, 30, 8000);

-- Insert common requirement templates
INSERT INTO requirement_templates (template_name, category, template_text, keywords, priority, mandatory, verification_method, typical_timeline_days, typical_cost_estimate) VALUES
('Secret Security Clearance', 'security_clearance', 'Personnel must possess active Secret security clearance', 
 '["security clearance", "secret", "personnel"]'::jsonb, 'critical', true, 'Clearance verification', 180, 25000),

('ISO 9001 Certification', 'certifications', 'Company must maintain ISO 9001 quality management certification', 
 '["ISO 9001", "quality management", "certification"]'::jsonb, 'high', false, 'Certificate verification', 90, 15000),

('5 Years Experience', 'experience', 'Minimum 5 years of relevant experience required', 
 '["5 years", "experience", "relevant"]'::jsonb, 'high', true, 'Reference verification', 30, 5000),

('$5M Annual Revenue', 'financial', 'Minimum $5 million annual revenue for past 3 years', 
 '["annual revenue", "5 million", "financial"]'::jsonb, 'critical', true, 'Financial statements', 45, 10000),

('Cloud Infrastructure', 'technical', 'Demonstrated cloud infrastructure management capability', 
 '["cloud", "infrastructure", "management"]'::jsonb, 'medium', false, 'Technical demonstration', 60, 15000),

('FISMA Compliance', 'legal', 'Must comply with FISMA security requirements', 
 '["FISMA", "compliance", "security"]'::jsonb, 'critical', true, 'Compliance documentation', 90, 20000),

('Small Business Set-Aside', 'small_business', 'Reserved for small business contractors only', 
 '["small business", "set-aside", "SBA"]'::jsonb, 'critical', true, 'SBA certification', 60, 5000),

('99.9% Uptime SLA', 'performance', 'System must maintain 99.9% uptime availability', 
 '["uptime", "99.9%", "availability", "SLA"]'::jsonb, 'high', true, 'Performance monitoring', 45, 8000),

('$2M Liability Insurance', 'insurance', 'General liability insurance minimum $2 million coverage', 
 '["liability insurance", "2 million", "coverage"]'::jsonb, 'medium', true, 'Insurance certificate', 14, 3000),

('CONUS Facility Required', 'geographic', 'Must maintain facility within Continental United States', 
 '["CONUS", "facility", "domestic"]'::jsonb, 'medium', false, 'Facility documentation', 30, 10000);

-- Sample company profile data
INSERT INTO company_profiles (company_id, profile_data) VALUES
('demo_company_001', '{
    "security_clearances": ["Secret", "Public Trust"],
    "certifications": ["ISO 9001:2015", "CMMI Level 3"],
    "experience_years": 12,
    "project_history": [
        {"title": "DOD IT Modernization", "value": 2500000, "duration": 24},
        {"title": "VA Healthcare System", "value": 1800000, "duration": 18}
    ],
    "domain_expertise": ["Cybersecurity", "Cloud Computing", "Data Analytics"],
    "annual_revenue": 15000000,
    "bonding_capacity": 10000000,
    "financial_strength": "excellent",
    "technical_capabilities": ["AWS", "Azure", "Kubernetes", "DevOps"],
    "technology_stack": ["Python", "Java", "React", "PostgreSQL"],
    "compliance_certifications": ["SOC 2 Type II", "FedRAMP Ready"],
    "regulatory_experience": ["FISMA", "NIST", "HIPAA"],
    "small_business_status": true,
    "sba_certifications": ["8(a)", "HUBZone"],
    "performance_metrics": {"uptime_percentage": 99.95, "customer_satisfaction": 4.8},
    "sla_history": [{"contract": "DOD-2023", "uptime": 99.97}, {"contract": "VA-2022", "uptime": 99.92}],
    "insurance_coverage": ["General Liability: $5M", "Professional Liability: $2M", "Cyber: $1M"],
    "locations": ["Washington, DC", "Atlanta, GA", "Denver, CO"],
    "facilities": ["HQ: Washington DC", "Dev Center: Atlanta"],
    "geographic_presence": ["United States"],
    "domestic_capability": true
}'::jsonb);

-- Comments for documentation
COMMENT ON TABLE compliance_matrices IS 'Main compliance analysis results for opportunities';
COMMENT ON TABLE compliance_requirements IS 'Extracted compliance requirements from opportunity documents';
COMMENT ON TABLE compliance_assessments IS 'Assessment results for each requirement against company capabilities';
COMMENT ON TABLE company_profiles IS 'Company compliance profiles and capabilities';
COMMENT ON TABLE compliance_categories IS 'Reference data for compliance categories';
COMMENT ON TABLE requirement_templates IS 'Common requirement patterns for reuse';

COMMENT ON COLUMN compliance_matrices.overall_compliance_score IS 'Overall compliance score (0.0-1.0)';
COMMENT ON COLUMN compliance_matrices.risk_level IS 'Risk level: Very Low, Low, Medium, High, Very High';
COMMENT ON COLUMN compliance_requirements.priority IS 'Requirement priority: critical, high, medium, low';
COMMENT ON COLUMN compliance_assessments.status IS 'Compliance status: compliant, partial, non_compliant, unknown, not_applicable';
COMMENT ON COLUMN compliance_assessments.confidence_score IS 'Assessment confidence (0.0-1.0)';

COMMENT ON VIEW compliance_score_trends IS 'Weekly compliance score trends by company';
COMMENT ON VIEW compliance_category_performance IS 'Performance metrics by compliance category';
COMMENT ON VIEW compliance_gap_analysis IS 'Analysis of compliance gaps and costs to close';
COMMENT ON VIEW company_readiness_dashboard IS 'Company compliance readiness dashboard summary';
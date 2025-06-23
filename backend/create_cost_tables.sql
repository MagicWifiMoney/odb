-- Cost Tracking Database Schema
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'POST',
    query_text TEXT NOT NULL,
    response_size_kb DECIMAL(10,3) DEFAULT 0,
    cost_usd DECIMAL(10,6) NOT NULL,
    response_time_ms INTEGER DEFAULT 0,
    status_code INTEGER DEFAULT 200,
    user_id VARCHAR(100),
    metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage_logs(user_id);

-- Create a simple cost summary view
CREATE OR REPLACE VIEW daily_cost_summary AS
SELECT 
    DATE(timestamp) as date,
    endpoint,
    COUNT(*) as api_calls,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time,
    SUM(response_size_kb) as total_data_kb
FROM api_usage_logs 
GROUP BY DATE(timestamp), endpoint
ORDER BY date DESC; 
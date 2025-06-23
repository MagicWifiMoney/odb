#!/usr/bin/env python3
"""
Manual table creation script for missing database tables
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all required tables manually"""
    
    # SQL to create the api_usage_logs table
    create_api_usage_sql = """
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
    """
    
    # Create indexes
    create_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_logs(timestamp);
    CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint);
    CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage_logs(user_id);
    """
    
    # Create view
    create_view_sql = """
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
    """
    
    try:
        # Get database connection
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        if conn is None:
            logger.error("Failed to get database connection")
            return False
            
        cursor = conn.cursor()
        
        # Create table
        logger.info("Creating api_usage_logs table...")
        cursor.execute(create_api_usage_sql)
        
        # Create indexes
        logger.info("Creating indexes...")
        cursor.execute(create_indexes_sql)
        
        # Create view
        logger.info("Creating view...")
        cursor.execute(create_view_sql)
        
        # Commit changes
        conn.commit()
        logger.info("✅ All tables created successfully!")
        
        # Test the table
        cursor.execute("SELECT COUNT(*) FROM api_usage_logs;")
        count = cursor.fetchone()[0]
        logger.info(f"✅ Table verification: api_usage_logs has {count} rows")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    logger.info("🚀 Creating database tables manually...")
    success = create_tables()
    
    if success:
        logger.info("🎉 Database setup completed successfully!")
        logger.info("You can now start the backend server.")
    else:
        logger.error("❌ Database setup failed. Check the error messages above.")
        sys.exit(1) 
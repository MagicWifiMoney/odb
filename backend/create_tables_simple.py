#!/usr/bin/env python3
"""
Simple table creation script using SQLAlchemy
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from src.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all required tables using SQLAlchemy"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure database
    database_url = os.getenv('DATABASE_URL', 'sqlite:///opportunities.db')
    
    # Handle postgres:// vs postgresql:// issue
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Test connection
            logger.info("Testing database connection...")
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            logger.info("✅ Database connection successful")
            
            # Create the table using raw SQL
            logger.info("Creating api_usage_logs table...")
            
            create_table_sql = """
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
            
            with db.engine.connect() as connection:
                connection.execute(db.text(create_table_sql))
                connection.commit()
            logger.info("✅ Table created successfully")
            
            # Create indexes
            logger.info("Creating indexes...")
            
            index_sqls = [
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_logs(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint);",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage_logs(user_id);"
            ]
            
            with db.engine.connect() as connection:
                for index_sql in index_sqls:
                    connection.execute(db.text(index_sql))
                connection.commit()
            logger.info("✅ Indexes created successfully")
            
            # Create view
            logger.info("Creating view...")
            
            # Drop view if exists (SQLite compatible)
            drop_view_sql = "DROP VIEW IF EXISTS daily_cost_summary;"
            
            view_sql = """
            CREATE VIEW daily_cost_summary AS
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
            
            with db.engine.connect() as connection:
                connection.execute(db.text(drop_view_sql))
                connection.execute(db.text(view_sql))
                connection.commit()
            logger.info("✅ View created successfully")
            
            # Test the table
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT COUNT(*) FROM api_usage_logs"))
                count = result.fetchone()[0]
            logger.info(f"✅ Table verification: api_usage_logs has {count} rows")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Creating database tables...")
    success = create_tables()
    
    if success:
        logger.info("🎉 Database setup completed successfully!")
        logger.info("You can now start the backend server.")
    else:
        logger.error("❌ Database setup failed. Check the error messages above.")
        sys.exit(1) 
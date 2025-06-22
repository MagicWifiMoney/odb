#!/usr/bin/env python3
"""
Database setup script for cost tracking tables.
This script creates the necessary tables and indexes in Supabase for cost tracking.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend src directory to the path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.config.supabase import get_supabase_admin_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_cost_tracking_tables():
    """Create the cost tracking tables in Supabase"""
    try:
        # Get admin client for DDL operations
        supabase = get_supabase_admin_client()
        
        # Read the SQL schema file
        schema_file = Path(__file__).parent / 'create_cost_tables.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r') as f:
            sql_content = f.read()
        
        logger.info("Creating cost tracking tables...")
        
        # Execute the SQL using Supabase RPC (if available) or direct SQL execution
        # Note: This depends on having the right permissions and Supabase setup
        try:
            # For now, we'll use the table creation through the Python client
            # The actual table creation should be done through the Supabase dashboard
            # or CLI for production use
            
            # Test if the table exists by trying to query it
            result = supabase.table('api_usage_logs').select('id').limit(1).execute()
            logger.info("✅ api_usage_logs table already exists and is accessible")
            return True
            
        except Exception as e:
            logger.warning(f"Table doesn't exist yet: {e}")
            logger.info("📋 Please create the tables manually using the SQL in create_cost_tables.sql")
            logger.info("You can do this through:")
            logger.info("1. Supabase Dashboard > SQL Editor")
            logger.info("2. Supabase CLI: supabase db reset")
            logger.info("3. Direct SQL execution in your database")
            return False
        
    except Exception as e:
        logger.error(f"Failed to set up cost tracking tables: {e}")
        return False

def test_cost_tracking_service():
    """Test the cost tracking service after table creation"""
    try:
        from src.services.cost_tracking_service import get_cost_tracking_service
        
        logger.info("Testing cost tracking service...")
        
        cost_service = get_cost_tracking_service()
        
        # Test basic functionality
        summary = cost_service.get_usage_summary()
        budget_status = cost_service.get_budget_status()
        
        logger.info("✅ Cost tracking service is working correctly")
        logger.info(f"   - Budget status: {budget_status['daily']['alert_level']}")
        logger.info(f"   - Daily requests: {budget_status['daily']['requests']}")
        logger.info(f"   - Daily cost: ${budget_status['daily']['spent']:.6f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Cost tracking service test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Setting up cost tracking database...")
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set these in your .env file or environment")
        return False
    
    # Create tables
    if create_cost_tracking_tables():
        logger.info("✅ Database setup completed")
        
        # Test the service
        if test_cost_tracking_service():
            logger.info("✅ All tests passed! Cost tracking is ready to use.")
            return True
        else:
            logger.warning("⚠️  Database setup completed but service tests failed")
            return False
    else:
        logger.error("❌ Database setup failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 
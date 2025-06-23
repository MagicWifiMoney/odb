#!/usr/bin/env python3
"""
Supabase Database Setup Script
This script helps set up the required tables in your Supabase database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from src.database import db
from src.models.opportunity import Opportunity

def setup_supabase():
    """Set up Supabase database with required tables"""
    
    print("🚀 Setting up Supabase database...")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please add your Supabase connection string to the .env file")
        return False
    
    if 'sqlite' in database_url.lower():
        print("⚠️  Warning: Using SQLite instead of Supabase")
        print("Make sure your DATABASE_URL points to your Supabase PostgreSQL database")
    
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
            print("🔗 Testing database connection...")
            from sqlalchemy import text
            result = db.session.execute(text('SELECT version()'))
            row = result.fetchone()
            if row:
                version = row[0]
                print(f"✅ Connected to PostgreSQL: {version[:50]}...")
            else:
                print("✅ Connected to database successfully")
            
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Create the API usage logs table
            print("📊 Creating API usage logs table...")
            create_api_logs_sql = """
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
                model_used VARCHAR(50),
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            db.session.execute(text(create_api_logs_sql))
            db.session.commit()
            print("✅ API usage logs table created")
            
            # Create indexes
            print("🔍 Creating database indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_logs(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint);",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage_logs(user_id);"
            ]
            
            for index_sql in indexes:
                db.session.execute(text(index_sql))
            
            db.session.commit()
            print("✅ Indexes created successfully")
            
            # Test inserting a sample opportunity
            print("🧪 Testing data insertion...")
            from datetime import datetime, timedelta
            
            test_opp = Opportunity(
                title='Test Opportunity - Supabase Setup',
                description='This is a test opportunity to verify Supabase connection',
                agency_name='Test Agency',
                opportunity_number='TEST-001',
                estimated_value=100000,
                due_date=datetime.now() + timedelta(days=30),
                source_type='test',
                source_name='Setup Script',
                location='Test Location',
                total_score=75
            )
            
            db.session.add(test_opp)
            db.session.commit()
            print("✅ Test data inserted successfully")
            
            # Count opportunities
            count = db.session.query(Opportunity).count()
            print(f"📊 Total opportunities in database: {count}")
            
            print("\n🎉 Supabase setup completed successfully!")
            print(f"🔗 Database URL: {database_url[:50]}...")
            print("🚀 You can now start your Flask application")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up database: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            
            if "password authentication failed" in str(e):
                print("\n💡 Tip: Check your database password in the DATABASE_URL")
            elif "could not connect to server" in str(e):
                print("\n💡 Tip: Check your Supabase project URL and network connection")
            elif "database does not exist" in str(e):
                print("\n💡 Tip: Make sure you're using the correct database name (usually 'postgres')")
            
            return False

def show_env_instructions():
    """Show instructions for setting up environment variables"""
    print("\n📝 To complete the setup, you need to:")
    print("1. Get your Supabase database password from:")
    print("   https://supabase.com/dashboard → Your Project → Settings → Database")
    print("2. Update the DATABASE_URL in your .env file with the correct password")
    print("3. Get your Supabase API keys from:")
    print("   https://supabase.com/dashboard → Your Project → Settings → API")
    print("4. Update SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY in .env")
    print("\nExample DATABASE_URL format:")
    print("DATABASE_URL=postgresql://postgres.zkdrpchjejelgsuuffli:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres")

if __name__ == '__main__':
    success = setup_supabase()
    
    if not success:
        show_env_instructions()
        sys.exit(1)
    else:
        print("\n✅ Setup complete! You can now run: python3 -m src.main") 
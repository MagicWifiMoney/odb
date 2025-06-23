#!/usr/bin/env python3
"""
Database setup script for Opportunity Dashboard
Executes the database schema SQL files
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

def execute_sql_file(cursor, filepath):
    """Execute SQL commands from file"""
    print(f"Executing {filepath}...")
    try:
        with open(filepath, 'r') as file:
            sql_content = file.read()
            
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"✓ Executed statement successfully")
                except Exception as e:
                    print(f"⚠ Warning executing statement: {e}")
                    continue
                    
    except Exception as e:
        print(f"✗ Error executing {filepath}: {e}")
        return False
    
    return True

def main():
    """Set up database schema"""
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("✗ DATABASE_URL not found in environment")
        return False
    
    print("🗄️  Setting up Opportunity Dashboard Database...")
    print(f"📡 Connecting to: {database_url.split('@')[1] if '@' in database_url else 'database'}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✓ Connected to database successfully")
        
        # Check if tables already exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'opportunities';
        """)
        
        if cursor.fetchone():
            print("⚠ Opportunities table already exists. Skipping basic schema.")
            schema_needed = False
        else:
            schema_needed = True
            
        # Execute schema files
        schema_files = []
        
        if schema_needed:
            schema_files.append('supabase_schema.sql')
            
        # Always run enhanced schema for upgrades
        schema_files.append('enhanced_schema.sql')
        
        for schema_file in schema_files:
            if os.path.exists(schema_file):
                if execute_sql_file(cursor, schema_file):
                    print(f"✓ {schema_file} executed successfully")
                else:
                    print(f"✗ Failed to execute {schema_file}")
            else:
                print(f"⚠ Schema file {schema_file} not found")
        
        # Verify installation
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT name FROM data_sources WHERE is_active = true;")
        sources = cursor.fetchall()
        
        print(f"\n🎉 Database setup complete!")
        print(f"📊 Created {table_count} tables")
        print(f"🔌 Configured {len(sources)} data sources:")
        for source in sources:
            print(f"   • {source[0]}")
            
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
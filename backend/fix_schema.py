#!/usr/bin/env python3
"""
Database schema migration script to fix sync service compatibility
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.opportunity import db
from src.main import create_app
app = create_app()
from sqlalchemy import text

def migrate_schema():
    """Apply schema migrations to fix sync service issues"""
    
    with app.app_context():
        try:
            print("🔧 Starting database schema migration...")
            
            # Migration 1: Rename 'type' column to 'source_type' in data_sources table
            print("📝 Migration 1: Renaming 'type' to 'source_type' in data_sources table...")
            
            # Check if the rename is needed
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'data_sources' AND column_name = 'type'
            """))
            
            if result.fetchone():
                db.session.execute(text("""
                    ALTER TABLE data_sources RENAME COLUMN type TO source_type;
                """))
                print("✅ Renamed 'type' to 'source_type'")
            else:
                print("ℹ️  Column 'source_type' already exists, skipping rename")
            
            # Migration 2: Update sync_logs table structure
            print("📝 Migration 2: Updating sync_logs table structure...")
            
            # Add missing columns to sync_logs if they don't exist
            missing_columns = [
                ("source_id", "INTEGER REFERENCES data_sources(id)"),
                ("sync_start", "TIMESTAMP WITH TIME ZONE"),
                ("sync_end", "TIMESTAMP WITH TIME ZONE"), 
                ("status", "VARCHAR(20) DEFAULT 'running'"),
                ("errors_count", "INTEGER DEFAULT 0")
            ]
            
            for col_name, col_def in missing_columns:
                # Check if column exists
                result = db.session.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'sync_logs' AND column_name = '{col_name}'
                """))
                
                if not result.fetchone():
                    try:
                        db.session.execute(text(f"""
                            ALTER TABLE sync_logs ADD COLUMN {col_name} {col_def};
                        """))
                        print(f"✅ Added column '{col_name}' to sync_logs")
                    except Exception as e:
                        print(f"⚠️  Could not add column '{col_name}': {e}")
                else:
                    print(f"ℹ️  Column '{col_name}' already exists in sync_logs")
            
            # Migration 3: Ensure all required columns exist in opportunities table
            print("📝 Migration 3: Checking opportunities table...")
            
            # Check if any required columns are missing from opportunities
            required_opportunity_columns = [
                ("source_id", "VARCHAR(255)"),
                ("close_date", "TIMESTAMP WITH TIME ZONE"),
                ("min_award_amount", "NUMERIC"),
                ("max_award_amount", "NUMERIC"),
                ("category", "VARCHAR(200)"),
                ("subcategory", "VARCHAR(200)"),
                ("naics_code", "VARCHAR(20)"),
                ("psc_code", "VARCHAR(20)"),
                ("cfda_number", "VARCHAR(20)"),
                ("place_of_performance_city", "VARCHAR(200)"),
                ("place_of_performance_state", "VARCHAR(10)"),
                ("place_of_performance_country", "VARCHAR(100)"),
                ("department", "VARCHAR(200)"),
                ("office", "VARCHAR(200)"),
                ("contact_name", "VARCHAR(200)"),
                ("contact_email", "VARCHAR(255)"),
                ("contact_phone", "VARCHAR(50)"),
                ("status", "VARCHAR(50) DEFAULT 'active'"),
                ("opportunity_type", "VARCHAR(100)"),
                ("set_aside_type", "VARCHAR(100)"),
                ("document_urls", "TEXT")
            ]
            
            for col_name, col_def in required_opportunity_columns:
                result = db.session.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'opportunities' AND column_name = '{col_name}'
                """))
                
                if not result.fetchone():
                    try:
                        db.session.execute(text(f"""
                            ALTER TABLE opportunities ADD COLUMN {col_name} {col_def};
                        """))
                        print(f"✅ Added column '{col_name}' to opportunities")
                    except Exception as e:
                        print(f"⚠️  Could not add column '{col_name}': {e}")
            
            # Commit all changes
            db.session.commit()
            print("🎉 Schema migration completed successfully!")
            
            # Verify the changes
            print("\n🔍 Verifying updated schema...")
            
            # Check data_sources table
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'data_sources' AND column_name = 'source_type'
            """))
            
            if result.fetchone():
                print("✅ data_sources.source_type column verified")
            else:
                print("❌ data_sources.source_type column missing")
            
            # Check sync_logs table has required columns
            sync_columns = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'sync_logs'
                ORDER BY ordinal_position
            """)).fetchall()
            
            print(f"✅ sync_logs table has {len(sync_columns)} columns")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate_schema()
    exit(0 if success else 1)
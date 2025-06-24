#!/usr/bin/env python3
"""
Clear sample data and trigger real government data sync
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.opportunity import Opportunity, DataSource, SyncLog
from src.services.data_sync_service import DataSyncService

# Load environment variables
load_dotenv()

def clear_sample_data():
    """Clear all sample data from the database"""
    with app.app_context():
        print("🗑️  Clearing sample data...")
        
        # Clear all opportunities
        opportunity_count = Opportunity.query.count()
        Opportunity.query.delete()
        
        # Clear all data sources
        source_count = DataSource.query.count()
        DataSource.query.delete()
        
        # Clear all sync logs
        log_count = SyncLog.query.count()
        SyncLog.query.delete()
        
        db.session.commit()
        
        print(f"✅ Cleared {opportunity_count} opportunities")
        print(f"✅ Cleared {source_count} data sources")
        print(f"✅ Cleared {log_count} sync logs")

def trigger_real_sync():
    """Trigger real government data sync"""
    with app.app_context():
        print("🔄 Triggering real government data sync...")
        
        try:
            sync_service = DataSyncService()
            
            # Check available API keys
            sam_key = os.getenv('SAM_API_KEY')
            perplexity_key = os.getenv('PERPLEXITY_API_KEY')
            firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
            
            print(f"🔑 SAM API Key: {'✅ Set' if sam_key else '❌ Missing'}")
            print(f"🔑 Perplexity API Key: {'✅ Set' if perplexity_key else '❌ Missing'}")
            print(f"🔑 Firecrawl API Key: {'✅ Set' if firecrawl_key else '❌ Missing'}")
            
            # Sync all sources
            results = sync_service.sync_all_sources()
            
            print("\n📊 Sync Results:")
            print(f"  Total processed: {results['total_processed']}")
            print(f"  Total added: {results['total_added']}")
            print(f"  Total updated: {results['total_updated']}")
            print(f"  Errors: {len(results['errors'])}")
            
            if results['errors']:
                print("\n❌ Errors:")
                for error in results['errors']:
                    print(f"  - {error}")
            
            # Show results by source
            print("\n📈 Results by Source:")
            for source_name, result in results['sources'].items():
                status = result.get('status', 'unknown')
                processed = result.get('processed', 0)
                added = result.get('added', 0)
                updated = result.get('updated', 0)
                print(f"  {source_name}: {status} - {processed} processed, {added} added, {updated} updated")
            
            return results
            
        except Exception as e:
            print(f"❌ Sync failed: {str(e)}")
            return None

def check_current_data():
    """Check current data in the database"""
    with app.app_context():
        print("\n📊 Current Database Status:")
        
        opportunity_count = Opportunity.query.count()
        source_count = DataSource.query.count()
        log_count = SyncLog.query.count()
        
        print(f"  Opportunities: {opportunity_count}")
        print(f"  Data Sources: {source_count}")
        print(f"  Sync Logs: {log_count}")
        
        if opportunity_count > 0:
            print("\n📋 Recent Opportunities:")
            recent_opps = Opportunity.query.order_by(Opportunity.created_at.desc()).limit(5).all()
            for opp in recent_opps:
                print(f"  - {opp.title[:50]}... (${opp.estimated_value:,.0f})")
        
        if log_count > 0:
            print("\n🔄 Recent Sync Activity:")
            recent_logs = SyncLog.query.order_by(SyncLog.sync_start.desc()).limit(3).all()
            for log in recent_logs:
                print(f"  - {log.source_name}: {log.status} ({log.records_added} added)")

def main():
    """Main function"""
    print("🚀 ODB Data Reset and Real Sync")
    print("=" * 50)
    
    # Check current data
    check_current_data()
    
    # Ask for confirmation
    response = input("\n❓ Do you want to clear sample data and sync real government data? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return
    
    # Clear sample data
    clear_sample_data()
    
    # Trigger real sync
    results = trigger_real_sync()
    
    # Check results
    if results:
        print("\n✅ Sync completed!")
        check_current_data()
    else:
        print("\n❌ Sync failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 
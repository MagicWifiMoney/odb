#!/usr/bin/env python3
"""
Simple one-time data sync script
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

def run_simple_sync():
    """Run a simple data sync without complex scheduling"""
    print("🔄 Running Simple Data Sync")
    print("=" * 40)
    
    try:
        # Import Flask app and create application context
        from src.main import app
        
        with app.app_context():
            # Import after environment is loaded
            from src.services.data_sync_service import DataSyncService
            
            # Initialize service
            sync_service = DataSyncService()
            
            print("📡 Starting government API sync...")
            
            # Sync from all government APIs
            result = sync_service.sync_all_sources(include_scraping=False)
            
            print(f"\n📊 Sync Results:")
            print(f"   Total processed: {result.get('total_processed', 0)}")
            print(f"   Total added: {result.get('total_added', 0)}")
            print(f"   Total updated: {result.get('total_updated', 0)}")
            
            # Show results by source
            for source_name, source_result in result.get('sources', {}).items():
                print(f"   {source_name}: {source_result.get('added', 0)} added, {source_result.get('updated', 0)} updated")
            
            if result.get('errors'):
                print(f"\n⚠️  Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    print(f"   - {error}")
            
            print("\n✅ Simple sync complete!")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_sync()
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
        # Import after environment is loaded
        from src.services.data_sync_service import DataSyncService
        
        # Initialize service
        sync_service = DataSyncService()
        
        print("📡 Starting government API sync...")
        
        # Sync from government APIs
        sam_result = sync_service.sync_sam_opportunities()
        print(f"   SAM.gov: {sam_result.get('message', 'Unknown result')}")
        
        grants_result = sync_service.sync_grants_opportunities()
        print(f"   Grants.gov: {grants_result.get('message', 'Unknown result')}")
        
        spending_result = sync_service.sync_usa_spending()
        print(f"   USASpending.gov: {spending_result.get('message', 'Unknown result')}")
        
        print("\n✅ Simple sync complete!")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_sync()
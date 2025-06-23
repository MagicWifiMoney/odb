#!/usr/bin/env python3
"""
Test data synchronization service
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Load environment
load_dotenv(os.path.join(backend_dir, '.env'))

# Initialize Flask app context
from src.main import create_app
app = create_app()

def test_data_sync():
    """Test data synchronization"""
    with app.app_context():
        print("📊 Testing Data Synchronization...")
        
        from src.services.data_sync_service import DataSyncService
        from src.models.opportunity import db, Opportunity
        
        # Check current opportunities count
        current_count = db.session.query(Opportunity).count()
        print(f"📈 Current opportunities in database: {current_count}")
        
        # Initialize sync service
        sync_service = DataSyncService()
        
        # Test individual sources
        print("\n🔄 Testing individual API sources...")
        
        try:
            # Test Grants.gov (no API key required)
            print("\n1. Testing Grants.gov sync...")
            if 'grants_gov' in sync_service.clients:
                result = sync_service.sync_source('grants_gov', sync_service.clients['grants_gov'])
                print(f"✓ Grants.gov sync result: {result}")
            else:
                print("⚠ Grants.gov client not available")
                
        except Exception as e:
            print(f"✗ Grants.gov sync failed: {e}")
        
        try:
            # Test USASpending.gov (no API key required)
            print("\n2. Testing USASpending.gov sync...")
            if 'usa_spending' in sync_service.clients:
                result = sync_service.sync_source('usa_spending', sync_service.clients['usa_spending'])
                print(f"✓ USASpending.gov sync result: {result}")
            else:
                print("⚠ USASpending.gov client not available")
                
        except Exception as e:
            print(f"✗ USASpending.gov sync failed: {e}")
        
        try:
            # Test SAM.gov (requires API key)
            print("\n3. Testing SAM.gov sync...")
            if 'sam_gov' in sync_service.clients:
                result = sync_service.sync_source('sam_gov', sync_service.clients['sam_gov'])
                print(f"✓ SAM.gov sync result: {result}")
            else:
                print("⚠ SAM.gov client not available")
                
        except Exception as e:
            print(f"✗ SAM.gov sync failed: {e}")
        
        # Check final count
        final_count = db.session.query(Opportunity).count()
        print(f"\n📊 Final opportunities count: {final_count}")
        print(f"📈 New opportunities added: {final_count - current_count}")
        
        # Show sample opportunities
        if final_count > 0:
            print("\n🔍 Sample opportunities:")
            sample_opps = db.session.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(3).all()
            
            for i, opp in enumerate(sample_opps, 1):
                print(f"\n{i}. {opp.title[:60]}...")
                print(f"   Agency: {opp.agency_name or 'Unknown'}")
                print(f"   Source: {opp.source_name}")
                print(f"   Value: ${opp.estimated_value or 0:,.2f}")
                print(f"   Score: {opp.total_score}/100")
                
        print("\n🎉 Data sync test completed!")

if __name__ == "__main__":
    test_data_sync()
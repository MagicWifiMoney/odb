#!/usr/bin/env python3
"""
Test API connections and fetch real data
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Load environment
load_dotenv(os.path.join(backend_dir, '.env'))

from src.services.api_clients import APIClientFactory

def test_api_connections():
    """Test connections to all configured APIs"""
    print("🔗 Testing API Connections...")
    
    # Test SAM.gov API
    print("\n1. Testing SAM.gov API...")
    try:
        sam_client = APIClientFactory.create_sam_gov_client()
        
        # Test with limited params to avoid rate limits
        test_params = {
            "limit": 5,
            "offset": 0,
            "ptype": "o"  # Solicitation type
        }
        
        result = sam_client.fetch_opportunities(test_params)
        opportunities = sam_client.transform_data(result)
        
        print(f"✓ SAM.gov connected successfully")
        print(f"  📊 Found {len(opportunities)} opportunities")
        
        if opportunities:
            first_opp = opportunities[0]
            print(f"  🔍 Sample: {first_opp.get('title', 'No title')[:50]}...")
            print(f"  🏢 Agency: {first_opp.get('agency_name', 'Unknown')}")
            print(f"  💰 Value: ${first_opp.get('estimated_value', 0):,.2f}")
            
    except Exception as e:
        print(f"✗ SAM.gov connection failed: {e}")
    
    # Test Grants.gov API
    print("\n2. Testing Grants.gov API...")
    try:
        grants_client = APIClientFactory.create_grants_gov_client()
        
        test_payload = {
            "rows": 5,
            "offset": 0,
            "oppStatuses": ["posted"]
        }
        
        result = grants_client.fetch_opportunities(test_payload)
        opportunities = grants_client.transform_data(result)
        
        print(f"✓ Grants.gov connected successfully")
        print(f"  📊 Found {len(opportunities)} grant opportunities")
        
        if opportunities:
            first_grant = opportunities[0]
            print(f"  🔍 Sample: {first_grant.get('title', 'No title')[:50]}...")
            print(f"  🏢 Agency: {first_grant.get('agency_name', 'Unknown')}")
            print(f"  💰 Value: ${first_grant.get('estimated_value', 0):,.2f}")
            
    except Exception as e:
        print(f"✗ Grants.gov connection failed: {e}")
    
    # Test USASpending.gov API
    print("\n3. Testing USASpending.gov API...")
    try:
        spending_client = APIClientFactory.create_usa_spending_client()
        
        test_payload = {
            "limit": 5
        }
        
        result = spending_client.fetch_recent_awards(test_payload)
        awards = spending_client.transform_award_data(result)
        
        print(f"✓ USASpending.gov connected successfully")
        print(f"  📊 Found {len(awards)} recent awards")
        
        if awards:
            first_award = awards[0]
            print(f"  🔍 Sample: {first_award.get('title', 'No title')[:50]}...")
            print(f"  🏢 Agency: {first_award.get('agency_name', 'Unknown')}")
            print(f"  💰 Value: ${first_award.get('estimated_value', 0):,.2f}")
            
    except Exception as e:
        print(f"✗ USASpending.gov connection failed: {e}")
    
    print("\n🎉 API connection tests completed!")

if __name__ == "__main__":
    test_api_connections()
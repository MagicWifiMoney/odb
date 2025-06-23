#!/usr/bin/env python3
"""
Simple deployment validation script for Railway
Run this after deployment to test your API endpoints
"""

import requests
import json
import sys

def test_railway_deployment(base_url):
    """Test Railway deployment endpoints"""
    
    print(f"🚀 Testing Railway deployment at: {base_url}")
    print("-" * 50)
    
    # Test endpoints
    endpoints = [
        ("/api/health-simple", "Simple health check"),
        ("/api/health", "Full health check"),
        ("/api", "API info"),
        ("/api/opportunities", "Opportunities endpoint")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Testing {description}: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                results.append(True)
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Connection error - {str(e)}")
            results.append(False)
        
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"DEPLOYMENT TEST RESULTS: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All tests passed! Your Railway deployment is working correctly.")
        return True
    else:
        print("⚠️  Some endpoints failed. Check Railway logs for details.")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_deployment.py <railway_url>")
        print("Example: python test_deployment.py https://web-production-1234.up.railway.app")
        sys.exit(1)
    
    railway_url = sys.argv[1].rstrip('/')
    success = test_railway_deployment(railway_url)
    sys.exit(0 if success else 1) 
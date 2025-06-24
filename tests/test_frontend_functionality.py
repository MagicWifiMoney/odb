#!/usr/bin/env python3
"""
Automated testing of frontend functionality and API integration
"""
import requests
import json
import time
from urllib.parse import urljoin

# Configuration
FRONTEND_URL = "https://frontend-73o5kxpn6-jacobs-projects-cf4c7bdb.vercel.app"
BACKEND_URL = "https://backend-bn42qj3a9-jacobs-projects-cf4c7bdb.vercel.app/api"

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    print("🌐 Testing frontend accessibility...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility failed: {e}")
        return False

def test_api_endpoints():
    """Test all API endpoints that frontend uses"""
    print("\n🔗 Testing API endpoints...")
    
    endpoints = [
        '/health',
        '/opportunities', 
        '/opportunities/stats',
        '/sync/status'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = urljoin(BACKEND_URL, endpoint)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    'status': 'success',
                    'data_size': len(str(data))
                }
                print(f"✅ {endpoint} - Working")
                
                # Specific checks
                if endpoint == '/opportunities':
                    opp_count = len(data.get('opportunities', []))
                    print(f"   📊 {opp_count} opportunities loaded")
                elif endpoint == '/opportunities/stats':
                    total_value = data.get('total_value', 0)
                    print(f"   💰 ${total_value:,.0f} total value")
                    
            else:
                results[endpoint] = {'status': 'failed', 'code': response.status_code}
                print(f"❌ {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            results[endpoint] = {'status': 'error', 'error': str(e)}
            print(f"❌ {endpoint} - Error: {e}")
    
    return results

def test_data_quality():
    """Test the quality and validity of API data"""
    print("\n📊 Testing data quality...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/opportunities", timeout=10)
        data = response.json()
        opportunities = data.get('opportunities', [])
        
        if not opportunities:
            print("❌ No opportunities found")
            return False
        
        print(f"✅ Found {len(opportunities)} opportunities")
        
        # Check data quality
        real_data_count = 0
        total_value = 0
        
        for opp in opportunities:
            # Check required fields
            if not opp.get('title'):
                print(f"⚠️ Missing title: {opp.get('id')}")
            if not opp.get('source_name'):
                print(f"⚠️ Missing source: {opp.get('id')}")
            
            # Check if it's real data
            if (opp.get('source_name') == 'USASpending.gov' and 
                opp.get('estimated_value', 0) > 1000000):
                real_data_count += 1
                total_value += opp.get('estimated_value', 0)
        
        print(f"✅ Real data: {real_data_count}/{len(opportunities)} opportunities")
        print(f"✅ Total value: ${total_value:,.2f}")
        
        if real_data_count == len(opportunities):
            print("🎉 All data is real (no sample data)")
            return True
        else:
            print("⚠️ Some sample data still present")
            return False
            
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        return False

def test_frontend_pages():
    """Test that frontend pages are accessible"""
    print("\n📱 Testing frontend pages...")
    
    # Since we can't run JavaScript tests, we'll check if pages return valid HTML
    pages = [
        '',  # Dashboard
        '/#/opportunities',
        '/#/search', 
        '/#/sync',
        '/#/settings'
    ]
    
    for page in pages:
        try:
            url = f"{FRONTEND_URL}{page}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 and 'html' in response.headers.get('content-type', ''):
                print(f"✅ {page or 'Dashboard'} - Accessible")
            else:
                print(f"❌ {page or 'Dashboard'} - Issue")
                
        except Exception as e:
            print(f"❌ {page or 'Dashboard'} - Error: {e}")

def test_sync_functionality():
    """Test data sync functionality"""
    print("\n🔄 Testing sync functionality...")
    
    try:
        # Test sync status
        response = requests.get(f"{BACKEND_URL}/sync/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Sync status endpoint working")
            print(f"   📡 {status_data.get('total_sources', 0)} data sources configured")
        
        # Note: We won't trigger actual sync to avoid API rate limits
        print("ℹ️ Sync trigger test skipped (avoiding API rate limits)")
        return True
        
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        return False

def generate_test_report(api_results, data_quality, sync_working):
    """Generate comprehensive test report"""
    print("\n" + "="*50)
    print("🎯 FRONTEND & API TEST REPORT")
    print("="*50)
    
    # API Status
    print("\n🔗 API Endpoints:")
    working_endpoints = sum(1 for result in api_results.values() if result['status'] == 'success')
    total_endpoints = len(api_results)
    print(f"   ✅ {working_endpoints}/{total_endpoints} endpoints working")
    
    for endpoint, result in api_results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_icon} {endpoint}")
    
    # Data Quality
    print(f"\n📊 Data Quality: {'✅ Excellent' if data_quality else '⚠️ Issues Found'}")
    
    # Sync Status
    print(f"🔄 Sync Functionality: {'✅ Working' if sync_working else '❌ Issues'}")
    
    # Overall Status
    overall_score = (
        (working_endpoints / total_endpoints) * 0.6 +
        (1 if data_quality else 0) * 0.3 +
        (1 if sync_working else 0) * 0.1
    )
    
    if overall_score >= 0.9:
        status = "🎉 EXCELLENT - Ready for production!"
    elif overall_score >= 0.7:
        status = "✅ GOOD - Minor issues to address"
    else:
        status = "⚠️ NEEDS WORK - Major issues found"
    
    print(f"\n🎯 Overall Status: {status}")
    print(f"📈 Score: {overall_score*100:.1f}%")
    
    return overall_score

if __name__ == "__main__":
    print("🔍 AUTOMATED FRONTEND & API TESTING")
    print("=" * 40)
    
    # Run all tests
    frontend_accessible = test_frontend_accessibility()
    
    if frontend_accessible:
        api_results = test_api_endpoints()
        data_quality = test_data_quality()
        test_frontend_pages()
        sync_working = test_sync_functionality()
        
        # Generate report
        score = generate_test_report(api_results, data_quality, sync_working)
        
        print(f"\n💡 Next Steps:")
        if score >= 0.9:
            print("   🎉 System is working perfectly!")
            print("   🚀 Ready for production use")
        else:
            print("   🔧 Check any failed endpoints above")
            print("   🧹 Ensure all sample data is removed")
            print("   📱 Test frontend manually for UI issues")
    
    else:
        print("\n❌ Frontend not accessible - check deployment")
        print("💡 Try redeploying the frontend or check Vercel logs")
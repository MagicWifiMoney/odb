#!/usr/bin/env python3
"""
Test Firecrawl API Connection
Simple test to verify if Firecrawl API key is working
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_firecrawl_connection():
    """Test basic Firecrawl API connection"""
    print("🔥 TESTING FIRECRAWL API CONNECTION")
    print("=" * 40)
    
    # Get API key
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Test endpoint
    base_url = "https://api.firecrawl.dev/v0"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"🌐 Testing endpoint: {base_url}")
    
    return api_key, headers, base_url

def test_simple_scrape():
    """Test simple webpage scraping"""
    api_key, headers, base_url = test_firecrawl_connection()
    
    if not api_key:
        return
    
    print("\n🧪 TESTING SIMPLE WEBPAGE SCRAPE")
    print("=" * 35)
    
    # Test with a simple government page
    test_url = "https://www.gsa.gov/"
    
    payload = {
        'url': test_url,
        'formats': ['markdown'],
        'onlyMainContent': True
    }
    
    print(f"📄 Testing URL: {test_url}")
    print("📤 Sending request...")
    
    try:
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Firecrawl is working")
            print(f"   📝 Response keys: {list(data.keys())}")
            
            if 'data' in data and 'markdown' in data['data']:
                content_length = len(data['data']['markdown'])
                print(f"   📊 Content length: {content_length} characters")
                print(f"   📖 Sample content: {data['data']['markdown'][:200]}...")
            
            return True
            
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"   📄 Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - Request took too long")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_structured_extraction():
    """Test structured data extraction"""
    api_key, headers, base_url = test_firecrawl_connection()
    
    if not api_key:
        return
    
    print("\n🏗️ TESTING STRUCTURED EXTRACTION")
    print("=" * 35)
    
    # Test with GSA page and extract specific information
    test_url = "https://www.gsa.gov/buy-through-us"
    
    extract_schema = {
        "type": "object",
        "properties": {
            "page_title": {"type": "string"},
            "main_sections": {
                "type": "array",
                "items": {"type": "string"}
            },
            "links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            }
        }
    }
    
    payload = {
        'url': test_url,
        'formats': ['extract'],
        'extract': {
            'schema': extract_schema
        }
    }
    
    print(f"📄 Testing URL: {test_url}")
    print("🔧 Using extraction schema...")
    
    try:
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Structured extraction working")
            
            if 'data' in data and 'extract' in data['data']:
                extracted = data['data']['extract']
                print(f"   📊 Extracted data: {json.dumps(extracted, indent=2)[:300]}...")
            
            return True
            
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"   📄 Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_government_site():
    """Test scraping a government contracting page"""
    api_key, headers, base_url = test_firecrawl_connection()
    
    if not api_key:
        return
    
    print("\n🏛️ TESTING GOVERNMENT CONTRACTING SITE")
    print("=" * 40)
    
    # Test with a government contracting page
    test_url = "https://sam.gov/content/opportunities"
    
    payload = {
        'url': test_url,
        'formats': ['markdown'],
        'onlyMainContent': True,
        'waitFor': 3000  # Wait for dynamic content
    }
    
    print(f"📄 Testing URL: {test_url}")
    print("⏳ Waiting for dynamic content...")
    
    try:
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Government site scraping working")
            
            if 'data' in data and 'markdown' in data['data']:
                content = data['data']['markdown']
                print(f"   📊 Content length: {len(content)} characters")
                
                # Look for opportunity-related keywords
                keywords = ['opportunity', 'contract', 'solicitation', 'rfp', 'award']
                found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
                print(f"   🔍 Found keywords: {found_keywords}")
                
                # Show sample content
                print(f"   📖 Sample content: {content[:300]}...")
            
            return True
            
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"   📄 Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all Firecrawl tests"""
    print("🚀 FIRECRAWL API COMPREHENSIVE TEST")
    print("=" * 50)
    
    results = {
        'connection': False,
        'simple_scrape': False,
        'structured_extraction': False,
        'government_site': False
    }
    
    # Test 1: Simple scrape
    results['simple_scrape'] = test_simple_scrape()
    
    # Test 2: Structured extraction
    if results['simple_scrape']:
        results['structured_extraction'] = test_structured_extraction()
    
    # Test 3: Government site
    if results['simple_scrape']:
        results['government_site'] = test_government_site()
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 25)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 Firecrawl is fully functional!")
        print("💡 Ready to implement enhanced government scraping")
    elif passed_tests > 0:
        print("⚠️  Firecrawl partially working - investigate failed tests")
    else:
        print("❌ Firecrawl not working - check API key or account status")
    
    return results

if __name__ == "__main__":
    main()
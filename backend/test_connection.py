#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing Supabase connection...")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')[:30]}...")
print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:30]}...")

try:
    from src.config.supabase import get_supabase_admin_client

    client = get_supabase_admin_client()
    response = client.table('data_sources').select('*').execute()

    print(f"✅ Supabase connected! Found {len(response.data)} data sources")
    for source in response.data:
        print(f"  - {source['name']} ({source['type']})")

    # Test opportunities table
    opp_response = client.table('opportunities').select('id').limit(1).execute()
    print(f"✅ Opportunities table ready (currently {len(opp_response.data)} records)")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()

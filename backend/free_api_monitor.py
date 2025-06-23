#!/usr/bin/env python3
"""
Free API Monitoring System - Only uses free government APIs
Respects rate limits and focuses on cost-free data sources
"""

import os
import sys
import time
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

class FreeAPIMonitor:
    """Monitoring system using only free government APIs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_sync_times = {}
        
        # Initialize Flask app context
        self.app = None
        self._init_flask_app()
        
        # Rate limit settings for free APIs
        self.rate_limits = {
            'sam_gov': {
                'requests_per_hour': 500,  # Free tier limit
                'requests_per_minute': 5,  # Conservative limit
                'min_interval': 12  # seconds between requests
            },
            'grants_gov': {
                'requests_per_hour': 1000,
                'requests_per_minute': 10,
                'min_interval': 6
            },
            'usa_spending': {
                'requests_per_hour': 1000,
                'requests_per_minute': 10,
                'min_interval': 6
            }
        }
        
        print("🆓 Free API Monitor initialized")
        print("📊 Rate limits configured:")
        for api, limits in self.rate_limits.items():
            print(f"   {api}: {limits['requests_per_hour']}/hour, {limits['requests_per_minute']}/min")
    
    def _init_flask_app(self):
        """Initialize Flask app for database context"""
        try:
            from flask import Flask
            from src.database import db
            
            self.app = Flask(__name__)
            
            # Database configuration
            database_url = os.getenv('DATABASE_URL', 'sqlite:///opportunities.db')
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            self.app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            db.init_app(self.app)
            print("✅ Flask app initialized for database context")
            
        except Exception as e:
            print(f"⚠️ Flask app initialization failed: {e}")
            self.app = None
    
    def can_make_request(self, api_name: str) -> bool:
        """Check if we can make a request without hitting rate limits"""
        if api_name not in self.last_sync_times:
            return True
        
        last_sync = self.last_sync_times[api_name]
        min_interval = self.rate_limits.get(api_name, {}).get('min_interval', 60)
        
        time_since_last = (datetime.now() - last_sync).total_seconds()
        return time_since_last >= min_interval
    
    def record_request(self, api_name: str):
        """Record that we made a request"""
        self.last_sync_times[api_name] = datetime.now()
    
    def sync_sam_opportunities(self) -> dict:
        """Sync from SAM.gov with rate limiting"""
        if not self.can_make_request('sam_gov'):
            return {'status': 'skipped', 'reason': 'rate_limit'}
        
        if not self.app:
            return {'status': 'error', 'error': 'Flask app not initialized'}
            
        try:
            with self.app.app_context():
                from src.services.data_sync_service import DataSyncService
                from src.services.api_clients import APIClientFactory
                
                sync_service = DataSyncService()
                
                # Get SAM.gov client and sync
                try:
                    sam_client = APIClientFactory.create_sam_gov_client()
                    self.record_request('sam_gov')
                    result = sync_service.sync_source('sam_gov', sam_client)
                    
                    print(f"   SAM.gov: Processed {result.get('processed', 0)}, Added {result.get('added', 0)}")
                    return result
                except ValueError as e:
                    print(f"   ⚠️ SAM.gov: API key not configured, skipping")
                    return {'status': 'skipped', 'reason': 'no_api_key'}
            
        except Exception as e:
            print(f"   ❌ SAM.gov error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def sync_grants_opportunities(self) -> dict:
        """Sync from Grants.gov with rate limiting"""
        if not self.can_make_request('grants_gov'):
            return {'status': 'skipped', 'reason': 'rate_limit'}
        
        if not self.app:
            return {'status': 'error', 'error': 'Flask app not initialized'}
            
        try:
            with self.app.app_context():
                from src.services.data_sync_service import DataSyncService
                from src.services.api_clients import APIClientFactory
                
                sync_service = DataSyncService()
                grants_client = APIClientFactory.create_grants_gov_client()
                
                self.record_request('grants_gov')
                result = sync_service.sync_source('grants_gov', grants_client)
                
                print(f"   Grants.gov: Processed {result.get('processed', 0)}, Added {result.get('added', 0)}")
                return result
            
        except Exception as e:
            print(f"   ❌ Grants.gov error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def sync_usa_spending(self) -> dict:
        """Sync from USASpending.gov with rate limiting"""
        if not self.can_make_request('usa_spending'):
            return {'status': 'skipped', 'reason': 'rate_limit'}
        
        if not self.app:
            return {'status': 'error', 'error': 'Flask app not initialized'}
            
        try:
            with self.app.app_context():
                from src.services.data_sync_service import DataSyncService
                from src.services.api_clients import APIClientFactory
                
                sync_service = DataSyncService()
                usa_client = APIClientFactory.create_usa_spending_client()
                
                self.record_request('usa_spending')
                result = sync_service.sync_source('usa_spending', usa_client)
                
                print(f"   USASpending.gov: Processed {result.get('processed', 0)}, Added {result.get('added', 0)}")
                return result
            
        except Exception as e:
            print(f"   ❌ USASpending.gov error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def run_hourly_sync(self):
        """Run every hour - light sync with one API"""
        print(f"\n⏰ Hourly Free API Sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Rotate between APIs each hour to spread load
        hour = datetime.now().hour
        
        if hour % 3 == 0:
            print("📡 Syncing SAM.gov (hourly)")
            self.sync_sam_opportunities()
        elif hour % 3 == 1:
            print("📡 Syncing Grants.gov (hourly)")
            self.sync_grants_opportunities()
        else:
            print("📡 Syncing USASpending.gov (hourly)")
            self.sync_usa_spending()
    
    def run_daily_sync(self):
        """Run daily - comprehensive sync from all free APIs"""
        print(f"\n📅 Daily Free API Sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        results = {}
        
        # Sync all APIs with delays to respect rate limits
        print("📡 Running comprehensive free API sync...")
        
        # SAM.gov
        print("   🏛️ SAM.gov...")
        results['sam'] = self.sync_sam_opportunities()
        time.sleep(15)  # 15 second delay
        
        # Grants.gov  
        print("   💰 Grants.gov...")
        results['grants'] = self.sync_grants_opportunities()
        time.sleep(10)  # 10 second delay
        
        # USASpending.gov
        print("   💵 USASpending.gov...")
        results['usa_spending'] = self.sync_usa_spending()
        
        # Log results
        try:
            from src.config.supabase import get_supabase_admin_client
            supabase = get_supabase_admin_client()
            
            log_data = {
                'source_name': 'FreeAPIMonitor',
                'sync_type': 'daily_comprehensive',
                'records_processed': sum(r.get('processed', 0) for r in results.values() if isinstance(r, dict)),
                'records_added': sum(r.get('added', 0) for r in results.values() if isinstance(r, dict)),
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            supabase.table('sync_logs').insert(log_data).execute()
            print("✅ Daily sync logged to database")
            
        except Exception as e:
            print(f"⚠️ Failed to log daily sync: {e}")
        
        print("\n✅ Daily comprehensive sync complete!")
    
    def run_weekly_analysis(self):
        """Run weekly - just analyze existing data (no API calls)"""
        print(f"\n📊 Weekly Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        try:
            from src.config.supabase import get_supabase_admin_client
            supabase = get_supabase_admin_client()
            
            # Get opportunity counts by source
            total_count = supabase.table('opportunities').select('*', count='exact').execute()
            
            # Get recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_count = supabase.table('opportunities')\
                .select('*', count='exact')\
                .gte('created_at', week_ago)\
                .execute()
            
            print(f"📈 Database Statistics:")
            print(f"   Total Opportunities: {total_count.count}")
            print(f"   Added This Week: {recent_count.count}")
            
            # Log weekly analysis
            log_data = {
                'source_name': 'FreeAPIMonitor',
                'sync_type': 'weekly_analysis',
                'records_processed': total_count.count,
                'records_added': recent_count.count,
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            supabase.table('sync_logs').insert(log_data).execute()
            print("✅ Weekly analysis complete and logged")
            
        except Exception as e:
            print(f"❌ Weekly analysis failed: {e}")

def main():
    """Start the free API monitoring system"""
    print("🆓 Starting Free API Monitoring System")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💰 Using only FREE government APIs")
    print("🚦 Rate limits configured to stay within free tiers")
    
    try:
        # Initialize monitor
        monitor = FreeAPIMonitor()
        
        # Setup conservative schedule
        schedule.every().hour.do(monitor.run_hourly_sync)
        schedule.every().day.at("09:00").do(monitor.run_daily_sync)
        schedule.every().monday.at("08:00").do(monitor.run_weekly_analysis)
        
        print("\n✅ Free API monitoring schedule configured:")
        print("   ⏰ Every hour: Single API rotation")
        print("   📅 Daily 9AM: All free APIs (with delays)")
        print("   📊 Weekly Monday 8AM: Data analysis only")
        print("\n🔄 Free API monitoring is now running...")
        print("   Press Ctrl+C to stop")
        
        # Run initial light sync
        print("\n🚀 Running initial sync...")
        monitor.run_hourly_sync()
        
        # Keep running scheduled tasks
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Free API monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Free API monitoring error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
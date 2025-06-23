#!/usr/bin/env python3
"""
Check the status of the free API monitoring system
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

def check_monitoring_status():
    """Check the current status of monitoring"""
    print("📊 Free API Monitoring System Status")
    print("=" * 50)
    print(f"⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Check if monitoring process is running
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'free_api_monitor.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Monitoring process is running (PID: {', '.join(pids)})")
        else:
            print("❌ Monitoring process is not running")
        
        # Check recent database activity
        from src.config.supabase import get_supabase_admin_client
        supabase = get_supabase_admin_client()
        
        # Get recent sync logs
        recent_logs = supabase.table('sync_logs')\
            .select('*')\
            .eq('source_name', 'FreeAPIMonitor')\
            .order('completed_at', desc=True)\
            .limit(5)\
            .execute()
        
        print(f"\n📋 Recent Monitoring Activity:")
        if recent_logs.data:
            for log in recent_logs.data:
                sync_time = log.get('completed_at', 'Unknown')
                sync_type = log.get('sync_type', 'Unknown')
                processed = log.get('records_processed', 0)
                added = log.get('records_added', 0)
                print(f"   {sync_time}: {sync_type} - Processed: {processed}, Added: {added}")
        else:
            print("   No recent monitoring activity found")
        
        # Get opportunity count
        total_count = supabase.table('opportunities').select('*', count='exact').execute()
        print(f"\n📈 Total Opportunities in Database: {total_count.count}")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

def show_commands():
    """Show available commands"""
    print("\n🔧 Available Commands:")
    print("   Start monitoring:      python3 free_api_monitor.py &")
    print("   Check status:          python3 check_monitoring.py")
    print("   Stop monitoring:       pkill -f free_api_monitor.py")
    print("   Manual sync:           python3 simple_sync.py")
    print("   AI budget status:      python3 ai_emergency_intel.py status")
    print("   Emergency AI query:    python3 ai_emergency_intel.py 'query focus'")
    print("   Test budget tracker:   python3 perplexity_budget_tracker.py")

if __name__ == "__main__":
    check_monitoring_status()
    show_commands()
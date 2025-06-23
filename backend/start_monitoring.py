#!/usr/bin/env python3
"""
Simple script to start the automated monitoring system as a background service
"""

import os
import sys
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))
from automated_monitoring import AutomatedContractMonitor

def main():
    """Start the automated monitoring system"""
    print("🚀 Starting Automated Contract Monitoring Service")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize monitor
        monitor = AutomatedContractMonitor()
        
        # Setup schedule
        schedule.every().hour.do(monitor.run_hourly_monitoring)
        schedule.every().day.at("09:00").do(monitor.run_daily_monitoring)
        schedule.every().monday.at("08:00").do(monitor.run_weekly_intelligence)
        
        print("\n✅ Monitoring schedule configured:")
        print("   ⏰ Hourly: Urgent announcements check")
        print("   📅 Daily 9AM: Comprehensive discovery")
        print("   📊 Weekly Monday 8AM: Market intelligence")
        print("\n🔄 Monitoring system is now running...")
        print("   Press Ctrl+C to stop")
        
        # Run initial discovery
        print("\n🚀 Running initial discovery session...")
        monitor.run_manual_discovery()
        
        # Keep running scheduled tasks
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring system stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring system error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
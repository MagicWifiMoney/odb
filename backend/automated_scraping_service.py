#!/usr/bin/env python3
"""
Automated Scraping Service for Continuous Government RFP Data Updates
Runs on schedule to keep the database fresh with new real opportunities
"""

import os
import sys
import time
import schedule
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from enhanced_real_data_scraper import EnhancedRealDataScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/scraping.log'),
        logging.StreamHandler()
    ]
)

class AutomatedScrapingService:
    """Service for automated, scheduled scraping of government opportunities"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scraper = EnhancedRealDataScraper(db_path)
        self.logger = logging.getLogger(__name__)
        
    def run_scheduled_scrape(self) -> Dict[str, Any]:
        """Run a scheduled scrape session"""
        self.logger.info("🤖 Starting automated scraping session...")
        
        try:
            # Run the enhanced scraper
            results = self.scraper.run_full_scrape()
            
            # Log results
            self.logger.info(f"✅ Automated scrape completed:")
            self.logger.info(f"   • SAM.gov: {results['sam_gov']} new opportunities")
            self.logger.info(f"   • Grants.gov: {results['grants_gov']} new opportunities") 
            self.logger.info(f"   • State Portals: {results['state_portals']} new opportunities")
            self.logger.info(f"   • Total New: {results['total_new']} opportunities")
            
            if results['errors']:
                self.logger.warning(f"   ⚠️  Encountered {len(results['errors'])} errors")
                for error in results['errors']:
                    self.logger.warning(f"      - {error}")
            
            # Update scraping statistics
            self._update_scrape_stats(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Automated scrape failed: {e}")
            return {'total_new': 0, 'errors': [str(e)]}
    
    def _update_scrape_stats(self, results: Dict[str, Any]):
        """Update scraping statistics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scrape_logs table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    sam_gov_new INTEGER,
                    grants_gov_new INTEGER,
                    state_portals_new INTEGER,
                    total_new INTEGER,
                    errors_count INTEGER,
                    duration_seconds REAL
                )
            """)
            
            # Insert scrape log
            cursor.execute("""
                INSERT INTO scrape_logs (
                    timestamp, sam_gov_new, grants_gov_new, state_portals_new,
                    total_new, errors_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                results.get('sam_gov', 0),
                results.get('grants_gov', 0), 
                results.get('state_portals', 0),
                results.get('total_new', 0),
                len(results.get('errors', []))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to update scrape stats: {e}")
    
    def cleanup_old_opportunities(self, days_old: int = 365):
        """Clean up old closed opportunities"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Delete old opportunities (only closed/awarded ones)
            cursor.execute("""
                DELETE FROM opportunities 
                WHERE created_at < ? 
                AND (
                    due_date < date('now', '-30 days') OR
                    title LIKE '%CLOSED%' OR 
                    title LIKE '%AWARDED%'
                )
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} old opportunities")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old opportunities: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM opportunities")
            total_count = cursor.fetchone()[0]
            
            # By source
            cursor.execute("""
                SELECT source_name, source_type, COUNT(*) 
                FROM opportunities 
                GROUP BY source_name, source_type 
                ORDER BY COUNT(*) DESC
            """)
            source_stats = cursor.fetchall()
            
            # Recent opportunities (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM opportunities 
                WHERE created_at > date('now', '-7 days')
            """)
            recent_count = cursor.fetchone()[0]
            
            # Total estimated value
            cursor.execute("""
                SELECT SUM(estimated_value) FROM opportunities 
                WHERE estimated_value IS NOT NULL
            """)
            total_value = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_opportunities': total_count,
                'recent_opportunities': recent_count,
                'total_estimated_value': total_value,
                'sources': [{'name': name, 'type': type_, 'count': count} 
                           for name, type_, count in source_stats]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}

def start_automated_service():
    """Start the automated scraping service with scheduling"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    service = AutomatedScrapingService(db_path)
    
    print("🤖 AUTOMATED GOVERNMENT RFP SCRAPING SERVICE")
    print("=" * 50)
    
    # Schedule different scraping frequencies
    
    # SAM.gov and state portals - every 6 hours (high frequency for contracts)
    schedule.every(6).hours.do(service.run_scheduled_scrape)
    
    # Cleanup old opportunities - weekly  
    schedule.every().monday.at("02:00").do(service.cleanup_old_opportunities)
    
    # Log database stats - daily
    def log_daily_stats():
        stats = service.get_database_stats()
        service.logger.info("📊 Daily Database Stats:")
        service.logger.info(f"   • Total Opportunities: {stats.get('total_opportunities', 0)}")
        service.logger.info(f"   • Added This Week: {stats.get('recent_opportunities', 0)}")
        service.logger.info(f"   • Total Value: ${stats.get('total_estimated_value', 0):,.0f}")
    
    schedule.every().day.at("09:00").do(log_daily_stats)
    
    print("📅 Scheduled Tasks:")
    print("   • Full scrape every 6 hours")
    print("   • Cleanup old opportunities weekly (Mondays 2:00 AM)")
    print("   • Daily stats logging at 9:00 AM")
    print("\n🚀 Service started! Press Ctrl+C to stop.")
    
    # Run initial stats
    log_daily_stats()
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Automated scraping service stopped.")

def run_immediate_scrape():
    """Run an immediate scrape (for testing/manual runs)"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    service = AutomatedScrapingService(db_path)
    
    print("🚀 Running immediate scrape...")
    results = service.run_scheduled_scrape()
    
    print(f"\n✅ Immediate scrape complete!")
    print(f"Added {results.get('total_new', 0)} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_scrape()
    else:
        start_automated_service()
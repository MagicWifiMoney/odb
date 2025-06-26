#!/usr/bin/env python3
"""
Firecrawl Scraping Orchestrator
Unified system to coordinate multiple specialized scrapers
"""

import os
import sys
import json
import time
import sqlite3
import schedule
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/firecrawl_orchestrator.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

@dataclass
class ScrapingResult:
    """Result from a scraping cycle"""
    scraper_name: str
    success: bool
    opportunities_found: int
    opportunities_saved: int
    duration_seconds: float
    errors: List[str]
    cycle_start: str
    cycle_end: str

class DatabaseManager:
    """Centralized database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure all required tables exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced opportunities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    agency_name TEXT,
                    opportunity_number TEXT,
                    estimated_value REAL,
                    posted_date TEXT,
                    due_date TEXT,
                    source_type TEXT,
                    source_name TEXT,
                    source_url TEXT,
                    location TEXT,
                    contact_info TEXT,
                    keywords TEXT,
                    relevance_score INTEGER,
                    urgency_score INTEGER,
                    value_score INTEGER,
                    competition_score INTEGER,
                    total_score INTEGER,
                    data_source_id INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    industry_category TEXT,
                    source_reliability_score REAL,
                    technical_requirements TEXT,
                    project_scope TEXT,
                    last_scraped_at TEXT
                )
            """)
            
            # Scraping cycles tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_start DATETIME,
                    cycle_end DATETIME,
                    total_scrapers INTEGER,
                    successful_scrapers INTEGER,
                    total_opportunities_found INTEGER,
                    total_opportunities_saved INTEGER,
                    total_duration_seconds REAL,
                    errors_count INTEGER,
                    cycle_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Individual scraper performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER,
                    scraper_name TEXT,
                    success BOOLEAN,
                    opportunities_found INTEGER,
                    opportunities_saved INTEGER,
                    duration_seconds REAL,
                    errors_count INTEGER,
                    error_details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cycle_id) REFERENCES scraping_cycles (id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to ensure database tables: {e}")
    
    def record_cycle_start(self, cycle_type: str = "automated") -> int:
        """Record the start of a scraping cycle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO scraping_cycles (cycle_start, cycle_type)
                VALUES (?, ?)
            """, (now, cycle_type))
            
            cycle_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return cycle_id
            
        except Exception as e:
            self.logger.error(f"Failed to record cycle start: {e}")
            return 0
    
    def record_cycle_completion(self, cycle_id: int, results: List[ScrapingResult]):
        """Record the completion of a scraping cycle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate aggregated stats
            total_found = sum(r.opportunities_found for r in results)
            total_saved = sum(r.opportunities_saved for r in results)
            total_duration = sum(r.duration_seconds for r in results)
            successful_scrapers = sum(1 for r in results if r.success)
            total_errors = sum(len(r.errors) for r in results)
            
            now = datetime.now().isoformat()
            
            # Update cycle record
            cursor.execute("""
                UPDATE scraping_cycles SET
                    cycle_end = ?,
                    total_scrapers = ?,
                    successful_scrapers = ?,
                    total_opportunities_found = ?,
                    total_opportunities_saved = ?,
                    total_duration_seconds = ?,
                    errors_count = ?
                WHERE id = ?
            """, (now, len(results), successful_scrapers, total_found, 
                  total_saved, total_duration, total_errors, cycle_id))
            
            # Record individual scraper performance
            for result in results:
                cursor.execute("""
                    INSERT INTO scraper_performance (
                        cycle_id, scraper_name, success, opportunities_found,
                        opportunities_saved, duration_seconds, errors_count, error_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cycle_id, result.scraper_name, result.success,
                      result.opportunities_found, result.opportunities_saved,
                      result.duration_seconds, len(result.errors),
                      json.dumps(result.errors)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to record cycle completion: {e}")
    
    def get_cycle_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get scraping cycle statistics for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get cycle summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cycles,
                    AVG(successful_scrapers) as avg_successful_scrapers,
                    SUM(total_opportunities_found) as total_found,
                    SUM(total_opportunities_saved) as total_saved,
                    AVG(total_duration_seconds) as avg_duration,
                    SUM(errors_count) as total_errors
                FROM scraping_cycles
                WHERE cycle_start >= ?
            """, (cutoff_date,))
            
            cycle_stats = cursor.fetchone()
            
            # Get scraper performance breakdown
            cursor.execute("""
                SELECT 
                    scraper_name,
                    COUNT(*) as runs,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_runs,
                    SUM(opportunities_found) as total_found,
                    SUM(opportunities_saved) as total_saved,
                    AVG(duration_seconds) as avg_duration
                FROM scraper_performance sp
                JOIN scraping_cycles sc ON sp.cycle_id = sc.id
                WHERE sc.cycle_start >= ?
                GROUP BY scraper_name
            """, (cutoff_date,))
            
            scraper_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'period_days': days,
                'cycle_summary': {
                    'total_cycles': cycle_stats[0] or 0,
                    'avg_successful_scrapers': round(cycle_stats[1] or 0, 2),
                    'total_opportunities_found': cycle_stats[2] or 0,
                    'total_opportunities_saved': cycle_stats[3] or 0,
                    'avg_duration_seconds': round(cycle_stats[4] or 0, 2),
                    'total_errors': cycle_stats[5] or 0
                },
                'scraper_breakdown': [
                    {
                        'name': row[0],
                        'runs': row[1],
                        'successful_runs': row[2],
                        'success_rate': round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0,
                        'total_found': row[3],
                        'total_saved': row[4],
                        'avg_duration': round(row[5], 2)
                    }
                    for row in scraper_stats
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cycle stats: {e}")
            return {}

class FirecrawlOrchestrator:
    """Unified orchestrator for all Firecrawl scrapers"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Scraper configurations
        self.scrapers = {
            'industry': {
                'script': 'firecrawl_industry_scraper.py',
                'name': 'Industry Scraper',
                'description': 'Data Centers + IT Industries',
                'priority': 1
            },
            'rfp': {
                'script': 'firecrawl_rfp_scraper.py',
                'name': 'RFP Platform Scraper',
                'description': 'RFP Platforms & Procurement Portals',
                'priority': 2
            },
            'government': {
                'script': 'firecrawl_government_scraper.py',
                'name': 'Government Portal Scraper',
                'description': 'Government Procurement Portals',
                'priority': 3
            }
        }
        
        # Verify Firecrawl API
        self.api_available = self._check_firecrawl_api()
    
    def _check_firecrawl_api(self) -> bool:
        """Check if Firecrawl API is available"""
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            self.logger.error("FIRECRAWL_API_KEY not found in environment")
            return False
        
        self.logger.info(f"✅ Firecrawl API key configured: {api_key[:20]}...")
        return True
    
    def run_scraper(self, scraper_key: str) -> ScrapingResult:
        """Run a single scraper and return results"""
        scraper_config = self.scrapers[scraper_key]
        script_path = scraper_config['script']
        
        self.logger.info(f"🚀 Running {scraper_config['name']}...")
        
        start_time = datetime.now()
        
        try:
            # Run the scraper with immediate flag
            result = subprocess.run(
                [sys.executable, script_path, 'immediate'],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout per scraper
                cwd=os.path.dirname(__file__)
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.returncode == 0:
                # Parse output for stats
                output = result.stdout
                opportunities_found = self._extract_stat(output, ['Found', 'opportunities'])
                opportunities_saved = self._extract_stat(output, ['Saved', 'new opportunities'])
                
                self.logger.info(f"✅ {scraper_config['name']} completed successfully")
                
                return ScrapingResult(
                    scraper_name=scraper_config['name'],
                    success=True,
                    opportunities_found=opportunities_found,
                    opportunities_saved=opportunities_saved,
                    duration_seconds=duration,
                    errors=[],
                    cycle_start=start_time.isoformat(),
                    cycle_end=end_time.isoformat()
                )
            else:
                error_msg = f"Script failed with return code {result.returncode}: {result.stderr}"
                self.logger.error(f"❌ {scraper_config['name']} failed: {error_msg}")
                
                return ScrapingResult(
                    scraper_name=scraper_config['name'],
                    success=False,
                    opportunities_found=0,
                    opportunities_saved=0,
                    duration_seconds=duration,
                    errors=[error_msg],
                    cycle_start=start_time.isoformat(),
                    cycle_end=end_time.isoformat()
                )
                
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Scraper timed out after {duration:.1f} seconds"
            self.logger.error(f"⏰ {scraper_config['name']} timed out")
            
            return ScrapingResult(
                scraper_name=scraper_config['name'],
                success=False,
                opportunities_found=0,
                opportunities_saved=0,
                duration_seconds=duration,
                errors=[error_msg],
                cycle_start=start_time.isoformat(),
                cycle_end=datetime.now().isoformat()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Unexpected error: {e}"
            self.logger.error(f"❌ {scraper_config['name']} failed: {error_msg}")
            
            return ScrapingResult(
                scraper_name=scraper_config['name'],
                success=False,
                opportunities_found=0,
                opportunities_saved=0,
                duration_seconds=duration,
                errors=[error_msg],
                cycle_start=start_time.isoformat(),
                cycle_end=datetime.now().isoformat()
            )
    
    def _extract_stat(self, output: str, keywords: List[str]) -> int:
        """Extract numeric stats from scraper output"""
        try:
            lines = output.split('\n')
            for line in lines:
                if all(keyword.lower() in line.lower() for keyword in keywords):
                    # Extract number from line
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        return int(numbers[0])
            return 0
        except:
            return 0
    
    def run_parallel_cycle(self) -> List[ScrapingResult]:
        """Run all scrapers in parallel"""
        if not self.api_available:
            self.logger.error("❌ Firecrawl API not available - skipping cycle")
            return []
        
        self.logger.info("🚀 Starting Parallel Firecrawl Scraping Cycle")
        self.logger.info("=" * 55)
        
        cycle_start = datetime.now()
        cycle_id = self.db_manager.record_cycle_start("parallel")
        
        results = []
        
        # Run scrapers in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all scraper tasks
            future_to_scraper = {
                executor.submit(self.run_scraper, scraper_key): scraper_key
                for scraper_key in self.scrapers.keys()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_scraper):
                scraper_key = future_to_scraper[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_msg = f"Failed to get result for {scraper_key}: {e}"
                    self.logger.error(error_msg)
                    
                    # Create error result
                    error_result = ScrapingResult(
                        scraper_name=self.scrapers[scraper_key]['name'],
                        success=False,
                        opportunities_found=0,
                        opportunities_saved=0,
                        duration_seconds=0,
                        errors=[error_msg],
                        cycle_start=cycle_start.isoformat(),
                        cycle_end=datetime.now().isoformat()
                    )
                    results.append(error_result)
        
        # Record cycle completion
        self.db_manager.record_cycle_completion(cycle_id, results)
        
        # Print summary
        cycle_end = datetime.now()
        total_duration = (cycle_end - cycle_start).total_seconds()
        total_found = sum(r.opportunities_found for r in results)
        total_saved = sum(r.opportunities_saved for r in results)
        successful_scrapers = sum(1 for r in results if r.success)
        
        self.logger.info(f"\n📊 PARALLEL SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Total Duration: {total_duration:.1f} seconds")
        self.logger.info(f"   ✅ Successful Scrapers: {successful_scrapers}/{len(results)}")
        self.logger.info(f"   🔍 Total Opportunities Found: {total_found}")
        self.logger.info(f"   💾 Total Opportunities Saved: {total_saved}")
        
        for result in results:
            status = "✅" if result.success else "❌"
            self.logger.info(f"   {status} {result.scraper_name}: {result.opportunities_saved} saved ({result.duration_seconds:.1f}s)")
        
        return results
    
    def run_sequential_cycle(self) -> List[ScrapingResult]:
        """Run scrapers sequentially (safer for rate limiting)"""
        if not self.api_available:
            self.logger.error("❌ Firecrawl API not available - skipping cycle")
            return []
        
        self.logger.info("🚀 Starting Sequential Firecrawl Scraping Cycle")
        self.logger.info("=" * 55)
        
        cycle_start = datetime.now()
        cycle_id = self.db_manager.record_cycle_start("sequential")
        
        results = []
        
        # Run scrapers sequentially in priority order
        sorted_scrapers = sorted(
            self.scrapers.items(),
            key=lambda x: x[1]['priority']
        )
        
        for scraper_key, scraper_config in sorted_scrapers:
            result = self.run_scraper(scraper_key)
            results.append(result)
            
            # Brief pause between scrapers
            time.sleep(5)
        
        # Record cycle completion
        self.db_manager.record_cycle_completion(cycle_id, results)
        
        # Print summary
        cycle_end = datetime.now()
        total_duration = (cycle_end - cycle_start).total_seconds()
        total_found = sum(r.opportunities_found for r in results)
        total_saved = sum(r.opportunities_saved for r in results)
        successful_scrapers = sum(1 for r in results if r.success)
        
        self.logger.info(f"\n📊 SEQUENTIAL SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Total Duration: {total_duration:.1f} seconds")
        self.logger.info(f"   ✅ Successful Scrapers: {successful_scrapers}/{len(results)}")
        self.logger.info(f"   🔍 Total Opportunities Found: {total_found}")
        self.logger.info(f"   💾 Total Opportunities Saved: {total_saved}")
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return self.db_manager.get_cycle_stats(days=7)

def start_automated_orchestration():
    """Start automated 2-hour orchestrated scraping cycles"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = FirecrawlOrchestrator(db_path)
    
    print("🤖 FIRECRAWL SCRAPING ORCHESTRATOR")
    print("=" * 50)
    print("🎯 Coordinating: 3 Specialized Scrapers")
    print("📊 Industries: Data Centers + IT + Government + RFPs")
    print("⏰ Frequency: Every 2 hours")
    print("🔄 Mode: Sequential (rate-limit friendly)")
    
    # Schedule every 2 hours
    schedule.every(2).hours.do(orchestrator.run_sequential_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial orchestrated cycle...")
    orchestrator.run_sequential_cycle()
    
    print(f"\n✅ Automated orchestration started!")
    print("🔄 Next cycle in 2 hours")
    print("📝 Logs: /tmp/firecrawl_orchestrator.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated orchestration stopped.")

def run_immediate_parallel_cycle():
    """Run immediate parallel scraping cycle for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = FirecrawlOrchestrator(db_path)
    
    results = orchestrator.run_parallel_cycle()
    
    print(f"\n✅ Immediate parallel cycle complete!")
    total_saved = sum(r.opportunities_saved for r in results)
    print(f"💾 Total saved: {total_saved} new opportunities")
    
    return results

def run_immediate_sequential_cycle():
    """Run immediate sequential scraping cycle for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = FirecrawlOrchestrator(db_path)
    
    results = orchestrator.run_sequential_cycle()
    
    print(f"\n✅ Immediate sequential cycle complete!")
    total_saved = sum(r.opportunities_saved for r in results)
    print(f"💾 Total saved: {total_saved} new opportunities")
    
    return results

def show_performance_report():
    """Show comprehensive performance report"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = FirecrawlOrchestrator(db_path)
    
    report = orchestrator.get_performance_report()
    
    print("📊 FIRECRAWL ORCHESTRATOR PERFORMANCE REPORT")
    print("=" * 50)
    print(f"📅 Period: Last {report.get('period_days', 7)} days")
    print()
    
    summary = report.get('cycle_summary', {})
    print("🔄 CYCLE SUMMARY:")
    print(f"   Total Cycles: {summary.get('total_cycles', 0)}")
    print(f"   Avg Successful Scrapers: {summary.get('avg_successful_scrapers', 0)}")
    print(f"   Total Opportunities Found: {summary.get('total_opportunities_found', 0)}")
    print(f"   Total Opportunities Saved: {summary.get('total_opportunities_saved', 0)}")
    print(f"   Avg Duration: {summary.get('avg_duration_seconds', 0):.1f} seconds")
    print(f"   Total Errors: {summary.get('total_errors', 0)}")
    print()
    
    print("🏭 SCRAPER BREAKDOWN:")
    for scraper in report.get('scraper_breakdown', []):
        print(f"   {scraper['name']}:")
        print(f"     Runs: {scraper['runs']}")
        print(f"     Success Rate: {scraper['success_rate']}%")
        print(f"     Total Found: {scraper['total_found']}")
        print(f"     Total Saved: {scraper['total_saved']}")
        print(f"     Avg Duration: {scraper['avg_duration']:.1f}s")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "parallel":
            run_immediate_parallel_cycle()
        elif sys.argv[1] == "sequential":
            run_immediate_sequential_cycle()
        elif sys.argv[1] == "report":
            show_performance_report()
        else:
            print("Usage: python firecrawl_orchestrator.py [parallel|sequential|report]")
    else:
        start_automated_orchestration()
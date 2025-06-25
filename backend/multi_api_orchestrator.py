#!/usr/bin/env python3
"""
Multi-API Orchestrator - FREE Data Collection Powerhouse
Coordinates Firecrawl + SAM.gov + NewsAPI + future free APIs
Massive data collection with 90%+ cost reduction vs paid-only approach
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
        logging.FileHandler('/tmp/multi_api_orchestrator.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

@dataclass
class ScrapingResult:
    """Result from a scraping cycle"""
    scraper_name: str
    scraper_type: str  # 'firecrawl', 'government_api', 'news_api'
    success: bool
    opportunities_found: int
    opportunities_saved: int
    duration_seconds: float
    errors: List[str]
    cycle_start: str
    cycle_end: str
    cost_estimate: float  # Estimated cost if this was a paid service

class MultiAPIOrchestrator:
    """Unified orchestrator for all free data collection APIs"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # All available scrapers organized by type and priority
        self.scrapers = {
            # Firecrawl-based scrapers (limited by plan)
            'firecrawl': {
                'industry': {
                    'script': 'firecrawl_industry_scraper.py',
                    'name': 'Firecrawl Industry Scraper',
                    'description': 'Data Centers + IT Industries',
                    'priority': 1,
                    'cost_per_request': 0.01,  # Estimated
                    'frequency_hours': 4
                },
                'rfp': {
                    'script': 'firecrawl_rfp_scraper.py',
                    'name': 'Firecrawl RFP Scraper',
                    'description': 'RFP Platforms & Procurement',
                    'priority': 2,
                    'cost_per_request': 0.01,
                    'frequency_hours': 4
                },
                'government': {
                    'script': 'firecrawl_government_scraper.py',
                    'name': 'Firecrawl Government Scraper',
                    'description': 'Government Portals',
                    'priority': 3,
                    'cost_per_request': 0.01,
                    'frequency_hours': 4
                }
            },
            
            # Government APIs (100% FREE)
            'government_api': {
                'sam_gov': {
                    'script': 'sam_gov_scraper.py',
                    'name': 'SAM.gov Official API',
                    'description': 'Federal Contract Opportunities',
                    'priority': 1,
                    'cost_per_request': 0.0,  # FREE
                    'frequency_hours': 3,
                    'rate_limit': '1000/hour'
                }
            },
            
            # News and Industry APIs (FREE tiers)
            'news_api': {
                'newsapi': {
                    'script': 'news_api_scraper.py',
                    'name': 'NewsAPI Industry Monitor',
                    'description': 'Contract News & Announcements',
                    'priority': 1,
                    'cost_per_request': 0.0,  # FREE tier
                    'frequency_hours': 6,
                    'rate_limit': '1000/day'
                }
            }
        }
        
        # Track scraper performance and scheduling
        self.scraper_schedules = {}
        self.last_run_times = {}
        
        # Initialize database tracking
        self._ensure_tracking_tables()
    
    def _ensure_tracking_tables(self):
        """Ensure all tracking tables exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Multi-API cycle tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS multi_api_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_start DATETIME,
                    cycle_end DATETIME,
                    total_scrapers_run INTEGER,
                    successful_scrapers INTEGER,
                    total_opportunities_found INTEGER,
                    total_opportunities_saved INTEGER,
                    total_duration_seconds REAL,
                    total_errors INTEGER,
                    estimated_cost_saved REAL,
                    cycle_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Individual scraper tracking with API type
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id INTEGER,
                    scraper_name TEXT,
                    scraper_type TEXT,
                    success BOOLEAN,
                    opportunities_found INTEGER,
                    opportunities_saved INTEGER,
                    duration_seconds REAL,
                    errors_count INTEGER,
                    error_details TEXT,
                    estimated_cost REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cycle_id) REFERENCES multi_api_cycles (id)
                )
            """)
            
            # API rate limiting tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT,
                    requests_made INTEGER,
                    limit_period TEXT,
                    reset_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to ensure tracking tables: {e}")
    
    def check_api_availability(self) -> Dict[str, bool]:
        """Check which APIs are available based on environment variables"""
        api_status = {
            'firecrawl': bool(os.getenv('FIRECRAWL_API_KEY')),
            'sam_gov': True,  # Can work without API key (public endpoints)
            'newsapi': bool(os.getenv('NEWS_API_KEY')),
            'sam_gov_api': bool(os.getenv('SAM_GOV_API_KEY')),  # Enhanced with API key
        }
        
        self.logger.info("🔍 API Availability Check:")
        for api_name, available in api_status.items():
            status = "✅ Available" if available else "❌ Missing API Key"
            self.logger.info(f"   {api_name}: {status}")
        
        return api_status
    
    def get_ready_scrapers(self) -> List[Dict[str, Any]]:
        """Get scrapers that are ready to run based on their schedules"""
        ready_scrapers = []
        current_time = datetime.now()
        
        api_status = self.check_api_availability()
        
        for scraper_type, scrapers in self.scrapers.items():
            # Skip scraper types with missing APIs
            if scraper_type == 'firecrawl' and not api_status.get('firecrawl'):
                continue
            if scraper_type == 'news_api' and not api_status.get('newsapi'):
                continue
            
            for scraper_key, scraper_config in scrapers.items():
                scraper_id = f"{scraper_type}_{scraper_key}"
                
                # Check if enough time has passed since last run
                last_run = self.last_run_times.get(scraper_id)
                frequency_hours = scraper_config['frequency_hours']
                
                if last_run is None:
                    # Never run before
                    ready_scrapers.append({
                        'id': scraper_id,
                        'type': scraper_type,
                        'config': scraper_config,
                        'reason': 'first_run'
                    })
                else:
                    time_since_run = (current_time - last_run).total_seconds() / 3600
                    if time_since_run >= frequency_hours:
                        ready_scrapers.append({
                            'id': scraper_id,
                            'type': scraper_type,
                            'config': scraper_config,
                            'reason': f'scheduled ({time_since_run:.1f}h ago)'
                        })
        
        # Sort by priority
        ready_scrapers.sort(key=lambda x: x['config']['priority'])
        
        return ready_scrapers
    
    def run_scraper(self, scraper_id: str, scraper_type: str, scraper_config: Dict[str, Any]) -> ScrapingResult:
        """Run a single scraper and return results"""
        script_path = scraper_config['script']
        
        self.logger.info(f"🚀 Running {scraper_config['name']}...")
        
        start_time = datetime.now()
        
        try:
            # Run the scraper with immediate flag
            result = subprocess.run(
                [sys.executable, script_path, 'immediate'],
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout per scraper
                cwd=os.path.dirname(__file__)
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.returncode == 0:
                # Parse output for stats
                output = result.stdout
                opportunities_found = self._extract_stat(output, ['Found', 'opportunities'])
                opportunities_saved = self._extract_stat(output, ['Saved', 'new opportunities'])
                
                # Estimate cost if this was a paid service
                estimated_cost = opportunities_found * scraper_config.get('cost_per_request', 0.01)
                
                self.logger.info(f"✅ {scraper_config['name']} completed successfully")
                
                # Update last run time
                self.last_run_times[scraper_id] = end_time
                
                return ScrapingResult(
                    scraper_name=scraper_config['name'],
                    scraper_type=scraper_type,
                    success=True,
                    opportunities_found=opportunities_found,
                    opportunities_saved=opportunities_saved,
                    duration_seconds=duration,
                    errors=[],
                    cycle_start=start_time.isoformat(),
                    cycle_end=end_time.isoformat(),
                    cost_estimate=estimated_cost
                )
            else:
                error_msg = f"Script failed with return code {result.returncode}: {result.stderr}"
                self.logger.error(f"❌ {scraper_config['name']} failed: {error_msg}")
                
                return ScrapingResult(
                    scraper_name=scraper_config['name'],
                    scraper_type=scraper_type,
                    success=False,
                    opportunities_found=0,
                    opportunities_saved=0,
                    duration_seconds=duration,
                    errors=[error_msg],
                    cycle_start=start_time.isoformat(),
                    cycle_end=end_time.isoformat(),
                    cost_estimate=0
                )
                
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Scraper timed out after {duration:.1f} seconds"
            self.logger.error(f"⏰ {scraper_config['name']} timed out")
            
            return ScrapingResult(
                scraper_name=scraper_config['name'],
                scraper_type=scraper_type,
                success=False,
                opportunities_found=0,
                opportunities_saved=0,
                duration_seconds=duration,
                errors=[error_msg],
                cycle_start=start_time.isoformat(),
                cycle_end=datetime.now().isoformat(),
                cost_estimate=0
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Unexpected error: {e}"
            self.logger.error(f"❌ {scraper_config['name']} failed: {error_msg}")
            
            return ScrapingResult(
                scraper_name=scraper_config['name'],
                scraper_type=scraper_type,
                success=False,
                opportunities_found=0,
                opportunities_saved=0,
                duration_seconds=duration,
                errors=[error_msg],
                cycle_start=start_time.isoformat(),
                cycle_end=datetime.now().isoformat(),
                cost_estimate=0
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
    
    def run_intelligent_cycle(self) -> List[ScrapingResult]:
        """Run intelligent cycle - only scrapers that are ready"""
        self.logger.info("🧠 Starting Intelligent Multi-API Cycle")
        self.logger.info("=" * 50)
        
        cycle_start = datetime.now()
        cycle_id = self._record_cycle_start("intelligent")
        
        # Get scrapers ready to run
        ready_scrapers = self.get_ready_scrapers()
        
        if not ready_scrapers:
            self.logger.info("   ℹ️  No scrapers ready to run")
            return []
        
        self.logger.info(f"   🎯 {len(ready_scrapers)} scrapers ready to run:")
        for scraper in ready_scrapers:
            self.logger.info(f"      - {scraper['config']['name']} ({scraper['reason']})")
        
        results = []
        
        # Run scrapers sequentially to respect rate limits
        for scraper in ready_scrapers:
            try:
                result = self.run_scraper(
                    scraper['id'],
                    scraper['type'], 
                    scraper['config']
                )
                results.append(result)
                
                # Brief pause between scrapers
                time.sleep(5)
                
            except Exception as e:
                error_msg = f"Failed to run {scraper['id']}: {e}"
                self.logger.error(error_msg)
                
                # Create error result
                error_result = ScrapingResult(
                    scraper_name=scraper['config']['name'],
                    scraper_type=scraper['type'],
                    success=False,
                    opportunities_found=0,
                    opportunities_saved=0,
                    duration_seconds=0,
                    errors=[error_msg],
                    cycle_start=cycle_start.isoformat(),
                    cycle_end=datetime.now().isoformat(),
                    cost_estimate=0
                )
                results.append(error_result)
        
        # Record cycle completion
        self._record_cycle_completion(cycle_id, results)
        
        # Print summary
        self._print_cycle_summary(results, cycle_start)
        
        return results
    
    def run_full_cycle(self) -> List[ScrapingResult]:
        """Run all available scrapers regardless of schedule"""
        self.logger.info("🌐 Starting Full Multi-API Cycle")
        self.logger.info("=" * 40)
        
        cycle_start = datetime.now()
        cycle_id = self._record_cycle_start("full")
        
        api_status = self.check_api_availability()
        results = []
        
        # Run all available scrapers
        for scraper_type, scrapers in self.scrapers.items():
            # Skip scraper types with missing APIs
            if scraper_type == 'firecrawl' and not api_status.get('firecrawl'):
                self.logger.info(f"   ⏭️  Skipping {scraper_type} scrapers (API key missing)")
                continue
            if scraper_type == 'news_api' and not api_status.get('newsapi'):
                self.logger.info(f"   ⏭️  Skipping {scraper_type} scrapers (API key missing)")
                continue
            
            for scraper_key, scraper_config in scrapers.items():
                scraper_id = f"{scraper_type}_{scraper_key}"
                
                try:
                    result = self.run_scraper(scraper_id, scraper_type, scraper_config)
                    results.append(result)
                    
                    # Update last run time
                    self.last_run_times[scraper_id] = datetime.now()
                    
                    # Pause between scrapers
                    time.sleep(10)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to run {scraper_id}: {e}")
        
        # Record cycle completion
        self._record_cycle_completion(cycle_id, results)
        
        # Print summary
        self._print_cycle_summary(results, cycle_start)
        
        return results
    
    def _record_cycle_start(self, cycle_type: str) -> int:
        """Record the start of a multi-API cycle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO multi_api_cycles (cycle_start, cycle_type)
                VALUES (?, ?)
            """, (now, cycle_type))
            
            cycle_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return cycle_id
            
        except Exception as e:
            self.logger.error(f"Failed to record cycle start: {e}")
            return 0
    
    def _record_cycle_completion(self, cycle_id: int, results: List[ScrapingResult]):
        """Record the completion of a multi-API cycle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate aggregated stats
            total_found = sum(r.opportunities_found for r in results)
            total_saved = sum(r.opportunities_saved for r in results)
            total_duration = sum(r.duration_seconds for r in results)
            successful_scrapers = sum(1 for r in results if r.success)
            total_errors = sum(len(r.errors) for r in results)
            estimated_cost_saved = sum(r.cost_estimate for r in results)
            
            now = datetime.now().isoformat()
            
            # Update cycle record
            cursor.execute("""
                UPDATE multi_api_cycles SET
                    cycle_end = ?,
                    total_scrapers_run = ?,
                    successful_scrapers = ?,
                    total_opportunities_found = ?,
                    total_opportunities_saved = ?,
                    total_duration_seconds = ?,
                    total_errors = ?,
                    estimated_cost_saved = ?
                WHERE id = ?
            """, (now, len(results), successful_scrapers, total_found,
                  total_saved, total_duration, total_errors, estimated_cost_saved, cycle_id))
            
            # Record individual scraper runs
            for result in results:
                cursor.execute("""
                    INSERT INTO scraper_runs (
                        cycle_id, scraper_name, scraper_type, success, opportunities_found,
                        opportunities_saved, duration_seconds, errors_count, error_details, estimated_cost
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cycle_id, result.scraper_name, result.scraper_type, result.success,
                      result.opportunities_found, result.opportunities_saved,
                      result.duration_seconds, len(result.errors),
                      json.dumps(result.errors), result.cost_estimate))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to record cycle completion: {e}")
    
    def _print_cycle_summary(self, results: List[ScrapingResult], cycle_start: datetime):
        """Print comprehensive cycle summary"""
        cycle_end = datetime.now()
        total_duration = (cycle_end - cycle_start).total_seconds()
        total_found = sum(r.opportunities_found for r in results)
        total_saved = sum(r.opportunities_saved for r in results)
        successful_scrapers = sum(1 for r in results if r.success)
        estimated_cost_saved = sum(r.cost_estimate for r in results)
        
        self.logger.info(f"\n📊 MULTI-API CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Total Duration: {total_duration:.1f} seconds")
        self.logger.info(f"   ✅ Successful Scrapers: {successful_scrapers}/{len(results)}")
        self.logger.info(f"   🔍 Total Opportunities Found: {total_found}")
        self.logger.info(f"   💾 Total Opportunities Saved: {total_saved}")
        self.logger.info(f"   💰 Estimated Cost Saved: ${estimated_cost_saved:.2f}")
        
        # Breakdown by scraper type
        type_breakdown = {}
        for result in results:
            if result.scraper_type not in type_breakdown:
                type_breakdown[result.scraper_type] = {'saved': 0, 'found': 0}
            type_breakdown[result.scraper_type]['saved'] += result.opportunities_saved
            type_breakdown[result.scraper_type]['found'] += result.opportunities_found
        
        self.logger.info(f"\n📈 BREAKDOWN BY API TYPE:")
        for api_type, stats in type_breakdown.items():
            self.logger.info(f"   {api_type}: {stats['saved']} saved, {stats['found']} found")
        
        # Individual scraper results
        self.logger.info(f"\n🔧 INDIVIDUAL RESULTS:")
        for result in results:
            status = "✅" if result.success else "❌"
            self.logger.info(f"   {status} {result.scraper_name}: {result.opportunities_saved} saved ({result.duration_seconds:.1f}s)")
    
    def get_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive multi-API performance report"""
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
                    SUM(total_errors) as total_errors,
                    SUM(estimated_cost_saved) as total_cost_saved
                FROM multi_api_cycles
                WHERE cycle_start >= ?
            """, (cutoff_date,))
            
            cycle_stats = cursor.fetchone()
            
            # Get API type breakdown
            cursor.execute("""
                SELECT 
                    scraper_type,
                    COUNT(*) as runs,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_runs,
                    SUM(opportunities_found) as total_found,
                    SUM(opportunities_saved) as total_saved,
                    AVG(duration_seconds) as avg_duration,
                    SUM(estimated_cost) as total_cost_estimate
                FROM scraper_runs sr
                JOIN multi_api_cycles mc ON sr.cycle_id = mc.id
                WHERE mc.cycle_start >= ?
                GROUP BY scraper_type
            """, (cutoff_date,))
            
            api_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'period_days': days,
                'cycle_summary': {
                    'total_cycles': cycle_stats[0] or 0,
                    'avg_successful_scrapers': round(cycle_stats[1] or 0, 2),
                    'total_opportunities_found': cycle_stats[2] or 0,
                    'total_opportunities_saved': cycle_stats[3] or 0,
                    'avg_duration_seconds': round(cycle_stats[4] or 0, 2),
                    'total_errors': cycle_stats[5] or 0,
                    'total_cost_saved': round(cycle_stats[6] or 0, 2)
                },
                'api_breakdown': [
                    {
                        'type': row[0],
                        'runs': row[1],
                        'successful_runs': row[2],
                        'success_rate': round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0,
                        'total_found': row[3],
                        'total_saved': row[4],
                        'avg_duration': round(row[5], 2),
                        'estimated_cost': round(row[6], 2)
                    }
                    for row in api_stats
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance report: {e}")
            return {}

def start_automated_multi_api_orchestration():
    """Start automated intelligent multi-API orchestration"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = MultiAPIOrchestrator(db_path)
    
    print("🤖 MULTI-API ORCHESTRATOR")
    print("=" * 40)
    print("🎯 APIs: Firecrawl + SAM.gov + NewsAPI + Future")
    print("💰 Cost: 90%+ Savings vs Paid-Only Approach")
    print("🧠 Mode: Intelligent Scheduling")
    print("⏰ Frequency: Continuous (respects rate limits)")
    
    # Schedule intelligent cycle every hour
    schedule.every(1).hours.do(orchestrator.run_intelligent_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial intelligent cycle...")
    orchestrator.run_intelligent_cycle()
    
    print(f"\n✅ Automated multi-API orchestration started!")
    print("🧠 Intelligent scheduling active")
    print("📝 Logs: /tmp/multi_api_orchestrator.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated multi-API orchestration stopped.")

def run_immediate_intelligent_cycle():
    """Run immediate intelligent cycle"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = MultiAPIOrchestrator(db_path)
    
    results = orchestrator.run_intelligent_cycle()
    
    if results:
        total_saved = sum(r.opportunities_saved for r in results)
        cost_saved = sum(r.cost_estimate for r in results)
        print(f"\n✅ Intelligent cycle complete!")
        print(f"💾 Total saved: {total_saved} opportunities")
        print(f"💰 Estimated cost saved: ${cost_saved:.2f}")
    else:
        print(f"\n ℹ️ No scrapers were ready to run")

def run_immediate_full_cycle():
    """Run immediate full cycle"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = MultiAPIOrchestrator(db_path)
    
    results = orchestrator.run_full_cycle()
    
    total_saved = sum(r.opportunities_saved for r in results)
    cost_saved = sum(r.cost_estimate for r in results)
    print(f"\n✅ Full cycle complete!")
    print(f"💾 Total saved: {total_saved} opportunities")
    print(f"💰 Estimated cost saved: ${cost_saved:.2f}")

def show_multi_api_report():
    """Show comprehensive multi-API performance report"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    orchestrator = MultiAPIOrchestrator(db_path)
    
    report = orchestrator.get_performance_report()
    
    print("📊 MULTI-API ORCHESTRATOR PERFORMANCE REPORT")
    print("=" * 55)
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
    print(f"   💰 Total Cost Saved: ${summary.get('total_cost_saved', 0):.2f}")
    print()
    
    print("🌐 API TYPE BREAKDOWN:")
    for api in report.get('api_breakdown', []):
        print(f"   {api['type'].upper()}:")
        print(f"     Runs: {api['runs']}")
        print(f"     Success Rate: {api['success_rate']}%")
        print(f"     Opportunities Found: {api['total_found']}")
        print(f"     Opportunities Saved: {api['total_saved']}")
        print(f"     Avg Duration: {api['avg_duration']:.1f}s")
        print(f"     Estimated Cost: ${api['estimated_cost']:.2f}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "intelligent":
            run_immediate_intelligent_cycle()
        elif sys.argv[1] == "full":
            run_immediate_full_cycle()
        elif sys.argv[1] == "report":
            show_multi_api_report()
        else:
            print("Usage: python multi_api_orchestrator.py [intelligent|full|report]")
    else:
        start_automated_multi_api_orchestration()
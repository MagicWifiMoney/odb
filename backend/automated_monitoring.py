#!/usr/bin/env python3
"""
Automated Contract Monitoring System
Combines Firecrawl scraping + Perplexity AI discovery
"""

import os
import sys
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))
from firecrawl_scraper import FirecrawlScraper
from perplexity_live_discovery import PerplexityLiveDiscovery
from src.config.supabase import get_supabase_admin_client

class AutomatedContractMonitor:
    """Automated system for continuous contract monitoring"""
    
    def __init__(self):
        self.firecrawl = None
        self.perplexity = None
        self.supabase = get_supabase_admin_client()
        
        # Initialize services if API keys available
        try:
            if os.getenv('FIRECRAWL_API_KEY'):
                self.firecrawl = FirecrawlScraper()
                print("✅ Firecrawl initialized")
        except Exception as e:
            print(f"⚠️ Firecrawl not available: {e}")
        
        try:
            if os.getenv('PERPLEXITY_API_KEY'):
                self.perplexity = PerplexityLiveDiscovery()
                print("✅ Perplexity AI initialized")
        except Exception as e:
            print(f"⚠️ Perplexity not available: {e}")
    
    def run_hourly_monitoring(self):
        """Run every hour - quick checks"""
        print(f"\n⏰ Hourly Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'hourly',
            'firecrawl_results': {},
            'ai_discoveries': {},
            'total_new_opportunities': 0
        }
        
        # Quick Perplexity check for breaking news
        if self.perplexity:
            try:
                print("🤖 Checking for urgent contract announcements...")
                
                prompt = f"""
                Find URGENT government contract announcements from the last 2 hours.
                
                Search for:
                - Breaking contract awards
                - Emergency procurement notices
                - Time-sensitive RFP releases
                - Major contract modifications
                
                Only return if there are genuinely urgent/breaking announcements.
                Format as brief summary with key details.
                """
                
                urgent_result = self.perplexity.query_perplexity(prompt, max_tokens=300)
                
                if urgent_result.get('choices'):
                    content = urgent_result['choices'][0]['message']['content']
                    if any(word in content.lower() for word in ['urgent', 'breaking', 'announced', 'awarded']):
                        print(f"🚨 Urgent announcement detected!")
                        results['ai_discoveries']['urgent_found'] = True
                        results['ai_discoveries']['content'] = content[:200]
                    else:
                        print("📊 No urgent announcements")
                        results['ai_discoveries']['urgent_found'] = False
                        
            except Exception as e:
                print(f"❌ Hourly AI check failed: {e}")
        
        self.log_monitoring_results(results)
        return results
    
    def run_daily_monitoring(self):
        """Run daily - comprehensive discovery"""
        print(f"\n📅 Daily Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'daily',
            'firecrawl_results': {},
            'ai_discoveries': {},
            'total_new_opportunities': 0
        }
        
        total_found = 0
        
        # Run Perplexity daily discovery
        if self.perplexity:
            try:
                print("🤖 Running daily AI discovery...")
                ai_results = self.perplexity.run_full_ai_discovery()
                results['ai_discoveries'] = ai_results
                total_found += ai_results.get('new_contracts_saved', 0)
                
            except Exception as e:
                print(f"❌ Daily AI discovery failed: {e}")
        
        # Run Firecrawl daily scraping (lighter version)
        if self.firecrawl:
            try:
                print("🔥 Running daily Firecrawl scraping...")
                scrape_results = self.run_targeted_daily_scraping()
                results['firecrawl_results'] = scrape_results
                total_found += sum(scrape_results.values())
                
            except Exception as e:
                print(f"❌ Daily Firecrawl scraping failed: {e}")
        
        results['total_new_opportunities'] = total_found
        
        print(f"\n🎯 Daily monitoring complete: {total_found} new opportunities found")
        self.log_monitoring_results(results)
        return results
    
    def run_targeted_daily_scraping(self) -> dict:
        """Run targeted daily scraping of key sources"""
        print("🎯 Targeted daily scraping...")
        
        results = {}
        
        # Key URLs to monitor daily
        daily_targets = [
            {
                'name': 'GSA_News',
                'url': 'https://www.gsa.gov/about-us/newsroom/news-releases',
                'extract_contracts': True
            },
            {
                'name': 'DOD_Contracts',
                'url': 'https://www.defense.gov/News/Contracts/',
                'extract_contracts': True
            },
            {
                'name': 'SAM_Opportunities',
                'url': 'https://sam.gov/content/opportunities',
                'extract_contracts': True
            }
        ]
        
        for target in daily_targets:
            try:
                print(f"   📡 Scraping {target['name']}...")
                
                # Simple content extraction
                scrape_result = self.firecrawl.scrape_url(target['url'])
                
                if scrape_result.get('success'):
                    content = scrape_result.get('data', {}).get('markdown', '')
                    
                    # Basic contract detection
                    contract_indicators = self.detect_contracts_in_content(content)
                    results[target['name']] = len(contract_indicators)
                    
                    print(f"   ✅ {target['name']}: {len(contract_indicators)} potential contracts")
                else:
                    results[target['name']] = 0
                    print(f"   ⚠️ {target['name']}: scraping failed")
                    
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ {target['name']} failed: {e}")
                results[target['name']] = 0
        
        return results
    
    def detect_contracts_in_content(self, content: str) -> list:
        """Detect potential contracts in scraped content"""
        indicators = []
        
        # Keywords that indicate contract opportunities
        contract_keywords = [
            'contract award', 'solicitation', 'RFP', 'RFQ', 'IFB',
            'procurement', 'opportunity', 'IDIQ', 'GSA Schedule',
            'million', 'billion', 'awarded to', 'selected for'
        ]
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains contract indicators
            if any(keyword in line_lower for keyword in contract_keywords):
                # Include some context
                context_start = max(0, i-1)
                context_end = min(len(lines), i+2)
                context = ' '.join(lines[context_start:context_end])
                
                indicators.append({
                    'line': line.strip(),
                    'context': context[:300],
                    'position': i
                })
        
        return indicators
    
    def run_weekly_intelligence(self):
        """Run weekly - deep market analysis"""
        print(f"\n📊 Weekly Intelligence - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'weekly',
            'market_trends': {},
            'predictions': {},
            'enhanced_opportunities': 0
        }
        
        if self.perplexity:
            try:
                # Weekly market analysis
                print("📈 Generating weekly market intelligence...")
                
                market_analysis = self.perplexity.analyze_market_trends()
                if market_analysis:
                    results['market_trends'] = market_analysis
                    print("✅ Market trends analysis complete")
                
                # Industry-specific predictions
                industries = ['IT Services', 'Healthcare', 'Defense', 'Energy']
                for industry in industries:
                    predictions = self.perplexity.predict_upcoming_opportunities(industry)
                    if predictions:
                        results['predictions'][industry] = predictions
                        print(f"✅ {industry} predictions generated")
                
                # Enhance more existing opportunities
                enhanced = self.perplexity.enhance_existing_opportunities()
                results['enhanced_opportunities'] = enhanced
                print(f"✅ Enhanced {enhanced} opportunities")
                
            except Exception as e:
                print(f"❌ Weekly intelligence failed: {e}")
        
        self.log_monitoring_results(results)
        return results
    
    def log_monitoring_results(self, results: dict):
        """Log monitoring results to database"""
        try:
            # Save to sync_logs table
            log_entry = {
                'source_name': 'AutomatedMonitor',
                'sync_type': results['type'],
                'records_processed': results.get('total_new_opportunities', 0),
                'status': 'completed',
                'details': results,
                'synced_at': datetime.now().isoformat()
            }
            
            self.supabase.table('sync_logs').insert(log_entry).execute()
            print(f"✅ Monitoring results logged")
            
        except Exception as e:
            print(f"⚠️ Failed to log results: {e}")
    
    def get_monitoring_status(self) -> dict:
        """Get current monitoring system status"""
        try:
            # Get recent logs
            recent_logs = self.supabase.table('sync_logs')\
                .select('*')\
                .eq('source_name', 'AutomatedMonitor')\
                .order('completed_at', desc=True)\
                .limit(10)\
                .execute()
            
            # Get opportunity counts
            total_opportunities = self.supabase.table('opportunities')\
                .select('*', count='exact')\
                .execute()
            
            return {
                'status': 'active',
                'services': {
                    'firecrawl': bool(self.firecrawl),
                    'perplexity': bool(self.perplexity)
                },
                'total_opportunities': total_opportunities.count,
                'recent_monitoring': recent_logs.data,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def setup_automated_schedule(self):
        """Setup automated monitoring schedule"""
        print("⏰ Setting up automated monitoring schedule...")
        
        # Schedule different monitoring frequencies
        schedule.every().hour.do(self.run_hourly_monitoring)
        schedule.every().day.at("09:00").do(self.run_daily_monitoring)
        schedule.every().monday.at("08:00").do(self.run_weekly_intelligence)
        
        print("✅ Monitoring schedule configured:")
        print("   ⏰ Hourly: Urgent announcements check")
        print("   📅 Daily 9AM: Comprehensive discovery")
        print("   📊 Weekly Monday 8AM: Market intelligence")
        
        return schedule
    
    def run_manual_discovery(self) -> dict:
        """Run a manual discovery session right now"""
        print("🚀 Manual Discovery Session")
        print("=" * 30)
        
        results = {}
        
        # Run both systems
        if self.perplexity:
            print("🤖 Running Perplexity AI discovery...")
            ai_results = self.perplexity.run_full_ai_discovery()
            results['ai_discovery'] = ai_results
        
        if self.firecrawl:
            print("🔥 Running Firecrawl scraping...")
            scrape_results = self.run_targeted_daily_scraping()
            results['firecrawl_scraping'] = scrape_results
        
        return results

def main():
    """Test automated monitoring system"""
    print("🤖 Automated Contract Monitoring System")
    print("=" * 50)
    
    try:
        monitor = AutomatedContractMonitor()
        
        # Show system status
        status = monitor.get_monitoring_status()
        print(f"\n📊 System Status:")
        print(f"   🔥 Firecrawl: {'✅ Active' if status['services']['firecrawl'] else '❌ Inactive'}")
        print(f"   🤖 Perplexity: {'✅ Active' if status['services']['perplexity'] else '❌ Inactive'}")
        print(f"   📈 Total Opportunities: {status['total_opportunities']}")
        
        # Run manual discovery session
        print(f"\n🚀 Running manual discovery session...")
        results = monitor.run_manual_discovery()
        
        print(f"\n🎯 Discovery Complete!")
        for service, result in results.items():
            if isinstance(result, dict):
                success_metrics = [k for k, v in result.items() if isinstance(v, int) and v > 0]
                print(f"   {service}: {len(success_metrics)} successful operations")
        
    except Exception as e:
        print(f"❌ Monitoring system failed: {e}")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Optimized Firecrawl RFP Platform Scraper
Targets actual RFP platforms and procurement portals for Data Centers & IT
"""

import os
import sys
import requests
import sqlite3
import json
import hashlib
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/firecrawl_rfp.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class OptimizedRFPScraper:
    """Optimized Firecrawl scraper for actual RFP platforms"""
    
    def __init__(self, db_path: str):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment")
        
        self.base_url = "https://api.firecrawl.dev/v0"
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Focus on actual RFP/procurement platforms
        self.rfp_platforms = [
            {
                'name': 'BidNet',
                'url': 'https://www.bidnet.com/bidsearch',
                'target': 'IT and Data Center RFPs',
                'reliability': 0.9
            },
            {
                'name': 'DemandStar',
                'url': 'https://www.demandstar.com/supplier/opportunity/public',
                'target': 'Government Technology RFPs',
                'reliability': 0.85
            },
            {
                'name': 'RFP Database',
                'url': 'https://www.rfpdb.com/categories/technology',
                'target': 'Technology RFPs',
                'reliability': 0.8
            },
            {
                'name': 'Federal Business Opportunities',
                'url': 'https://sam.gov/search/?keywords=data%20center&sort=-relevance',
                'target': 'Federal Data Center Contracts',
                'reliability': 0.95
            },
            {
                'name': 'GovWin IQ',
                'url': 'https://www.govwin.com/intel/opportunities',
                'target': 'Federal IT Opportunities',
                'reliability': 0.9
            }
        ]
    
    def scrape_rfp_platform(self, platform: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape RFP platform with optimized extraction"""
        self.logger.info(f"🔍 Scraping {platform['name']} for {platform['target']}...")
        
        # Use markdown format for better text extraction
        payload = {
            'url': platform['url'],
            'formats': ['markdown'],
            'onlyMainContent': True,
            'waitFor': 5000,  # Wait for dynamic content
            'timeout': 60000
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        opportunities = []
        
        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=70
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'markdown' in data['data']:
                    markdown_content = data['data']['markdown']
                    opportunities = self._extract_opportunities_from_markdown(
                        markdown_content, platform
                    )
                    
                    self.logger.info(f"   ✅ Extracted {len(opportunities)} opportunities from {platform['name']}")
                else:
                    self.logger.warning(f"   ⚠️  No markdown content from {platform['name']}")
            else:
                self.logger.error(f"   ❌ Failed to scrape {platform['name']}: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"   ❌ Error scraping {platform['name']}: {e}")
        
        # Rate limiting
        time.sleep(3)
        
        return opportunities
    
    def _extract_opportunities_from_markdown(self, content: str, platform: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract opportunity information from markdown content"""
        opportunities = []
        
        try:
            # Look for common RFP/opportunity patterns
            lines = content.split('\n')
            current_opp = {}
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    if current_opp and 'title' in current_opp:
                        opportunities.append(current_opp.copy())
                        current_opp = {}
                    continue
                
                # Look for opportunity indicators
                lower_line = line.lower()
                
                # Title patterns
                if any(keyword in lower_line for keyword in [
                    'rfp', 'request for proposal', 'solicitation', 'bid', 'contract',
                    'opportunity', 'procurement', 'data center', 'datacenter', 'cloud',
                    'infrastructure', 'technology', 'it services', 'software'
                ]):
                    # Clean up the title
                    title = line.replace('#', '').replace('*', '').strip()
                    if len(title) > 10 and len(title) < 200:
                        current_opp['title'] = title
                
                # Value patterns
                if '$' in line and any(keyword in lower_line for keyword in [
                    'million', 'billion', 'value', 'budget', 'amount', 'contract'
                ]):
                    current_opp['estimated_value'] = line
                
                # Date patterns
                if any(keyword in lower_line for keyword in [
                    'due', 'deadline', 'closes', 'closing', 'submission'
                ]) and any(char.isdigit() for char in line):
                    current_opp['due_date'] = line
                
                # Organization patterns
                if any(keyword in lower_line for keyword in [
                    'agency', 'department', 'city of', 'state of', 'university', 'county'
                ]):
                    org = line.replace('*', '').strip()
                    if len(org) > 5 and len(org) < 100:
                        current_opp['organization'] = org
            
            # Add final opportunity if exists
            if current_opp and 'title' in current_opp:
                opportunities.append(current_opp)
            
            # Filter and enhance opportunities
            filtered_opportunities = []
            for opp in opportunities:
                if self._is_relevant_opportunity(opp):
                    enhanced_opp = self._enhance_opportunity(opp, platform)
                    if enhanced_opp:
                        filtered_opportunities.append(enhanced_opp)
            
            return filtered_opportunities
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error extracting opportunities: {e}")
            return []
    
    def _is_relevant_opportunity(self, opp: Dict[str, Any]) -> bool:
        """Check if opportunity is relevant to data centers or IT"""
        title = opp.get('title', '').lower()
        
        # Must have title
        if not title or len(title) < 10:
            return False
        
        # Check for relevant keywords
        relevant_keywords = [
            'data center', 'datacenter', 'cloud', 'infrastructure', 'technology',
            'it services', 'software', 'network', 'security', 'database',
            'application', 'platform', 'digital', 'cyber', 'analytics'
        ]
        
        return any(keyword in title for keyword in relevant_keywords)
    
    def _enhance_opportunity(self, opp: Dict[str, Any], platform: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance opportunity with additional metadata"""
        try:
            title = opp.get('title', '')
            description = opp.get('description', title)  # Use title as description if none
            organization = opp.get('organization', 'Unknown Organization')
            
            # Generate unique hash for duplicate detection
            hash_input = f"{title}{organization}{platform['name']}"
            duplicate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            # Check if already exists
            if self._is_duplicate(duplicate_hash):
                return None
            
            # Extract estimated value
            estimated_value = self._extract_value(opp.get('estimated_value', ''))
            
            # Create enhanced opportunity
            enhanced = {
                'title': title[:500],
                'description': description[:2000],
                'organization': organization[:200],
                'opportunity_id': f"FC-RFP-{hash(duplicate_hash) % 100000}",
                'estimated_value': estimated_value,
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'due_date': self._extract_date(opp.get('due_date', '')),
                'source_name': f"Firecrawl-{platform['name']}",
                'source_url': platform['url'],
                'industry_category': self._classify_industry(title),
                'source_reliability_score': platform['reliability'],
                'duplicate_hash': duplicate_hash,
                'last_scraped_at': datetime.now().isoformat()
            }
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error enhancing opportunity: {e}")
            return None
    
    def _is_duplicate(self, duplicate_hash: str) -> bool:
        """Check if opportunity already exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create hash table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunity_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    duplicate_hash TEXT UNIQUE,
                    created_at DATETIME
                )
            """)
            
            cursor.execute(
                "SELECT id FROM opportunity_hashes WHERE duplicate_hash = ?",
                (duplicate_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception:
            return False
    
    def _extract_value(self, value_text: str) -> Optional[float]:
        """Extract numeric value from text"""
        if not value_text:
            return None
        
        try:
            import re
            # Look for dollar amounts
            pattern = r'\$([0-9,\.]+)\s*(million|billion|m|b|k)?'
            match = re.search(pattern, value_text.lower())
            
            if match:
                amount = float(match.group(1).replace(',', ''))
                unit = match.group(2) or ''
                
                if 'billion' in unit or 'b' == unit:
                    return amount * 1_000_000_000
                elif 'million' in unit or 'm' == unit:
                    return amount * 1_000_000
                elif 'k' == unit:
                    return amount * 1_000
                else:
                    return amount
            
            return None
            
        except Exception:
            return None
    
    def _extract_date(self, date_text: str) -> Optional[str]:
        """Extract date from text"""
        if not date_text:
            return None
        
        try:
            import re
            # Look for date patterns
            date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            match = re.search(date_pattern, date_text)
            
            if match:
                return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _classify_industry(self, title: str) -> str:
        """Classify opportunity by industry"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in [
            'data center', 'datacenter', 'colocation', 'hosting', 'cloud infrastructure'
        ]):
            return 'data_center'
        elif any(keyword in title_lower for keyword in [
            'software', 'application', 'platform', 'database', 'analytics'
        ]):
            return 'information_technology'
        else:
            return 'general_technology'
    
    def save_opportunity(self, opp: Dict[str, Any]) -> bool:
        """Save opportunity to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert opportunity
            cursor.execute("""
                INSERT INTO opportunities (
                    title, description, agency_name, opportunity_number, estimated_value,
                    posted_date, due_date, source_type, source_name, source_url,
                    location, contact_info, relevance_score, urgency_score,
                    value_score, competition_score, total_score, created_at, updated_at,
                    industry_category, source_reliability_score, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp['title'], opp['description'], opp['organization'], opp['opportunity_id'],
                opp['estimated_value'], opp['posted_date'], opp['due_date'], 'rfp_platform',
                opp['source_name'], opp['source_url'], None, None,
                85, 70, 75, 65, 295, datetime.now().isoformat(), datetime.now().isoformat(),
                opp['industry_category'], opp['source_reliability_score'], opp['last_scraped_at']
            ))
            
            opportunity_id = cursor.lastrowid
            
            # Record hash
            cursor.execute("""
                INSERT OR IGNORE INTO opportunity_hashes (duplicate_hash, created_at)
                VALUES (?, ?)
            """, (opp['duplicate_hash'], datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"   ✅ Saved: {opp['title'][:50]}... (ID: {opportunity_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save opportunity: {e}")
            return False
    
    def run_rfp_scraping_cycle(self) -> Dict[str, Any]:
        """Run complete RFP scraping cycle"""
        cycle_start = datetime.now()
        self.logger.info("🚀 Starting Firecrawl RFP Platform Scraping Cycle")
        self.logger.info("=" * 55)
        
        results = {
            'platforms_scraped': 0,
            'opportunities_found': 0,
            'opportunities_saved': 0,
            'cycle_start': cycle_start.isoformat(),
            'errors': []
        }
        
        for platform in self.rfp_platforms:
            try:
                opportunities = self.scrape_rfp_platform(platform)
                results['platforms_scraped'] += 1
                results['opportunities_found'] += len(opportunities)
                
                saved_count = 0
                for opp in opportunities:
                    if self.save_opportunity(opp):
                        saved_count += 1
                
                results['opportunities_saved'] += saved_count
                
            except Exception as e:
                error_msg = f"Failed to scrape {platform['name']}: {e}"
                self.logger.error(f"   ❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = duration
        
        self.logger.info(f"\n📊 RFP SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"   🌐 Platforms Scraped: {results['platforms_scraped']}")
        self.logger.info(f"   🔍 Opportunities Found: {results['opportunities_found']}")
        self.logger.info(f"   💾 Opportunities Saved: {results['opportunities_saved']}")
        
        if results['errors']:
            self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
        
        return results

def start_automated_rfp_scraping():
    """Start automated 2-hour RFP scraping cycles"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = OptimizedRFPScraper(db_path)
    
    print("🤖 FIRECRAWL RFP PLATFORM SCRAPER")
    print("=" * 40)
    print("🎯 Targeting: RFP Platforms & Procurement Portals")
    print("🔍 Focus: Data Centers + IT Opportunities")
    print("⏰ Frequency: Every 2 hours")
    
    # Schedule every 2 hours
    schedule.every(2).hours.do(scraper.run_rfp_scraping_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial RFP scraping cycle...")
    scraper.run_rfp_scraping_cycle()
    
    print(f"\n✅ Automated RFP scraping started!")
    print("🔄 Next cycle in 2 hours")
    print("📝 Logs: /tmp/firecrawl_rfp.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated RFP scraping stopped.")

def run_immediate_rfp_cycle():
    """Run immediate RFP scraping cycle for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = OptimizedRFPScraper(db_path)
    
    results = scraper.run_rfp_scraping_cycle()
    print(f"\n✅ Immediate RFP cycle complete!")
    print(f"🎯 Found {results['opportunities_found']} opportunities")
    print(f"💾 Saved {results['opportunities_saved']} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_rfp_cycle()
    else:
        start_automated_rfp_scraping()
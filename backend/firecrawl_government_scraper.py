#!/usr/bin/env python3
"""
Firecrawl Government Site Scraper - Targeted Approach
Focus on publicly accessible government procurement pages
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
        logging.FileHandler('/tmp/firecrawl_gov.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class GovernmentSiteScraper:
    """Focused scraper for accessible government procurement sites"""
    
    def __init__(self, db_path: str):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment")
        
        self.base_url = "https://api.firecrawl.dev/v0"
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Target publicly accessible government procurement sites
        self.government_sites = [
            {
                'name': 'GSA Multiple Award Schedules',
                'url': 'https://www.gsa.gov/buy-through-us/purchasing-programs/gsa-schedules',
                'focus': 'Federal IT Schedules',
                'reliability': 0.95
            },
            {
                'name': 'California eProcure',
                'url': 'https://caleprocure.ca.gov/pages/PublicSearch.aspx',
                'focus': 'California State Procurement',
                'reliability': 0.9
            },
            {
                'name': 'Texas Procurement',
                'url': 'https://www.txsmartbuy.com/sp',
                'focus': 'Texas State Contracts',
                'reliability': 0.9
            },
            {
                'name': 'NYC PASSPort',
                'url': 'https://www1.nyc.gov/site/mocs/systems/about-passport.page',
                'focus': 'NYC Procurement Opportunities',
                'reliability': 0.85
            },
            {
                'name': 'Florida Procurement',
                'url': 'https://www.myfloridamarketplace.com/',
                'focus': 'Florida State Contracts',
                'reliability': 0.8
            }
        ]
    
    def scrape_government_site(self, site: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape government site for procurement information"""
        self.logger.info(f"🏛️ Scraping {site['name']} for {site['focus']}...")
        
        # Use markdown extraction for better content parsing
        payload = {
            'url': site['url'],
            'formats': ['markdown'],
            'onlyMainContent': True,
            'waitFor': 5000,
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
                    content = data['data']['markdown']
                    
                    # Log content length for debugging
                    self.logger.info(f"   📄 Content length: {len(content)} characters")
                    
                    # Extract opportunities from content
                    opportunities = self._extract_from_content(content, site)
                    
                    self.logger.info(f"   ✅ Found {len(opportunities)} opportunities from {site['name']}")
                    
                    # Log sample content for debugging
                    if content:
                        sample = content[:300].replace('\n', ' ')
                        self.logger.info(f"   📖 Sample content: {sample}...")
                else:
                    self.logger.warning(f"   ⚠️  No content extracted from {site['name']}")
            else:
                self.logger.error(f"   ❌ Failed to scrape {site['name']}: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"   ❌ Error scraping {site['name']}: {e}")
        
        # Rate limiting
        time.sleep(3)
        
        return opportunities
    
    def _extract_from_content(self, content: str, site: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract procurement opportunities from markdown content"""
        opportunities = []
        
        try:
            # Look for technology-related content
            tech_keywords = [
                'technology', 'data center', 'cloud', 'software', 'hardware',
                'network', 'security', 'database', 'application', 'platform',
                'infrastructure', 'digital', 'cyber', 'analytics', 'artificial intelligence'
            ]
            
            lines = content.lower().split('\n')
            tech_lines = []
            
            # Find lines with technology keywords
            for line in lines:
                if any(keyword in line for keyword in tech_keywords):
                    tech_lines.append(line.strip())
            
            # Create opportunities from tech-related content
            if tech_lines:
                # Group related lines into opportunities
                current_opp_lines = []
                
                for line in tech_lines[:10]:  # Limit to first 10 relevant lines
                    if line and len(line) > 20:  # Meaningful content
                        current_opp_lines.append(line)
                        
                        # If we have enough content, create an opportunity
                        if len(current_opp_lines) >= 2:
                            opp = self._create_opportunity_from_lines(current_opp_lines, site)
                            if opp:
                                opportunities.append(opp)
                            current_opp_lines = []
                
                # Handle remaining lines
                if current_opp_lines:
                    opp = self._create_opportunity_from_lines(current_opp_lines, site)
                    if opp:
                        opportunities.append(opp)
            
            # If no tech-specific content, create a general opportunity
            if not opportunities and content:
                general_opp = self._create_general_opportunity(content, site)
                if general_opp:
                    opportunities.append(general_opp)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error extracting from content: {e}")
            return []
    
    def _create_opportunity_from_lines(self, lines: List[str], site: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create opportunity from content lines"""
        try:
            # Combine lines into title and description
            title_line = lines[0][:100].title()
            description_lines = lines[1:3] if len(lines) > 1 else [title_line]
            description = ' '.join(description_lines)[:500]
            
            # Clean up title
            title = f"{site['focus']} - Technology Procurement Opportunity"
            
            # Create opportunity
            opportunity = {
                'title': title,
                'description': description,
                'organization': site['name'],
                'source_url': site['url'],
                'focus_area': site['focus'],
                'reliability': site['reliability'],
                'scraped_content': ' '.join(lines)[:1000]
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error creating opportunity: {e}")
            return None
    
    def _create_general_opportunity(self, content: str, site: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create general opportunity from site content"""
        try:
            # Extract first meaningful paragraph as description
            paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
            description = paragraphs[0][:500] if paragraphs else "Government procurement opportunity"
            
            opportunity = {
                'title': f"{site['focus']} - Government Procurement Portal",
                'description': description,
                'organization': site['name'],
                'source_url': site['url'],
                'focus_area': site['focus'],
                'reliability': site['reliability'],
                'scraped_content': content[:1000]
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error creating general opportunity: {e}")
            return None
    
    def save_opportunity(self, opp: Dict[str, Any]) -> bool:
        """Save opportunity to database with enhanced metadata"""
        try:
            # Generate unique hash
            hash_input = f"{opp['title']}{opp['organization']}{opp.get('scraped_content', '')[:100]}"
            duplicate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            # Check for duplicates
            if self._is_duplicate(duplicate_hash):
                self.logger.info(f"   ⏭️  Skipping duplicate: {opp['title'][:50]}...")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create enhanced opportunity record
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO opportunities (
                    title, description, agency_name, opportunity_number, estimated_value,
                    posted_date, due_date, source_type, source_name, source_url,
                    location, contact_info, relevance_score, urgency_score,
                    value_score, competition_score, total_score, created_at, updated_at,
                    industry_category, source_reliability_score, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp['title'], opp['description'], opp['organization'], 
                f"FC-GOV-{hash(duplicate_hash) % 100000}", None,  # estimated_value
                now.split('T')[0], None,  # posted_date, due_date
                'government_portal', f"Firecrawl-{opp['organization']}", opp['source_url'],
                None, None,  # location, contact_info
                80, 70, 60, 65, 275,  # scores
                now, now,  # created_at, updated_at
                'government_technology', opp['reliability'], now  # industry, reliability, last_scraped
            ))
            
            opportunity_id = cursor.lastrowid
            
            # Record hash for duplicate detection
            cursor.execute("""
                INSERT OR IGNORE INTO opportunity_hashes (duplicate_hash, created_at)
                VALUES (?, ?)
            """, (duplicate_hash, now))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"   ✅ Saved: {opp['title'][:50]}... (ID: {opportunity_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save opportunity: {e}")
            return False
    
    def _is_duplicate(self, duplicate_hash: str) -> bool:
        """Check for duplicate opportunities"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure hash table exists
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
    
    def run_government_scraping_cycle(self) -> Dict[str, Any]:
        """Run complete government site scraping cycle"""
        cycle_start = datetime.now()
        self.logger.info("🚀 Starting Government Site Scraping Cycle")
        self.logger.info("=" * 45)
        
        results = {
            'sites_scraped': 0,
            'opportunities_found': 0,
            'opportunities_saved': 0,
            'cycle_start': cycle_start.isoformat(),
            'errors': []
        }
        
        for site in self.government_sites:
            try:
                opportunities = self.scrape_government_site(site)
                results['sites_scraped'] += 1
                results['opportunities_found'] += len(opportunities)
                
                saved_count = 0
                for opp in opportunities:
                    if self.save_opportunity(opp):
                        saved_count += 1
                
                results['opportunities_saved'] += saved_count
                
            except Exception as e:
                error_msg = f"Failed to scrape {site['name']}: {e}"
                self.logger.error(f"   ❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = duration
        
        self.logger.info(f"\n📊 GOVERNMENT SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"   🏛️  Sites Scraped: {results['sites_scraped']}")
        self.logger.info(f"   🔍 Opportunities Found: {results['opportunities_found']}")
        self.logger.info(f"   💾 Opportunities Saved: {results['opportunities_saved']}")
        
        if results['errors']:
            self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
        
        return results

def start_automated_government_scraping():
    """Start automated 2-hour government scraping cycles"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = GovernmentSiteScraper(db_path)
    
    print("🤖 FIRECRAWL GOVERNMENT PROCUREMENT SCRAPER")
    print("=" * 45)
    print("🎯 Targeting: Government Procurement Portals")
    print("🔍 Focus: Technology & Infrastructure Opportunities")
    print("⏰ Frequency: Every 2 hours")
    
    # Schedule every 2 hours
    schedule.every(2).hours.do(scraper.run_government_scraping_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial government scraping cycle...")
    scraper.run_government_scraping_cycle()
    
    print(f"\n✅ Automated government scraping started!")
    print("🔄 Next cycle in 2 hours")
    print("📝 Logs: /tmp/firecrawl_gov.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated government scraping stopped.")

def run_immediate_government_cycle():
    """Run immediate government scraping cycle for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = GovernmentSiteScraper(db_path)
    
    results = scraper.run_government_scraping_cycle()
    print(f"\n✅ Immediate government cycle complete!")
    print(f"🎯 Found {results['opportunities_found']} opportunities")
    print(f"💾 Saved {results['opportunities_saved']} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_government_cycle()
    else:
        start_automated_government_scraping()
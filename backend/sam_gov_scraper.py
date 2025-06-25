#!/usr/bin/env python3
"""
SAM.gov API Scraper - FREE Government Data
Official US Government API for federal contract opportunities
Rate Limit: 1,000 requests/hour (FREE)
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
        logging.FileHandler('/tmp/sam_gov.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

@dataclass
class SamOpportunity:
    """SAM.gov opportunity data structure"""
    notice_id: str
    title: str
    description: str
    organization: str
    posted_date: Optional[str]
    response_date: Optional[str]
    naics_code: Optional[str]
    classification_code: Optional[str]
    award_amount: Optional[str]
    award_number: Optional[str]
    opportunity_category: str
    source_url: str
    contact_info: Optional[str]
    duplicate_hash: str

class SamGovScraper:
    """Official SAM.gov API scraper for federal opportunities"""
    
    def __init__(self, db_path: str):
        self.api_key = os.getenv('SAM_GOV_API_KEY')
        # SAM.gov API is free but requires registration
        if not self.api_key:
            self.logger = logging.getLogger(__name__)
            self.logger.warning("SAM_GOV_API_KEY not found - will try public endpoints")
        
        self.base_url = "https://api.sam.gov"
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Target NAICS codes for Data Centers and IT
        self.target_naics = [
            '518210',  # Data Processing, Hosting Services
            '541511',  # Custom Computer Programming Services
            '541512',  # Computer Systems Design Services
            '541513',  # Computer Facilities Management Services
            '541519',  # Other Computer Related Services
            '518111',  # Internet Service Providers
            '518112',  # Web Search Portals
            '541330',  # Engineering Services
            '237130',  # Power and Communication Line Construction
            '238210',  # Electrical Contractors
        ]
        
        # Request headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'OpportunityDashboard/1.0'
        }
        
        if self.api_key:
            self.headers['X-Api-Key'] = self.api_key
    
    def search_opportunities(self, days_back: int = 30) -> List[SamOpportunity]:
        """Search for recent opportunities using SAM.gov API"""
        self.logger.info(f"🏛️ Searching SAM.gov for opportunities (last {days_back} days)...")
        
        opportunities = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format dates for API
        start_date_str = start_date.strftime('%m/%d/%Y')
        end_date_str = end_date.strftime('%m/%d/%Y')
        
        try:
            # Use the opportunities endpoint
            endpoint = f"{self.base_url}/opportunities/v2/search"
            
            # Search parameters
            params = {
                'limit': 1000,  # Maximum allowed
                'postedFrom': start_date_str,
                'postedTo': end_date_str,
                'ptype': 'o',  # Opportunities
                'typeOfSetAsideDescription': '',
                'typeOfSetAside': '',
            }
            
            # Add NAICS codes to search
            for naics in self.target_naics:
                params['ncode'] = naics
                
                self.logger.info(f"   🔍 Searching NAICS {naics}...")
                
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'opportunitiesData' in data:
                        raw_opportunities = data['opportunitiesData']
                        self.logger.info(f"   📄 Found {len(raw_opportunities)} raw opportunities for NAICS {naics}")
                        
                        for raw_opp in raw_opportunities:
                            processed_opp = self._process_sam_opportunity(raw_opp)
                            if processed_opp:
                                opportunities.append(processed_opp)
                    
                elif response.status_code == 429:
                    self.logger.warning(f"   ⏰ Rate limited - waiting 60 seconds...")
                    time.sleep(60)
                    continue
                    
                else:
                    self.logger.error(f"   ❌ API error {response.status_code}: {response.text[:200]}")
                
                # Rate limiting - 1000 requests/hour = ~1 request/3.6 seconds
                time.sleep(4)
            
            # Try general search without NAICS filtering
            self._search_general_opportunities(params, opportunities)
            
        except Exception as e:
            self.logger.error(f"❌ Error searching SAM.gov opportunities: {e}")
        
        self.logger.info(f"   ✅ Total processed opportunities: {len(opportunities)}")
        return opportunities
    
    def _search_general_opportunities(self, base_params: Dict, opportunities: List[SamOpportunity]):
        """Search for general tech opportunities using keywords"""
        tech_keywords = [
            'data center', 'datacenter', 'cloud', 'infrastructure',
            'information technology', 'software', 'network', 'cybersecurity'
        ]
        
        for keyword in tech_keywords:
            try:
                params = base_params.copy()
                params['q'] = keyword
                params.pop('ncode', None)  # Remove NAICS filter
                
                self.logger.info(f"   🔍 Searching keyword: '{keyword}'...")
                
                endpoint = f"{self.base_url}/opportunities/v2/search"
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'opportunitiesData' in data:
                        raw_opportunities = data['opportunitiesData']
                        
                        for raw_opp in raw_opportunities:
                            processed_opp = self._process_sam_opportunity(raw_opp)
                            if processed_opp and not self._is_duplicate_opportunity(processed_opp, opportunities):
                                opportunities.append(processed_opp)
                
                # Rate limiting
                time.sleep(4)
                
            except Exception as e:
                self.logger.error(f"   ⚠️  Error searching keyword '{keyword}': {e}")
    
    def _process_sam_opportunity(self, raw_opp: Dict[str, Any]) -> Optional[SamOpportunity]:
        """Process raw SAM.gov opportunity data"""
        try:
            # Extract basic fields
            notice_id = raw_opp.get('noticeId', '')
            title = raw_opp.get('title', '').strip()
            description = raw_opp.get('description', '').strip()
            organization = raw_opp.get('organizationName', 'Unknown Agency').strip()
            
            if not title or len(title) < 10:
                return None
            
            # Dates
            posted_date = raw_opp.get('postedDate', '')
            response_date = raw_opp.get('responseDate', '')
            
            # Classification
            naics_code = raw_opp.get('naicsCode', '')
            classification_code = raw_opp.get('classificationCode', '')
            
            # Award information
            award_amount = raw_opp.get('awardAmount', '')
            award_number = raw_opp.get('awardNumber', '')
            
            # Contact info
            primary_contact = raw_opp.get('primaryContact', {})
            contact_info = self._format_contact_info(primary_contact)
            
            # Opportunity category
            opportunity_category = raw_opp.get('typeOfOpportunity', 'federal_opportunity')
            
            # Source URL
            source_url = f"https://sam.gov/opp/{notice_id}" if notice_id else "https://sam.gov"
            
            # Generate duplicate hash
            hash_input = f"{title}{organization}{notice_id}"
            duplicate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            # Create opportunity object
            opportunity = SamOpportunity(
                notice_id=notice_id,
                title=title[:500],
                description=description[:2000],
                organization=organization,
                posted_date=posted_date,
                response_date=response_date,
                naics_code=naics_code,
                classification_code=classification_code,
                award_amount=award_amount,
                award_number=award_number,
                opportunity_category=opportunity_category,
                source_url=source_url,
                contact_info=contact_info,
                duplicate_hash=duplicate_hash
            )
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error processing opportunity: {e}")
            return None
    
    def _format_contact_info(self, contact: Dict[str, Any]) -> Optional[str]:
        """Format contact information from SAM.gov data"""
        try:
            if not contact:
                return None
            
            parts = []
            
            # Name
            full_name = contact.get('fullName', '')
            if full_name:
                parts.append(f"Contact: {full_name}")
            
            # Email
            email = contact.get('email', '')
            if email:
                parts.append(f"Email: {email}")
            
            # Phone
            phone = contact.get('phone', '')
            if phone:
                parts.append(f"Phone: {phone}")
            
            return ' | '.join(parts) if parts else None
            
        except:
            return None
    
    def _is_duplicate_opportunity(self, new_opp: SamOpportunity, existing_opps: List[SamOpportunity]) -> bool:
        """Check if opportunity is duplicate in current batch"""
        return any(existing.duplicate_hash == new_opp.duplicate_hash for existing in existing_opps)
    
    def _is_duplicate_in_db(self, duplicate_hash: str) -> bool:
        """Check if opportunity already exists in database"""
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
    
    def save_opportunity(self, opp: SamOpportunity) -> bool:
        """Save SAM.gov opportunity to database"""
        try:
            # Check for duplicates
            if self._is_duplicate_in_db(opp.duplicate_hash):
                self.logger.debug(f"   ⏭️  Skipping duplicate: {opp.title[:50]}...")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract estimated value
            estimated_value = self._extract_numeric_value(opp.award_amount)
            
            # Calculate scores
            relevance_score = self._calculate_relevance_score(opp)
            urgency_score = self._calculate_urgency_score(opp)
            value_score = self._calculate_value_score(estimated_value)
            competition_score = 70  # Default for government contracts
            total_score = relevance_score + urgency_score + value_score + competition_score
            
            now = datetime.now().isoformat()
            
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
                opp.title, opp.description, opp.organization, opp.notice_id,
                estimated_value, opp.posted_date, opp.response_date, 'sam_gov_api',
                'SAM.gov API', opp.source_url, None, opp.contact_info,
                relevance_score, urgency_score, value_score, competition_score, total_score,
                now, now, self._classify_industry(opp), 0.95, now
            ))
            
            opportunity_id = cursor.lastrowid
            
            # Record hash for duplicate detection
            cursor.execute("""
                INSERT OR IGNORE INTO opportunity_hashes (duplicate_hash, created_at)
                VALUES (?, ?)
            """, (opp.duplicate_hash, now))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"   ✅ Saved: {opp.title[:50]}... (ID: {opportunity_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save opportunity: {e}")
            return False
    
    def _extract_numeric_value(self, value_text: Optional[str]) -> Optional[float]:
        """Extract numeric value from award amount text"""
        if not value_text:
            return None
        
        try:
            import re
            # Remove currency symbols and commas
            clean_text = re.sub(r'[^\d\.]', '', str(value_text))
            if clean_text:
                return float(clean_text)
        except:
            pass
        
        return None
    
    def _calculate_relevance_score(self, opp: SamOpportunity) -> int:
        """Calculate relevance score based on content"""
        score = 60  # Base score for SAM.gov opportunities
        
        text = f"{opp.title} {opp.description}".lower()
        
        # Data center keywords
        dc_keywords = ['data center', 'datacenter', 'cloud', 'hosting', 'infrastructure']
        if any(keyword in text for keyword in dc_keywords):
            score += 15
        
        # IT keywords
        it_keywords = ['software', 'network', 'cybersecurity', 'information technology']
        if any(keyword in text for keyword in it_keywords):
            score += 10
        
        # High-value indicators
        value_keywords = ['enterprise', 'mission critical', 'scalable']
        if any(keyword in text for keyword in value_keywords):
            score += 5
        
        return min(score, 100)
    
    def _calculate_urgency_score(self, opp: SamOpportunity) -> int:
        """Calculate urgency score based on dates"""
        try:
            if opp.response_date:
                response_date = datetime.fromisoformat(opp.response_date.replace('Z', '+00:00'))
                days_remaining = (response_date - datetime.now()).days
                
                if days_remaining <= 7:
                    return 90
                elif days_remaining <= 30:
                    return 70
                elif days_remaining <= 60:
                    return 50
                else:
                    return 30
        except:
            pass
        
        return 50  # Default
    
    def _calculate_value_score(self, estimated_value: Optional[float]) -> int:
        """Calculate value score based on contract size"""
        if not estimated_value:
            return 50
        
        if estimated_value >= 10_000_000:  # $10M+
            return 90
        elif estimated_value >= 1_000_000:  # $1M+
            return 80
        elif estimated_value >= 100_000:   # $100K+
            return 70
        elif estimated_value >= 10_000:    # $10K+
            return 60
        else:
            return 40
    
    def _classify_industry(self, opp: SamOpportunity) -> str:
        """Classify opportunity by industry based on NAICS and content"""
        # Check NAICS code first
        if opp.naics_code:
            if opp.naics_code.startswith('518'):  # Data/hosting services
                return 'data_center'
            elif opp.naics_code.startswith('541'):  # Computer services
                return 'information_technology'
        
        # Check content
        text = f"{opp.title} {opp.description}".lower()
        if any(keyword in text for keyword in ['data center', 'datacenter', 'hosting']):
            return 'data_center'
        elif any(keyword in text for keyword in ['software', 'application', 'cybersecurity']):
            return 'information_technology'
        else:
            return 'government_technology'
    
    def run_sam_scraping_cycle(self) -> Dict[str, Any]:
        """Run complete SAM.gov scraping cycle"""
        cycle_start = datetime.now()
        self.logger.info("🚀 Starting SAM.gov API Scraping Cycle")
        self.logger.info("=" * 45)
        
        results = {
            'opportunities_found': 0,
            'opportunities_saved': 0,
            'cycle_start': cycle_start.isoformat(),
            'errors': []
        }
        
        try:
            # Search for opportunities
            opportunities = self.search_opportunities(days_back=7)  # Last week
            results['opportunities_found'] = len(opportunities)
            
            # Save opportunities
            saved_count = 0
            for opp in opportunities:
                if self.save_opportunity(opp):
                    saved_count += 1
            
            results['opportunities_saved'] = saved_count
            
        except Exception as e:
            error_msg = f"SAM.gov scraping cycle failed: {e}"
            self.logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = duration
        
        self.logger.info(f"\n📊 SAM.GOV SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"   🔍 Opportunities Found: {results['opportunities_found']}")
        self.logger.info(f"   💾 Opportunities Saved: {results['opportunities_saved']}")
        
        if results['errors']:
            self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
        
        return results

def start_automated_sam_scraping():
    """Start automated SAM.gov scraping"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = SamGovScraper(db_path)
    
    print("🤖 SAM.GOV API SCRAPER")
    print("=" * 30)
    print("🎯 Source: Official US Government API")
    print("🆓 Cost: 100% FREE (1,000 requests/hour)")
    print("📊 Focus: Federal Contract Opportunities")
    print("⏰ Frequency: Every 4 hours")
    
    # Schedule every 4 hours (conservative for rate limits)
    schedule.every(4).hours.do(scraper.run_sam_scraping_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial SAM.gov cycle...")
    scraper.run_sam_scraping_cycle()
    
    print(f"\n✅ Automated SAM.gov scraping started!")
    print("🔄 Next cycle in 4 hours")
    print("📝 Logs: /tmp/sam_gov.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated SAM.gov scraping stopped.")

def run_immediate_sam_cycle():
    """Run immediate SAM.gov scraping cycle"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = SamGovScraper(db_path)
    
    results = scraper.run_sam_scraping_cycle()
    print(f"\n✅ Immediate SAM.gov cycle complete!")
    print(f"🎯 Found {results['opportunities_found']} opportunities")
    print(f"💾 Saved {results['opportunities_saved']} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_sam_cycle()
    else:
        start_automated_sam_scraping()
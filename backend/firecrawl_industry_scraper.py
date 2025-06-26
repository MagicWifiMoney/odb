#!/usr/bin/env python3
"""
Optimized Firecrawl Industry Scraper - Data Centers & IT Focus
High-frequency scraping with duplicate detection and comprehensive timestamping
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
        logging.FileHandler('/tmp/firecrawl_industry.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

@dataclass
class IndustryOpportunity:
    """Enhanced opportunity data structure for industry-specific data"""
    title: str
    description: str
    organization: str
    opportunity_id: str
    estimated_value: Optional[float]
    posted_date: Optional[str]
    due_date: Optional[str]
    industry_category: str
    source_name: str
    source_url: str
    location: Optional[str]
    contact_info: Optional[str]
    technical_requirements: Optional[str]
    compliance_requirements: Optional[str]
    project_scope: Optional[str]
    duplicate_hash: str
    source_reliability_score: float
    relevance_score: float

class DuplicateDetector:
    """Advanced duplicate detection using content hashing"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_hash_table()
    
    def _ensure_hash_table(self):
        """Ensure duplicate hash tracking table exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunity_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    duplicate_hash TEXT UNIQUE,
                    opportunity_id INTEGER,
                    created_at DATETIME,
                    last_seen_at DATETIME
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to create hash table: {e}")
    
    def generate_hash(self, title: str, organization: str, description: str) -> str:
        """Generate unique hash for opportunity"""
        # Normalize text for better duplicate detection
        normalized_title = title.lower().strip()
        normalized_org = organization.lower().strip()
        normalized_desc = description[:500].lower().strip()  # First 500 chars
        
        # Create composite string
        composite = f"{normalized_title}|{normalized_org}|{normalized_desc}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(composite.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, duplicate_hash: str) -> bool:
        """Check if opportunity is a duplicate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM opportunity_hashes WHERE duplicate_hash = ?",
                (duplicate_hash,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logging.error(f"Duplicate check failed: {e}")
            return False
    
    def record_hash(self, duplicate_hash: str, opportunity_id: int):
        """Record hash for future duplicate detection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO opportunity_hashes 
                (duplicate_hash, opportunity_id, created_at, last_seen_at)
                VALUES (?, ?, ?, ?)
            """, (duplicate_hash, opportunity_id, now, now))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to record hash: {e}")

class IndustryClassifier:
    """Classify and score opportunities by industry relevance"""
    
    def __init__(self):
        self.data_center_keywords = [
            'data center', 'datacenter', 'colocation', 'colo', 'hyperscale',
            'edge computing', 'cloud infrastructure', 'server farm', 'hosting',
            'rack space', 'cooling system', 'ups', 'generator', 'fiber optic',
            'network infrastructure', 'bandwidth', 'connectivity', 'peering'
        ]
        
        self.it_keywords = [
            'information technology', 'software development', 'cloud services',
            'cybersecurity', 'network security', 'database', 'application',
            'system integration', 'digital transformation', 'automation',
            'artificial intelligence', 'machine learning', 'analytics',
            'enterprise software', 'saas', 'platform', 'api', 'microservices'
        ]
    
    def classify_industry(self, title: str, description: str) -> str:
        """Classify opportunity into industry category"""
        text = f"{title} {description}".lower()
        
        dc_score = sum(1 for keyword in self.data_center_keywords if keyword in text)
        it_score = sum(1 for keyword in self.it_keywords if keyword in text)
        
        if dc_score > it_score and dc_score > 0:
            return 'data_center'
        elif it_score > 0:
            return 'information_technology'
        else:
            return 'general_technology'
    
    def calculate_relevance_score(self, title: str, description: str, industry: str) -> float:
        """Calculate relevance score 0-100"""
        text = f"{title} {description}".lower()
        
        # Base score
        score = 50.0
        
        # Industry-specific keyword matching
        keywords = self.data_center_keywords if industry == 'data_center' else self.it_keywords
        keyword_matches = sum(1 for keyword in keywords if keyword in text)
        score += min(keyword_matches * 5, 30)  # Max 30 points for keywords
        
        # Value indicators
        value_keywords = ['million', 'billion', '$', 'budget', 'contract value']
        if any(keyword in text for keyword in value_keywords):
            score += 10
        
        # Urgency indicators
        urgency_keywords = ['urgent', 'immediate', 'asap', 'rush', 'priority']
        if any(keyword in text for keyword in urgency_keywords):
            score += 5
        
        # Quality indicators
        quality_keywords = ['enterprise', 'mission critical', 'scalable', 'robust']
        if any(keyword in text for keyword in quality_keywords):
            score += 5
        
        return min(score, 100.0)

class ValueEstimator:
    """Extract and estimate contract values from text"""
    
    def __init__(self):
        import re
        self.value_pattern = re.compile(
            r'[\$]([0-9,\.]+)\s*(million|billion|m|b|k|thousand)?',
            re.IGNORECASE
        )
        self.range_pattern = re.compile(
            r'[\$]([0-9,\.]+)\s*(?:to|-)?\s*[\$]?([0-9,\.]+)\s*(million|billion|m|b|k|thousand)?',
            re.IGNORECASE
        )
    
    def extract_value(self, text: str) -> Optional[float]:
        """Extract estimated contract value from text"""
        try:
            # Look for range first
            range_match = self.range_pattern.search(text)
            if range_match:
                low = float(range_match.group(1).replace(',', ''))
                high = float(range_match.group(2).replace(',', ''))
                multiplier = self._get_multiplier(range_match.group(3))
                return ((low + high) / 2) * multiplier
            
            # Look for single value
            value_match = self.value_pattern.search(text)
            if value_match:
                amount = float(value_match.group(1).replace(',', ''))
                multiplier = self._get_multiplier(value_match.group(2))
                return amount * multiplier
            
            return None
            
        except Exception:
            return None
    
    def _get_multiplier(self, unit: Optional[str]) -> float:
        """Get numeric multiplier for unit"""
        if not unit:
            return 1.0
        
        unit = unit.lower()
        if unit in ['billion', 'b']:
            return 1_000_000_000
        elif unit in ['million', 'm']:
            return 1_000_000
        elif unit in ['thousand', 'k']:
            return 1_000
        else:
            return 1.0

class FirecrawlIndustryScraper:
    """Optimized Firecrawl scraper for Data Center and IT industries"""
    
    def __init__(self, db_path: str):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment")
        
        self.base_url = "https://api.firecrawl.dev/v0"
        self.db_path = db_path
        
        # Initialize components
        self.duplicate_detector = DuplicateDetector(db_path)
        self.industry_classifier = IndustryClassifier()
        self.value_estimator = ValueEstimator()
        
        # Industry-specific targets
        self.target_sites = {
            'data_center': [
                {
                    'name': 'Uptime Institute',
                    'url': 'https://uptimeinstitute.com/about-ui/press-releases',
                    'reliability': 0.9
                },
                {
                    'name': 'Data Center Knowledge',
                    'url': 'https://www.datacenterknowledge.com/industry',
                    'reliability': 0.85
                },
                {
                    'name': 'DCD (DatacenterDynamics)',
                    'url': 'https://www.datacenterdynamics.com/en/news/',
                    'reliability': 0.9
                }
            ],
            'information_technology': [
                {
                    'name': 'Federal News Network',
                    'url': 'https://federalnewsnetwork.com/category/technology/',
                    'reliability': 0.8
                },
                {
                    'name': 'FCW (Federal Computer Week)',
                    'url': 'https://fcw.com/procurement',
                    'reliability': 0.85
                },
                {
                    'name': 'Government Technology',
                    'url': 'https://www.govtech.com/procurement/',
                    'reliability': 0.8
                }
            ]
        }
        
        self.logger = logging.getLogger(__name__)
    
    def scrape_site(self, site_config: Dict[str, Any]) -> List[IndustryOpportunity]:
        """Scrape a single site for opportunities"""
        self.logger.info(f"🔍 Scraping {site_config['name']}...")
        
        opportunities = []
        
        # Industry-specific extraction schema
        extract_schema = {
            "type": "object",
            "properties": {
                "opportunities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "organization": {"type": "string"},
                            "posted_date": {"type": "string"},
                            "due_date": {"type": "string"},
                            "estimated_value": {"type": "string"},
                            "location": {"type": "string"},
                            "contact_info": {"type": "string"},
                            "technical_requirements": {"type": "string"},
                            "project_scope": {"type": "string"},
                            "link": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        payload = {
            'url': site_config['url'],
            'formats': ['extract'],
            'extract': {'schema': extract_schema},
            'waitFor': 3000,
            'timeout': 45000
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'extract' in data['data']:
                    raw_opportunities = data['data']['extract'].get('opportunities', [])
                    
                    for raw_opp in raw_opportunities:
                        processed_opp = self._process_opportunity(raw_opp, site_config)
                        if processed_opp:
                            opportunities.append(processed_opp)
                    
                    self.logger.info(f"   ✅ Found {len(opportunities)} opportunities from {site_config['name']}")
                else:
                    self.logger.warning(f"   ⚠️  No data extracted from {site_config['name']}")
            else:
                self.logger.error(f"   ❌ Failed to scrape {site_config['name']}: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"   ❌ Error scraping {site_config['name']}: {e}")
        
        # Rate limiting
        time.sleep(2)
        
        return opportunities
    
    def _process_opportunity(self, raw_opp: Dict[str, Any], site_config: Dict[str, Any]) -> Optional[IndustryOpportunity]:
        """Process raw opportunity data into structured format"""
        try:
            title = raw_opp.get('title', '').strip()
            description = raw_opp.get('description', '').strip()
            organization = raw_opp.get('organization', site_config['name']).strip()
            
            if not title or len(title) < 10:  # Skip low-quality entries
                return None
            
            # Generate duplicate hash
            duplicate_hash = self.duplicate_detector.generate_hash(title, organization, description)
            
            # Check for duplicates
            if self.duplicate_detector.is_duplicate(duplicate_hash):
                self.logger.debug(f"   ⏭️  Skipping duplicate: {title[:50]}...")
                return None
            
            # Classify industry
            industry_category = self.industry_classifier.classify_industry(title, description)
            
            # Calculate relevance score
            relevance_score = self.industry_classifier.calculate_relevance_score(title, description, industry_category)
            
            # Skip low-relevance opportunities
            if relevance_score < 60:
                return None
            
            # Extract estimated value
            value_text = f"{title} {description} {raw_opp.get('estimated_value', '')}"
            estimated_value = self.value_estimator.extract_value(value_text)
            
            # Create opportunity object
            opportunity = IndustryOpportunity(
                title=title[:500],
                description=description[:2000],
                organization=organization,
                opportunity_id=f"FC-{site_config['name'][:3].upper()}-{hash(duplicate_hash) % 100000}",
                estimated_value=estimated_value,
                posted_date=raw_opp.get('posted_date'),
                due_date=raw_opp.get('due_date'),
                industry_category=industry_category,
                source_name=f"Firecrawl-{site_config['name']}",
                source_url=raw_opp.get('link', site_config['url']),
                location=raw_opp.get('location'),
                contact_info=raw_opp.get('contact_info'),
                technical_requirements=raw_opp.get('technical_requirements'),
                compliance_requirements=None,
                project_scope=raw_opp.get('project_scope'),
                duplicate_hash=duplicate_hash,
                source_reliability_score=site_config['reliability'],
                relevance_score=relevance_score
            )
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Failed to process opportunity: {e}")
            return None
    
    def save_opportunity(self, opp: IndustryOpportunity) -> bool:
        """Save opportunity to database with enhanced schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced table schema
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
            
            now = datetime.now().isoformat()
            
            # Insert opportunity
            cursor.execute("""
                INSERT INTO opportunities (
                    title, description, agency_name, opportunity_number, estimated_value,
                    posted_date, due_date, source_type, source_name, source_url,
                    location, contact_info, relevance_score, urgency_score,
                    value_score, competition_score, total_score, created_at, updated_at,
                    industry_category, source_reliability_score, technical_requirements,
                    project_scope, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp.title, opp.description, opp.organization, opp.opportunity_id,
                opp.estimated_value, opp.posted_date, opp.due_date, 'industry_scrape',
                opp.source_name, opp.source_url, opp.location, opp.contact_info,
                int(opp.relevance_score), 70, 75, 65, int(opp.relevance_score * 0.8),
                now, now, opp.industry_category, opp.source_reliability_score,
                opp.technical_requirements, opp.project_scope, now
            ))
            
            opportunity_id = cursor.lastrowid
            
            # Record hash for duplicate detection
            self.duplicate_detector.record_hash(opp.duplicate_hash, opportunity_id)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"   ✅ Saved: {opp.title[:50]}... (ID: {opportunity_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save opportunity: {e}")
            return False
    
    def run_scraping_cycle(self) -> Dict[str, Any]:
        """Run complete scraping cycle for all target sites"""
        cycle_start = datetime.now()
        self.logger.info("🚀 Starting Firecrawl Industry Scraping Cycle")
        self.logger.info("=" * 50)
        
        results = {
            'data_center': 0,
            'information_technology': 0,
            'total_processed': 0,
            'total_saved': 0,
            'cycle_start': cycle_start.isoformat(),
            'errors': []
        }
        
        # Scrape all target sites
        for industry, sites in self.target_sites.items():
            self.logger.info(f"\n📊 Scraping {industry.replace('_', ' ').title()} Sites...")
            
            for site_config in sites:
                try:
                    opportunities = self.scrape_site(site_config)
                    saved_count = 0
                    
                    for opp in opportunities:
                        if self.save_opportunity(opp):
                            saved_count += 1
                            results[industry] += 1
                    
                    results['total_processed'] += len(opportunities)
                    results['total_saved'] += saved_count
                    
                except Exception as e:
                    error_msg = f"Failed to scrape {site_config['name']}: {e}"
                    self.logger.error(f"   ❌ {error_msg}")
                    results['errors'].append(error_msg)
        
        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = duration
        
        self.logger.info(f"\n📊 SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"   📊 Data Centers: {results['data_center']} new opportunities")
        self.logger.info(f"   💻 IT: {results['information_technology']} new opportunities")
        self.logger.info(f"   🎯 Total Saved: {results['total_saved']} opportunities")
        
        if results['errors']:
            self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
        
        return results

def start_automated_industry_scraping():
    """Start automated 2-hour scraping cycles"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = FirecrawlIndustryScraper(db_path)
    
    print("🤖 FIRECRAWL INDUSTRY SCRAPER - 2-HOUR CYCLES")
    print("=" * 50)
    print("🎯 Targeting: Data Centers + Information Technology")
    print("⏰ Frequency: Every 2 hours")
    print("🔍 Features: Duplicate detection, timestamping, relevance scoring")
    
    # Schedule every 2 hours
    schedule.every(2).hours.do(scraper.run_scraping_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial scraping cycle...")
    scraper.run_scraping_cycle()
    
    print(f"\n✅ Automated scraping started!")
    print("🔄 Next cycle in 2 hours")
    print("📝 Logs: /tmp/firecrawl_industry.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n🛑 Automated scraping stopped.")

def run_immediate_cycle():
    """Run immediate scraping cycle for testing"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = FirecrawlIndustryScraper(db_path)
    
    results = scraper.run_scraping_cycle()
    print(f"\n✅ Immediate cycle complete!")
    print(f"🎯 Saved {results['total_saved']} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_cycle()
    else:
        start_automated_industry_scraping()
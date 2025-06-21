#!/usr/bin/env python3
"""
Opportunity Dashboard - Scale to 10,000+ Opportunities
Automated data sync from multiple government sources
"""

import os
import sys
import json
import time
import requests
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OpportunityData:
    """Standardized opportunity data structure"""
    title: str
    description: str
    agency_name: str
    opportunity_number: Optional[str]
    estimated_value: Optional[float]
    posted_date: Optional[datetime]
    due_date: Optional[datetime]
    source_type: str
    source_name: str
    source_url: Optional[str]
    location: Optional[str]
    contact_info: Optional[str]
    keywords: Optional[List[str]]
    external_id: str

class DatabaseManager:
    """Handles database operations for opportunity scaling"""
    
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def create_performance_indexes(self):
        """Create indexes for optimal performance with large datasets"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_opportunities_due_date ON opportunities(due_date) WHERE due_date IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_value ON opportunities(estimated_value) WHERE estimated_value IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_agency ON opportunities(agency_name) WHERE agency_name IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_type, source_name);",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_posted ON opportunities(posted_date) WHERE posted_date IS NOT NULL;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_active ON opportunities(due_date) WHERE due_date >= CURRENT_DATE;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_high_value ON opportunities(estimated_value) WHERE estimated_value >= 100000;",
            "CREATE INDEX IF NOT EXISTS idx_opportunities_search ON opportunities USING GIN(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(agency_name, '')));"
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for index_sql in indexes:
                    try:
                        cur.execute(index_sql)
                        logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        logger.warning(f"Index creation warning: {e}")
                conn.commit()
    
    def bulk_insert_opportunities(self, opportunities: List[OpportunityData]) -> int:
        """Bulk insert opportunities with conflict handling"""
        if not opportunities:
            return 0
        
        insert_sql = """
        INSERT INTO opportunities (
            external_id, title, description, agency_name, opportunity_number,
            estimated_value, posted_date, due_date, source_type, source_name,
            source_url, location, contact_info, keywords, created_at, updated_at
        ) VALUES %s
        ON CONFLICT (external_id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            agency_name = EXCLUDED.agency_name,
            estimated_value = EXCLUDED.estimated_value,
            due_date = EXCLUDED.due_date,
            updated_at = CURRENT_TIMESTAMP
        """
        
        # Prepare data for bulk insert
        values = []
        for opp in opportunities:
            values.append((
                opp.external_id,
                opp.title[:500] if opp.title else None,  # Truncate to fit VARCHAR(500)
                opp.description,
                opp.agency_name[:200] if opp.agency_name else None,
                opp.opportunity_number,
                opp.estimated_value,
                opp.posted_date,
                opp.due_date,
                opp.source_type,
                opp.source_name,
                opp.source_url,
                opp.location,
                opp.contact_info,
                json.dumps(opp.keywords) if opp.keywords else None,
                datetime.now(),
                datetime.now()
            ))
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    from psycopg2.extras import execute_values
                    execute_values(
                        cur, insert_sql, values,
                        template=None, page_size=1000
                    )
                    conn.commit()
                    logger.info(f"Successfully inserted/updated {len(opportunities)} opportunities")
                    return len(opportunities)
                except Exception as e:
                    logger.error(f"Bulk insert error: {e}")
                    conn.rollback()
                    return 0
    
    def get_opportunity_count(self) -> int:
        """Get total opportunity count"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM opportunities")
                result = cur.fetchone()
                return result[0] if result else 0
    
    def cleanup_old_opportunities(self, days_old: int = 365):
        """Clean up very old opportunities to maintain performance"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM opportunities 
                    WHERE created_at < %s 
                    AND (due_date IS NULL OR due_date < %s)
                """, (
                    datetime.now() - timedelta(days=days_old),
                    datetime.now() - timedelta(days=30)  # Keep if due within 30 days
                ))
                deleted_count = cur.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old opportunities")

class SAMGovScraper:
    """Scraper for SAM.gov opportunities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SAM_GOV_API_KEY')
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'X-Api-Key': self.api_key})
    
    def fetch_opportunities(self, limit: int = 1000, days_back: int = 30) -> List[OpportunityData]:
        """Fetch opportunities from SAM.gov"""
        opportunities = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'limit': min(limit, 1000),  # API limit per request
            'offset': 0,
            'postedFrom': start_date.strftime('%m/%d/%Y'),
            'postedTo': end_date.strftime('%m/%d/%Y'),
            'ptype': 'o',  # Opportunities
            'stype': 'o'   # Open opportunities
        }
        
        try:
            logger.info(f"Fetching SAM.gov opportunities from {start_date.date()} to {end_date.date()}")
            
            while len(opportunities) < limit:
                response = self.session.get(self.base_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'opportunitiesData' not in data or not data['opportunitiesData']:
                        logger.info("No more SAM.gov opportunities found")
                        break
                    
                    for item in data['opportunitiesData']:
                        try:
                            opp = self._parse_sam_opportunity(item)
                            if opp:
                                opportunities.append(opp)
                        except Exception as e:
                            logger.warning(f"Error parsing SAM opportunity: {e}")
                    
                    # Check if we have more pages
                    if len(data['opportunitiesData']) < params['limit']:
                        break
                    
                    params['offset'] += params['limit']
                    time.sleep(0.1)  # Rate limiting
                    
                else:
                    logger.error(f"SAM.gov API error: {response.status_code}")
                    break
                    
        except Exception as e:
            logger.error(f"SAM.gov fetch error: {e}")
        
        logger.info(f"Fetched {len(opportunities)} opportunities from SAM.gov")
        return opportunities[:limit]
    
    def _parse_sam_opportunity(self, item: Dict) -> Optional[OpportunityData]:
        """Parse SAM.gov opportunity data"""
        try:
            # Extract basic information
            title = item.get('title', '').strip()
            if not title:
                return None
            
            # Parse dates
            posted_date = None
            due_date = None
            
            if item.get('postedDate'):
                try:
                    posted_date = datetime.strptime(item['postedDate'], '%m/%d/%Y')
                except:
                    pass
            
            if item.get('responseDeadLine'):
                try:
                    due_date = datetime.strptime(item['responseDeadLine'], '%m/%d/%Y %H:%M:%S %Z')
                except:
                    try:
                        due_date = datetime.strptime(item['responseDeadLine'], '%m/%d/%Y')
                    except:
                        pass
            
            # Parse estimated value
            estimated_value = None
            if item.get('awardCeiling'):
                try:
                    estimated_value = float(item['awardCeiling'])
                except:
                    pass
            
            # Build opportunity
            return OpportunityData(
                external_id=f"sam_{item.get('noticeId', item.get('solicitationNumber', str(hash(title))))}",
                title=title,
                description=item.get('description', '').strip(),
                agency_name=item.get('fullParentPathName', '').strip() or item.get('departmentName', '').strip(),
                opportunity_number=item.get('solicitationNumber'),
                estimated_value=estimated_value,
                posted_date=posted_date,
                due_date=due_date,
                source_type='federal_contract',
                source_name='SAM.gov',
                source_url=item.get('uiLink'),
                location=item.get('placeOfPerformance', {}).get('fullName'),
                contact_info=item.get('pointOfContact', [{}])[0].get('email') if item.get('pointOfContact') else None,
                keywords=item.get('naicsCode', []) if isinstance(item.get('naicsCode'), list) else []
            )
            
        except Exception as e:
            logger.warning(f"Error parsing SAM opportunity: {e}")
            return None

class USASpendingScraper:
    """Scraper for USASpending.gov opportunities"""
    
    def __init__(self):
        self.base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award"
        self.session = requests.Session()
    
    def fetch_opportunities(self, limit: int = 1000) -> List[OpportunityData]:
        """Fetch contract opportunities from USASpending.gov"""
        opportunities = []
        
        payload = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],  # Contract types
                "time_period": [
                    {
                        "start_date": (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        "end_date": datetime.now().strftime('%Y-%m-%d')
                    }
                ]
            },
            "fields": [
                "Award ID", "Recipient Name", "Award Amount", "Award Date",
                "Description", "Awarding Agency", "Awarding Sub Agency",
                "Place of Performance State", "Period of Performance Start Date",
                "Period of Performance Current End Date"
            ],
            "page": 1,
            "limit": min(limit, 100),  # API limit per request
            "sort": "Award Amount",
            "order": "desc"
        }
        
        try:
            logger.info("Fetching USASpending.gov contract opportunities")
            
            page = 1
            while len(opportunities) < limit:
                payload["page"] = page
                
                response = self.session.post(self.base_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data.get('results'):
                        logger.info("No more USASpending opportunities found")
                        break
                    
                    for item in data['results']:
                        try:
                            opp = self._parse_usaspending_opportunity(item)
                            if opp:
                                opportunities.append(opp)
                        except Exception as e:
                            logger.warning(f"Error parsing USASpending opportunity: {e}")
                    
                    # Check if we have more pages
                    if len(data['results']) < payload['limit']:
                        break
                    
                    page += 1
                    time.sleep(0.2)  # Rate limiting
                    
                else:
                    logger.error(f"USASpending API error: {response.status_code}")
                    break
                    
        except Exception as e:
            logger.error(f"USASpending fetch error: {e}")
        
        logger.info(f"Fetched {len(opportunities)} opportunities from USASpending.gov")
        return opportunities[:limit]
    
    def _parse_usaspending_opportunity(self, item: Dict) -> Optional[OpportunityData]:
        """Parse USASpending.gov opportunity data"""
        try:
            # Extract basic information
            title = item.get('Description', '').strip()
            if not title or len(title) < 10:
                title = f"Contract Opportunity - {item.get('Recipient Name', 'Unknown')}"
            
            # Parse dates
            award_date = None
            due_date = None
            
            if item.get('Award Date'):
                try:
                    award_date = datetime.strptime(item['Award Date'], '%Y-%m-%d')
                except:
                    pass
            
            if item.get('Period of Performance Current End Date'):
                try:
                    due_date = datetime.strptime(item['Period of Performance Current End Date'], '%Y-%m-%d')
                except:
                    pass
            
            # Parse estimated value
            estimated_value = None
            if item.get('Award Amount'):
                try:
                    estimated_value = float(item['Award Amount'])
                except:
                    pass
            
            # Build opportunity
            return OpportunityData(
                external_id=f"usa_{item.get('Award ID', str(hash(title)))}",
                title=title,
                description=f"Contract opportunity with {item.get('Recipient Name', 'contractor')}. " + 
                           item.get('Description', ''),
                agency_name=item.get('Awarding Agency', '').strip(),
                opportunity_number=item.get('Award ID'),
                estimated_value=estimated_value,
                posted_date=award_date,
                due_date=due_date,
                source_type='federal_contract',
                source_name='USASpending.gov',
                source_url=f"https://www.usaspending.gov/award/{item.get('Award ID')}" if item.get('Award ID') else None,
                location=item.get('Place of Performance State'),
                contact_info=None,
                keywords=[]
            )
            
        except Exception as e:
            logger.warning(f"Error parsing USASpending opportunity: {e}")
            return None

class SyntheticDataGenerator:
    """Generate realistic synthetic opportunities for testing and demo"""
    
    def __init__(self):
        self.agencies = [
            "Department of Defense", "Department of Health and Human Services",
            "Department of Homeland Security", "Department of Veterans Affairs",
            "General Services Administration", "Department of Energy",
            "Department of Transportation", "Department of Education",
            "Environmental Protection Agency", "National Aeronautics and Space Administration",
            "Department of Agriculture", "Department of Commerce",
            "Department of Justice", "Department of Labor",
            "Small Business Administration", "Department of State"
        ]
        
        self.opportunity_types = [
            "IT Services and Solutions", "Construction and Infrastructure",
            "Professional Services", "Research and Development",
            "Medical Equipment and Supplies", "Security Services",
            "Environmental Services", "Training and Education",
            "Logistics and Transportation", "Telecommunications",
            "Energy and Utilities", "Food Services",
            "Maintenance and Repair", "Consulting Services"
        ]
        
        self.locations = [
            "Washington, DC", "Virginia", "Maryland", "California",
            "Texas", "New York", "Florida", "Illinois",
            "Pennsylvania", "Ohio", "Georgia", "North Carolina",
            "Michigan", "New Jersey", "Arizona", "Tennessee"
        ]
    
    def generate_opportunities(self, count: int = 5000) -> List[OpportunityData]:
        """Generate synthetic opportunities for testing"""
        import random
        
        opportunities = []
        
        logger.info(f"Generating {count} synthetic opportunities")
        
        for i in range(count):
            # Random opportunity details
            agency = random.choice(self.agencies)
            opp_type = random.choice(self.opportunity_types)
            location = random.choice(self.locations)
            
            # Random dates
            posted_date = datetime.now() - timedelta(days=random.randint(1, 90))
            due_date = posted_date + timedelta(days=random.randint(14, 120))
            
            # Random value
            value_ranges = [
                (10000, 100000),      # Small contracts
                (100000, 1000000),    # Medium contracts  
                (1000000, 10000000),  # Large contracts
                (10000000, 100000000) # Major contracts
            ]
            min_val, max_val = random.choice(value_ranges)
            estimated_value = random.randint(min_val, max_val)
            
            title = f"{opp_type} - {agency} - {random.randint(1000, 9999)}"
            
            opportunity = OpportunityData(
                external_id=f"synthetic_{i+1:06d}",
                title=title,
                description=f"Comprehensive {opp_type.lower()} opportunity for {agency}. "
                           f"This contract involves providing high-quality services and solutions "
                           f"to support mission-critical operations. Location: {location}. "
                           f"Estimated duration: {random.randint(12, 60)} months.",
                agency_name=agency,
                opportunity_number=f"SYN-{random.randint(100000, 999999)}",
                estimated_value=float(estimated_value),
                posted_date=posted_date,
                due_date=due_date,
                source_type='synthetic',
                source_name='Demo Data Generator',
                source_url=None,
                location=location,
                contact_info=f"contracting.{agency.lower().replace(' ', '').replace('department', 'dept')}@gov.demo",
                keywords=[opp_type.lower(), agency.lower(), location.lower()]
            )
            
            opportunities.append(opportunity)
        
        logger.info(f"Generated {len(opportunities)} synthetic opportunities")
        return opportunities

class OpportunityScaler:
    """Main class to orchestrate opportunity scaling"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.sam_scraper = SAMGovScraper()
        self.usa_scraper = USASpendingScraper()
        self.synthetic_generator = SyntheticDataGenerator()
    
    def scale_to_target(self, target_count: int = 10000):
        """Scale opportunities to target count"""
        logger.info(f"🚀 Starting opportunity scaling to {target_count:,} opportunities")
        
        # Get current count
        current_count = self.db.get_opportunity_count()
        logger.info(f"Current opportunities: {current_count:,}")
        
        if current_count >= target_count:
            logger.info(f"Already at target! Current: {current_count:,}, Target: {target_count:,}")
            return current_count
        
        needed = target_count - current_count
        logger.info(f"Need to add: {needed:,} opportunities")
        
        # Step 1: Create performance indexes
        logger.info("🔧 Creating performance indexes...")
        self.db.create_performance_indexes()
        
        # Step 2: Fetch real data from APIs (parallel execution)
        real_opportunities = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            # SAM.gov opportunities (up to 3000)
            if needed > 0:
                sam_limit = min(3000, needed // 2)
                futures.append(executor.submit(self.sam_scraper.fetch_opportunities, sam_limit))
            
            # USASpending opportunities (up to 2000)  
            if needed > 3000:
                usa_limit = min(2000, needed // 3)
                futures.append(executor.submit(self.usa_scraper.fetch_opportunities, usa_limit))
            
            # Collect results
            for future in as_completed(futures):
                try:
                    opportunities = future.result()
                    real_opportunities.extend(opportunities)
                    logger.info(f"Collected {len(opportunities)} opportunities from API")
                except Exception as e:
                    logger.error(f"API fetch error: {e}")
        
        # Step 3: Generate synthetic data to fill remaining gap
        total_real = len(real_opportunities)
        remaining_needed = needed - total_real
        
        if remaining_needed > 0:
            logger.info(f"Generating {remaining_needed:,} synthetic opportunities to reach target")
            synthetic_opportunities = self.synthetic_generator.generate_opportunities(remaining_needed)
            real_opportunities.extend(synthetic_opportunities)
        
        # Step 4: Bulk insert all opportunities
        logger.info(f"💾 Inserting {len(real_opportunities):,} opportunities into database...")
        
        # Insert in batches for better performance
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(real_opportunities), batch_size):
            batch = real_opportunities[i:i + batch_size]
            inserted = self.db.bulk_insert_opportunities(batch)
            total_inserted += inserted
            
            if (i // batch_size + 1) % 5 == 0:  # Progress update every 5 batches
                logger.info(f"Progress: {total_inserted:,}/{len(real_opportunities):,} opportunities inserted")
        
        # Step 5: Final count and cleanup
        final_count = self.db.get_opportunity_count()
        logger.info(f"🎉 Scaling complete! Final count: {final_count:,} opportunities")
        
        # Clean up very old opportunities if we exceeded target significantly
        if final_count > target_count * 1.2:
            logger.info("🧹 Cleaning up old opportunities...")
            self.db.cleanup_old_opportunities()
            final_count = self.db.get_opportunity_count()
            logger.info(f"After cleanup: {final_count:,} opportunities")
        
        return final_count

def main():
    """Main execution function"""
    try:
        # Initialize scaler
        scaler = OpportunityScaler()
        
        # Scale to 10,000 opportunities
        target = 10000
        final_count = scaler.scale_to_target(target)
        
        print(f"\n🚀 SUCCESS! Scaled to {final_count:,} opportunities!")
        print(f"🎯 Target: {target:,}")
        print(f"📊 Achievement: {(final_count/target)*100:.1f}%")
        print(f"🔗 Check your dashboard: https://frontend-ehe4r9mtg-jacobs-projects-cf4c7bdb.vercel.app")
        
    except Exception as e:
        logger.error(f"Scaling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
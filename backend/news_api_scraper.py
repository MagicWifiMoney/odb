#!/usr/bin/env python3
"""
NewsAPI Scraper - FREE Industry News Monitoring
Monitor news for contract announcements, industry trends, company updates
Rate Limit: 1,000 requests/day (FREE)
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
        logging.FileHandler('/tmp/news_api.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

@dataclass
class NewsOpportunity:
    """News-derived opportunity data structure"""
    title: str
    description: str
    source_name: str
    published_at: str
    url: str
    author: Optional[str]
    content: Optional[str]
    relevance_score: int
    opportunity_type: str
    companies_mentioned: List[str]
    contract_keywords: List[str]
    duplicate_hash: str

class NewsAPIScraper:
    """NewsAPI scraper for industry news and contract announcements"""
    
    def __init__(self, db_path: str):
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment")
        
        self.base_url = "https://newsapi.org/v2"
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Industry-specific search queries
        self.search_queries = [
            {
                'query': 'data center contract government',
                'category': 'data_center',
                'priority': 1
            },
            {
                'query': 'government IT contract award',
                'category': 'information_technology',
                'priority': 1
            },
            {
                'query': 'federal technology procurement',
                'category': 'government_technology',
                'priority': 2
            },
            {
                'query': 'cloud infrastructure contract',
                'category': 'data_center',
                'priority': 2
            },
            {
                'query': 'cybersecurity government contract',
                'category': 'cybersecurity',
                'priority': 2
            },
            {
                'query': 'enterprise software procurement',
                'category': 'information_technology',
                'priority': 3
            },
            {
                'query': 'digital transformation government',
                'category': 'digital_transformation',
                'priority': 3
            }
        ]
        
        # Contract-related keywords for filtering
        self.contract_keywords = [
            'contract', 'award', 'procurement', 'rfp', 'solicitation',
            'bid', 'tender', 'agreement', 'deal', 'acquisition',
            'partnership', 'vendor', 'supplier', 'outsourcing'
        ]
        
        # Major tech companies to monitor
        self.tech_companies = [
            'microsoft', 'amazon', 'google', 'oracle', 'ibm',
            'cisco', 'dell', 'hp', 'vmware', 'salesforce',
            'servicenow', 'snowflake', 'databricks', 'palantir'
        ]
        
        # Request headers
        self.headers = {
            'X-API-Key': self.api_key,
            'User-Agent': 'OpportunityDashboard/1.0'
        }
    
    def search_news(self, days_back: int = 3) -> List[NewsOpportunity]:
        """Search for industry news using NewsAPI"""
        self.logger.info(f"📰 Searching NewsAPI for industry news (last {days_back} days)...")
        
        all_opportunities = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format date for API (ISO format)
        from_date = start_date.strftime('%Y-%m-%d')
        
        for query_config in self.search_queries:
            try:
                self.logger.info(f"   🔍 Searching: '{query_config['query']}'...")
                
                # Search everything endpoint
                endpoint = f"{self.base_url}/everything"
                
                params = {
                    'q': query_config['query'],
                    'from': from_date,
                    'sortBy': 'relevancy',
                    'language': 'en',
                    'pageSize': 100  # Maximum allowed
                }
                
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    self.logger.info(f"   📄 Found {len(articles)} articles")
                    
                    for article in articles:
                        opportunity = self._process_news_article(article, query_config)
                        if opportunity and not self._is_duplicate_opportunity(opportunity, all_opportunities):
                            all_opportunities.append(opportunity)
                
                elif response.status_code == 429:
                    self.logger.warning("   ⏰ Rate limited - stopping search")
                    break
                    
                else:
                    self.logger.error(f"   ❌ API error {response.status_code}: {response.text[:200]}")
                
                # Rate limiting - be conservative with free tier
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"   ❌ Error searching '{query_config['query']}': {e}")
        
        # Filter and rank opportunities
        filtered_opportunities = self._filter_and_rank_opportunities(all_opportunities)
        
        self.logger.info(f"   ✅ Total relevant opportunities: {len(filtered_opportunities)}")
        return filtered_opportunities
    
    def _process_news_article(self, article: Dict[str, Any], query_config: Dict[str, Any]) -> Optional[NewsOpportunity]:
        """Process news article into opportunity format"""
        try:
            title = article.get('title', '').strip()
            description = article.get('description', '').strip()
            content = article.get('content', '').strip()
            
            if not title or len(title) < 20:
                return None
            
            # Check for contract relevance
            full_text = f"{title} {description} {content}".lower()
            contract_matches = [kw for kw in self.contract_keywords if kw in full_text]
            
            if not contract_matches:
                return None  # Not contract-related
            
            # Extract company mentions
            companies_mentioned = [comp for comp in self.tech_companies if comp in full_text]
            
            # Calculate relevance score
            relevance_score = self._calculate_news_relevance(full_text, contract_matches, companies_mentioned)
            
            if relevance_score < 60:
                return None  # Not relevant enough
            
            # Extract other fields
            source_name = article.get('source', {}).get('name', 'Unknown Source')
            published_at = article.get('publishedAt', '')
            url = article.get('url', '')
            author = article.get('author', '')
            
            # Determine opportunity type
            opportunity_type = self._classify_opportunity_type(full_text)
            
            # Generate duplicate hash
            hash_input = f"{title}{url}{published_at}"
            duplicate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            opportunity = NewsOpportunity(
                title=title[:500],
                description=description[:1000],
                source_name=source_name,
                published_at=published_at,
                url=url,
                author=author,
                content=content[:2000] if content else None,
                relevance_score=relevance_score,
                opportunity_type=opportunity_type,
                companies_mentioned=companies_mentioned,
                contract_keywords=contract_matches,
                duplicate_hash=duplicate_hash
            )
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"   ⚠️  Error processing article: {e}")
            return None
    
    def _calculate_news_relevance(self, text: str, contract_keywords: List[str], companies: List[str]) -> int:
        """Calculate relevance score for news article"""
        score = 40  # Base score
        
        # Contract keyword bonus
        score += min(len(contract_keywords) * 10, 30)
        
        # Company mention bonus
        score += min(len(companies) * 5, 20)
        
        # High-value keywords
        value_keywords = ['million', 'billion', '$', 'federal', 'government', 'enterprise']
        value_matches = sum(1 for kw in value_keywords if kw in text)
        score += min(value_matches * 5, 15)
        
        # Data center specific keywords
        dc_keywords = ['data center', 'datacenter', 'cloud', 'infrastructure', 'hosting']
        if any(kw in text for kw in dc_keywords):
            score += 10
        
        # IT specific keywords
        it_keywords = ['software', 'cybersecurity', 'digital transformation', 'automation']
        if any(kw in text for kw in it_keywords):
            score += 5
        
        return min(score, 100)
    
    def _classify_opportunity_type(self, text: str) -> str:
        """Classify the type of opportunity based on content"""
        if any(kw in text for kw in ['data center', 'datacenter', 'cloud infrastructure']):
            return 'data_center_news'
        elif any(kw in text for kw in ['cybersecurity', 'security contract']):
            return 'cybersecurity_news'
        elif any(kw in text for kw in ['software', 'application', 'platform']):
            return 'software_news'
        elif any(kw in text for kw in ['digital transformation', 'modernization']):
            return 'digital_transformation_news'
        else:
            return 'general_tech_news'
    
    def _is_duplicate_opportunity(self, new_opp: NewsOpportunity, existing_opps: List[NewsOpportunity]) -> bool:
        """Check if opportunity is duplicate in current batch"""
        return any(existing.duplicate_hash == new_opp.duplicate_hash for existing in existing_opps)
    
    def _filter_and_rank_opportunities(self, opportunities: List[NewsOpportunity]) -> List[NewsOpportunity]:
        """Filter and rank opportunities by relevance"""
        # Sort by relevance score descending
        sorted_opps = sorted(opportunities, key=lambda x: x.relevance_score, reverse=True)
        
        # Take top 50 to avoid overwhelming the database
        return sorted_opps[:50]
    
    def _is_duplicate_in_db(self, duplicate_hash: str) -> bool:
        """Check if opportunity already exists in database"""
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
            
        except Exception:
            return False
    
    def save_opportunity(self, opp: NewsOpportunity) -> bool:
        """Save news opportunity to database"""
        try:
            # Check for duplicates
            if self._is_duplicate_in_db(opp.duplicate_hash):
                self.logger.debug(f"   ⏭️  Skipping duplicate: {opp.title[:50]}...")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate scores
            relevance_score = opp.relevance_score
            urgency_score = self._calculate_urgency_score(opp)
            value_score = 60  # Default for news-based opportunities
            competition_score = 50  # Lower for news vs direct opportunities
            total_score = relevance_score + urgency_score + value_score + competition_score
            
            now = datetime.now().isoformat()
            
            # Prepare description with news context
            description = f"News Source: {opp.source_name}\n\n{opp.description}"
            if opp.companies_mentioned:
                description += f"\n\nCompanies Mentioned: {', '.join(opp.companies_mentioned)}"
            if opp.contract_keywords:
                description += f"\nContract Keywords: {', '.join(opp.contract_keywords)}"
            
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
                opp.title, description[:2000], opp.source_name, f"NEWS-{hash(opp.duplicate_hash) % 100000}",
                None, opp.published_at, None, 'news_api', f"NewsAPI-{opp.source_name}",
                opp.url, None, opp.author, relevance_score, urgency_score,
                value_score, competition_score, total_score, now, now,
                opp.opportunity_type, 0.7, now  # News has lower reliability than direct sources
            ))
            
            opportunity_id = cursor.lastrowid
            
            # Record hash for duplicate detection
            cursor.execute("""
                INSERT OR IGNORE INTO opportunity_hashes (duplicate_hash, created_at)
                VALUES (?, ?)
            """, (opp.duplicate_hash, now))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"   ✅ Saved: {opp.title[:50]}... (Score: {relevance_score})")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ Failed to save opportunity: {e}")
            return False
    
    def _calculate_urgency_score(self, opp: NewsOpportunity) -> int:
        """Calculate urgency score based on publish date"""
        try:
            if opp.published_at:
                # Parse ISO date
                publish_date = datetime.fromisoformat(opp.published_at.replace('Z', '+00:00'))
                hours_old = (datetime.now() - publish_date.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_old <= 24:
                    return 80  # Very recent news
                elif hours_old <= 72:
                    return 60  # Recent news
                else:
                    return 40  # Older news
        except:
            pass
        
        return 50  # Default
    
    def run_news_scraping_cycle(self) -> Dict[str, Any]:
        """Run complete news scraping cycle"""
        cycle_start = datetime.now()
        self.logger.info("🚀 Starting NewsAPI Scraping Cycle")
        self.logger.info("=" * 40)
        
        results = {
            'opportunities_found': 0,
            'opportunities_saved': 0,
            'cycle_start': cycle_start.isoformat(),
            'errors': []
        }
        
        try:
            # Search for news opportunities
            opportunities = self.search_news(days_back=2)  # Last 2 days
            results['opportunities_found'] = len(opportunities)
            
            # Save opportunities
            saved_count = 0
            for opp in opportunities:
                if self.save_opportunity(opp):
                    saved_count += 1
            
            results['opportunities_saved'] = saved_count
            
        except Exception as e:
            error_msg = f"NewsAPI scraping cycle failed: {e}"
            self.logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        results['cycle_end'] = cycle_end.isoformat()
        results['duration_seconds'] = duration
        
        self.logger.info(f"\n📊 NEWSAPI SCRAPING CYCLE COMPLETE")
        self.logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
        self.logger.info(f"   🔍 Opportunities Found: {results['opportunities_found']}")
        self.logger.info(f"   💾 Opportunities Saved: {results['opportunities_saved']}")
        
        if results['errors']:
            self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
        
        return results

def start_automated_news_scraping():
    """Start automated NewsAPI scraping"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = NewsAPIScraper(db_path)
    
    print("🤖 NEWSAPI INDUSTRY MONITOR")
    print("=" * 35)
    print("📰 Source: 80,000+ News Sources")
    print("🆓 Cost: FREE (1,000 requests/day)")
    print("🎯 Focus: Contract Announcements & Industry News")
    print("⏰ Frequency: Every 6 hours")
    
    # Schedule every 6 hours (conservative for rate limits)
    schedule.every(6).hours.do(scraper.run_news_scraping_cycle)
    
    # Run initial cycle
    print("\n🚀 Running initial NewsAPI cycle...")
    scraper.run_news_scraping_cycle()
    
    print(f"\n✅ Automated NewsAPI scraping started!")
    print("🔄 Next cycle in 6 hours")
    print("📝 Logs: /tmp/news_api.log")
    print("\n⏸️  Press Ctrl+C to stop")
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Automated NewsAPI scraping stopped.")

def run_immediate_news_cycle():
    """Run immediate NewsAPI scraping cycle"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'opportunities.db')
    scraper = NewsAPIScraper(db_path)
    
    results = scraper.run_news_scraping_cycle()
    print(f"\n✅ Immediate NewsAPI cycle complete!")
    print(f"📰 Found {results['opportunities_found']} news opportunities")
    print(f"💾 Saved {results['opportunities_saved']} new opportunities")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "immediate":
        run_immediate_news_cycle()
    else:
        start_automated_news_scraping()
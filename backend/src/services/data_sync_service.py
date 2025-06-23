from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy.exc import IntegrityError
from src.database import db
from src.models.opportunity import Opportunity, DataSource, SyncLog
from src.services.api_clients import APIClientFactory, APIError, RateLimitError
from src.services.firecrawl_service import FirecrawlScrapeService
from src.services.scoring_service import ScoringService


class DataSyncService:
    """Service for synchronizing data from external APIs and web scraping"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scoring_service = ScoringService()
        self.clients = {}
        self.firecrawl_service = None
        
        # Initialize API clients
        try:
            self.clients = APIClientFactory.get_all_clients()
            self.logger.info(f"Initialized {len(self.clients)} API clients")
        except Exception as e:
            self.logger.error(f"Failed to initialize API clients: {str(e)}")
        
        # Initialize Firecrawl service
        try:
            self.firecrawl_service = FirecrawlScrapeService()
            self.logger.info("Initialized Firecrawl scraping service")
        except Exception as e:
            self.logger.warning(f"Firecrawl service not available: {str(e)}")
    
    def sync_all_sources(self, include_scraping: bool = True) -> Dict[str, Any]:
        """Sync data from all configured sources including web scraping"""
        results = {
            'total_processed': 0,
            'total_added': 0,
            'total_updated': 0,
            'sources': {},
            'errors': []
        }
        
        # Sync API sources
        for source_name, client in self.clients.items():
            try:
                result = self.sync_source(source_name, client)
                results['sources'][source_name] = result
                results['total_processed'] += result['processed']
                results['total_added'] += result['added']
                results['total_updated'] += result['updated']
                
            except Exception as e:
                error_msg = f"Failed to sync {source_name}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['sources'][source_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'processed': 0,
                    'added': 0,
                    'updated': 0
                }
        
        # Sync scraping sources if enabled and available
        if include_scraping and self.firecrawl_service:
            scraping_results = self.sync_scraping_sources()
            results['sources'].update(scraping_results['sources'])
            results['total_processed'] += scraping_results['total_processed']
            results['total_added'] += scraping_results['total_added']
            results['total_updated'] += scraping_results['total_updated']
            results['errors'].extend(scraping_results['errors'])
        
        return results
    
    def sync_scraping_sources(self) -> Dict[str, Any]:
        """Sync data from web scraping sources"""
        if not self.firecrawl_service:
            return {
                'total_processed': 0,
                'total_added': 0,
                'total_updated': 0,
                'sources': {},
                'errors': ['Firecrawl service not available']
            }
        
        results = {
            'total_processed': 0,
            'total_added': 0,
            'total_updated': 0,
            'sources': {},
            'errors': []
        }
        
        # Get available scraping sources
        available_sources = self.firecrawl_service.get_available_sources()
        
        for source_info in available_sources:
            source_key = source_info['key']
            source_name = f"firecrawl_{source_key}"
            
            try:
                result = self.sync_scraping_source(source_key, source_name)
                results['sources'][source_name] = result
                results['total_processed'] += result['processed']
                results['total_added'] += result['added']
                results['total_updated'] += result['updated']
                
            except Exception as e:
                error_msg = f"Failed to scrape {source_key}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['sources'][source_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'processed': 0,
                    'added': 0,
                    'updated': 0
                }
        
        return results
    
    def sync_scraping_source(self, source_key: str, source_name: str) -> Dict[str, Any]:
        """Sync data from a specific scraping source"""
        self.logger.info(f"Starting scrape for {source_key}")
        
        # Create sync log
        sync_log = SyncLog(
            source_name=source_name,
            sync_type='scraper',
            sync_start=datetime.utcnow(),
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            # Scrape the source
            scrape_result = self.firecrawl_service.scrape_source(source_key)
            
            if not scrape_result['success']:
                raise Exception(scrape_result.get('error', 'Scraping failed'))
            
            opportunities = scrape_result.get('opportunities', [])
            
            # Process and store data
            added, updated = self.process_opportunities(opportunities)
            
            # Update sync log
            sync_log.sync_end = datetime.utcnow()
            sync_log.records_processed = len(opportunities)
            sync_log.records_added = added
            sync_log.records_updated = updated
            sync_log.status = 'completed'
            db.session.commit()
            
            self.logger.info(f"Completed scrape for {source_key}: {added} added, {updated} updated")
            
            return {
                'status': 'completed',
                'processed': len(opportunities),
                'added': added,
                'updated': updated
            }
            
        except Exception as e:
            # Update sync log with error
            sync_log.sync_end = datetime.utcnow()
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.errors_count = 1
            db.session.commit()
            
            self.logger.error(f"Failed to scrape {source_key}: {str(e)}")
            raise
    
    def scrape_custom_url(self, url: str, source_name: str = 'Custom') -> Dict[str, Any]:
        """Scrape a custom URL for opportunities"""
        if not self.firecrawl_service:
            return {
                'success': False,
                'error': 'Firecrawl service not available'
            }
        
        try:
            result = self.firecrawl_service.scrape_custom_url(url, source_name)
            
            if result['success']:
                opportunities = result.get('opportunities', [])
                added, updated = self.process_opportunities(opportunities)
                
                result['added'] = added
                result['updated'] = updated
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scraping custom URL {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_source(self, source_name: str, client) -> Dict[str, Any]:
        """Sync data from a specific source"""
        self.logger.info(f"Starting sync for {source_name}")
        
        # Create sync log
        sync_log = SyncLog(
            source_name=source_name,
            sync_type='api',
            sync_start=datetime.utcnow(),
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            # Fetch data from API
            if source_name == 'sam_gov':
                raw_data = client.fetch_opportunities()
                opportunities = client.transform_data(raw_data)
            elif source_name == 'grants_gov':
                raw_data = client.fetch_opportunities()
                opportunities = client.transform_data(raw_data)
            elif source_name == 'usa_spending':
                raw_data = client.fetch_recent_awards()
                opportunities = client.transform_award_data(raw_data)
            else:
                raise ValueError(f"Unknown source: {source_name}")
            
            # Process and store data
            added, updated = self.process_opportunities(opportunities)
            
            # Update sync log
            sync_log.sync_end = datetime.utcnow()
            sync_log.records_processed = len(opportunities)
            sync_log.records_added = added
            sync_log.records_updated = updated
            sync_log.status = 'completed'
            db.session.commit()
            
            self.logger.info(f"Completed sync for {source_name}: {added} added, {updated} updated")
            
            return {
                'status': 'completed',
                'processed': len(opportunities),
                'added': added,
                'updated': updated
            }
            
        except Exception as e:
            # Update sync log with error
            sync_log.sync_end = datetime.utcnow()
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.errors_count = 1
            db.session.commit()
            
            self.logger.error(f"Failed to sync {source_name}: {str(e)}")
            raise
    
    def process_opportunities(self, opportunities: List[Dict[str, Any]]) -> tuple[int, int]:
        """Process and store opportunities in database"""
        added = 0
        updated = 0
        
        for opp_data in opportunities:
            try:
                # Skip if missing required fields
                if not opp_data.get('source_id') or not opp_data.get('title'):
                    continue
                
                # Check for existing opportunity
                existing = db.session.query(Opportunity).filter_by(
                    source_id=opp_data['source_id']
                ).first()
                
                if existing:
                    if self._has_changes(existing, opp_data):
                        self._update_opportunity(existing, opp_data)
                        updated += 1
                else:
                    self._create_opportunity(opp_data)
                    added += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process opportunity {opp_data.get('source_id')}: {str(e)}")
                continue
        
        db.session.commit()
        return added, updated
    
    def _create_opportunity(self, opp_data: Dict[str, Any]):
        """Create new opportunity in database"""
        # Calculate scores
        scores = self.scoring_service.calculate_total_score(opp_data)
        
        # Create opportunity object
        opportunity = Opportunity(
            source_id=opp_data.get('source_id'),
            source_type=opp_data.get('source_type'),
            source_name=opp_data.get('source_name'),
            title=opp_data.get('title'),
            description=opp_data.get('description'),
            opportunity_number=opp_data.get('opportunity_number'),
            posted_date=opp_data.get('posted_date'),
            due_date=opp_data.get('due_date'),
            close_date=opp_data.get('close_date'),
            estimated_value=opp_data.get('estimated_value'),
            min_award_amount=opp_data.get('min_award_amount'),
            max_award_amount=opp_data.get('max_award_amount'),
            category=opp_data.get('category'),
            subcategory=opp_data.get('subcategory'),
            naics_code=opp_data.get('naics_code'),
            psc_code=opp_data.get('psc_code'),
            cfda_number=opp_data.get('cfda_number'),
            place_of_performance_city=opp_data.get('place_of_performance_city'),
            place_of_performance_state=opp_data.get('place_of_performance_state'),
            place_of_performance_country=opp_data.get('place_of_performance_country', 'USA'),
            agency_name=opp_data.get('agency_name'),
            department=opp_data.get('department'),
            office=opp_data.get('office'),
            contact_name=opp_data.get('contact_name'),
            contact_email=opp_data.get('contact_email'),
            contact_phone=opp_data.get('contact_phone'),
            status=opp_data.get('status', 'active'),
            opportunity_type=opp_data.get('opportunity_type'),
            set_aside_type=opp_data.get('set_aside_type'),
            source_url=opp_data.get('source_url'),
            document_urls=opp_data.get('document_urls'),
            relevance_score=scores['relevance_score'],
            urgency_score=scores['urgency_score'],
            value_score=scores['value_score'],
            competition_score=scores['competition_score'],
            total_score=scores['total_score']
        )
        
        db.session.add(opportunity)
    
    def _update_opportunity(self, existing: Opportunity, opp_data: Dict[str, Any]):
        """Update existing opportunity in database"""
        # Calculate new scores
        scores = self.scoring_service.calculate_total_score(opp_data)
        
        # Update fields
        existing.title = opp_data.get('title', existing.title)
        existing.description = opp_data.get('description', existing.description)
        existing.due_date = opp_data.get('due_date', existing.due_date)
        existing.close_date = opp_data.get('close_date', existing.close_date)
        existing.estimated_value = opp_data.get('estimated_value', existing.estimated_value)
        existing.status = opp_data.get('status', existing.status)
        existing.contact_name = opp_data.get('contact_name', existing.contact_name)
        existing.contact_email = opp_data.get('contact_email', existing.contact_email)
        existing.contact_phone = opp_data.get('contact_phone', existing.contact_phone)
        existing.source_url = opp_data.get('source_url', existing.source_url)
        
        # Update scores
        existing.relevance_score = scores['relevance_score']
        existing.urgency_score = scores['urgency_score']
        existing.value_score = scores['value_score']
        existing.competition_score = scores['competition_score']
        existing.total_score = scores['total_score']
        existing.updated_at = datetime.utcnow()
    
    def _has_changes(self, existing: Opportunity, opp_data: Dict[str, Any]) -> bool:
        """Check if opportunity data has changed"""
        # Check key fields for changes
        fields_to_check = [
            'title', 'description', 'due_date', 'estimated_value', 
            'status', 'contact_email', 'source_url'
        ]
        
        for field in fields_to_check:
            existing_value = getattr(existing, field, None)
            new_value = opp_data.get(field)
            
            if existing_value != new_value:
                return True
        
        return False
    
    def _get_or_create_data_source(self, source_name: str, source_type: str = 'api') -> DataSource:
        """Get or create data source record"""
        source = db.session.query(DataSource).filter_by(name=source_name).first()
        
        if not source:
            source_config = {
                'sam_gov': {
                    'type': 'api',
                    'base_url': 'https://api.sam.gov/opportunities/v2/search',
                    'api_key_required': True,
                    'rate_limit_per_hour': 500
                },
                'grants_gov': {
                    'type': 'api',
                    'base_url': 'https://api.grants.gov/v1/api/search2',
                    'api_key_required': False,
                    'rate_limit_per_hour': 1000
                },
                'usa_spending': {
                    'type': 'api',
                    'base_url': 'https://api.usaspending.gov/api/v2',
                    'api_key_required': False,
                    'rate_limit_per_hour': 1000
                }
            }
            
            config = source_config.get(source_name, {})
            
            source = DataSource(
                name=source_name,
                source_type=config.get('type', source_type),
                is_active=True
            )
            
            db.session.add(source)
            db.session.commit()
        
        return source
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get status of recent synchronizations"""
        # Get latest sync for each source
        latest_syncs = {}
        
        for source_name in self.clients.keys():
            source = self._get_or_create_data_source(source_name)
            latest_sync = db.session.query(SyncLog).filter_by(
                source_id=source.id
            ).order_by(SyncLog.sync_start.desc()).first()
            
            if latest_sync:
                latest_syncs[source_name] = {
                    'last_sync': latest_sync.sync_start.isoformat(),
                    'status': latest_sync.status,
                    'records_processed': latest_sync.records_processed,
                    'records_added': latest_sync.records_added,
                    'records_updated': latest_sync.records_updated,
                    'errors_count': latest_sync.errors_count,
                    'error_message': latest_sync.error_message
                }
            else:
                latest_syncs[source_name] = {
                    'last_sync': None,
                    'status': 'never_synced'
                }
        
        # Check for stale data
        stale_threshold = datetime.utcnow() - timedelta(hours=25)
        stale_sources = []
        
        for source_name, sync_info in latest_syncs.items():
            if (not sync_info['last_sync'] or 
                datetime.fromisoformat(sync_info['last_sync']) < stale_threshold):
                stale_sources.append(source_name)
        
        return {
            'sources': latest_syncs,
            'stale_sources': stale_sources,
            'total_opportunities': db.session.query(Opportunity).count(),
            'active_opportunities': db.session.query(Opportunity).filter_by(status='active').count()
        }
    
    def cleanup_old_opportunities(self, days_old: int = 365) -> int:
        """Remove opportunities older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_opportunities = db.session.query(Opportunity).filter(
            Opportunity.created_at < cutoff_date,
            Opportunity.status.in_(['closed', 'awarded', 'cancelled'])
        )
        
        count = old_opportunities.count()
        old_opportunities.delete()
        db.session.commit()
        
        self.logger.info(f"Cleaned up {count} old opportunities")
        return count


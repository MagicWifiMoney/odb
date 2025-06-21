import os
import posthog
from datetime import datetime
from flask import request, g
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.is_initialized = False
        self.init()
    
    def init(self):
        """Initialize PostHog analytics"""
        api_key = os.getenv('POSTHOG_API_KEY')
        host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
        
        # Only initialize in production or when explicitly enabled
        is_enabled = (
            os.getenv('POSTHOG_ENABLED', 'false').lower() == 'true' or 
            os.getenv('FLASK_ENV') == 'production'
        )
        
        if is_enabled and api_key:
            posthog.api_key = api_key
            posthog.host = host
            self.is_initialized = True
            logger.info("📊 PostHog Analytics initialized for backend")
        else:
            logger.info("📊 PostHog Analytics disabled (dev mode or missing API key)")
    
    def get_user_context(self):
        """Get user context from request"""
        context = {
            'ip': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add user ID if available
        if hasattr(g, 'user_id'):
            context['user_id'] = g.user_id
            
        return context
    
    def track_api_request(self, endpoint, method, status_code, duration_ms=None, user_id=None):
        """Track API requests"""
        if not self.is_initialized:
            return
            
        properties = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'anonymous',
            event='api_request',
            properties=properties
        )
    
    def track_opportunity_created(self, opportunity_data, user_id=None):
        """Track when opportunities are created/synced"""
        if not self.is_initialized:
            return
            
        properties = {
            'opportunity_id': opportunity_data.get('id'),
            'agency': opportunity_data.get('agency_name'),
            'source_type': opportunity_data.get('source_type'),
            'estimated_value': opportunity_data.get('estimated_value'),
            'total_score': opportunity_data.get('total_score'),
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'system',
            event='opportunity_created',
            properties=properties
        )
    
    def track_opportunity_updated(self, opportunity_id, changes, user_id=None):
        """Track opportunity updates"""
        if not self.is_initialized:
            return
            
        properties = {
            'opportunity_id': opportunity_id,
            'changes': changes,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'system',
            event='opportunity_updated',
            properties=properties
        )
    
    def track_user_action(self, action, user_id, properties=None):
        """Track user actions"""
        if not self.is_initialized:
            return
            
        event_properties = {
            'action': action,
            **(properties or {}),
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id,
            event='user_action',
            properties=event_properties
        )
    
    def track_data_sync(self, sync_type, status, duration_ms=None, records_processed=None, errors=None):
        """Track data synchronization events"""
        if not self.is_initialized:
            return
            
        properties = {
            'sync_type': sync_type,
            'status': status,
            'duration_ms': duration_ms,
            'records_processed': records_processed,
            'errors': errors,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id='system',
            event='data_sync',
            properties=properties
        )
    
    def track_search_query(self, query, filters, results_count, user_id=None):
        """Track search queries"""
        if not self.is_initialized:
            return
            
        properties = {
            'query': query,
            'filters': filters,
            'results_count': results_count,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'anonymous',
            event='search_query',
            properties=properties
        )
    
    def track_error(self, error_type, error_message, context=None, user_id=None):
        """Track application errors"""
        if not self.is_initialized:
            return
            
        properties = {
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'system',
            event='error_occurred',
            properties=properties
        )
    
    def track_performance_metric(self, metric_name, value, context=None):
        """Track performance metrics"""
        if not self.is_initialized:
            return
            
        properties = {
            'metric_name': metric_name,
            'value': value,
            'context': context,
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id='system',
            event='performance_metric',
            properties=properties
        )
    
    def identify_user(self, user_id, properties=None):
        """Identify a user with properties"""
        if not self.is_initialized:
            return
            
        user_properties = {
            'platform': 'web',
            'app_version': '2.0.0',
            **(properties or {}),
            **self.get_user_context()
        }
        
        posthog.identify(
            distinct_id=user_id,
            properties=user_properties
        )
    
    def track_custom_event(self, event_name, properties=None, user_id=None):
        """Track custom events"""
        if not self.is_initialized:
            return
            
        event_properties = {
            **(properties or {}),
            **self.get_user_context()
        }
        
        posthog.capture(
            distinct_id=user_id or 'anonymous',
            event=event_name,
            properties=event_properties
        )
    
    def is_enabled(self):
        """Check if analytics is enabled"""
        return self.is_initialized

# Create singleton instance
analytics_service = AnalyticsService() 
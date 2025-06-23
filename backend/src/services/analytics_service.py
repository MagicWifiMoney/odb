import os
import logging
from datetime import datetime
from flask import request, g

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.is_initialized = False
        self.init()
    
    def init(self):
        """Initialize analytics - simplified version for Railway deployment"""
        # Only initialize in production or when explicitly enabled
        is_enabled = (
            os.getenv('POSTHOG_ENABLED', 'false').lower() == 'true' or 
            os.getenv('FLASK_ENV') == 'production'
        )
        
        if is_enabled:
            try:
                import posthog
                api_key = os.getenv('POSTHOG_API_KEY')
                host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
                
                if api_key:
                    posthog.api_key = api_key
                    posthog.host = host
                    self.posthog = posthog
                    self.is_initialized = True
                    logger.info("📊 PostHog Analytics initialized for backend")
                else:
                    logger.info("📊 PostHog Analytics disabled (missing API key)")
            except ImportError:
                logger.info("📊 PostHog Analytics disabled (posthog package not available)")
        else:
            logger.info("📊 PostHog Analytics disabled (dev mode)")
    
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
            
        try:
            properties = {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'duration_ms': duration_ms,
                **self.get_user_context()
            }
            
            self.posthog.capture(
                distinct_id=user_id or 'anonymous',
                event='api_request',
                properties=properties
            )
        except Exception as e:
            logger.warning(f"Failed to track API request: {e}")
    
    def track_custom_event(self, event_name, properties=None, user_id=None):
        """Track custom events"""
        if not self.is_initialized:
            return
            
        try:
            event_properties = {
                **(properties or {}),
                **self.get_user_context()
            }
            
            self.posthog.capture(
                distinct_id=user_id or 'anonymous',
                event=event_name,
                properties=event_properties
            )
        except Exception as e:
            logger.warning(f"Failed to track custom event: {e}")
    
    def is_enabled(self):
        """Check if analytics is enabled"""
        return self.is_initialized

# Create singleton instance
analytics_service = AnalyticsService() 
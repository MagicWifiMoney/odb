import time
import logging
import functools
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import request, g
from .analytics_service import analytics_service
from .cache_service import get_cache, CacheStrategy

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Comprehensive performance monitoring for API endpoints and database queries.
    Integrates with existing analytics service and Redis cache for metrics storage.
    """
    
    def __init__(self):
        self.cache = get_cache()
        self.metrics_cache_key = "performance_metrics"
        self.slow_query_threshold = 1000  # ms
        self.slow_endpoint_threshold = 2000  # ms
        
    async def record_api_performance(self, endpoint: str, method: str, 
                                   duration_ms: float, status_code: int,
                                   user_id: Optional[str] = None) -> None:
        """Record API endpoint performance metrics"""
        try:
            # Track with analytics service
            analytics_service.track_api_request(
                endpoint=endpoint,
                method=method, 
                status_code=status_code,
                duration_ms=duration_ms,
                user_id=user_id
            )
            
            # Store detailed metrics in cache for real-time monitoring
            metrics_key = f"api_metrics_{endpoint}_{method}"
            current_metrics = await self.cache.get(metrics_key, CacheStrategy.SESSION) or {
                'total_requests': 0,
                'total_duration': 0,
                'slow_requests': 0,
                'error_requests': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Update metrics
            current_metrics['total_requests'] += 1
            current_metrics['total_duration'] += duration_ms
            current_metrics['last_updated'] = datetime.utcnow().isoformat()
            
            if duration_ms > self.slow_endpoint_threshold:
                current_metrics['slow_requests'] += 1
                
            if status_code >= 400:
                current_metrics['error_requests'] += 1
                
            # Calculate derived metrics
            current_metrics['avg_duration'] = current_metrics['total_duration'] / current_metrics['total_requests']
            current_metrics['slow_request_rate'] = (current_metrics['slow_requests'] / current_metrics['total_requests']) * 100
            current_metrics['error_rate'] = (current_metrics['error_requests'] / current_metrics['total_requests']) * 100
            
            # Cache updated metrics
            await self.cache.set(metrics_key, current_metrics, CacheStrategy.SESSION)
            
            # Log slow requests
            if duration_ms > self.slow_endpoint_threshold:
                logger.warning(f"Slow API request: {method} {endpoint} took {duration_ms:.2f}ms")
                
        except Exception as e:
            logger.error(f"Failed to record API performance: {e}")
    
    async def record_query_performance(self, query_type: str, duration_ms: float, 
                                     query_params: Optional[Dict] = None) -> None:
        """Record database query performance metrics"""
        try:
            metrics_key = f"query_metrics_{query_type}"
            current_metrics = await self.cache.get(metrics_key, CacheStrategy.SESSION) or {
                'total_queries': 0,
                'total_duration': 0,
                'slow_queries': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Update metrics
            current_metrics['total_queries'] += 1
            current_metrics['total_duration'] += duration_ms
            current_metrics['last_updated'] = datetime.utcnow().isoformat()
            
            if duration_ms > self.slow_query_threshold:
                current_metrics['slow_queries'] += 1
                
            # Calculate derived metrics
            current_metrics['avg_duration'] = current_metrics['total_duration'] / current_metrics['total_queries']
            current_metrics['slow_query_rate'] = (current_metrics['slow_queries'] / current_metrics['total_queries']) * 100
            
            # Cache updated metrics
            await self.cache.set(metrics_key, current_metrics, CacheStrategy.SESSION)
            
            # Log slow queries
            if duration_ms > self.slow_query_threshold:
                logger.warning(f"Slow query: {query_type} took {duration_ms:.2f}ms")
                if query_params:
                    logger.debug(f"Query params: {query_params}")
                    
        except Exception as e:
            logger.error(f"Failed to record query performance: {e}")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            summary = {
                'api_endpoints': {},
                'database_queries': {},
                'cache_stats': self.cache.get_stats(),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Get all API metrics from cache
            # Note: In a real implementation, you'd want to scan Redis keys
            # For now, we'll return what we can get from cache stats
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    async def record_cache_performance(self, operation: str, cache_key: str, 
                                     hit: bool, duration_ms: float) -> None:
        """Record cache operation performance"""
        try:
            metrics_key = f"cache_metrics_{operation}"
            current_metrics = await self.cache.get(metrics_key, CacheStrategy.SESSION) or {
                'total_operations': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'total_duration': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Update metrics
            current_metrics['total_operations'] += 1
            current_metrics['total_duration'] += duration_ms
            current_metrics['last_updated'] = datetime.utcnow().isoformat()
            
            if hit:
                current_metrics['cache_hits'] += 1
            else:
                current_metrics['cache_misses'] += 1
                
            # Calculate derived metrics
            current_metrics['hit_rate'] = (current_metrics['cache_hits'] / current_metrics['total_operations']) * 100
            current_metrics['avg_duration'] = current_metrics['total_duration'] / current_metrics['total_operations']
            
            # Cache updated metrics
            await self.cache.set(metrics_key, current_metrics, CacheStrategy.SESSION)
            
        except Exception as e:
            logger.error(f"Failed to record cache performance: {e}")

def monitor_performance(operation_type: str = "api"):
    """
    Decorator to monitor function performance
    
    Args:
        operation_type: Type of operation ('api', 'query', 'cache')
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record performance based on operation type
                monitor = PerformanceMonitor()
                
                if operation_type == "api":
                    endpoint = getattr(request, 'endpoint', func.__name__)
                    method = getattr(request, 'method', 'GET')
                    status_code = 200
                    user_id = getattr(g, 'user_id', None)
                    
                    await monitor.record_api_performance(
                        endpoint=endpoint,
                        method=method,
                        duration_ms=duration_ms,
                        status_code=status_code,
                        user_id=user_id
                    )
                    
                elif operation_type == "query":
                    await monitor.record_query_performance(
                        query_type=func.__name__,
                        duration_ms=duration_ms
                    )
                    
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if operation_type == "api":
                    monitor = PerformanceMonitor()
                    endpoint = getattr(request, 'endpoint', func.__name__)
                    method = getattr(request, 'method', 'GET')
                    status_code = 500
                    user_id = getattr(g, 'user_id', None)
                    
                    await monitor.record_api_performance(
                        endpoint=endpoint,
                        method=method,
                        duration_ms=duration_ms,
                        status_code=status_code,
                        user_id=user_id
                    )
                
                raise e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Log performance for sync functions
                if duration_ms > 1000:  # Log if over 1 second
                    logger.warning(f"Slow {operation_type} operation: {func.__name__} took {duration_ms:.2f}ms")
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Failed {operation_type} operation: {func.__name__} took {duration_ms:.2f}ms")
                raise e
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and 'await' in func.__code__.co_names:
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Create singleton instance
performance_monitor = PerformanceMonitor() 
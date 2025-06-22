import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from ..config.supabase import get_supabase_client, get_supabase_admin_client

logger = logging.getLogger(__name__)

@dataclass
class CostBreakdown:
    """Cost breakdown for API usage"""
    base_cost: Decimal
    token_cost: Decimal
    request_cost: Decimal
    total_cost: Decimal
    pricing_model: str
    calculation_details: Dict[str, Any]

@dataclass
class UsageSummary:
    """Summary of API usage for a time period"""
    period_start: datetime
    period_end: datetime
    total_requests: int
    api_calls: int
    cache_hits: int
    similar_matches: int
    total_cost_usd: Decimal
    cache_savings_usd: Decimal
    average_response_time_ms: float
    most_expensive_query: Optional[Dict]
    cost_by_endpoint: Dict[str, Decimal]
    cost_by_user: Dict[str, Decimal]

class CostTrackingService:
    """
    Comprehensive cost tracking service for API usage monitoring.
    Tracks all Perplexity API calls, calculates costs, and provides usage analytics.
    """
    
    # Perplexity API pricing (as of 2024)
    PRICING_CONFIG = {
        'perplexity-2024': {
            'base_request_cost': 0.005,  # $0.005 per request
            'token_cost_per_1k': 0.002,  # $0.002 per 1000 tokens
            'search_multiplier': 1.0,    # Standard search
            'research_multiplier': 1.5,  # Research queries cost more
            'max_tokens_default': 1000,
            'currency': 'USD'
        }
    }
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.admin_supabase = get_supabase_admin_client()
        self._ensure_tables()
        
        # Budget tracking
        self.daily_budget = Decimal(os.getenv('DAILY_API_BUDGET', '50.00'))
        self.monthly_budget = Decimal(os.getenv('MONTHLY_API_BUDGET', '1000.00'))
        
        # Alert thresholds (percentage of budget)
        self.warning_threshold = float(os.getenv('COST_WARNING_THRESHOLD', '0.75'))
        self.critical_threshold = float(os.getenv('COST_CRITICAL_THRESHOLD', '0.90'))
        
        logger.info(f"Cost tracking initialized - Daily: ${self.daily_budget}, Monthly: ${self.monthly_budget}")
    
    def _ensure_tables(self):
        """Ensure the API usage tracking table exists"""
        try:
            # Check if table exists by trying to query it
            result = self.supabase.table('api_usage_logs').select('id').limit(1).execute()
            logger.info("API usage tracking table verified")
        except Exception as e:
            logger.warning(f"API usage table may not exist yet: {e}")
            # For now, we'll continue without the table and handle gracefully
    
    def calculate_cost(self, 
                      endpoint: str,
                      tokens_used: int = 0,
                      query_type: str = 'search',
                      response_size: int = 0,
                      pricing_model: str = 'perplexity-2024') -> CostBreakdown:
        """Calculate the cost for an API call based on usage metrics."""
        try:
            config = self.PRICING_CONFIG.get(pricing_model, self.PRICING_CONFIG['perplexity-2024'])
            
            # Base request cost
            base_cost = Decimal(str(config['base_request_cost']))
            
            # Token-based cost
            if tokens_used > 0:
                token_cost = Decimal(str(tokens_used)) / 1000 * Decimal(str(config['token_cost_per_1k']))
            else:
                # Estimate tokens based on response size
                estimated_tokens = max(response_size // 4, 100)
                token_cost = Decimal(str(estimated_tokens)) / 1000 * Decimal(str(config['token_cost_per_1k']))
            
            # Query type multiplier
            multiplier = config.get(f'{query_type}_multiplier', 1.0)
            
            # Calculate total
            request_cost = (base_cost + token_cost) * Decimal(str(multiplier))
            total_cost = request_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            return CostBreakdown(
                base_cost=base_cost,
                token_cost=token_cost,
                request_cost=request_cost,
                total_cost=total_cost,
                pricing_model=pricing_model,
                calculation_details={
                    'tokens_used': tokens_used,
                    'query_type': query_type,
                    'multiplier': multiplier,
                    'response_size_bytes': response_size
                }
            )
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return CostBreakdown(
                base_cost=Decimal('0.001'),
                token_cost=Decimal('0.000'),
                request_cost=Decimal('0.001'),
                total_cost=Decimal('0.001'),
                pricing_model=pricing_model,
                calculation_details={'error': str(e)}
            )
    
    def log_api_call(self,
                    endpoint: str,
                    method: str = 'POST',
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    request_payload: Optional[Dict] = None,
                    query_text: Optional[str] = None,
                    query_type: str = 'search',
                    response_size_bytes: int = 0,
                    response_time_ms: int = 0,
                    tokens_used: int = 0,
                    from_cache: str = 'api_call',
                    similarity_score: float = 0.0,
                    status: str = 'success',
                    error_message: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Optional[int]:
        """Log an API call with all relevant cost and usage information."""
        try:
            # Calculate cost
            cost_breakdown = self.calculate_cost(
                endpoint=endpoint,
                tokens_used=tokens_used,
                query_type=query_type,
                response_size=response_size_bytes
            )
            
            # Calculate cache savings
            cache_savings = Decimal('0.000000')
            if from_cache in ['cache_hit', 'similar_match']:
                cache_savings = cost_breakdown.total_cost
            
            # Prepare log entry
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'user_id': user_id,
                'query_text': query_text or '',
                'response_size_kb': float(response_size_bytes / 1024) if response_size_bytes > 0 else 0.0,
                'cost_usd': float(cost_breakdown.total_cost),
                'response_time_ms': response_time_ms,
                'status_code': 200 if status == 'success' else 500,
                'metadata': {
                    'session_id': session_id,
                    'request_payload': request_payload,
                    'query_type': query_type,
                    'tokens_used': tokens_used,
                    'from_cache': from_cache,
                    'similarity_score': similarity_score,
                    'cache_savings_usd': float(cache_savings),
                    'pricing_model': cost_breakdown.pricing_model,
                    'calculation_details': cost_breakdown.calculation_details,
                    'error_message': error_message,
                    **(metadata or {})
                }
            }
            
            # Insert into Supabase
            result = self.supabase.table('api_usage_logs').insert(log_entry).execute()
            
            if result.data:
                log_id = result.data[0]['id']
                logger.info(f"API call logged successfully: {log_id}")
                
                # Check budget alerts
                self._check_budget_alerts()
                
                return log_id
            else:
                logger.error("Failed to log API call - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
            # Fallback to console logging
            logger.info(f"API Call - Endpoint: {endpoint}, Cost: ${cost_breakdown.total_cost}, Time: {response_time_ms}ms")
            return None
    
    def get_usage_summary(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         user_id: Optional[str] = None) -> UsageSummary:
        """Get comprehensive usage summary for a time period."""
        try:
            # Default to last 24 hours
            if not start_date:
                start_date = datetime.utcnow() - timedelta(hours=24)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Build query
            query = self.supabase.table('api_usage_logs').select('*')
            query = query.gte('timestamp', start_date.isoformat())
            query = query.lte('timestamp', end_date.isoformat())
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            logs = result.data if result.data else []
            
            # Calculate summary statistics
            total_requests = len(logs)
            api_calls = len([log for log in logs if log.get('metadata', {}).get('from_cache') == 'api_call'])
            cache_hits = len([log for log in logs if log.get('metadata', {}).get('from_cache') == 'cache_hit'])
            similar_matches = len([log for log in logs if log.get('metadata', {}).get('from_cache') == 'similar_match'])
            
            total_cost_usd = sum((Decimal(str(log.get('cost_usd', 0))) for log in logs), Decimal('0.000000'))
            cache_savings_usd = sum(
                (Decimal(str(log.get('metadata', {}).get('cache_savings_usd', 0))) for log in logs),
                Decimal('0.000000')
            )
            
            response_times = [log.get('response_time_ms', 0) for log in logs if log.get('response_time_ms', 0) > 0]
            average_response_time_ms = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Most expensive query
            most_expensive_query = None
            if logs:
                most_expensive = max(logs, key=lambda x: x.get('cost_usd', 0))
                most_expensive_query = {
                    'query': most_expensive.get('query_text', 'Unknown'),
                    'cost': float(most_expensive.get('cost_usd', 0)),
                    'timestamp': most_expensive.get('timestamp'),
                    'endpoint': most_expensive.get('endpoint')
                }
            
            # Cost by endpoint
            cost_by_endpoint = {}
            for log in logs:
                endpoint = log.get('endpoint', 'unknown')
                cost = Decimal(str(log.get('cost_usd', 0)))
                cost_by_endpoint[endpoint] = cost_by_endpoint.get(endpoint, Decimal('0')) + cost
            
            # Cost by user
            cost_by_user = {}
            for log in logs:
                user = log.get('user_id') or 'anonymous'
                cost = Decimal(str(log.get('cost_usd', 0)))
                cost_by_user[user] = cost_by_user.get(user, Decimal('0')) + cost
            
            return UsageSummary(
                period_start=start_date,
                period_end=end_date,
                total_requests=total_requests,
                api_calls=api_calls,
                cache_hits=cache_hits,
                similar_matches=similar_matches,
                total_cost_usd=total_cost_usd,
                cache_savings_usd=cache_savings_usd,
                average_response_time_ms=average_response_time_ms,
                most_expensive_query=most_expensive_query,
                cost_by_endpoint=cost_by_endpoint,
                cost_by_user=cost_by_user
            )
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            # Return empty summary
            return UsageSummary(
                period_start=start_date or datetime.utcnow(),
                period_end=end_date or datetime.utcnow(),
                total_requests=0,
                api_calls=0,
                cache_hits=0,
                similar_matches=0,
                total_cost_usd=Decimal('0.000000'),
                cache_savings_usd=Decimal('0.000000'),
                average_response_time_ms=0.0,
                most_expensive_query=None,
                cost_by_endpoint={},
                cost_by_user={}
            )
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and alerts."""
        try:
            # Get today's usage
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_summary = self.get_usage_summary(start_date=today)
            
            # Get this month's usage
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_summary = self.get_usage_summary(start_date=month_start)
            
            # Calculate percentages
            daily_percentage = float(today_summary.total_cost_usd / self.daily_budget * 100) if self.daily_budget > 0 else 0
            monthly_percentage = float(month_summary.total_cost_usd / self.monthly_budget * 100) if self.monthly_budget > 0 else 0
            
            # Determine alert levels
            daily_alert = 'none'
            monthly_alert = 'none'
            
            if daily_percentage >= self.critical_threshold * 100:
                daily_alert = 'critical'
            elif daily_percentage >= self.warning_threshold * 100:
                daily_alert = 'warning'
            
            if monthly_percentage >= self.critical_threshold * 100:
                monthly_alert = 'critical'
            elif monthly_percentage >= self.warning_threshold * 100:
                monthly_alert = 'warning'
            
            return {
                'daily': {
                    'budget': float(self.daily_budget),
                    'spent': float(today_summary.total_cost_usd),
                    'remaining': float(self.daily_budget - today_summary.total_cost_usd),
                    'percentage': daily_percentage,
                    'alert_level': daily_alert,
                    'requests': today_summary.total_requests
                },
                'monthly': {
                    'budget': float(self.monthly_budget),
                    'spent': float(month_summary.total_cost_usd),
                    'remaining': float(self.monthly_budget - month_summary.total_cost_usd),
                    'percentage': monthly_percentage,
                    'alert_level': monthly_alert,
                    'requests': month_summary.total_requests
                },
                'cache_efficiency': {
                    'daily_savings': float(today_summary.cache_savings_usd),
                    'monthly_savings': float(month_summary.cache_savings_usd),
                    'daily_hit_rate': (today_summary.cache_hits / today_summary.total_requests * 100) if today_summary.total_requests > 0 else 0,
                    'monthly_hit_rate': (month_summary.cache_hits / month_summary.total_requests * 100) if month_summary.total_requests > 0 else 0
                },
                'thresholds': {
                    'warning': self.warning_threshold * 100,
                    'critical': self.critical_threshold * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get budget status: {e}")
            return {
                'daily': {'budget': float(self.daily_budget), 'spent': 0.0, 'remaining': float(self.daily_budget), 'percentage': 0.0, 'alert_level': 'none', 'requests': 0},
                'monthly': {'budget': float(self.monthly_budget), 'spent': 0.0, 'remaining': float(self.monthly_budget), 'percentage': 0.0, 'alert_level': 'none', 'requests': 0},
                'cache_efficiency': {'daily_savings': 0.0, 'monthly_savings': 0.0, 'daily_hit_rate': 0.0, 'monthly_hit_rate': 0.0},
                'thresholds': {'warning': self.warning_threshold * 100, 'critical': self.critical_threshold * 100}
            }
    
    def _check_budget_alerts(self):
        """Check budget thresholds and log alerts."""
        try:
            budget_status = self.get_budget_status()
            
            daily_alert = budget_status['daily']['alert_level']
            monthly_alert = budget_status['monthly']['alert_level']
            
            if daily_alert in ['warning', 'critical']:
                logger.warning(f"Daily budget alert ({daily_alert}): ${budget_status['daily']['spent']:.2f} / ${budget_status['daily']['budget']:.2f}")
            
            if monthly_alert in ['warning', 'critical']:
                logger.warning(f"Monthly budget alert ({monthly_alert}): ${budget_status['monthly']['spent']:.2f} / ${budget_status['monthly']['budget']:.2f}")
                
        except Exception as e:
            logger.error(f"Failed to check budget alerts: {e}")
    
    def get_cost_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get cost trends over the specified number of days."""
        try:
            trends = []
            end_date = datetime.utcnow()
            
            for i in range(days):
                day_start = (end_date - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                day_summary = self.get_usage_summary(start_date=day_start, end_date=day_end)
                
                trends.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'total_cost': float(day_summary.total_cost_usd),
                    'api_calls': day_summary.api_calls,
                    'cache_hits': day_summary.cache_hits,
                    'cache_savings': float(day_summary.cache_savings_usd),
                    'average_response_time': day_summary.average_response_time_ms
                })
            
            return list(reversed(trends))  # Most recent first
            
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}")
            return []

# Global instance
cost_tracking_service = CostTrackingService()

def get_cost_tracking_service() -> CostTrackingService:
    """Get the cost tracking service instance"""
    return cost_tracking_service 
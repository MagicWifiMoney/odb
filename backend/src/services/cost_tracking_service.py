import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import Column, Integer, String, DateTime, Decimal as SQLDecimal, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from dataclasses import dataclass

from src.database import db

logger = logging.getLogger(__name__)

Base = declarative_base()

class APIUsageLog(Base):
    """Database model for tracking API usage and costs"""
    __tablename__ = 'api_usage_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Request details
    request_payload = Column(JSON)
    query_text = Column(Text)
    query_type = Column(String(50), nullable=True, index=True)
    
    # Response details
    response_size_bytes = Column(Integer, default=0)
    response_time_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    
    # Cost tracking
    cost_usd = Column(SQLDecimal(10, 6), default=0.000000)
    pricing_model = Column(String(50), default='perplexity-2024')
    
    # Caching info
    from_cache = Column(String(20), default='api_call')
    cache_savings_usd = Column(SQLDecimal(10, 6), default=0.000000)
    similarity_score = Column(SQLDecimal(3, 2), default=0.00)
    
    # Status and metadata
    status = Column(String(20), default='success')
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON)

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
        self.session = db.session
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
            Base.metadata.create_all(db.engine)
            logger.info("API usage tracking table verified/created")
        except Exception as e:
            logger.error(f"Failed to create API usage table: {e}")
    
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
            
            # Create log entry
            log_entry = APIUsageLog(
                timestamp=datetime.utcnow(),
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                session_id=session_id,
                request_payload=request_payload,
                query_text=query_text[:1000] if query_text else None,
                query_type=query_type,
                response_size_bytes=response_size_bytes,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                cost_usd=cost_breakdown.total_cost if from_cache == 'api_call' else Decimal('0.000000'),
                pricing_model=cost_breakdown.pricing_model,
                from_cache=from_cache,
                cache_savings_usd=cache_savings,
                similarity_score=Decimal(str(similarity_score)).quantize(Decimal('0.01')),
                status=status,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Save to database
            self.session.add(log_entry)
            self.session.commit()
            
            logger.debug(f"Logged API call: {endpoint} - Cost: ${cost_breakdown.total_cost}")
            
            # Check budget alerts
            self._check_budget_alerts()
            
            return log_entry.id
            
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
            self.session.rollback()
            return None
    
    def get_usage_summary(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         user_id: Optional[str] = None) -> UsageSummary:
        """Get usage summary for a time period."""
        try:
            if not start_date:
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Build query
            query = self.session.query(APIUsageLog).filter(
                APIUsageLog.timestamp >= start_date,
                APIUsageLog.timestamp <= end_date
            )
            
            if user_id:
                query = query.filter(APIUsageLog.user_id == user_id)
            
            logs = query.all()
            
            # Calculate metrics
            total_requests = len(logs)
            api_calls = len([l for l in logs if l.from_cache == 'api_call'])
            cache_hits = len([l for l in logs if l.from_cache == 'cache_hit'])
            similar_matches = len([l for l in logs if l.from_cache == 'similar_match'])
            
            total_cost = sum(l.cost_usd for l in logs)
            cache_savings = sum(l.cache_savings_usd for l in logs)
            
            avg_response_time = sum(l.response_time_ms for l in logs) / max(total_requests, 1)
            
            # Most expensive query
            most_expensive = None
            if logs:
                max_cost_log = max(logs, key=lambda l: l.cost_usd)
                if max_cost_log.cost_usd > 0:
                    most_expensive = {
                        'query': max_cost_log.query_text[:100] + '...' if max_cost_log.query_text and len(max_cost_log.query_text) > 100 else max_cost_log.query_text,
                        'cost': float(max_cost_log.cost_usd),
                        'endpoint': max_cost_log.endpoint,
                        'timestamp': max_cost_log.timestamp.isoformat()
                    }
            
            # Cost by endpoint
            cost_by_endpoint = {}
            for log in logs:
                endpoint = log.endpoint
                cost_by_endpoint[endpoint] = cost_by_endpoint.get(endpoint, Decimal('0')) + log.cost_usd
            
            # Cost by user
            cost_by_user = {}
            for log in logs:
                if log.user_id:
                    user = log.user_id
                    cost_by_user[user] = cost_by_user.get(user, Decimal('0')) + log.cost_usd
            
            return UsageSummary(
                period_start=start_date,
                period_end=end_date,
                total_requests=total_requests,
                api_calls=api_calls,
                cache_hits=cache_hits,
                similar_matches=similar_matches,
                total_cost_usd=total_cost,
                cache_savings_usd=cache_savings,
                average_response_time_ms=avg_response_time,
                most_expensive_query=most_expensive,
                cost_by_endpoint={k: float(v) for k, v in cost_by_endpoint.items()},
                cost_by_user={k: float(v) for k, v in cost_by_user.items()}
            )
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return UsageSummary(
                period_start=start_date or datetime.utcnow(),
                period_end=end_date or datetime.utcnow(),
                total_requests=0,
                api_calls=0,
                cache_hits=0,
                similar_matches=0,
                total_cost_usd=Decimal('0'),
                cache_savings_usd=Decimal('0'),
                average_response_time_ms=0.0,
                most_expensive_query=None,
                cost_by_endpoint={},
                cost_by_user={}
            )
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and alert levels"""
        try:
            # Daily usage
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_summary = self.get_usage_summary(start_date=today_start)
            
            # Monthly usage
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_summary = self.get_usage_summary(start_date=month_start)
            
            # Calculate percentages
            daily_percent = float(daily_summary.total_cost_usd / self.daily_budget * 100) if self.daily_budget > 0 else 0
            monthly_percent = float(monthly_summary.total_cost_usd / self.monthly_budget * 100) if self.monthly_budget > 0 else 0
            
            # Determine alert levels
            daily_alert = 'none'
            monthly_alert = 'none'
            
            if daily_percent >= self.critical_threshold * 100:
                daily_alert = 'critical'
            elif daily_percent >= self.warning_threshold * 100:
                daily_alert = 'warning'
            
            if monthly_percent >= self.critical_threshold * 100:
                monthly_alert = 'critical'
            elif monthly_percent >= self.warning_threshold * 100:
                monthly_alert = 'warning'
            
            return {
                'daily': {
                    'budget': float(self.daily_budget),
                    'spent': float(daily_summary.total_cost_usd),
                    'remaining': float(self.daily_budget - daily_summary.total_cost_usd),
                    'percent_used': daily_percent,
                    'alert_level': daily_alert,
                    'requests_today': daily_summary.total_requests,
                    'cache_savings': float(daily_summary.cache_savings_usd)
                },
                'monthly': {
                    'budget': float(self.monthly_budget),
                    'spent': float(monthly_summary.total_cost_usd),
                    'remaining': float(self.monthly_budget - monthly_summary.total_cost_usd),
                    'percent_used': monthly_percent,
                    'alert_level': monthly_alert,
                    'requests_month': monthly_summary.total_requests,
                    'cache_savings': float(monthly_summary.cache_savings_usd)
                },
                'thresholds': {
                    'warning': self.warning_threshold * 100,
                    'critical': self.critical_threshold * 100
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get budget status: {e}")
            return {
                'daily': {'budget': 0, 'spent': 0, 'remaining': 0, 'percent_used': 0, 'alert_level': 'error'},
                'monthly': {'budget': 0, 'spent': 0, 'remaining': 0, 'percent_used': 0, 'alert_level': 'error'},
                'error': str(e)
            }
    
    def _check_budget_alerts(self):
        """Check if budget thresholds have been exceeded and log alerts"""
        try:
            status = self.get_budget_status()
            
            # Check for alerts
            alerts = []
            
            if status['daily']['alert_level'] == 'critical':
                alerts.append(f"CRITICAL: Daily budget {status['daily']['percent_used']:.1f}% used")
            elif status['daily']['alert_level'] == 'warning':
                alerts.append(f"WARNING: Daily budget {status['daily']['percent_used']:.1f}% used")
            
            if status['monthly']['alert_level'] == 'critical':
                alerts.append(f"CRITICAL: Monthly budget {status['monthly']['percent_used']:.1f}% used")
            elif status['monthly']['alert_level'] == 'warning':
                alerts.append(f"WARNING: Monthly budget {status['monthly']['percent_used']:.1f}% used")
            
            # Log alerts
            for alert in alerts:
                logger.warning(f"BUDGET ALERT: {alert}")
                
        except Exception as e:
            logger.error(f"Budget alert check failed: {e}")
    
    def get_cost_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily cost trends for the specified number of days"""
        try:
            trends = []
            
            for i in range(days):
                day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                summary = self.get_usage_summary(start_date=day_start, end_date=day_end)
                
                trends.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'total_cost': float(summary.total_cost_usd),
                    'cache_savings': float(summary.cache_savings_usd),
                    'requests': summary.total_requests,
                    'api_calls': summary.api_calls,
                    'cache_hits': summary.cache_hits,
                    'avg_response_time': summary.average_response_time_ms
                })
            
            return list(reversed(trends))
            
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}")
            return []

# Global instance
cost_tracker = CostTrackingService() 
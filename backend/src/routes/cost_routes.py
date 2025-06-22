from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

try:
    from src.services.cost_tracking_service import cost_tracker
except ImportError:
    # Fallback if cost tracker not available
    cost_tracker = None

logger = logging.getLogger(__name__)

cost_bp = Blueprint('costs', __name__, url_prefix='/api/costs')

@cost_bp.route('/summary', methods=['GET'])
def get_cost_summary():
    """
    Get cost usage summary for a time period.
    
    Query parameters:
    - days: Number of days to look back (default: 1 for today)
    - user_id: Optional user filter
    """
    try:
        if not cost_tracker:
            return jsonify({
                'error': 'Cost tracking service not available',
                'daily': {'budget': 50, 'spent': 0, 'remaining': 50, 'percent_used': 0},
                'monthly': {'budget': 1000, 'spent': 0, 'remaining': 1000, 'percent_used': 0}
            }), 503
        
        days = request.args.get('days', 1, type=int)
        user_id = request.args.get('user_id')
        
        # Calculate start date
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if days > 1:
            start_date = start_date - timedelta(days=days-1)
        
        # Get usage summary
        summary = cost_tracker.get_usage_summary(
            start_date=start_date,
            user_id=user_id
        )
        
        # Get budget status
        budget_status = cost_tracker.get_budget_status()
        
        return jsonify({
            'success': True,
            'period': {
                'start': summary.period_start.isoformat(),
                'end': summary.period_end.isoformat(),
                'days': days
            },
            'usage': {
                'total_requests': summary.total_requests,
                'api_calls': summary.api_calls,
                'cache_hits': summary.cache_hits,
                'similar_matches': summary.similar_matches,
                'total_cost_usd': float(summary.total_cost_usd),
                'cache_savings_usd': float(summary.cache_savings_usd),
                'average_response_time_ms': summary.average_response_time_ms,
                'most_expensive_query': summary.most_expensive_query
            },
            'budgets': budget_status,
            'breakdown': {
                'by_endpoint': summary.cost_by_endpoint,
                'by_user': summary.cost_by_user
            }
        })
        
    except Exception as e:
        logger.error(f"Cost summary endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'daily': {'budget': 50, 'spent': 0, 'remaining': 50, 'percent_used': 0},
            'monthly': {'budget': 1000, 'spent': 0, 'remaining': 1000, 'percent_used': 0}
        }), 500

@cost_bp.route('/budget', methods=['GET'])
def get_budget_status():
    """Get current budget status and alert levels"""
    try:
        if not cost_tracker:
            return jsonify({
                'daily': {
                    'budget': 50.0,
                    'spent': 0.0,
                    'remaining': 50.0,
                    'percent_used': 0.0,
                    'alert_level': 'none',
                    'requests_today': 0,
                    'cache_savings': 0.0
                },
                'monthly': {
                    'budget': 1000.0,
                    'spent': 0.0,
                    'remaining': 1000.0,
                    'percent_used': 0.0,
                    'alert_level': 'none',
                    'requests_month': 0,
                    'cache_savings': 0.0
                },
                'thresholds': {
                    'warning': 75.0,
                    'critical': 90.0
                },
                'timestamp': datetime.utcnow().isoformat(),
                'service_status': 'unavailable'
            })
        
        status = cost_tracker.get_budget_status()
        status['service_status'] = 'active'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Budget status endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'service_status': 'error'
        }), 500

@cost_bp.route('/trends', methods=['GET'])
def get_cost_trends():
    """
    Get cost trends over time.
    
    Query parameters:
    - days: Number of days to include (default: 7)
    """
    try:
        if not cost_tracker:
            # Return mock data for demonstration
            days = request.args.get('days', 7, type=int)
            mock_trends = []
            for i in range(days):
                day = datetime.utcnow() - timedelta(days=i)
                mock_trends.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'total_cost': 0.0,
                    'cache_savings': 0.0,
                    'requests': 0,
                    'api_calls': 0,
                    'cache_hits': 0,
                    'avg_response_time': 0.0
                })
            
            return jsonify({
                'success': True,
                'trends': list(reversed(mock_trends)),
                'service_status': 'unavailable'
            })
        
        days = request.args.get('days', 7, type=int)
        trends = cost_tracker.get_cost_trends(days=days)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'period_days': days,
            'service_status': 'active'
        })
        
    except Exception as e:
        logger.error(f"Cost trends endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'service_status': 'error'
        }), 500

@cost_bp.route('/log', methods=['POST'])
def log_api_usage():
    """
    Manually log an API usage event.
    This endpoint can be used by other services to log their API usage.
    
    Request body:
    {
        "endpoint": "/api/perplexity/search",
        "method": "POST",
        "user_id": "user123",
        "query_text": "What is machine learning?",
        "query_type": "search",
        "response_size_bytes": 1500,
        "response_time_ms": 800,
        "tokens_used": 150,
        "from_cache": "api_call",
        "status": "success"
    }
    """
    try:
        if not cost_tracker:
            return jsonify({
                'success': False,
                'error': 'Cost tracking service not available',
                'estimated_cost': 0.001
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract data with defaults
        endpoint = data.get('endpoint', '/api/unknown')
        method = data.get('method', 'POST')
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        query_text = data.get('query_text')
        query_type = data.get('query_type', 'search')
        response_size_bytes = data.get('response_size_bytes', 0)
        response_time_ms = data.get('response_time_ms', 0)
        tokens_used = data.get('tokens_used', 0)
        from_cache = data.get('from_cache', 'api_call')
        similarity_score = data.get('similarity_score', 0.0)
        status = data.get('status', 'success')
        error_message = data.get('error_message')
        metadata = data.get('metadata', {})
        
        # Log the usage
        log_id = cost_tracker.log_api_call(
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            session_id=session_id,
            request_payload=data,
            query_text=query_text,
            query_type=query_type,
            response_size_bytes=response_size_bytes,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            from_cache=from_cache,
            similarity_score=similarity_score,
            status=status,
            error_message=error_message,
            metadata=metadata
        )
        
        # Calculate estimated cost for response
        cost_breakdown = cost_tracker.calculate_cost(
            endpoint=endpoint,
            tokens_used=tokens_used,
            query_type=query_type,
            response_size=response_size_bytes
        )
        
        return jsonify({
            'success': True,
            'log_id': log_id,
            'estimated_cost_usd': float(cost_breakdown.total_cost),
            'cost_breakdown': {
                'base_cost': float(cost_breakdown.base_cost),
                'token_cost': float(cost_breakdown.token_cost),
                'total_cost': float(cost_breakdown.total_cost)
            },
            'from_cache': from_cache
        })
        
    except Exception as e:
        logger.error(f"API usage logging error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cost_bp.route('/estimate', methods=['POST'])
def estimate_cost():
    """
    Estimate the cost of an API call without logging it.
    
    Request body:
    {
        "endpoint": "/api/perplexity/search",
        "query_text": "What is machine learning?",
        "query_type": "search",
        "tokens_used": 150
    }
    """
    try:
        if not cost_tracker:
            return jsonify({
                'success': True,
                'estimated_cost_usd': 0.005,
                'message': 'Cost tracking service not available - returning default estimate'
            })
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        endpoint = data.get('endpoint', '/api/unknown')
        query_text = data.get('query_text', '')
        query_type = data.get('query_type', 'search')
        tokens_used = data.get('tokens_used', 0)
        
        # Estimate response size if not provided
        response_size = data.get('response_size_bytes', len(query_text) * 2)
        
        # Calculate cost
        cost_breakdown = cost_tracker.calculate_cost(
            endpoint=endpoint,
            tokens_used=tokens_used,
            query_type=query_type,
            response_size=response_size
        )
        
        return jsonify({
            'success': True,
            'estimated_cost_usd': float(cost_breakdown.total_cost),
            'cost_breakdown': {
                'base_cost': float(cost_breakdown.base_cost),
                'token_cost': float(cost_breakdown.token_cost),
                'total_cost': float(cost_breakdown.total_cost),
                'pricing_model': cost_breakdown.pricing_model
            },
            'calculation_details': cost_breakdown.calculation_details
        })
        
    except Exception as e:
        logger.error(f"Cost estimation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'estimated_cost_usd': 0.005  # Fallback estimate
        }), 500

@cost_bp.route('/health', methods=['GET'])
def cost_service_health():
    """Check the health of the cost tracking service"""
    try:
        if not cost_tracker:
            return jsonify({
                'status': 'unavailable',
                'message': 'Cost tracking service not imported',
                'features': {
                    'logging': False,
                    'budget_tracking': False,
                    'cost_estimation': True  # Can still provide basic estimates
                }
            })
        
        # Try to get a simple budget status to test the service
        status = cost_tracker.get_budget_status()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Cost tracking service is operational',
            'features': {
                'logging': True,
                'budget_tracking': True,
                'cost_estimation': True,
                'database_connection': True
            },
            'daily_budget': status.get('daily', {}).get('budget', 0),
            'monthly_budget': status.get('monthly', {}).get('budget', 0)
        })
        
    except Exception as e:
        logger.error(f"Cost service health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Cost tracking service error: {str(e)}',
            'features': {
                'logging': False,
                'budget_tracking': False,
                'cost_estimation': False
            }
        }), 500 
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from src.services.cost_tracking_service import get_cost_tracking_service

logger = logging.getLogger(__name__)

cost_bp = Blueprint('costs', __name__, url_prefix='/api/costs')

@cost_bp.route('/summary', methods=['GET'])
def get_cost_summary():
    """
    Get cost usage summary for a time period.
    """
    try:
        days = int(request.args.get('days', 1))
        user_id = request.args.get('user_id')
        
        # Get cost tracking service
        cost_service = get_cost_tracking_service()
        
        # Get usage summary for the requested period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        summary = cost_service.get_usage_summary(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # Get budget status
        budget_status = cost_service.get_budget_status()
        
        # Calculate projected monthly cost based on current daily average
        if days >= 1:
            daily_avg = float(summary.total_cost_usd) / days
            projected_monthly = daily_avg * 30
        else:
            projected_monthly = 0.0
        
        response_data = {
            'daily': {
                'budget': budget_status['daily']['budget'],
                'spent': budget_status['daily']['spent'],
                'remaining': budget_status['daily']['remaining'],
                'percent_used': budget_status['daily']['percentage'],
                'alert_level': budget_status['daily']['alert_level'],
                'api_calls': budget_status['daily']['requests'],
                'projected_monthly': projected_monthly
            },
            'monthly': {
                'budget': budget_status['monthly']['budget'],
                'spent': budget_status['monthly']['spent'],
                'remaining': budget_status['monthly']['remaining'],
                'percent_used': budget_status['monthly']['percentage'],
                'alert_level': budget_status['monthly']['alert_level'],
                'api_calls': budget_status['monthly']['requests'],
                'days_remaining': (datetime.utcnow().replace(month=datetime.utcnow().month+1, day=1) - datetime.utcnow()).days if datetime.utcnow().month < 12 else (datetime.utcnow().replace(year=datetime.utcnow().year+1, month=1, day=1) - datetime.utcnow()).days
            },
            'cache_efficiency': {
                'hit_rate': budget_status['cache_efficiency']['daily_hit_rate'] / 100 if budget_status['cache_efficiency']['daily_hit_rate'] > 0 else 0,
                'cost_saved': budget_status['cache_efficiency']['daily_savings'],
                'calls_saved': summary.cache_hits + summary.similar_matches
            },
            'recent_activity': []
        }
        
        # Add most expensive query if available
        if summary.most_expensive_query:
            response_data['recent_activity'].append({
                'timestamp': summary.most_expensive_query['timestamp'],
                'endpoint': summary.most_expensive_query['endpoint'],
                'cost': summary.most_expensive_query['cost'],
                'query': summary.most_expensive_query['query'][:100] + '...' if len(summary.most_expensive_query['query']) > 100 else summary.most_expensive_query['query'],
                'response_time': 0  # We don't track this in the summary
            })
        
        return jsonify({
            'success': True,
            'data': response_data,
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Cost summary endpoint failed: {e}")
        return jsonify({'error': 'Failed to retrieve cost summary', 'details': str(e)}), 500

@cost_bp.route('/budget', methods=['GET'])
def get_budget_status():
    """Get current budget status and alerts"""
    try:
        # Get cost tracking service
        cost_service = get_cost_tracking_service()
        budget_status = cost_service.get_budget_status()
        
        # Calculate time remaining
        now = datetime.utcnow()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        time_remaining_hours = int((end_of_day - now).total_seconds() / 3600)
        
        # Build alerts based on status
        alerts = []
        recommendations = []
        
        if budget_status['daily']['alert_level'] == 'critical':
            alerts.append(f"CRITICAL: Daily budget {budget_status['daily']['percentage']:.1f}% used")
        elif budget_status['daily']['alert_level'] == 'warning':
            alerts.append(f"WARNING: Daily budget {budget_status['daily']['percentage']:.1f}% used")
        
        if budget_status['monthly']['alert_level'] == 'critical':
            alerts.append(f"CRITICAL: Monthly budget {budget_status['monthly']['percentage']:.1f}% used")
        elif budget_status['monthly']['alert_level'] == 'warning':
            alerts.append(f"WARNING: Monthly budget {budget_status['monthly']['percentage']:.1f}% used")
        
        # Add recommendations
        if budget_status['cache_efficiency']['daily_hit_rate'] > 70:
            recommendations.append(f"Cache hit rate of {budget_status['cache_efficiency']['daily_hit_rate']:.1f}% is saving significant costs")
        elif budget_status['cache_efficiency']['daily_hit_rate'] > 0:
            recommendations.append("Consider optimizing cache usage to reduce API costs")
        
        if budget_status['daily']['percentage'] < 50:
            recommendations.append("Your current usage is well within daily budget")
        
        budget_data = {
            'daily': {
                'budget': budget_status['daily']['budget'],
                'spent': budget_status['daily']['spent'],
                'percent_used': budget_status['daily']['percentage'],
                'alert_level': budget_status['daily']['alert_level'],
                'time_remaining_hours': time_remaining_hours
            },
            'monthly': {
                'budget': budget_status['monthly']['budget'],
                'spent': budget_status['monthly']['spent'],
                'percent_used': budget_status['monthly']['percentage'],
                'alert_level': budget_status['monthly']['alert_level'],
                'days_remaining': (datetime.utcnow().replace(month=datetime.utcnow().month+1, day=1) - datetime.utcnow()).days if datetime.utcnow().month < 12 else (datetime.utcnow().replace(year=datetime.utcnow().year+1, month=1, day=1) - datetime.utcnow()).days
            },
            'alerts': alerts,
            'recommendations': recommendations
        }
        
        return jsonify(budget_data)
        
    except Exception as e:
        logger.error(f"Budget status endpoint failed: {e}")
        return jsonify({'error': 'Failed to retrieve budget status'}), 500

@cost_bp.route('/trends', methods=['GET'])
def get_cost_trends():
    """Get cost trends over time"""
    try:
        days = int(request.args.get('days', 7))
        
        # Get cost tracking service
        cost_service = get_cost_tracking_service()
        trends_data = cost_service.get_cost_trends(days=days)
        
        # Calculate additional metrics
        if trends_data:
            total_costs = [day['total_cost'] for day in trends_data]
            total_calls = [day['api_calls'] for day in trends_data]
            
            average_daily_cost = sum(total_costs) / len(total_costs) if total_costs else 0
            total_api_calls = sum(total_calls)
            cost_per_call_avg = average_daily_cost / (total_api_calls / len(total_calls)) if total_api_calls > 0 else 0
            
            # Determine trend direction
            if len(total_costs) >= 3:
                recent_avg = sum(total_costs[-3:]) / 3
                earlier_avg = sum(total_costs[:-3]) / len(total_costs[:-3]) if len(total_costs) > 3 else recent_avg
                
                if recent_avg > earlier_avg * 1.1:
                    trend_direction = 'increasing'
                elif recent_avg < earlier_avg * 0.9:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'stable'
        else:
            average_daily_cost = 0
            cost_per_call_avg = 0
            trend_direction = 'stable'
        
        trends = {
            'daily_costs': [
                {
                    'date': day['date'],
                    'cost': day['total_cost'],
                    'calls': day['api_calls']
                }
                for day in trends_data
            ],
            'average_daily_cost': average_daily_cost,
            'trend_direction': trend_direction,
            'cost_per_call_avg': cost_per_call_avg
        }
        
        return jsonify({
            'success': True,
            'data': trends,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Cost trends endpoint failed: {e}")
        return jsonify({'error': 'Failed to retrieve cost trends'}), 500

@cost_bp.route('/realtime', methods=['GET'])
def get_realtime_costs():
    """Get real-time cost information"""
    try:
        # Get cost tracking service
        cost_service = get_cost_tracking_service()
        
        # Get today's summary
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_summary = cost_service.get_usage_summary(start_date=today)
        
        # Get current session data (last hour)
        session_start = datetime.utcnow() - timedelta(hours=1)
        session_summary = cost_service.get_usage_summary(start_date=session_start)
        
        realtime_data = {
            'current_session': {
                'api_calls': session_summary.api_calls,
                'cache_hits': session_summary.cache_hits,
                'total_cost': float(session_summary.total_cost_usd),
                'session_start': session_start.isoformat()
            },
            'today_so_far': {
                'api_calls': today_summary.api_calls,
                'cache_hits': today_summary.cache_hits,
                'total_cost': float(today_summary.total_cost_usd),
                'cost_saved': float(today_summary.cache_savings_usd)
            },
            'most_expensive_query': today_summary.most_expensive_query
        }
        
        return jsonify(realtime_data)
        
    except Exception as e:
        logger.error(f"Realtime costs endpoint failed: {e}")
        return jsonify({'error': 'Failed to retrieve realtime costs'}), 500

@cost_bp.route('/health', methods=['GET'])
def cost_health():
    """Health check for cost tracking service"""
    try:
        # Test the cost tracking service
        cost_service = get_cost_tracking_service()
        
        # Try to get a simple summary to test database connectivity
        test_summary = cost_service.get_usage_summary()
        database_connected = True
        
        return jsonify({
            'status': 'healthy',
            'service': 'cost_tracking',
            'version': '1.0.0',
            'database_connected': database_connected,
            'mock_data': False,
            'supabase_integration': True
        })
        
    except Exception as e:
        logger.error(f"Cost health check failed: {e}")
        return jsonify({
            'status': 'degraded',
            'service': 'cost_tracking',
            'version': '1.0.0',
            'database_connected': False,
            'mock_data': False,
            'error': str(e)
        }), 503 
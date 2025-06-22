from flask import Blueprint, jsonify, request
import logging
import asyncio
from ..services.cache_service import get_cache
from ..config.feature_flags import feature_flags, is_enabled

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__)

@performance_bp.route('/performance/summary', methods=['GET'])
def get_performance_summary():
    """Get comprehensive performance summary"""
    try:
        if not is_enabled('performance_monitoring'):
            return jsonify({
                'status': 'disabled',
                'message': 'Performance monitoring is disabled via feature flag'
            }), 503
            
        cache = get_cache()
        summary = {
            'cache_stats': cache.get_stats(),
            'redis_enabled': cache.use_redis and is_enabled('redis_cache_enabled'),
            'performance_monitoring': 'active',
            'generated_at': cache.get_stats().get('timestamp', 'unknown'),
            'feature_flags': feature_flags.get_enabled_flags()
        }
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@performance_bp.route('/performance/cache-stats', methods=['GET'])
def get_cache_stats():
    """Get current cache statistics"""
    try:
        if not is_enabled('redis_cache_enabled'):
            return jsonify({
                'status': 'disabled',
                'message': 'Redis cache is disabled via feature flag'
            }), 503
            
        cache = get_cache()
        stats = cache.get_stats()
        return jsonify({
            'status': 'success',
            'data': {
                'cache_stats': stats,
                'redis_enabled': cache.use_redis,
                'intelligent_caching': is_enabled('intelligent_caching'),
                'timestamp': cache.get_stats().get('timestamp', 'unknown')
            }
        })
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@performance_bp.route('/performance/health', methods=['GET'])
def performance_health():
    """Performance monitoring health check"""
    try:
        cache = get_cache()
        return jsonify({
            'status': 'healthy',
            'performance_monitoring': 'enabled' if is_enabled('performance_monitoring') else 'disabled',
            'redis_cache': 'enabled' if (cache.use_redis and is_enabled('redis_cache_enabled')) else 'disabled',
            'analytics_tracking': 'enabled' if is_enabled('detailed_analytics') else 'basic',
            'cost_tracking': 'enabled' if is_enabled('cost_tracking') else 'disabled',
            'timestamp': cache.get_stats().get('timestamp', 'unknown')
        })
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@performance_bp.route('/performance/feature-flags', methods=['GET'])
def get_feature_flags():
    """Get current feature flag configuration"""
    try:
        return jsonify({
            'status': 'success',
            'data': feature_flags.to_dict()
        })
    except Exception as e:
        logger.error(f"Failed to get feature flags: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@performance_bp.route('/performance/feature-flags/<flag_name>', methods=['POST'])
def toggle_feature_flag(flag_name):
    """Toggle a feature flag (for testing/admin use)"""
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        if flag_name not in feature_flags.get_all_flags():
            return jsonify({
                'status': 'error',
                'message': f'Unknown feature flag: {flag_name}'
            }), 404
        
        feature_flags.set_flag(flag_name, enabled)
        
        return jsonify({
            'status': 'success',
            'data': {
                'flag': flag_name,
                'enabled': enabled,
                'message': f'Feature flag {flag_name} {"enabled" if enabled else "disabled"}'
            }
        })
    except Exception as e:
        logger.error(f"Failed to toggle feature flag {flag_name}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@performance_bp.route('/performance/cost-tracking', methods=['GET'])
def get_cost_tracking():
    """Get cost tracking information"""
    try:
        if not is_enabled('cost_tracking'):
            return jsonify({
                'status': 'disabled',
                'message': 'Cost tracking is disabled via feature flag'
            }), 503
        
        cache = get_cache()
        stats = cache.get_stats()
        
        # Calculate estimated cost savings
        api_calls_saved = stats.get('api_calls_saved', 0)
        estimated_cost_per_call = 0.01  # $0.01 per API call estimate
        estimated_savings = api_calls_saved * estimated_cost_per_call
        
        return jsonify({
            'status': 'success',
            'data': {
                'cost_tracking_enabled': True,
                'api_calls_saved': api_calls_saved,
                'estimated_cost_per_call': estimated_cost_per_call,
                'estimated_total_savings': round(estimated_savings, 4),
                'cache_hit_rate': stats.get('hit_rate_percent', 0),
                'timestamp': stats.get('timestamp', 'unknown')
            }
        })
    except Exception as e:
        logger.error(f"Failed to get cost tracking: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 
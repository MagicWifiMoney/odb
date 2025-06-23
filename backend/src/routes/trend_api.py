"""
Trend Analysis API Endpoints
Flask blueprints for trend analysis and anomaly detection
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps

from ..services.trend_service import get_trend_service
from ..services.cache_service import CacheStrategy

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
trend_bp = Blueprint('trends', __name__, url_prefix='/api/trends')

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            # Create new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(f(*args, **kwargs))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Async route error: {e}")
            return jsonify({"error": str(e)}), 500
    return wrapper

def validate_date_range(start_date_str: str, end_date_str: str = None):
    """Validate and parse date range parameters"""
    try:
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()
        
        # Validate range
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        # Limit to reasonable range (2 years max)
        max_range = timedelta(days=730)
        if end_date - start_date > max_range:
            raise ValueError("Date range cannot exceed 2 years")
        
        return start_date, end_date
        
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

@trend_bp.route('/daily', methods=['GET'])
@async_route
async def get_daily_trends():
    """
    Get daily trend analysis
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90, max: 365)
    - include_forecast: Include trend forecast (default: false)
    """
    try:
        # Parse parameters
        days_back = min(int(request.args.get('days_back', 90)), 365)
        include_forecast = request.args.get('include_forecast', 'false').lower() == 'true'
        
        # Get trend service
        trend_service = get_trend_service()
        
        # Analyze daily trends
        result = await trend_service.analyze_daily_trends(days_back)
        
        # Add forecast if requested
        if include_forecast and 'trends' in result:
            forecasts = {}
            for metric in ['opportunity_count', 'total_value']:
                if metric in result['trends']:
                    forecast = await trend_service.get_trend_forecast(metric, 30)
                    if 'error' not in forecast:
                        forecasts[metric] = forecast
            
            if forecasts:
                result['forecasts'] = forecasts
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "daily_trends",
                "timestamp": datetime.utcnow().isoformat(),
                "cache_info": "Cached for 12 hours"
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Daily trends API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/weekly', methods=['GET'])
@async_route
async def get_weekly_trends():
    """Get weekly trend analysis"""
    try:
        weeks_back = min(int(request.args.get('weeks_back', 12)), 52)
        days_back = weeks_back * 7
        
        trend_service = get_trend_service()
        result = await trend_service.analyze_daily_trends(days_back)
        
        # Modify analysis type in response
        if 'analysis_type' in result:
            result['analysis_type'] = 'weekly'
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "weekly_trends",
                "weeks_analyzed": weeks_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Weekly trends API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/anomalies', methods=['GET'])
@async_route
async def get_anomalies():
    """
    Detect anomalies in opportunity data
    
    Query Parameters:
    - analysis_type: daily, weekly, monthly (default: daily)
    - sensitivity: 1.0-5.0 (default: 2.5, lower = more sensitive)
    - limit: Maximum number of anomalies to return (default: 20, max: 100)
    """
    try:
        analysis_type = request.args.get('analysis_type', 'daily')
        sensitivity = float(request.args.get('sensitivity', 2.5))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Validate parameters
        if analysis_type not in ['daily', 'weekly', 'monthly']:
            return jsonify({"error": "Invalid analysis_type"}), 400
        
        if not 1.0 <= sensitivity <= 5.0:
            return jsonify({"error": "Sensitivity must be between 1.0 and 5.0"}), 400
        
        trend_service = get_trend_service()
        result = await trend_service.detect_anomalies(analysis_type, sensitivity)
        
        # Limit results
        if 'anomalies' in result:
            result['anomalies'] = result['anomalies'][:limit]
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "anomalies",
                "analysis_type": analysis_type,
                "sensitivity": sensitivity,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Anomalies API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/keywords', methods=['GET'])
@async_route
async def get_keyword_trends():
    """
    Analyze keyword trends
    
    Query Parameters:
    - keywords: Comma-separated list of keywords to analyze
    - days_back: Number of days to analyze (default: 30, max: 90)
    """
    try:
        keywords_param = request.args.get('keywords', '')
        keywords = [k.strip() for k in keywords_param.split(',') if k.strip()] if keywords_param else None
        days_back = min(int(request.args.get('days_back', 30)), 90)
        
        trend_service = get_trend_service()
        result = await trend_service.analyze_keyword_trends(keywords, days_back)
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "keyword_trends",
                "target_keywords": keywords,
                "days_analyzed": days_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Keyword trends API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/forecast/<metric>', methods=['GET'])
@async_route
async def get_trend_forecast(metric):
    """
    Get trend forecast for a specific metric
    
    Path Parameters:
    - metric: opportunity_count, total_value, avg_value
    
    Query Parameters:
    - days_ahead: Number of days to forecast (default: 30, max: 90)
    """
    try:
        # Validate metric
        valid_metrics = ['opportunity_count', 'total_value', 'avg_value']
        if metric not in valid_metrics:
            return jsonify({
                "error": f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
            }), 400
        
        days_ahead = min(int(request.args.get('days_ahead', 30)), 90)
        
        trend_service = get_trend_service()
        result = await trend_service.get_trend_forecast(metric, days_ahead)
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "trend_forecast",
                "metric": metric,
                "forecast_days": days_ahead,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Trend forecast API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/industries', methods=['GET'])
@async_route
async def get_industry_trends():
    """Get trend analysis by industry"""
    try:
        days_back = min(int(request.args.get('days_back', 60)), 180)
        
        trend_service = get_trend_service()
        
        # Get daily trends which includes industry analysis
        result = await trend_service.analyze_daily_trends(days_back)
        
        # Extract industry-specific data
        industry_data = result.get('industry_trends', {})
        
        return jsonify({
            "success": True,
            "data": {
                "industries": industry_data,
                "analysis_period": {
                    "days_back": days_back,
                    "date_range": result.get('date_range', {})
                },
                "summary": {
                    "total_industries": len(industry_data),
                    "trending_industries": [
                        industry for industry, data in industry_data.items()
                        if data.get('trend', {}).get('trend_type') == 'increasing'
                    ]
                }
            },
            "meta": {
                "endpoint": "industry_trends",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Industry trends API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/summary', methods=['GET'])
@async_route
async def get_trends_summary():
    """Get comprehensive trends summary dashboard"""
    try:
        # Get overview data
        trend_service = get_trend_service()
        
        # Get data for different time periods
        daily_trends = await trend_service.analyze_daily_trends(30)
        weekly_trends = await trend_service.analyze_daily_trends(90)
        anomalies = await trend_service.detect_anomalies('daily', 2.5)
        keyword_trends = await trend_service.analyze_keyword_trends(None, 30)
        
        # Compile summary
        summary = {
            "overview": {
                "30_day_trends": daily_trends.get('summary', {}),
                "90_day_trends": weekly_trends.get('summary', {}),
                "recent_anomalies": len(anomalies.get('anomalies', [])),
                "trending_keywords": len(keyword_trends.get('trending_keywords', []))
            },
            "key_metrics": {
                "opportunity_trend": daily_trends.get('trends', {}).get('opportunity_count', {}),
                "value_trend": daily_trends.get('trends', {}).get('total_value', {}),
                "top_anomalies": anomalies.get('anomalies', [])[:5],
                "top_keywords": keyword_trends.get('trending_keywords', [])[:10]
            },
            "insights": {
                "daily_ai_insights": daily_trends.get('ai_insights', {}),
                "anomaly_analysis": anomalies.get('ai_analysis', {}),
                "keyword_suggestions": keyword_trends.get('ai_suggestions', {})
            }
        }
        
        return jsonify({
            "success": True,
            "data": summary,
            "meta": {
                "endpoint": "trends_summary",
                "generated_at": datetime.utcnow().isoformat(),
                "data_freshness": "Real-time analysis"
            }
        })
        
    except Exception as e:
        logger.error(f"Trends summary API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@trend_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for trend analysis service"""
    try:
        trend_service = get_trend_service()
        
        return jsonify({
            "status": "healthy",
            "service": "trend_analysis",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "daily_trends": True,
                "anomaly_detection": True,
                "keyword_analysis": True,
                "forecasting": True,
                "industry_analysis": True,
                "ai_insights": True
            }
        })
        
    except Exception as e:
        logger.error(f"Trend service health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Error handlers
@trend_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/trends/daily",
            "/api/trends/weekly", 
            "/api/trends/anomalies",
            "/api/trends/keywords",
            "/api/trends/forecast/<metric>",
            "/api/trends/industries",
            "/api/trends/summary",
            "/api/trends/health"
        ]
    }), 404

@trend_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred in the trend analysis service"
    }), 500
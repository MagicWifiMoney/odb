from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from src.services.trend_analysis_service import TrendAnalysisService
from src.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

trend_bp = Blueprint('trend', __name__, url_prefix='/api/trend')

@trend_bp.route('/analyze', methods=['POST'])
def run_trend_analysis():
    """
    Run time-series trend analysis on RFP data.
    
    Request body:
    {
        "days_back": 90,
        "analysis_types": ["daily", "weekly"],
        "detection_methods": ["isolation_forest", "lof", "statistical"]
    }
    """
    try:
        data = request.get_json() or {}
        
        # Extract parameters with defaults
        days_back = data.get('days_back', 90)
        analysis_types = data.get('analysis_types', ['daily', 'weekly'])
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({
                'error': 'days_back must be between 1 and 365'
            }), 400
        
        valid_analysis_types = ['daily', 'weekly', 'monthly']
        if not all(t in valid_analysis_types for t in analysis_types):
            return jsonify({
                'error': f'analysis_types must be one of: {valid_analysis_types}'
            }), 400
        
        # Initialize service and run analysis
        trend_service = TrendAnalysisService()
        results = trend_service.run_full_analysis(
            days_back=days_back,
            analysis_types=analysis_types
        )
        
        # Track analytics
        analytics_service.track_custom_event(
            'trend_analysis_requested',
            {
                'days_back': days_back,
                'analysis_types': analysis_types,
                'success': results.get('success', False),
                'data_points': results.get('data_points', 0)
            }
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in trend analysis: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@trend_bp.route('/anomalies', methods=['GET'])
def get_recent_anomalies():
    """
    Get recent anomalies detected by the trend analysis system.
    
    Query parameters:
    - limit: Number of anomalies to return (default: 10)
    - days: Number of days to look back (default: 30)
    - min_score: Minimum anomaly score (default: 5.0)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        days = request.args.get('days', 30, type=int)
        min_score = request.args.get('min_score', 5.0, type=float)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        if days < 1 or days > 365:
            return jsonify({'error': 'days must be between 1 and 365'}), 400
        
        if min_score < 0 or min_score > 10:
            return jsonify({'error': 'min_score must be between 0 and 10'}), 400
        
        # Query database for recent anomalies
        from sqlalchemy import text
        from src.database import db
        
        query = text("""
            SELECT 
                analysis_date,
                analysis_type,
                opportunity_count,
                total_value,
                anomaly_score,
                anomaly_type,
                trending_keywords,
                rolling_30_day_avg
            FROM trend_analysis 
            WHERE 
                is_anomaly = true 
                AND analysis_date >= :start_date
                AND anomaly_score >= :min_score
            ORDER BY anomaly_score DESC, analysis_date DESC
            LIMIT :limit
        """)
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = db.session.execute(query, {
            'start_date': start_date.date(),
            'min_score': min_score,
            'limit': limit
        })
        
        anomalies = []
        for row in result:
            anomaly = {
                'analysis_date': row.analysis_date.isoformat() if row.analysis_date else None,
                'analysis_type': row.analysis_type,
                'opportunity_count': row.opportunity_count,
                'total_value': float(row.total_value) if row.total_value else 0,
                'anomaly_score': float(row.anomaly_score) if row.anomaly_score else 0,
                'anomaly_type': row.anomaly_type,
                'trending_keywords': row.trending_keywords,
                'rolling_30_day_avg': float(row.rolling_30_day_avg) if row.rolling_30_day_avg else 0
            }
            anomalies.append(anomaly)
        
        return jsonify({
            'anomalies': anomalies,
            'count': len(anomalies),
            'parameters': {
                'limit': limit,
                'days': days,
                'min_score': min_score
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@trend_bp.route('/metrics', methods=['GET'])
def get_trend_metrics():
    """
    Get aggregated trend metrics for dashboard display.
    
    Query parameters:
    - period: 'week', 'month', 'quarter' (default: 'month')
    - analysis_type: 'daily', 'weekly', 'monthly' (default: 'daily')
    """
    try:
        period = request.args.get('period', 'month')
        analysis_type = request.args.get('analysis_type', 'daily')
        
        # Validate parameters
        valid_periods = ['week', 'month', 'quarter']
        if period not in valid_periods:
            return jsonify({'error': f'period must be one of: {valid_periods}'}), 400
        
        valid_analysis_types = ['daily', 'weekly', 'monthly']
        if analysis_type not in valid_analysis_types:
            return jsonify({'error': f'analysis_type must be one of: {valid_analysis_types}'}), 400
        
        # Calculate date range based on period
        end_date = datetime.now().date()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # quarter
            start_date = end_date - timedelta(days=90)
        
        # Query aggregated metrics
        from sqlalchemy import text
        from src.database import db
        
        query = text("""
            SELECT 
                COUNT(*) as total_periods,
                SUM(opportunity_count) as total_opportunities,
                AVG(opportunity_count) as avg_opportunities_per_period,
                SUM(total_value) as total_value,
                AVG(total_value) as avg_value_per_period,
                COUNT(CASE WHEN is_anomaly = true THEN 1 END) as anomaly_count,
                AVG(anomaly_score) as avg_anomaly_score,
                MAX(analysis_date) as latest_analysis,
                MIN(analysis_date) as earliest_analysis
            FROM trend_analysis 
            WHERE 
                analysis_type = :analysis_type
                AND analysis_date >= :start_date 
                AND analysis_date <= :end_date
        """)
        
        result = db.session.execute(query, {
            'analysis_type': analysis_type,
            'start_date': start_date,
            'end_date': end_date
        }).fetchone()
        
        if result:
            metrics = {
                'period': period,
                'analysis_type': analysis_type,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_periods': result.total_periods or 0,
                'total_opportunities': result.total_opportunities or 0,
                'avg_opportunities_per_period': float(result.avg_opportunities_per_period) if result.avg_opportunities_per_period else 0,
                'total_value': float(result.total_value) if result.total_value else 0,
                'avg_value_per_period': float(result.avg_value_per_period) if result.avg_value_per_period else 0,
                'anomaly_count': result.anomaly_count or 0,
                'avg_anomaly_score': float(result.avg_anomaly_score) if result.avg_anomaly_score else 0,
                'latest_analysis': result.latest_analysis.isoformat() if result.latest_analysis else None,
                'earliest_analysis': result.earliest_analysis.isoformat() if result.earliest_analysis else None
            }
        else:
            metrics = {
                'period': period,
                'analysis_type': analysis_type,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'message': 'No data available for the specified period'
            }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error fetching trend metrics: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@trend_bp.route('/keywords/trending', methods=['GET'])
def get_trending_keywords():
    """
    Get currently trending keywords from recent trend analysis.
    
    Query parameters:
    - days: Number of days to analyze (default: 7)
    - limit: Number of keywords to return (default: 20)
    """
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Validate parameters
        if days < 1 or days > 90:
            return jsonify({'error': 'days must be between 1 and 90'}), 400
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        # Query trending keywords
        from sqlalchemy import text
        from src.database import db
        import json
        
        query = text("""
            SELECT trending_keywords, analysis_date
            FROM trend_analysis 
            WHERE 
                analysis_date >= :start_date
                AND trending_keywords IS NOT NULL
                AND trending_keywords != 'null'
                AND trending_keywords != '{}'
            ORDER BY analysis_date DESC
        """)
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = db.session.execute(query, {
            'start_date': start_date.date()
        })
        
        # Aggregate keyword counts
        keyword_totals = {}
        for row in result:
            try:
                if isinstance(row.trending_keywords, str):
                    keywords = json.loads(row.trending_keywords)
                else:
                    keywords = row.trending_keywords
                
                if isinstance(keywords, dict):
                    for keyword, count in keywords.items():
                        if keyword in keyword_totals:
                            keyword_totals[keyword] += count
                        else:
                            keyword_totals[keyword] = count
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Sort by total count and limit results
        trending_keywords = sorted(
            keyword_totals.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        return jsonify({
            'trending_keywords': [
                {'keyword': keyword, 'count': count} 
                for keyword, count in trending_keywords
            ],
            'total_keywords': len(trending_keywords),
            'analysis_period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error fetching trending keywords: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500 
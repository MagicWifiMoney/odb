"""
Win Probability API Endpoints
Flask blueprints for win probability predictions and model management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import logging
from functools import wraps

from ..services.win_probability_service import get_win_probability_service

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
win_probability_bp = Blueprint('win_probability', __name__, url_prefix='/api/win-probability')

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

@win_probability_bp.route('/predict/<opportunity_id>', methods=['GET'])
@async_route
async def predict_opportunity_win_probability(opportunity_id):
    """
    Predict win probability for a specific opportunity
    
    Path Parameters:
    - opportunity_id: ID of the opportunity to analyze
    
    Query Parameters:
    - company_id: ID of the company (optional, defaults to current user's company)
    """
    try:
        company_id = request.args.get('company_id')
        
        service = get_win_probability_service()
        prediction = await service.predict_win_probability(opportunity_id, company_id)
        
        if 'error' in prediction:
            return jsonify({
                "success": False,
                "error": prediction['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": prediction,
            "meta": {
                "endpoint": "predict_win_probability",
                "opportunity_id": opportunity_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Win probability prediction API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/batch-predict', methods=['POST'])
@async_route
async def batch_predict_win_probabilities():
    """
    Predict win probabilities for multiple opportunities
    
    Request Body:
    {
        "opportunity_ids": ["opp1", "opp2", "opp3"],
        "company_id": "optional_company_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'opportunity_ids' not in data:
            return jsonify({"error": "opportunity_ids required in request body"}), 400
        
        opportunity_ids = data['opportunity_ids']
        company_id = data.get('company_id')
        
        if not isinstance(opportunity_ids, list) or len(opportunity_ids) == 0:
            return jsonify({"error": "opportunity_ids must be a non-empty list"}), 400
        
        if len(opportunity_ids) > 50:
            return jsonify({"error": "Maximum 50 opportunities per batch request"}), 400
        
        service = get_win_probability_service()
        predictions = await service.batch_predict_opportunities(opportunity_ids, company_id)
        
        # Separate successful predictions from errors
        successful = [p for p in predictions if 'error' not in p]
        errors = [p for p in predictions if 'error' in p]
        
        return jsonify({
            "success": True,
            "data": {
                "predictions": successful,
                "errors": errors,
                "summary": {
                    "total_requested": len(opportunity_ids),
                    "successful_predictions": len(successful),
                    "failed_predictions": len(errors)
                }
            },
            "meta": {
                "endpoint": "batch_predict",
                "batch_size": len(opportunity_ids),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Batch prediction API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/top-opportunities', methods=['GET'])
@async_route
async def get_top_opportunities():
    """
    Get opportunities ranked by win probability
    
    Query Parameters:
    - limit: Maximum number of opportunities to return (default: 20, max: 100)
    - company_id: ID of the company (optional)
    - min_probability: Minimum win probability threshold (0.0-1.0)
    """
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        company_id = request.args.get('company_id')
        min_probability = float(request.args.get('min_probability', 0.0))
        
        if not 0.0 <= min_probability <= 1.0:
            return jsonify({"error": "min_probability must be between 0.0 and 1.0"}), 400
        
        service = get_win_probability_service()
        opportunities = await service.get_top_opportunities(company_id, limit)
        
        if 'error' in opportunities:
            return jsonify({
                "success": False,
                "error": opportunities['error']
            }), 400
        
        # Filter by minimum probability if specified
        if min_probability > 0.0:
            opportunities = [
                opp for opp in opportunities 
                if opp.get('win_probability', 0) >= min_probability
            ]
        
        return jsonify({
            "success": True,
            "data": {
                "opportunities": opportunities,
                "summary": {
                    "total_opportunities": len(opportunities),
                    "avg_win_probability": sum(o.get('win_probability', 0) for o in opportunities) / max(1, len(opportunities)),
                    "min_probability_filter": min_probability
                }
            },
            "meta": {
                "endpoint": "top_opportunities",
                "limit": limit,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Top opportunities API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/analyze-factors/<opportunity_id>', methods=['GET'])
@async_route
async def analyze_prediction_factors(opportunity_id):
    """
    Analyze factors that influence win probability prediction
    
    Path Parameters:
    - opportunity_id: ID of the opportunity to analyze
    """
    try:
        service = get_win_probability_service()
        analysis = await service.analyze_prediction_factors(opportunity_id)
        
        if 'error' in analysis:
            return jsonify({
                "success": False,
                "error": analysis['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": analysis,
            "meta": {
                "endpoint": "analyze_factors",
                "opportunity_id": opportunity_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Factor analysis API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/model/train', methods=['POST'])
@async_route
async def train_model():
    """
    Train or retrain the win probability model
    
    Request Body:
    {
        "retrain": true/false  // Force retrain even if recent model exists
    }
    """
    try:
        data = request.get_json() or {}
        retrain = data.get('retrain', False)
        
        service = get_win_probability_service()
        result = await service.train_model(retrain)
        
        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result,
            "meta": {
                "endpoint": "train_model",
                "retrain_forced": retrain,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Model training API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/model/performance', methods=['GET'])
@async_route
async def get_model_performance():
    """
    Get current model performance metrics and status
    """
    try:
        service = get_win_probability_service()
        performance = await service.get_model_performance()
        
        if 'error' in performance:
            return jsonify({
                "success": False,
                "error": performance['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": performance,
            "meta": {
                "endpoint": "model_performance",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Model performance API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/insights/<opportunity_id>', methods=['GET'])
@async_route
async def get_opportunity_insights(opportunity_id):
    """
    Get comprehensive insights and recommendations for an opportunity
    
    Path Parameters:
    - opportunity_id: ID of the opportunity
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - include_ai_analysis: Include AI-powered strategic analysis (default: true)
    """
    try:
        company_id = request.args.get('company_id')
        include_ai = request.args.get('include_ai_analysis', 'true').lower() == 'true'
        
        service = get_win_probability_service()
        
        # Get prediction with AI insights
        prediction = await service.predict_win_probability(opportunity_id, company_id)
        
        if 'error' in prediction:
            return jsonify({
                "success": False,
                "error": prediction['error']
            }), 400
        
        # Get factor analysis
        factors = await service.analyze_prediction_factors(opportunity_id)
        
        # Combine insights
        insights = {
            "prediction": {
                "win_probability": prediction.get('win_probability'),
                "confidence_score": prediction.get('confidence_score'),
                "risk_factors": prediction.get('risk_factors', []),
                "success_factors": prediction.get('success_factors', []),
                "competitive_analysis": prediction.get('competitive_analysis', {})
            },
            "factor_analysis": factors.get('feature_analysis', {}),
            "recommendations": {
                "key_focus_areas": factors.get('key_factors', {}).get('top_positive', [])[:3],
                "areas_to_improve": factors.get('key_factors', {}).get('top_negative', [])[:3],
                "strategic_priorities": prediction.get('success_factors', [])[:3]
            }
        }
        
        if include_ai and 'ai_insights' in prediction:
            insights['ai_analysis'] = prediction['ai_insights']
        
        return jsonify({
            "success": True,
            "data": insights,
            "meta": {
                "endpoint": "opportunity_insights",
                "opportunity_id": opportunity_id,
                "ai_analysis_included": include_ai,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Opportunity insights API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/dashboard', methods=['GET'])
@async_route
async def get_win_probability_dashboard():
    """
    Get comprehensive win probability dashboard data
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - days_back: Number of days of data to include (default: 30, max: 90)
    """
    try:
        company_id = request.args.get('company_id')
        days_back = min(int(request.args.get('days_back', 30)), 90)
        
        service = get_win_probability_service()
        
        # Get top opportunities
        top_opportunities = await service.get_top_opportunities(company_id, 10)
        
        # Get model performance
        model_performance = await service.get_model_performance()
        
        # Calculate summary statistics
        if isinstance(top_opportunities, list) and top_opportunities:
            probabilities = [opp.get('win_probability', 0) for opp in top_opportunities]
            avg_probability = sum(probabilities) / len(probabilities)
            high_probability_count = len([p for p in probabilities if p > 0.7])
            medium_probability_count = len([p for p in probabilities if 0.3 <= p <= 0.7])
            low_probability_count = len([p for p in probabilities if p < 0.3])
        else:
            avg_probability = 0
            high_probability_count = 0
            medium_probability_count = 0
            low_probability_count = 0
        
        dashboard = {
            "summary": {
                "total_opportunities": len(top_opportunities) if isinstance(top_opportunities, list) else 0,
                "avg_win_probability": avg_probability,
                "high_probability_opportunities": high_probability_count,
                "medium_probability_opportunities": medium_probability_count,
                "low_probability_opportunities": low_probability_count
            },
            "top_opportunities": top_opportunities[:5] if isinstance(top_opportunities, list) else [],
            "model_status": model_performance,
            "insights": {
                "trending_up": high_probability_count > medium_probability_count,
                "recommendation": "Focus on high-probability opportunities" if high_probability_count > 0 else "Consider improving proposal strategy",
                "total_estimated_value": sum(
                    opp.get('opportunity', {}).get('estimated_value', 0) 
                    for opp in (top_opportunities[:10] if isinstance(top_opportunities, list) else [])
                )
            }
        }
        
        return jsonify({
            "success": True,
            "data": dashboard,
            "meta": {
                "endpoint": "win_probability_dashboard",
                "days_back": days_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@win_probability_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for win probability service"""
    try:
        service = get_win_probability_service()
        
        return jsonify({
            "status": "healthy",
            "service": "win_probability",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "prediction": True,
                "batch_prediction": True,
                "factor_analysis": True,
                "model_training": True,
                "ai_insights": True,
                "top_opportunities": True,
                "dashboard": True
            },
            "model_status": "trained" if service.ml_engine.is_trained else "not_trained"
        })
        
    except Exception as e:
        logger.error(f"Win probability service health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Error handlers
@win_probability_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/win-probability/predict/<opportunity_id>",
            "/api/win-probability/batch-predict",
            "/api/win-probability/top-opportunities",
            "/api/win-probability/analyze-factors/<opportunity_id>",
            "/api/win-probability/model/train",
            "/api/win-probability/model/performance",
            "/api/win-probability/insights/<opportunity_id>",
            "/api/win-probability/dashboard",
            "/api/win-probability/health"
        ]
    }), 404

@win_probability_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred in the win probability service"
    }), 500
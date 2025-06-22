"""
Fast-Fail Filter API Endpoints
Flask blueprints for opportunity filtering and rule management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import logging
from functools import wraps

from ..services.fast_fail_service import get_fast_fail_service

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
fast_fail_bp = Blueprint('fast_fail', __name__, url_prefix='/api/fast-fail')

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

@fast_fail_bp.route('/assess/<opportunity_id>', methods=['GET'])
@async_route
async def assess_opportunity(opportunity_id):
    """
    Assess a single opportunity for fast-fail filtering
    
    Path Parameters:
    - opportunity_id: ID of the opportunity to assess
    
    Query Parameters:
    - company_id: ID of the company (optional, defaults to current user's company)
    - force_refresh: Force new assessment even if cached (default: false)
    """
    try:
        company_id = request.args.get('company_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        service = get_fast_fail_service()
        
        # Clear cache if force refresh requested
        if force_refresh:
            cache_key = f"fast_fail_assessment:{opportunity_id}:{company_id or 'default'}"
            await service.cache.delete(cache_key)
        
        assessment = await service.assess_opportunity(opportunity_id, company_id)
        
        if 'error' in assessment:
            return jsonify({
                "success": False,
                "error": assessment['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": assessment,
            "meta": {
                "endpoint": "assess_opportunity",
                "opportunity_id": opportunity_id,
                "timestamp": datetime.utcnow().isoformat(),
                "force_refresh": force_refresh
            }
        })
        
    except Exception as e:
        logger.error(f"Fast-fail assessment API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/batch-assess', methods=['POST'])
@async_route
async def batch_assess_opportunities():
    """
    Assess multiple opportunities in batch
    
    Request Body:
    {
        "opportunity_ids": ["id1", "id2", "id3"],
        "company_id": "optional_company_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        opportunity_ids = data.get('opportunity_ids', [])
        company_id = data.get('company_id')
        
        if not opportunity_ids:
            return jsonify({"error": "opportunity_ids required"}), 400
        
        if len(opportunity_ids) > 100:
            return jsonify({"error": "Maximum 100 opportunities per batch"}), 400
        
        service = get_fast_fail_service()
        results = await service.batch_assess_opportunities(opportunity_ids, company_id)
        
        if 'error' in results:
            return jsonify({
                "success": False,
                "error": results['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": results,
            "meta": {
                "endpoint": "batch_assess",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Batch assessment API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/dashboard', methods=['GET'])
@async_route
async def get_filter_dashboard():
    """
    Get comprehensive fast-fail filter dashboard
    
    Query Parameters:
    - company_id: ID of the company (optional)
    """
    try:
        company_id = request.args.get('company_id')
        
        service = get_fast_fail_service()
        dashboard = await service.get_filter_dashboard(company_id)
        
        if 'error' in dashboard:
            return jsonify({
                "success": False,
                "error": dashboard['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": dashboard,
            "meta": {
                "endpoint": "filter_dashboard",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/rules', methods=['GET'])
def get_filter_rules():
    """
    Get all filter rules
    
    Query Parameters:
    - enabled_only: Show only enabled rules (default: true)
    - rule_type: Filter by rule type (optional)
    - priority: Filter by priority level (optional)
    """
    try:
        enabled_only = request.args.get('enabled_only', 'true').lower() == 'true'
        rule_type_filter = request.args.get('rule_type')
        priority_filter = request.args.get('priority')
        
        service = get_fast_fail_service()
        rules = service.engine.list_rules(enabled_only)
        
        # Apply additional filters
        if rule_type_filter:
            rules = [rule for rule in rules if rule.rule_type.value == rule_type_filter]
        
        if priority_filter:
            rules = [rule for rule in rules if rule.priority.value == priority_filter]
        
        # Convert to dict format
        rules_data = []
        for rule in rules:
            rule_data = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "priority": rule.priority.value,
                "action": rule.action.value,
                "enabled": rule.enabled,
                "conditions": rule.conditions,
                "created_date": rule.created_date.isoformat(),
                "last_applied": rule.last_applied.isoformat() if rule.last_applied else None,
                "success_count": rule.success_count,
                "total_applications": rule.total_applications,
                "success_rate": rule.success_count / rule.total_applications if rule.total_applications > 0 else 0
            }
            rules_data.append(rule_data)
        
        return jsonify({
            "success": True,
            "data": {
                "rules": rules_data,
                "total_rules": len(rules_data),
                "filters_applied": {
                    "enabled_only": enabled_only,
                    "rule_type": rule_type_filter,
                    "priority": priority_filter
                }
            },
            "meta": {
                "endpoint": "get_rules",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Get rules API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/rules/<rule_id>', methods=['GET', 'PUT'])
@async_route
async def manage_filter_rule(rule_id):
    """
    Get or update a specific filter rule
    
    GET: Retrieve rule details
    PUT: Update rule configuration
    
    Request Body (PUT):
    {
        "enabled": true,
        "priority": "high",
        "conditions": {
            "threshold": 100000
        }
    }
    """
    try:
        service = get_fast_fail_service()
        
        if request.method == 'GET':
            rule = service.engine.get_rule(rule_id)
            
            if not rule:
                return jsonify({"error": f"Rule {rule_id} not found"}), 404
            
            rule_data = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "priority": rule.priority.value,
                "action": rule.action.value,
                "enabled": rule.enabled,
                "conditions": rule.conditions,
                "created_date": rule.created_date.isoformat(),
                "last_applied": rule.last_applied.isoformat() if rule.last_applied else None,
                "success_count": rule.success_count,
                "total_applications": rule.total_applications
            }
            
            return jsonify({
                "success": True,
                "data": rule_data,
                "meta": {
                    "endpoint": "get_rule",
                    "rule_id": rule_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Request body required"}), 400
            
            result = await service.update_filter_rule(rule_id, data)
            
            if 'error' in result:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
            return jsonify({
                "success": True,
                "data": result,
                "meta": {
                    "endpoint": "update_rule",
                    "rule_id": rule_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"Rule management API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/rules', methods=['POST'])
@async_route
async def create_filter_rule():
    """
    Create a new filter rule
    
    Request Body:
    {
        "id": "unique_rule_id",
        "name": "Rule Name",
        "description": "Rule description",
        "rule_type": "threshold",
        "priority": "high",
        "action": "exclude",
        "conditions": {
            "field": "estimated_value",
            "operator": "lt",
            "threshold": 50000
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        required_fields = ['id', 'name', 'description', 'rule_type', 'priority', 'action', 'conditions']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400
        
        service = get_fast_fail_service()
        
        # Check if rule ID already exists
        existing_rule = service.engine.get_rule(data['id'])
        if existing_rule:
            return jsonify({"error": f"Rule with ID {data['id']} already exists"}), 409
        
        # Import required enums
        from ..services.fast_fail_engine import FilterRule, FilterRuleType, FilterPriority, FilterAction
        
        try:
            # Create new rule
            rule = FilterRule(
                id=data['id'],
                name=data['name'],
                description=data['description'],
                rule_type=FilterRuleType(data['rule_type']),
                priority=FilterPriority(data['priority']),
                action=FilterAction(data['action']),
                conditions=data['conditions'],
                enabled=data.get('enabled', True)
            )
            
            # Validate rule
            if not service._validate_rule(rule):
                return jsonify({"error": "Rule validation failed"}), 400
            
            # Add rule
            service.engine.add_rule(rule)
            
            # Clear cache
            await service._clear_assessment_cache()
            
            return jsonify({
                "success": True,
                "data": {
                    "rule_id": rule.id,
                    "name": rule.name,
                    "created": True
                },
                "meta": {
                    "endpoint": "create_rule",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
        except ValueError as e:
            return jsonify({"error": f"Invalid enum value: {e}"}), 400
        
    except Exception as e:
        logger.error(f"Create rule API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/rules/<rule_id>', methods=['DELETE'])
@async_route
async def delete_filter_rule(rule_id):
    """
    Delete a filter rule
    
    Path Parameters:
    - rule_id: ID of the rule to delete
    """
    try:
        service = get_fast_fail_service()
        
        success = service.engine.remove_rule(rule_id)
        
        if not success:
            return jsonify({"error": f"Rule {rule_id} not found"}), 404
        
        # Clear cache
        await service._clear_assessment_cache()
        
        return jsonify({
            "success": True,
            "data": {
                "rule_id": rule_id,
                "deleted": True
            },
            "meta": {
                "endpoint": "delete_rule",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Delete rule API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/recommendations', methods=['GET'])
@async_route
async def get_filter_recommendations():
    """
    Get filter optimization recommendations
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - days_back: Days of history to analyze (default: 30, max: 90)
    """
    try:
        company_id = request.args.get('company_id')
        days_back = min(int(request.args.get('days_back', 30)), 90)
        
        service = get_fast_fail_service()
        recommendations = await service.get_filter_recommendations(company_id, days_back)
        
        if 'error' in recommendations:
            return jsonify({
                "success": False,
                "error": recommendations['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": recommendations,
            "meta": {
                "endpoint": "filter_recommendations",
                "days_back": days_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Recommendations API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/statistics', methods=['GET'])
def get_filter_statistics():
    """
    Get filter rule statistics and performance metrics
    """
    try:
        service = get_fast_fail_service()
        stats = service.engine.get_rule_statistics()
        
        return jsonify({
            "success": True,
            "data": stats,
            "meta": {
                "endpoint": "filter_statistics",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Statistics API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@fast_fail_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for fast-fail service"""
    try:
        service = get_fast_fail_service()
        rule_count = len(service.engine.list_rules())
        
        return jsonify({
            "status": "healthy",
            "service": "fast_fail_filter",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "opportunity_assessment": True,
                "batch_processing": True,
                "rule_management": True,
                "filter_optimization": True,
                "dashboard": True,
                "ai_insights": True
            },
            "statistics": {
                "total_rules": rule_count,
                "active_rules": len([r for r in service.engine.list_rules() if r.enabled])
            }
        })
        
    except Exception as e:
        logger.error(f"Fast-fail service health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Error handlers
@fast_fail_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/fast-fail/assess/<opportunity_id>",
            "/api/fast-fail/batch-assess",
            "/api/fast-fail/dashboard",
            "/api/fast-fail/rules",
            "/api/fast-fail/rules/<rule_id>",
            "/api/fast-fail/recommendations",
            "/api/fast-fail/statistics",
            "/api/fast-fail/health"
        ]
    }), 404

@fast_fail_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred in the fast-fail filter service"
    }), 500
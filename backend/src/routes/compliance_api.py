"""
Compliance Matrix API Endpoints
Flask blueprints for compliance analysis and assessment management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import logging
from functools import wraps

from ..services.compliance_service import get_compliance_service

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/compliance')

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

@compliance_bp.route('/analyze/<opportunity_id>', methods=['GET'])
@async_route
async def analyze_opportunity_compliance(opportunity_id):
    """
    Analyze compliance requirements for a specific opportunity
    
    Path Parameters:
    - opportunity_id: ID of the opportunity to analyze
    
    Query Parameters:
    - company_id: ID of the company (optional, defaults to current user's company)
    - force_refresh: Force new analysis even if cached (default: false)
    """
    try:
        company_id = request.args.get('company_id')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        service = get_compliance_service()
        
        # Check for existing analysis if not forcing refresh
        if not force_refresh:
            # Try to get cached analysis first
            pass  # Implement caching logic if needed
        
        analysis = await service.analyze_opportunity_compliance(opportunity_id, company_id)
        
        if 'error' in analysis:
            return jsonify({
                "success": False,
                "error": analysis['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": analysis,
            "meta": {
                "endpoint": "analyze_compliance",
                "opportunity_id": opportunity_id,
                "timestamp": datetime.utcnow().isoformat(),
                "force_refresh": force_refresh
            }
        })
        
    except Exception as e:
        logger.error(f"Compliance analysis API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/summary', methods=['GET'])
@async_route
async def get_compliance_summary():
    """
    Get compliance summary across multiple opportunities
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - days_back: Number of days to analyze (default: 30, max: 90)
    """
    try:
        company_id = request.args.get('company_id')
        days_back = min(int(request.args.get('days_back', 30)), 90)
        
        service = get_compliance_service()
        summary = await service.get_compliance_summary(company_id, days_back)
        
        if 'error' in summary:
            return jsonify({
                "success": False,
                "error": summary['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": summary,
            "meta": {
                "endpoint": "compliance_summary",
                "days_back": days_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameters: {e}"}), 400
    except Exception as e:
        logger.error(f"Compliance summary API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/gaps-report', methods=['GET'])
@async_route
async def get_compliance_gaps_report():
    """
    Generate comprehensive compliance gaps report
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - format: Response format (json, summary) (default: json)
    """
    try:
        company_id = request.args.get('company_id')
        report_format = request.args.get('format', 'json')
        
        service = get_compliance_service()
        report = await service.get_compliance_gaps_report(company_id)
        
        if 'error' in report:
            return jsonify({
                "success": False,
                "error": report['error']
            }), 400
        
        # Format response based on requested format
        if report_format == 'summary':
            # Return simplified summary
            gaps_analysis = report.get('gaps_analysis', {})
            response_data = {
                "total_gap_categories": len(gaps_analysis.get('category_gap_frequency', {})),
                "high_impact_categories": gaps_analysis.get('high_impact_gap_categories', []),
                "total_gap_instances": gaps_analysis.get('total_gap_instances', 0),
                "ai_summary": report.get('ai_recommendations', {}).get('recommendations', '')[:200] + "..."
            }
        else:
            response_data = report
        
        return jsonify({
            "success": True,
            "data": response_data,
            "meta": {
                "endpoint": "gaps_report",
                "format": report_format,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Gaps report API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/readiness-score', methods=['GET'])
@async_route
async def get_compliance_readiness_score():
    """
    Calculate overall compliance readiness score
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - categories: Comma-separated list of categories to analyze (optional)
    """
    try:
        company_id = request.args.get('company_id')
        categories_param = request.args.get('categories')
        
        # Parse categories if provided
        target_categories = None
        if categories_param:
            target_categories = [cat.strip() for cat in categories_param.split(',')]
        
        service = get_compliance_service()
        readiness = await service.get_compliance_readiness_score(company_id)
        
        if 'error' in readiness:
            return jsonify({
                "success": False,
                "error": readiness['error']
            }), 400
        
        # Filter by categories if specified
        if target_categories:
            category_scores = readiness.get('category_scores', {})
            filtered_scores = {
                cat: score for cat, score in category_scores.items() 
                if cat in target_categories
            }
            readiness['category_scores'] = filtered_scores
            readiness['overall_readiness_score'] = sum(filtered_scores.values()) / len(filtered_scores) if filtered_scores else 0
        
        return jsonify({
            "success": True,
            "data": readiness,
            "meta": {
                "endpoint": "readiness_score",
                "target_categories": target_categories,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Readiness score API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/profile', methods=['GET', 'PUT'])
@async_route
async def manage_company_profile():
    """
    Get or update company compliance profile
    
    GET: Retrieve current profile
    PUT: Update profile with new information
    
    Query Parameters (GET):
    - company_id: ID of the company (optional)
    
    Request Body (PUT):
    {
        "company_id": "optional_company_id",
        "profile_updates": {
            "certifications": ["ISO 9001", "CMMI Level 3"],
            "security_clearances": ["Secret", "Top Secret"],
            "experience_years": 10,
            ...
        }
    }
    """
    try:
        if request.method == 'GET':
            company_id = request.args.get('company_id', 'default_company')
            
            service = get_compliance_service()
            profile = await service._fetch_company_profile(company_id)
            
            return jsonify({
                "success": True,
                "data": {
                    "company_id": company_id,
                    "profile": profile
                },
                "meta": {
                    "endpoint": "get_profile",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Request body required"}), 400
            
            company_id = data.get('company_id', 'default_company')
            profile_updates = data.get('profile_updates', {})
            
            if not profile_updates:
                return jsonify({"error": "profile_updates required"}), 400
            
            service = get_compliance_service()
            result = await service.update_company_profile(company_id, profile_updates)
            
            if 'error' in result:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
            return jsonify({
                "success": True,
                "data": result,
                "meta": {
                    "endpoint": "update_profile",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        
    except Exception as e:
        logger.error(f"Profile management API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/requirements/<opportunity_id>', methods=['GET'])
@async_route
async def get_extracted_requirements(opportunity_id):
    """
    Get extracted compliance requirements for an opportunity
    
    Path Parameters:
    - opportunity_id: ID of the opportunity
    
    Query Parameters:
    - category: Filter by compliance category (optional)
    - priority: Filter by priority level (optional)
    - mandatory_only: Show only mandatory requirements (default: false)
    """
    try:
        category_filter = request.args.get('category')
        priority_filter = request.args.get('priority')
        mandatory_only = request.args.get('mandatory_only', 'false').lower() == 'true'
        
        # Get requirements from database
        service = get_compliance_service()
        
        # Fetch from compliance_requirements table
        query = service.supabase.table('compliance_requirements').select('*').eq(
            'opportunity_id', opportunity_id
        )
        
        if category_filter:
            query = query.eq('category', category_filter)
        
        if priority_filter:
            query = query.eq('priority', priority_filter)
        
        if mandatory_only:
            query = query.eq('mandatory', True)
        
        response = query.execute()
        requirements = response.data if response.data else []
        
        # Group by category
        by_category = {}
        for req in requirements:
            category = req.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(req)
        
        return jsonify({
            "success": True,
            "data": {
                "opportunity_id": opportunity_id,
                "total_requirements": len(requirements),
                "requirements": requirements,
                "by_category": by_category,
                "filters_applied": {
                    "category": category_filter,
                    "priority": priority_filter,
                    "mandatory_only": mandatory_only
                }
            },
            "meta": {
                "endpoint": "extracted_requirements",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Requirements extraction API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/assessment/<opportunity_id>', methods=['GET'])
@async_route
async def get_compliance_assessment(opportunity_id):
    """
    Get detailed compliance assessment for an opportunity
    
    Path Parameters:
    - opportunity_id: ID of the opportunity
    
    Query Parameters:
    - include_evidence: Include evidence details (default: true)
    - status_filter: Filter by compliance status (optional)
    """
    try:
        include_evidence = request.args.get('include_evidence', 'true').lower() == 'true'
        status_filter = request.args.get('status_filter')
        
        service = get_compliance_service()
        
        # Fetch assessments
        query = service.supabase.table('compliance_assessments').select('*').eq(
            'opportunity_id', opportunity_id
        )
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        response = query.execute()
        assessments = response.data if response.data else []
        
        # Remove evidence if not requested
        if not include_evidence:
            for assessment in assessments:
                assessment.pop('evidence', None)
        
        # Calculate summary statistics
        status_counts = {}
        total_effort = 0
        total_cost = 0
        
        for assessment in assessments:
            status = assessment.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            total_effort += assessment.get('effort_estimate', 0) or 0
            total_cost += assessment.get('cost_estimate', 0) or 0
        
        return jsonify({
            "success": True,
            "data": {
                "opportunity_id": opportunity_id,
                "assessments": assessments,
                "summary": {
                    "total_assessments": len(assessments),
                    "status_distribution": status_counts,
                    "total_effort_estimate": total_effort,
                    "total_cost_estimate": total_cost
                }
            },
            "meta": {
                "endpoint": "compliance_assessment",
                "include_evidence": include_evidence,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Assessment API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/dashboard', methods=['GET'])
@async_route
async def get_compliance_dashboard():
    """
    Get comprehensive compliance dashboard data
    
    Query Parameters:
    - company_id: ID of the company (optional)
    - timeframe: Analysis timeframe (30, 60, 90 days) (default: 30)
    """
    try:
        company_id = request.args.get('company_id')
        timeframe = int(request.args.get('timeframe', 30))
        
        if timeframe not in [30, 60, 90]:
            return jsonify({"error": "Invalid timeframe. Must be 30, 60, or 90 days"}), 400
        
        service = get_compliance_service()
        
        # Get multiple data sources
        readiness_score = await service.get_compliance_readiness_score(company_id)
        compliance_summary = await service.get_compliance_summary(company_id, timeframe)
        gaps_report = await service.get_compliance_gaps_report(company_id)
        
        # Compile dashboard
        dashboard = {
            "overview": {
                "readiness_score": readiness_score.get('overall_readiness_score', 0),
                "average_compliance": compliance_summary.get('average_compliance_score', 0),
                "total_opportunities_analyzed": compliance_summary.get('total_opportunities_analyzed', 0),
                "high_impact_gaps": len(gaps_report.get('gaps_analysis', {}).get('high_impact_gap_categories', []))
            },
            "readiness_by_category": readiness_score.get('category_scores', {}),
            "compliance_trends": {
                "trend": compliance_summary.get('compliance_trend', 'stable'),
                "risk_distribution": compliance_summary.get('risk_level_distribution', {}),
                "most_common_gaps": compliance_summary.get('most_common_gaps', [])
            },
            "recommendations": {
                "improvement_areas": readiness_score.get('improvement_areas', []),
                "quick_actions": readiness_score.get('recommendations', [])[:3],
                "ai_insights": gaps_report.get('ai_recommendations', {}).get('recommendations', '')[:300] + "..."
            },
            "metrics": {
                "total_effort_estimate": compliance_summary.get('total_effort_estimate', 0),
                "total_cost_estimate": compliance_summary.get('total_cost_estimate', 0),
                "gap_instances": gaps_report.get('gaps_analysis', {}).get('total_gap_instances', 0)
            }
        }
        
        return jsonify({
            "success": True,
            "data": dashboard,
            "meta": {
                "endpoint": "compliance_dashboard",
                "timeframe_days": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@compliance_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for compliance service"""
    try:
        service = get_compliance_service()
        
        return jsonify({
            "status": "healthy",
            "service": "compliance_matrix",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "requirement_extraction": True,
                "compliance_assessment": True,
                "gap_analysis": True,
                "readiness_scoring": True,
                "ai_insights": True,
                "profile_management": True,
                "dashboard": True
            }
        })
        
    except Exception as e:
        logger.error(f"Compliance service health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Error handlers
@compliance_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/compliance/analyze/<opportunity_id>",
            "/api/compliance/summary",
            "/api/compliance/gaps-report",
            "/api/compliance/readiness-score",
            "/api/compliance/profile",
            "/api/compliance/requirements/<opportunity_id>",
            "/api/compliance/assessment/<opportunity_id>",
            "/api/compliance/dashboard",
            "/api/compliance/health"
        ]
    }), 404

@compliance_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred in the compliance service"
    }), 500
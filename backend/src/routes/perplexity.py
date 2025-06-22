from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
import sys
import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from perplexity_live_discovery import PerplexityLiveDiscovery
except ImportError:
    # Fallback import path
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from perplexity_live_discovery import PerplexityLiveDiscovery

from ..services.perplexity_client import (
    get_perplexity_client, 
    QueryType, 
    QueryResult
)

# Auth import - temporarily disabled until auth module is available
# from ..auth.dependencies import require_auth

# Temporary auth placeholder
def require_auth(request):
    """Placeholder auth function until auth module is implemented"""
    return {"user_id": "demo_user"}

perplexity_bp = Blueprint('perplexity', __name__)
logger = logging.getLogger(__name__)

# Import cost tracking service
try:
    from ..services.cost_tracking_service import cost_tracker
except ImportError:
    cost_tracker = None
    logger.warning("Cost tracking service not available - costs will not be logged")

router = APIRouter(prefix="/perplexity", tags=["perplexity"])

# Request/Response Models
class PerplexitySearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    query_type: str = Field(default="search", description="Type of query for optimization")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")
    use_cache: bool = Field(default=True, description="Whether to use caching")
    force_refresh: bool = Field(default=False, description="Force refresh from API")
    similarity_threshold: float = Field(default=0.8, description="Similarity threshold for cached results")

class BatchQueryRequest(BaseModel):
    queries: List[Dict[str, Any]] = Field(..., description="List of queries to batch process")

class QueryStatsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    api_calls: int
    cost_saved: float
    similarity_hits: int
    hit_rate_percent: float
    estimated_savings: str
    cache_efficiency: str
    similarity_efficiency: str

class QueryResponse(BaseModel):
    content: str
    timestamp: str
    query_type: str
    from_cache: bool = False
    from_similar: bool = False
    similarity_score: float = 0.0
    cost_estimate: float = 0.0
    processing_time: float = 0.0
    cache_timestamp: Optional[datetime] = None

class TemplateQueryRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to use")
    params: Dict[str, str] = Field(..., description="Template parameters")


class PerplexityFinancialService:
    """Extended Perplexity service for financial data queries"""
    
    def __init__(self):
        try:
            self.perplexity = PerplexityLiveDiscovery()
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity service: {e}")
            self.perplexity = None
    
    def search_financial_data(self, query: str) -> dict:
        """Search for financial and market data using Perplexity AI"""
        if not self.perplexity:
            return {'error': 'Perplexity service not available'}
        
        try:
            # Enhanced financial search prompt
            financial_prompt = f"""
            Search for current financial and market data related to: {query}
            
            Focus on:
            - Government contracting market trends
            - Federal spending patterns
            - Contract award values and statistics
            - Market analysis and forecasts
            - Economic indicators affecting government procurement
            - Industry-specific financial insights
            
            Provide specific data points with sources and dates.
            Include numerical values, percentages, and concrete financial metrics.
            Format as detailed analysis with citations.
            """
            
            result = self.perplexity.query_perplexity(financial_prompt, max_tokens=800)
            
            if result.get('choices'):
                content = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'query': query,
                    'analysis': content,
                    'citations': citations,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'perplexity-financial'
                }
            else:
                return {'error': 'No results from Perplexity API'}
                
        except Exception as e:
            logger.error(f"Financial search failed: {e}")
            return {'error': str(e)}
    
    def get_market_analysis(self) -> dict:
        """Get comprehensive market analysis"""
        if not self.perplexity:
            return {'error': 'Perplexity service not available'}
        
        try:
            current_date = datetime.now().strftime('%B %Y')
            
            prompt = f"""
            Provide a comprehensive government contracting market analysis for {current_date}.
            
            Include:
            1. Overall market size and growth trends
            2. Top 5 fastest-growing sectors with specific percentage growth
            3. Federal agencies with highest contract spending
            4. Average contract values by category
            5. Small business participation rates
            6. Regional distribution of contract awards
            7. Upcoming major procurement opportunities
            8. Economic factors affecting the market
            
            Provide specific numbers, percentages, and dollar amounts with recent sources.
            Focus on actionable insights for contractors and businesses.
            """
            
            result = self.perplexity.query_perplexity(prompt, max_tokens=1000)
            
            if result.get('choices'):
                analysis = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'analysis': analysis,
                    'citations': citations,
                    'generated_at': datetime.now().isoformat(),
                    'period': current_date,
                    'analysis_type': 'comprehensive_market_analysis'
                }
            else:
                return {'error': 'No market analysis available'}
                
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {'error': str(e)}
    
    def get_financial_metrics(self) -> dict:
        """Get current financial metrics and KPIs"""
        if not self.perplexity:
            return {'error': 'Perplexity service not available'}
        
        try:
            prompt = f"""
            Provide current financial metrics for the government contracting market:
            
            1. Average federal contract value (last 30 days)
            2. Total contract awards this month vs last month
            3. Small business contract percentage
            4. Top spending federal agencies by dollar amount
            5. Contract competition rates (average number of bidders)
            6. Award turnaround times
            7. Most valuable recent contract awards
            8. Budget execution rates by agency
            
            Provide exact numbers with sources and dates.
            Include month-over-month and year-over-year changes where available.
            """
            
            result = self.perplexity.query_perplexity(prompt, max_tokens=800)
            
            if result.get('choices'):
                content = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'metrics': content,
                    'citations': citations,
                    'timestamp': datetime.now().isoformat(),
                    'data_type': 'financial_kpis'
                }
            else:
                return {'error': 'No financial metrics available'}
                
        except Exception as e:
            logger.error(f"Financial metrics query failed: {e}")
            return {'error': str(e)}
    
    def predict_opportunities(self, sector: str = None) -> dict:
        """Predict upcoming opportunities using AI analysis"""
        if not self.perplexity:
            return {'error': 'Perplexity service not available'}
        
        try:
            sector_filter = f" in the {sector} sector" if sector else ""
            
            prompt = f"""
            Predict upcoming government contracting opportunities{sector_filter} for the next 60 days.
            
            Based on:
            - Historical spending patterns and budget cycles
            - Current agency priorities and initiatives
            - Recent policy announcements
            - Budget allocations and appropriations
            - Market trends and demands
            
            Provide:
            - Specific opportunity types likely to be released
            - Estimated values and timeframes
            - Agencies most likely to issue solicitations
            - Key requirements and qualifications needed
            - Market competition levels
            - Strategic recommendations for positioning
            
            Focus on high-probability, high-value opportunities with specific details.
            """
            
            result = self.perplexity.query_perplexity(prompt, max_tokens=900)
            
            if result.get('choices'):
                predictions = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'predictions': predictions,
                    'citations': citations,
                    'sector_focus': sector,
                    'prediction_horizon': '60 days',
                    'generated_at': datetime.now().isoformat(),
                    'analysis_type': 'opportunity_forecast'
                }
            else:
                return {'error': 'No predictions available'}
                
        except Exception as e:
            logger.error(f"Opportunity prediction failed: {e}")
            return {'error': str(e)}


# Initialize service
financial_service = PerplexityFinancialService()

def log_api_cost(endpoint, query, cost_estimate, tokens_used=0, response_time=0.0):
    """Helper function to log API costs"""
    try:
        if cost_tracker:
            cost_tracker.log_api_call(
                endpoint=endpoint,
                method='POST',
                query=query,
                response_size_kb=tokens_used / 1000,  # Rough estimate
                cost_usd=cost_estimate,
                response_time_ms=response_time * 1000,
                metadata={'tokens': tokens_used, 'query_length': len(query)}
            )
        else:
            # Fallback logging to console
            logger.info(f"API Cost: {endpoint} - Query: {query[:50]}... - Cost: ${cost_estimate:.4f}")
    except Exception as e:
        logger.error(f"Failed to log API cost: {e}")

@perplexity_bp.route('/perplexity/search', methods=['POST'])
def search_financial_data():
    """Search for financial data using Perplexity AI with cost tracking"""
    start_time = datetime.now()
    cost_estimate = 0.0
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter required'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        result = financial_service.search_financial_data(query)
        
        # Calculate cost estimate (Perplexity pricing: ~$0.002 per query)
        cost_estimate = 0.002
        tokens_estimated = len(query.split()) * 3  # Rough estimate
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Log the API cost
        log_api_cost(
            endpoint='/perplexity/search',
            query=query,
            cost_estimate=cost_estimate,
            tokens_used=tokens_estimated,
            response_time=response_time
        )
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Add cost tracking info to response
        result['cost_tracking'] = {
            'cost_usd': cost_estimate,
            'tokens_estimated': tokens_estimated,
            'response_time_ms': response_time * 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        # Still log the failed attempt
        response_time = (datetime.now() - start_time).total_seconds()
        log_api_cost(
            endpoint='/perplexity/search',
            query=data.get('query', 'unknown') if data else 'no_query',
            cost_estimate=cost_estimate,
            response_time=response_time
        )
        
        logger.error(f"Financial search endpoint failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@perplexity_bp.route('/perplexity/market-analysis', methods=['GET'])
def get_market_analysis():
    """Get comprehensive market analysis"""
    try:
        result = financial_service.get_market_analysis()
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Market analysis endpoint failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@perplexity_bp.route('/perplexity/financial-metrics', methods=['GET'])
def get_financial_metrics():
    """Get current financial metrics and KPIs"""
    try:
        result = financial_service.get_financial_metrics()
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Financial metrics endpoint failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@perplexity_bp.route('/perplexity/predict-opportunities', methods=['GET'])
def predict_opportunities():
    """Predict upcoming opportunities"""
    try:
        sector = request.args.get('sector')
        
        result = financial_service.predict_opportunities(sector)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Opportunity prediction endpoint failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@perplexity_bp.route('/perplexity/enrich-opportunity', methods=['POST'])
def enrich_opportunity():
    """Enrich opportunity with comprehensive intelligence"""
    try:
        data = request.get_json()
        
        if not data or 'opportunity' not in data:
            return jsonify({'error': 'Opportunity data required'}), 400
        
        opportunity = data['opportunity']
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.enrich_opportunity(opportunity)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Opportunity enrichment failed: {e}")
        return jsonify({'error': 'Enrichment failed'}), 500


@perplexity_bp.route('/perplexity/score-opportunity', methods=['POST'])
def score_opportunity():
    """Score opportunity using AI analysis"""
    try:
        data = request.get_json()
        
        if not data or 'opportunity' not in data:
            return jsonify({'error': 'Opportunity data required'}), 400
        
        opportunity = data['opportunity']
        user_profile = data.get('user_profile', {})
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.score_opportunity_with_ai(opportunity, user_profile)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Opportunity scoring failed: {e}")
        return jsonify({'error': 'Scoring failed'}), 500


@perplexity_bp.route('/perplexity/competitive-landscape', methods=['POST'])
def analyze_competitive_landscape():
    """Analyze competitive landscape for market segment"""
    try:
        data = request.get_json()
        
        if not data or 'naics_codes' not in data or 'agency' not in data:
            return jsonify({'error': 'NAICS codes and agency required'}), 400
        
        naics_codes = data['naics_codes']
        agency = data['agency']
        timeframe = data.get('timeframe', '2years')
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.analyze_competitive_landscape(naics_codes, agency, timeframe)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Competitive analysis failed: {e}")
        return jsonify({'error': 'Analysis failed'}), 500


@perplexity_bp.route('/perplexity/bulk-enrich', methods=['POST'])
def bulk_enrich_opportunities():
    """Bulk enrich multiple opportunities"""
    try:
        data = request.get_json()
        
        if not data or 'opportunity_ids' not in data:
            return jsonify({'error': 'Opportunity IDs required'}), 400
        
        opportunity_ids = data['opportunity_ids']
        max_enrichments = min(len(opportunity_ids), 10)  # Limit to 10 for API efficiency
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        # Get opportunities from database
        from src.models.opportunity import Opportunity
        opportunities = Opportunity.query.filter(Opportunity.id.in_(opportunity_ids[:max_enrichments])).all()
        
        enriched_results = []
        for opp in opportunities:
            try:
                opp_data = {
                    'title': opp.title,
                    'agency_name': opp.agency_name,
                    'estimated_value': opp.estimated_value,
                    'opportunity_number': opp.opportunity_number,
                    'description': opp.description,
                    'due_date': opp.due_date.isoformat() if opp.due_date else None,
                    'location': opp.location
                }
                
                enrichment = financial_service.perplexity.enrich_opportunity(opp_data)
                enriched_results.append({
                    'opportunity_id': opp.id,
                    'enrichment': enrichment
                })
                
            except Exception as e:
                logger.error(f"Failed to enrich opportunity {opp.id}: {e}")
                enriched_results.append({
                    'opportunity_id': opp.id,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'data': {
                'enriched_count': len(enriched_results),
                'results': enriched_results
            }
        })
        
    except Exception as e:
        logger.error(f"Bulk enrichment failed: {e}")
        return jsonify({'error': 'Bulk enrichment failed'}), 500


@perplexity_bp.route('/perplexity/compliance-analysis', methods=['POST'])
def analyze_compliance_requirements():
    """Analyze compliance and requirements for an opportunity"""
    try:
        data = request.get_json()
        
        if not data or 'opportunity' not in data:
            return jsonify({'error': 'Opportunity data required'}), 400
        
        opportunity = data['opportunity']
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.analyze_compliance_requirements(opportunity)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Compliance analysis failed: {e}")
        return jsonify({'error': 'Compliance analysis failed'}), 500


@perplexity_bp.route('/perplexity/smart-alerts', methods=['POST'])
def generate_smart_alerts():
    """Generate smart opportunity alerts with context"""
    try:
        data = request.get_json() or {}
        user_profile = data.get('user_profile', {})
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.generate_smart_alerts(user_profile)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Smart alerts generation failed: {e}")
        return jsonify({'error': 'Smart alerts failed'}), 500


@perplexity_bp.route('/perplexity/trend-analysis', methods=['POST'])
def analyze_market_trends():
    """Analyze market trends and intelligence"""
    try:
        data = request.get_json() or {}
        timeframe = data.get('timeframe', '6months')
        focus_areas = data.get('focus_areas', [])
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.analyze_market_trends(timeframe, focus_areas)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return jsonify({'error': 'Trend analysis failed'}), 500


@perplexity_bp.route('/perplexity/market-forecast', methods=['POST'])
def forecast_market_conditions():
    """Generate market forecasting and predictions"""
    try:
        data = request.get_json() or {}
        horizon = data.get('horizon', '12months')
        
        if not financial_service.perplexity:
            return jsonify({'error': 'Perplexity service not available'}), 503
        
        result = financial_service.perplexity.forecast_market_conditions(horizon)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Market forecasting failed: {e}")
        return jsonify({'error': 'Market forecasting failed'}), 500


@perplexity_bp.route('/perplexity/status', methods=['GET'])
def get_perplexity_status():
    """Get Perplexity integration status"""
    try:
        api_key_configured = bool(os.getenv('PERPLEXITY_API_KEY'))
        service_available = financial_service.perplexity is not None
        
        return jsonify({
            'success': True,
            'data': {
                'api_key_configured': api_key_configured,
                'service_available': service_available,
                'status': 'operational' if (api_key_configured and service_available) else 'configuration_needed',
                'features': {
                    'opportunity_enrichment': True,
                    'ai_scoring': True,
                    'competitive_analysis': True,
                    'market_intelligence': True,
                    'bulk_processing': True,
                    'compliance_analysis': True,
                    'smart_alerts': True,
                    'trend_analysis': True,
                    'market_forecasting': True
                },
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': 'Status check failed'}), 500


@router.post("/search", response_model=QueryResponse)
async def search_perplexity(
    request: PerplexitySearchRequest,
    current_user: Dict = require_auth
):
    """
    Enhanced Perplexity search with intelligent caching and optimization
    """
    try:
        client = get_perplexity_client()
        
        # Validate query type
        try:
            query_type = QueryType(request.query_type.lower())
        except ValueError:
            query_type = QueryType.SEARCH
        
        # Execute optimized query
        result = await client.query(
            query=request.query,
            query_type=query_type,
            params=request.params,
            use_cache=request.use_cache,
            force_refresh=request.force_refresh,
            similarity_threshold=request.similarity_threshold
        )
        
        # Format response
        response_data = {
            "content": result.data.get('content', ''),
            "timestamp": result.timestamp.isoformat(),
            "query_type": result.query_type.value,
            "from_cache": result.from_cache,
            "from_similar": result.from_similar,
            "similarity_score": result.similarity_score,
            "cost_estimate": result.cost_estimate,
            "processing_time": result.processing_time
        }
        
        if result.from_cache and hasattr(result, 'cache_timestamp'):
            response_data["cache_timestamp"] = result.data.get('timestamp')
            
        return QueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Perplexity search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/batch", response_model=List[QueryResponse])
async def batch_query_perplexity(
    request: BatchQueryRequest,
    current_user: Dict = require_auth
):
    """
    Execute multiple Perplexity queries efficiently using intelligent batching
    """
    try:
        client = get_perplexity_client()
        
        # Execute batch query
        results = await client.batch_query(request.queries)
        
        # Format responses
        responses = []
        for result in results:
            response_data = {
                "content": result.data.get('content', ''),
                "timestamp": result.timestamp.isoformat(),
                "query_type": result.query_type.value,
                "from_cache": result.from_cache,
                "from_similar": result.from_similar,
                "similarity_score": result.similarity_score,
                "cost_estimate": result.cost_estimate,
                "processing_time": result.processing_time
            }
            
            if result.from_cache and hasattr(result, 'cache_timestamp'):
                response_data["cache_timestamp"] = result.data.get('timestamp')
                
            responses.append(QueryResponse(**response_data))
        
        return responses
        
    except Exception as e:
        logger.error(f"Batch query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}")

@router.post("/template-query", response_model=QueryResponse)
async def template_query_perplexity(
    request: TemplateQueryRequest,
    current_user: Dict = require_auth
):
    """
    Execute a templated query for consistent, optimized results
    """
    try:
        from ..lib.perplexity_templates import QUERY_TEMPLATES, buildQuery
        
        # Get template
        template = QUERY_TEMPLATES.get(request.template_id.upper())
        if not template:
            raise HTTPException(status_code=400, detail=f"Template '{request.template_id}' not found")
        
        # Build query from template
        built_query = buildQuery(request.template_id.upper(), request.params)
        if not built_query['isComplete']:
            missing_params = built_query['remainingPlaceholders']
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required parameters: {missing_params}"
            )
        
        # Execute query
        client = get_perplexity_client()
        query_type = QueryType(template['category'].lower().replace(' ', '_'))
        
        result = await client.query(
            query=built_query['query'],
            query_type=query_type,
            params=request.params,
            use_cache=True
        )
        
        # Format response
        response_data = {
            "content": result.data.get('content', ''),
            "timestamp": result.timestamp.isoformat(),
            "query_type": result.query_type.value,
            "from_cache": result.from_cache,
            "from_similar": result.from_similar,
            "similarity_score": result.similarity_score,
            "cost_estimate": result.cost_estimate,
            "processing_time": result.processing_time
        }
        
        return QueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Template query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template query failed: {str(e)}")

@router.get("/templates")
async def get_query_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: Dict = require_auth
):
    """
    Get available query templates for the frontend
    """
    try:
        from ..lib.perplexity_templates import QUERY_TEMPLATES, CATEGORIES
        
        templates = QUERY_TEMPLATES
        
        if category:
            templates = {
                k: v for k, v in templates.items() 
                if v['category'].lower() == category.lower()
            }
        
        return {
            "templates": templates,
            "categories": CATEGORIES
        }
        
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/presets")
async def get_query_presets(current_user: Dict = require_auth):
    """
    Get preset query workflows
    """
    try:
        from ..lib.perplexity_templates import PRESET_QUERIES, USAGE_RECOMMENDATIONS
        
        return {
            "presets": PRESET_QUERIES,
            "usage_recommendations": USAGE_RECOMMENDATIONS
        }
        
    except Exception as e:
        logger.error(f"Failed to get presets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get presets: {str(e)}")

@router.get("/stats", response_model=QueryStatsResponse)
async def get_perplexity_stats(current_user: Dict = require_auth):
    """
    Get Perplexity client performance statistics
    """
    try:
        client = get_perplexity_client()
        stats = client.get_stats()
        
        return QueryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/clear-cache")
async def clear_perplexity_cache(
    query_type: Optional[str] = Query(None, description="Specific query type to clear"),
    current_user: Dict = require_auth
):
    """
    Clear Perplexity cache (admin only)
    """
    try:
        # Check if user has admin privileges
        if not current_user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        client = get_perplexity_client()
        
        cache_query_type = None
        if query_type:
            try:
                cache_query_type = QueryType(query_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid query type: {query_type}")
        
        await client.clear_cache(cache_query_type)
        
        return {
            "message": f"Cache cleared successfully" + (f" for {query_type}" if query_type else ""),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/cache-metadata")
async def get_cache_metadata(current_user: Dict = require_auth):
    """
    Get cache metadata for debugging and optimization
    """
    try:
        client = get_perplexity_client()
        metadata = client.getCacheMetadata()
        
        return {
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache metadata: {str(e)}")

# Legacy endpoints for backward compatibility
@router.post("/query")
async def legacy_query_perplexity(
    query: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = require_auth
):
    """Legacy endpoint for backward compatibility"""
    
    try:
        request = PerplexitySearchRequest(query=query)
        result = await search_perplexity(request, current_user)
        return result
        
    except Exception as e:
        logger.error(f"Legacy query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("/health")
async def perplexity_health_check():
    """Health check endpoint for Perplexity service"""
    try:
        client = get_perplexity_client()
        stats = client.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
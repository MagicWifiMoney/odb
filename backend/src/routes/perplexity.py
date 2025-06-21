from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from perplexity_live_discovery import PerplexityLiveDiscovery
except ImportError:
    # Fallback import path
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from perplexity_live_discovery import PerplexityLiveDiscovery

perplexity_bp = Blueprint('perplexity', __name__)
logger = logging.getLogger(__name__)


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


@perplexity_bp.route('/perplexity/search', methods=['POST'])
def search_financial_data():
    """Search for financial data using Perplexity AI"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter required'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        result = financial_service.search_financial_data(query)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
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
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': 'Status check failed'}), 500
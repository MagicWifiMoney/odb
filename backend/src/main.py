#!/usr/bin/env python3
"""
Opportunity Dashboard - Unified Backend
Clean, simple Flask app with proper CORS and working Perplexity integration
"""

import os
import requests
import sqlite3
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import advanced Perplexity functionality
try:
    from perplexity_live_discovery import PerplexityLiveDiscovery
    PERPLEXITY_ADVANCED_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Advanced Perplexity features not available: {e}")
    PERPLEXITY_ADVANCED_AVAILABLE = False

# Load environment variables
load_dotenv()

<<<<<<< feature/advanced-perplexity-intelligence
# Create Flask app
=======
# Create Flask app instance
>>>>>>> main
app = Flask(__name__)

# Enable CORS properly - allow all origins for development
CORS(app, 
     origins=["http://localhost:5175", "http://localhost:5174", "http://localhost:5173", "http://localhost:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'opportunities.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.route('/api/health-simple')
@app.route('/api/health')
def health():
    """Simple health check"""
    # Check database connection
    db_healthy = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        opportunity_count = cursor.fetchone()[0]
        conn.close()
        db_healthy = True
    except Exception as e:
        opportunity_count = 0
        
    return jsonify({
        'status': 'healthy',
        'message': 'Opportunity Dashboard Backend Running',
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            'DATABASE_CONFIGURED': db_healthy,
            'OPPORTUNITY_COUNT': opportunity_count,
            'PERPLEXITY_CONFIGURED': bool(os.getenv('PERPLEXITY_API_KEY'))
        }
    })

# ============================================================================
# OPPORTUNITIES ENDPOINTS - SERVING REAL DATA
# ============================================================================

@app.route('/api/opportunities')
def get_opportunities():
    """Get opportunities with pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        search = request.args.get('search', '')
        
        conn = get_db_connection()
        
        # Build query
        where_clause = ""
        params = []
        
        if search:
            where_clause = "WHERE title LIKE ? OR description LIKE ? OR agency_name LIKE ?"
            search_term = f"%{search}%"
            params = [search_term, search_term, search_term]
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM opportunities {where_clause}"
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get opportunities
        offset = (page - 1) * per_page
        query = f"""
            SELECT id, title, description, agency_name, opportunity_number, 
                   estimated_value, posted_date, due_date, source_type, 
                   source_name, source_url, location, relevance_score,
                   total_score, created_at, updated_at
            FROM opportunities 
            {where_clause}
            ORDER BY posted_date DESC, total_score DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, params + [per_page, offset])
        rows = cursor.fetchall()
        
        opportunities = []
        for row in rows:
            opportunities.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'agency_name': row['agency_name'],
                'opportunity_number': row['opportunity_number'],
                'estimated_value': row['estimated_value'],
                'posted_date': row['posted_date'],
                'due_date': row['due_date'],
                'source_type': row['source_type'],
                'source_name': row['source_name'],
                'source_url': row['source_url'],
                'location': row['location'],
                'relevance_score': row['relevance_score'],
                'total_score': row['total_score'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        conn.close()
        
        return jsonify({
            'opportunities': opportunities,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/opportunities/<int:opportunity_id>')
def get_opportunity_detail(opportunity_id):
    """Get single opportunity details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM opportunities WHERE id = ?
        """, (opportunity_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Opportunity not found'}), 404
            
        opportunity = {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'agency_name': row['agency_name'],
            'opportunity_number': row['opportunity_number'],
            'estimated_value': row['estimated_value'],
            'posted_date': row['posted_date'],
            'due_date': row['due_date'],
            'source_type': row['source_type'],
            'source_name': row['source_name'],
            'source_url': row['source_url'],
            'location': row['location'],
            'contact_info': row['contact_info'],
            'keywords': row['keywords'],
            'relevance_score': row['relevance_score'],
            'urgency_score': row['urgency_score'],
            'value_score': row['value_score'],
            'competition_score': row['competition_score'],
            'total_score': row['total_score'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
        
        return jsonify({
            'opportunity': opportunity,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/opportunities/stats')
def get_opportunity_stats():
    """Get opportunity statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total opportunities
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        total = cursor.fetchone()[0]
        
        # Total estimated value
        cursor.execute("SELECT SUM(estimated_value) FROM opportunities WHERE estimated_value IS NOT NULL")
        total_value = cursor.fetchone()[0] or 0
        
        # Opportunities by source type
        cursor.execute("""
            SELECT source_type, COUNT(*) as count 
            FROM opportunities 
            GROUP BY source_type 
            ORDER BY count DESC
        """)
        by_source = [{'source_type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Recent opportunities (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM opportunities 
            WHERE posted_date > datetime('now', '-30 days')
        """)
        recent = cursor.fetchone()[0]
        
        # Top agencies
        cursor.execute("""
            SELECT agency_name, COUNT(*) as count 
            FROM opportunities 
            WHERE agency_name IS NOT NULL
            GROUP BY agency_name 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_agencies = [{'agency': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'stats': {
                'total_opportunities': total,
                'total_estimated_value': total_value,
                'recent_opportunities': recent,
                'by_source_type': by_source,
                'top_agencies': top_agencies
            },
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# ============================================================================
# PERPLEXITY AI ENDPOINTS - WORKING
# ============================================================================

@app.route('/api/perplexity/status')
def perplexity_status():
    """Check Perplexity API status"""
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    
    return jsonify({
        'configured': bool(perplexity_key),
        'api_key_present': bool(perplexity_key),
        'status': 'ready' if perplexity_key else 'needs_api_key',
        'service': 'perplexity'
    })

@app.route('/api/perplexity/search', methods=['POST'])
def perplexity_search():
    """Search using Perplexity API"""
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    
    if not perplexity_key:
        return jsonify({
            'error': 'Perplexity API key not configured',
            'message': 'Add PERPLEXITY_API_KEY to your environment variables'
        }), 400
    
    try:
        data = request.get_json()
        query = data.get('query', '') if data else ''
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Make real Perplexity API call
        headers = {
            'Authorization': f'Bearer {perplexity_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'sonar-pro',
            'messages': [
                {
                    'role': 'user',
                    'content': f'Analyze this government contracting market query: {query}. Provide insights on market trends, opportunities, and key players.'
                }
            ],
            'max_tokens': 1000,
            'temperature': 0.1
        }
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
            
            return jsonify({
                'query': query,
                'status': 'success',
                'analysis': content,
                'model': 'sonar-pro',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': f'Perplexity API error: {response.status_code}',
                'message': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/perplexity/market-analysis')
def perplexity_market_analysis():
    """Market analysis endpoint"""
    return jsonify({
        'status': 'success',
        'analysis': 'Market analysis is available through the search endpoint. Use specific market queries to get detailed analysis.',
        'message': 'Use /api/perplexity/search with market-specific queries',
        'service': 'perplexity'
    })

@app.route('/api/perplexity/trend-analysis', methods=['POST'])
def perplexity_trend_analysis():
    """Trend analysis endpoint"""
    return jsonify({
        'status': 'success',
        'analysis': 'Trend analysis is available through the search endpoint. Use trend-specific queries.',
        'message': 'Use /api/perplexity/search with trend analysis queries',
        'service': 'perplexity'
    })

# ============================================================================
# ADVANCED PERPLEXITY AI ENDPOINTS
# ============================================================================

@app.route('/api/perplexity/enrich-opportunity', methods=['POST'])
def enrich_opportunity():
    """Enrich opportunity data with AI analysis"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json()
        opportunity = data.get('opportunity', {})
        
        if not opportunity:
            return jsonify({'error': 'Opportunity data is required'}), 400
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Enrich the opportunity
        enriched = perplexity_client.enrich_opportunity(opportunity)
        
        return jsonify({
            'status': 'success',
            'enriched_opportunity': enriched,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Enrichment failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/perplexity/score-opportunity', methods=['POST'])
def score_opportunity():
    """Score opportunity with AI analysis"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json()
        opportunity = data.get('opportunity', {})
        user_profile = data.get('user_profile', {})
        
        if not opportunity:
            return jsonify({'error': 'Opportunity data is required'}), 400
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Score the opportunity
        scoring_result = perplexity_client.score_opportunity_with_ai(opportunity, user_profile)
        
        return jsonify({
            'status': 'success',
            'scoring_result': scoring_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Scoring failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/perplexity/competitive-landscape', methods=['POST'])
def analyze_competitive_landscape():
    """Analyze competitive landscape"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json()
        naics_codes = data.get('naics_codes', [])
        agency = data.get('agency', '')
        timeframe = data.get('timeframe', '2years')
        
        if not naics_codes or not agency:
            return jsonify({'error': 'NAICS codes and agency are required'}), 400
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Analyze competitive landscape
        analysis = perplexity_client.analyze_competitive_landscape(naics_codes, agency, timeframe)
        
        return jsonify({
            'status': 'success',
            'competitive_analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Competitive analysis failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/perplexity/smart-alerts', methods=['POST'])
def generate_smart_alerts():
    """Generate smart alerts based on user profile"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json() or {}
        user_profile = data.get('user_profile', {})
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Generate smart alerts
        alerts = perplexity_client.generate_smart_alerts(user_profile)
        
        return jsonify({
            'status': 'success',
            'smart_alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Smart alerts generation failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/perplexity/market-forecast', methods=['POST'])
def forecast_market_conditions():
    """Forecast market conditions"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json() or {}
        horizon = data.get('horizon', '12months')
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Generate market forecast
        forecast = perplexity_client.forecast_market_conditions(horizon)
        
        return jsonify({
            'status': 'success',
            'market_forecast': forecast,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Market forecast failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/perplexity/compliance-analysis', methods=['POST'])
def analyze_compliance():
    """Analyze compliance requirements for opportunity"""
    if not PERPLEXITY_ADVANCED_AVAILABLE:
        return jsonify({
            'error': 'Advanced Perplexity features not available',
            'message': 'PerplexityLiveDiscovery module not found'
        }), 503
    
    try:
        data = request.get_json()
        opportunity = data.get('opportunity', {})
        
        if not opportunity:
            return jsonify({'error': 'Opportunity data is required'}), 400
        
        # Initialize Perplexity client
        perplexity_client = PerplexityLiveDiscovery()
        
        # Analyze compliance requirements
        compliance_analysis = perplexity_client.analyze_compliance_requirements(opportunity)
        
        return jsonify({
            'status': 'success',
            'compliance_analysis': compliance_analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Compliance analysis failed: {str(e)}',
            'status': 'error'
        }), 500

# ============================================================================
# MOCK ENDPOINTS - FOR BROKEN SERVICES
# ============================================================================

@app.route('/api/fast-fail/dashboard')
@app.route('/api/fast-fail/health')
def fast_fail_service():
    """Mock fast-fail service"""
    return jsonify({
        'status': 'service_offline',
        'message': 'Fast-fail service not implemented yet',
        'service': 'fast-fail',
        'data': []
    })

@app.route('/api/win-probability/dashboard')
@app.route('/api/win-probability/health')
def win_probability_service():
    """Mock win probability service"""
    return jsonify({
        'status': 'service_offline',
        'message': 'Win probability service not implemented yet',
        'service': 'win-probability',
        'data': []
    })

@app.route('/api/compliance/dashboard')
@app.route('/api/compliance/health')
def compliance_service():
    """Mock compliance service"""
    return jsonify({
        'status': 'service_offline',
        'message': 'Compliance service not implemented yet',
        'service': 'compliance',
        'data': []
    })

@app.route('/api/trends/dashboard')
@app.route('/api/trends/health')
def trends_service():
    """Mock trends service"""
    return jsonify({
        'status': 'service_offline',
        'message': 'Trends service not implemented yet',
        'service': 'trends',
        'data': []
    })

@app.route('/api/fast-fail/batch-assess', methods=['POST'])
def fast_fail_batch_assess():
    """Mock fast-fail batch assessment"""
    return jsonify({
        'status': 'service_offline',
        'message': 'Fast-fail batch assessment not implemented yet',
        'service': 'fast-fail',
        'data': []
    })

# ============================================================================
# CATCH-ALL FOR MISSING ENDPOINTS
# ============================================================================

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all_api(path):
    """Catch-all for any missing API endpoints"""
    return jsonify({
        'status': 'endpoint_not_implemented',
        'path': f'/api/{path}',
        'message': f'Endpoint /api/{path} is not implemented yet',
        'method': request.method
    }), 404

# ============================================================================
# CORS PREFLIGHT HANDLER
# ============================================================================

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'path': request.path,
        'message': 'This endpoint is not implemented'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on the server'
    }), 500

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5555))
    print(f"🚀 Starting Opportunity Dashboard Backend on port {port}")
    print(f"📊 Perplexity API: {'✅ Configured' if os.getenv('PERPLEXITY_API_KEY') else '❌ Not configured'}")
    print(f"🔗 Health check: http://localhost:{port}/api/health")
    print(f"🧠 Perplexity status: http://localhost:{port}/api/perplexity/status")
    
    app.run(host='0.0.0.0', port=port, debug=True)
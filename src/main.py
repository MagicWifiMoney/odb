import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request, g
from flask_cors import CORS
from src.models.opportunity import db, Opportunity
from src.routes.user import user_bp
from src.routes.opportunities import opportunities_bp
from src.routes.scraping import scraping_bp
from src.routes.rfp_enhanced import rfp_enhanced_bp
from src.routes.perplexity import perplexity_bp
from src.services.analytics_service import analytics_service
from datetime import datetime, timedelta
import random
import logging
import time

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Enable CORS for all routes
CORS(app)

# Analytics middleware
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # Track API requests
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        
        # Only track API endpoints (not static files)
        if request.path.startswith('/api/'):
            analytics_service.track_api_request(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=getattr(g, 'user_id', None)
            )
    
    return response

# Health endpoint for Railway deployment
@app.route('/api/health')
def health():
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
    db_type = 'PostgreSQL' if 'postgresql' in database_url else 'SQLite'
    
    # Test database connection
    db_status = 'unknown'
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)[:100]}'
    
    # Track health check
    analytics_service.track_custom_event('health_check', {
        'database_status': db_status,
        'database_type': db_type
    })
    
    return jsonify({
        'status': 'healthy',
        'message': 'Opportunity Dashboard API is running',
        'database': db_type,
        'database_status': db_status,
        'database_url_prefix': database_url[:50] + '...' if len(database_url) > 50 else database_url,
        'supabase_configured': bool(os.getenv('SUPABASE_URL')),
        'analytics_enabled': analytics_service.is_enabled()
    })

# API info endpoint
@app.route('/api')
def api_info():
    return jsonify({
        'name': 'Opportunity Dashboard API',
        'version': '2.0.0',
        'status': 'running',
        'analytics_enabled': analytics_service.is_enabled(),
        'available_endpoints': [
            '/api',
            '/api/health', 
            '/api/opportunities',
            '/api/opportunities/stats',
            '/api/sync/status',
            '/api/init-data'
        ]
    })

# ... existing code ... 
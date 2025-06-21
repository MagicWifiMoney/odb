import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.opportunity import db, Opportunity
from src.routes.user import user_bp
from src.routes.opportunities import opportunities_bp
from src.routes.scraping import scraping_bp
from src.routes.rfp_enhanced import rfp_enhanced_bp
from datetime import datetime, timedelta

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Enable CORS for all routes
CORS(app)

# Health endpoint for Railway deployment
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Opportunity Dashboard API is running',
        'database': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
    })

# API info endpoint
@app.route('/api')
def api_info():
    return jsonify({
        'name': 'Opportunity Dashboard API',
        'version': '1.0.0',
        'status': 'running',
        'available_endpoints': [
            '/api',
            '/api/health', 
            '/api/opportunities',
            '/api/opportunities/stats',
            '/api/sync/status',
            '/api/init-data'
        ]
    })

# Initialize database with sample data
@app.route('/api/init-data', methods=['POST'])
def init_sample_data():
    try:
        # Create sample opportunities
        sample_opportunities = [
            {
                'title': 'IT Infrastructure Modernization',
                'description': 'Large-scale IT infrastructure modernization project for federal agency',
                'agency_name': 'Department of Defense',
                'opportunity_number': 'DOD-IT-2024-001',
                'estimated_value': 15000000,
                'due_date': datetime.now() + timedelta(days=30),
                'source_type': 'government',
                'source_name': 'SAM.gov',
                'location': 'Washington, DC',
                'total_score': 85
            },
            {
                'title': 'Cloud Migration Services',
                'description': 'Cloud migration and modernization services for state government',
                'agency_name': 'California State Government',
                'opportunity_number': 'CA-CLOUD-2024-002',
                'estimated_value': 8500000,
                'due_date': datetime.now() + timedelta(days=45),
                'source_type': 'government',
                'source_name': 'Grants.gov',
                'location': 'Sacramento, CA',
                'total_score': 78
            },
            {
                'title': 'Cybersecurity Assessment',
                'description': 'Comprehensive cybersecurity assessment and implementation',
                'agency_name': 'Department of Homeland Security',
                'opportunity_number': 'DHS-SEC-2024-003',
                'estimated_value': 12000000,
                'due_date': datetime.now() + timedelta(days=21),
                'source_type': 'government',
                'source_name': 'USASpending.gov',
                'location': 'Multiple Locations',
                'total_score': 92
            }
        ]
        
        added = 0
        for opp_data in sample_opportunities:
            existing = Opportunity.query.filter_by(opportunity_number=opp_data['opportunity_number']).first()
            if not existing:
                opportunity = Opportunity(**opp_data)
                db.session.add(opportunity)
                added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Added {added} sample opportunities',
            'total_opportunities': Opportunity.query.count()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Test opportunities endpoint (bypass complex filtering)
@app.route('/api/opportunities-simple', methods=['GET'])
def get_opportunities_simple():
    try:
        opportunities = Opportunity.query.limit(10).all()
        return jsonify({
            'opportunities': [opp.to_dict() for opp in opportunities],
            'count': len(opportunities)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to fetch opportunities'
        }), 500

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(opportunities_bp, url_prefix='/api')
app.register_blueprint(scraping_bp, url_prefix='/api')
app.register_blueprint(rfp_enhanced_bp, url_prefix='/api')

# Database configuration - support both PostgreSQL (Supabase) and SQLite
database_url = os.getenv('DATABASE_URL', 'sqlite:///opportunities.db')

# Handle different database URLs
if database_url.startswith('postgres://'):
    # Convert postgres:// to postgresql:// for SQLAlchemy 2.0+
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def serve_index():
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    else:
        return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

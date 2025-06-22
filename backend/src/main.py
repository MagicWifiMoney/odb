import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.database import db
from src.models.opportunity import Opportunity

# Import blueprints with error handling
try:
    from src.routes.user import user_bp
    print("✅ User blueprint imported")
except Exception as e:
    print(f"❌ User blueprint import failed: {e}")
    user_bp = None

try:
    from src.routes.opportunities import opportunities_bp
    print("✅ Opportunities blueprint imported")
except Exception as e:
    print(f"❌ Opportunities blueprint import failed: {e}")
    opportunities_bp = None

try:
    from src.routes.scraping import scraping_bp
    print("✅ Scraping blueprint imported")
except Exception as e:
    print(f"❌ Scraping blueprint import failed: {e}")
    scraping_bp = None

try:
    from src.routes.rfp_enhanced import rfp_enhanced_bp
    print("✅ RFP Enhanced blueprint imported")
except Exception as e:
    print(f"❌ RFP Enhanced blueprint import failed: {e}")
    rfp_enhanced_bp = None

try:
    from src.routes.perplexity import perplexity_bp
    print("✅ Perplexity blueprint imported")
except Exception as e:
    print(f"❌ Perplexity blueprint import failed: {e}")
    perplexity_bp = None

try:
    from src.routes.trend_routes import trend_bp
    print("✅ Trend analysis blueprint imported")
except Exception as e:
    print(f"❌ Trend analysis blueprint import failed: {e}")
    trend_bp = None

try:
    from src.routes.cost_routes import cost_bp
    print("✅ Cost tracking blueprint imported")
except Exception as e:
    print(f"❌ Cost tracking blueprint import failed: {e}")
    cost_bp = None
# Analytics service
from datetime import datetime, timedelta
import random
import logging
import time

# Analytics temporarily removed for stability

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Enable CORS for all routes
CORS(app)

# Analytics middleware removed for stability

@app.after_request
def after_request(response):
    # Analytics tracking removed for stability
    return response

# Minimal health endpoint that should always work
@app.route('/api/health-simple')
def health_simple():
    return jsonify({
        'status': 'healthy',
        'message': 'Flask app is running'
    })

# Health endpoint for Railway deployment - simplified for debugging
@app.route('/api/health')
def health():
    try:
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
        
        # Analytics tracking removed for stability
        
        return jsonify({
            'status': 'healthy',
            'message': 'Opportunity Dashboard API is running',
            'database': db_type,
            'database_status': db_status,
            'database_url_prefix': database_url[:50] + '...' if len(database_url) > 50 else database_url,
            'supabase_configured': bool(os.getenv('SUPABASE_URL')),
            'analytics_enabled': False
        })
        
    except Exception as e:
        # Return a basic response even if everything fails
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'error': str(e)
        }), 500

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

# Import performance blueprint
try:
    from src.routes.performance_api import performance_bp
    print("✅ Performance API blueprint imported successfully")
except ImportError as e:
    performance_bp = None
    print(f"⚠️ Performance API blueprint import failed: {e}")

# Register blueprints - only if they imported successfully
blueprints = [
    (user_bp, 'user'),
    (opportunities_bp, 'opportunities'), 
    (scraping_bp, 'scraping'),
    (rfp_enhanced_bp, 'rfp_enhanced'),
    (perplexity_bp, 'perplexity'),
    (performance_bp, 'performance'),
    (trend_bp, 'trend_analysis'),
    (cost_bp, 'cost_tracking')
]

for blueprint, name in blueprints:
    if blueprint:
        try:
            app.register_blueprint(blueprint, url_prefix='/api')
            print(f"✅ {name} blueprint registered successfully")
        except Exception as e:
            print(f"❌ {name} blueprint registration failed: {e}")
    else:
        print(f"⚠️ {name} blueprint skipped (import failed)")

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

# Safer database initialization with error handling
try:
    with app.app_context():
        # Test the connection first
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # If connection works, create tables
        db.create_all()
        print(f"✅ Database connected successfully: {database_url[:50]}...")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"🔧 DATABASE_URL: {database_url[:50]}...")
    print("⚠️  App will start but database operations may fail")
    
    # For Railway deployment, we still want the app to start
    # so we can see the error in logs and debug
    pass

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

# Bulk insert endpoint for scaling
@app.route('/api/bulk-insert', methods=['POST'])
def bulk_insert_opportunities():
    """Bulk insert opportunities for scaling"""
    try:
        data = request.get_json()
        opportunities_data = data.get('opportunities', [])
        
        if not opportunities_data:
            return jsonify({'error': 'No opportunities provided'}), 400
        
        added_count = 0
        
        for opp_data in opportunities_data:
            try:
                # Create opportunity object
                opportunity = Opportunity(
                    title=opp_data.get('title', '')[:500],
                    description=opp_data.get('description', ''),
                    agency_name=opp_data.get('agency_name', '')[:200],
                    opportunity_number=opp_data.get('opportunity_number'),
                    estimated_value=opp_data.get('estimated_value'),
                    posted_date=datetime.fromisoformat(opp_data['posted_date'].replace('Z', '+00:00')) if opp_data.get('posted_date') else None,
                    due_date=datetime.fromisoformat(opp_data['due_date'].replace('Z', '+00:00')) if opp_data.get('due_date') else None,
                    source_type=opp_data.get('source_type', 'synthetic'),
                    source_name=opp_data.get('source_name', 'Bulk Insert'),
                    location=opp_data.get('location'),
                    contact_info=opp_data.get('contact_info'),
                    keywords=opp_data.get('keywords'),
                    relevance_score=opp_data.get('relevance_score', 75),
                    urgency_score=opp_data.get('urgency_score', 70),
                    value_score=opp_data.get('value_score', 65),
                    competition_score=opp_data.get('competition_score', 60),
                    total_score=opp_data.get('total_score', 70)
                )
                
                db.session.add(opportunity)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    db.session.commit()
                    
            except Exception as e:
                logger.warning(f"Error adding opportunity: {e}")
                continue
        
        # Final commit
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully added {added_count} opportunities',
            'added': added_count,
            'total_opportunities': db.session.query(Opportunity).count()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Bulk insert error: {str(e)}")
        return jsonify({'error': 'Failed to bulk insert opportunities'}), 500

# Enhanced init-data endpoint for better scaling
@app.route('/api/init-data-large', methods=['POST'])
def init_large_sample_data():
    """Initialize with larger sample data set"""
    try:
        # Get count parameter
        data = request.get_json() if request.is_json else {}
        count = data.get('count', 100) if data else 100
        count = min(count, 1000)  # Limit to 1000 per request
        
        agencies = [
            "Department of Defense", "Department of Health and Human Services",
            "Department of Homeland Security", "Department of Veterans Affairs",
            "General Services Administration", "Department of Energy",
            "Department of Transportation", "Department of Education"
        ]
        
        opportunity_types = [
            "IT Services", "Construction", "Professional Services", "Research",
            "Medical Supplies", "Security Services", "Environmental Services",
            "Training", "Logistics", "Telecommunications"
        ]
        
        locations = [
            "Washington, DC", "Virginia", "Maryland", "California",
            "Texas", "New York", "Florida", "Illinois"
        ]
        
        added_count = 0
        
        for i in range(count):
            agency = random.choice(agencies)
            opp_type = random.choice(opportunity_types)
            location = random.choice(locations)
            
            posted_date = datetime.now() - timedelta(days=random.randint(1, 90))
            due_date = posted_date + timedelta(days=random.randint(14, 120))
            estimated_value = random.randint(50000, 50000000)
            
            opportunity = Opportunity(
                title=f"{opp_type} - {agency} - {random.randint(1000, 9999)}",
                description=f"Large-scale {opp_type.lower()} opportunity for {agency}. "
                           f"This contract involves comprehensive services and solutions. "
                           f"Location: {location}. Duration: {random.randint(12, 48)} months.",
                agency_name=agency,
                opportunity_number=f"LARGE-{random.randint(100000, 999999)}",
                estimated_value=float(estimated_value),
                posted_date=posted_date,
                due_date=due_date,
                source_type='federal_contract',
                source_name='Large Sample Generator',
                location=location,
                contact_info=f"contact.{agency.lower().replace(' ', '')}@example.gov",
                keywords=[opp_type.lower(), agency.lower()],
                relevance_score=random.randint(70, 95),
                urgency_score=random.randint(60, 90),
                value_score=random.randint(50, 85),
                competition_score=random.randint(40, 80),
                total_score=random.randint(65, 90)
            )
            
            db.session.add(opportunity)
            added_count += 1
            
            # Commit in batches
            if added_count % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        total_count = db.session.query(Opportunity).count()
        
        return jsonify({
            'message': f'Successfully added {added_count} large sample opportunities',
            'added': added_count,
            'total_opportunities': total_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Large sample data creation error: {str(e)}")
        return jsonify({'error': 'Failed to create large sample data'}), 500

# Performance-optimized opportunities endpoint for large datasets
@app.route('/api/opportunities-fast', methods=['GET'])
def get_opportunities_fast():
    """Fast opportunities endpoint optimized for large datasets"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        sort_by = request.args.get('sort_by', 'total_score')
        sort_order = request.args.get('sort_order', 'desc')
        search = request.args.get('search', '')
        
        # Build base query with selective loading
        query = db.session.query(
            Opportunity.id,
            Opportunity.title,
            Opportunity.agency_name,
            Opportunity.estimated_value,
            Opportunity.due_date,
            Opportunity.posted_date,
            Opportunity.source_type,
            Opportunity.source_name,
            Opportunity.total_score,
            Opportunity.relevance_score,
            Opportunity.urgency_score,
            Opportunity.value_score,
            Opportunity.competition_score,
            Opportunity.location,
            Opportunity.opportunity_number
        )
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Opportunity.title.ilike(search_filter),
                    Opportunity.agency_name.ilike(search_filter),
                    Opportunity.description.ilike(search_filter)
                )
            )
        
        # Apply sorting
        sort_column = getattr(Opportunity, sort_by, Opportunity.total_score)
        if sort_order.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count efficiently
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        opportunities = query.offset(offset).limit(per_page).all()
        
        # Format results
        results = []
        for opp in opportunities:
            results.append({
                'id': opp.id,
                'title': opp.title,
                'agency_name': opp.agency_name,
                'estimated_value': opp.estimated_value,
                'due_date': opp.due_date.isoformat() if opp.due_date else None,
                'posted_date': opp.posted_date.isoformat() if opp.posted_date else None,
                'source_type': opp.source_type,
                'source_name': opp.source_name,
                'total_score': opp.total_score,
                'relevance_score': opp.relevance_score,
                'urgency_score': opp.urgency_score,
                'value_score': opp.value_score,
                'competition_score': opp.competition_score,
                'location': opp.location,
                'opportunity_number': opp.opportunity_number
            })
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'opportunities': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'total': total_count,
            'pages': total_pages
        })
        
    except Exception as e:
        logger.error(f"Fast opportunities fetch error: {str(e)}")
        return jsonify({'error': 'Failed to fetch opportunities'}), 500

# Debug endpoint for testing large dataset queries
@app.route('/api/opportunities-debug', methods=['GET'])
def debug_opportunities():
    """Debug endpoint to test opportunities query"""
    try:
        # Simple count first
        total_count = db.session.query(Opportunity).count()
        
        # Get first 10 opportunities with minimal fields
        opportunities = db.session.query(
            Opportunity.id,
            Opportunity.title,
            Opportunity.agency_name,
            Opportunity.total_score
        ).limit(10).all()
        
        results = []
        for opp in opportunities:
            results.append({
                'id': opp.id,
                'title': opp.title,
                'agency_name': opp.agency_name,
                'total_score': opp.total_score
            })
        
        return jsonify({
            'total_count': total_count,
            'sample_opportunities': results,
            'message': 'Debug query successful'
        })
        
    except Exception as e:
        logger.error(f"Debug query error: {str(e)}")
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

# Simple working opportunities endpoint
@app.route('/api/opportunities-working', methods=['GET'])
def get_opportunities_working():
    """Simple working opportunities endpoint for large datasets"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        search = request.args.get('search', '')
        
        # Build base query
        query = db.session.query(Opportunity)
        
        # Apply search if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Opportunity.title.ilike(search_filter),
                    Opportunity.agency_name.ilike(search_filter)
                )
            )
        
        # Order by score
        query = query.order_by(Opportunity.total_score.desc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        opportunities_data = query.offset(offset).limit(per_page).all()
        
        # Convert to simplified dict format
        opportunities = []
        for opp in opportunities_data:
            opportunities.append({
                'id': opp.id,
                'title': opp.title,
                'agency_name': opp.agency_name,
                'estimated_value': opp.estimated_value,
                'due_date': opp.due_date.isoformat() if opp.due_date else None,
                'posted_date': opp.posted_date.isoformat() if opp.posted_date else None,
                'source_type': opp.source_type,
                'source_name': opp.source_name,
                'total_score': opp.total_score,
                'location': opp.location,
                'opportunity_number': opp.opportunity_number
            })
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'opportunities': opportunities,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'total': total_count,
            'pages': total_pages
        })
        
    except Exception as e:
        logger.error(f"Working opportunities error: {str(e)}")
        return jsonify({'error': f'Failed to fetch opportunities: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

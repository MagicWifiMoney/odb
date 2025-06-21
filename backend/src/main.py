import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.opportunity import db
from src.routes.user import user_bp
from src.routes.opportunities import opportunities_bp
from src.routes.scraping import scraping_bp
from src.routes.rfp_enhanced import rfp_enhanced_bp

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
            '/api/sync/status'
        ]
    })

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

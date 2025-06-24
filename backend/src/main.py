import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app instance
app = Flask(__name__)
CORS(app)

@app.route('/api/health-simple')
def health_simple():
    return jsonify({
        'status': 'healthy',
        'message': 'Basic Flask app is running'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Full health check',
        'environment': {
            'FLASK_ENV': os.getenv('FLASK_ENV', 'unknown'),
            'DATABASE_CONFIGURED': bool(os.getenv('DATABASE_URL'))
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

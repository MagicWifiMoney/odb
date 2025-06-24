from flask import Flask, jsonify
import os
import sys

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

app = Flask(__name__)

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Simple health check
        health_status = {
            "status": "healthy",
            "service": "ODB API",
            "environment": os.getenv("VERCEL_ENV", "development")
        }
        
        # Check environment variables
        required_env_vars = [
            "VITE_SUPABASE_URL",
            "VITE_SUPABASE_ANON_KEY"
        ]
        
        env_status = {}
        for var in required_env_vars:
            env_status[var] = "configured" if os.getenv(var) else "missing"
        
        health_status["environment_variables"] = env_status
        
        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
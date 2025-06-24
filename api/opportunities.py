from flask import Flask, jsonify, request
import os
import sys

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

app = Flask(__name__)

def handler(request):
    """Vercel serverless function handler for opportunities API"""
    try:
        if request.method == 'GET':
            # Mock opportunities data for now
            opportunities = [
                {
                    "id": 1,
                    "title": "Sample Federal Contract Opportunity",
                    "agency": "Department of Defense",
                    "value": "$50,000",
                    "deadline": "2025-07-15",
                    "status": "active"
                },
                {
                    "id": 2,
                    "title": "IT Services Contract",
                    "agency": "General Services Administration",
                    "value": "$125,000",
                    "deadline": "2025-08-01",
                    "status": "active"
                }
            ]
            
            return jsonify({
                "status": "success",
                "data": opportunities,
                "count": len(opportunities)
            })
        
        return jsonify({
            "status": "error",
            "message": "Method not allowed"
        }), 405
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
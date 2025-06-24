#!/bin/bash

echo "🚀 Starting Opportunity Dashboard Locally..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

echo "🗄️  Starting backend server..."
export FLASK_ENV=development
export DATABASE_URL=sqlite:///instance/opportunities.db
export SECRET_KEY=dev-secret-key
python src/main.py &
BACKEND_PID=$!

echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install --legacy-peer-deps

echo "🎨 Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Opportunity Dashboard is starting..."
echo "🔗 Frontend: http://localhost:5173"
echo "🔗 Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
trap "echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
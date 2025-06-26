# 🚀 Opportunity Dashboard - Simple Local Setup

## Super Quick Start (1 Command!)

```bash
./start-local.sh
```

This will:
- ✅ Install all dependencies automatically
- ✅ Start backend with your existing SQLite database
- ✅ Start frontend with hot reload
- ✅ Show you the URLs to access

## Manual Setup (if script doesn't work)

### 1. Start Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=sqlite:///instance/opportunities.db
export SECRET_KEY=dev-secret-key

# Start Flask server
python src/main.py
```

### 2. Start Frontend (in new terminal)
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

## Access Your Dashboard

- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend API**: http://localhost:5000 (Flask server)
- **Health Check**: http://localhost:5000/api/health-simple

## Your Data

Your existing SQLite database at `backend/instance/opportunities.db` contains real data and will be used automatically. No setup required!

## Requirements

- Python 3.9+
- Node.js 18+
- Your existing SQLite database (already present)

## If You Get Errors

### Python/pip issues:
```bash
# Install Python dependencies manually
cd backend
pip install Flask Flask-Cors Flask-SQLAlchemy requests python-dotenv psycopg2-binary gunicorn supabase
```

### Node.js issues:
```bash
# Install with force
cd frontend
npm install --legacy-peer-deps --force
```

### Database issues:
Your SQLite database should already exist at `backend/instance/opportunities.db`. If it's missing, that's the problem!

## Next Steps for Production

Once this works locally, you can:
1. Use the Docker setup (when Docker is running)
2. Deploy to Railway/Render/DigitalOcean
3. Use VS Code devcontainer

---

🎯 **Goal**: Get your dashboard running locally with real data in under 2 minutes!
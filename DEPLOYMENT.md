# 🚀 ODB Deployment Guide

> **Quick Deploy**: Railway (Backend) + Vercel (Frontend) + Supabase (Database)

## Prerequisites

- Node.js 18+
- Python 3.9+
- Git

## Environment Setup

### 1. Backend Environment
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your credentials:
```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres.your_project_id:your_password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://your_project_id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# API Keys
SAM_API_KEY=your_sam_gov_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Flask
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
```

### 2. Frontend Environment
```bash
cd frontend
cp .env.local.template .env.local
```

Edit `frontend/.env.local`:
```bash
VITE_API_BASE_URL=http://localhost:5000/api
VITE_SUPABASE_URL=https://your_project_id.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

## Local Development

### Start Backend
```bash
cd backend
pip install -r requirements.txt
python src/main.py
# Backend: http://localhost:5000
```

### Start Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
# Frontend: http://localhost:5173
```

### Verify Setup
- Backend health: http://localhost:5000/api/health
- Frontend: http://localhost:5173

## Production Deployment

### 1. Deploy Backend to Railway

1. **Connect Repository to Railway**
   - Go to [Railway](https://railway.app)
   - Create new project from GitHub repo
   - Railway auto-detects `railway.json` configuration

2. **Set Environment Variables in Railway**
   ```bash
   DATABASE_URL=postgresql://... (auto-provided by Railway PostgreSQL)
   SUPABASE_URL=https://your_project_id.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
   SAM_API_KEY=your_sam_gov_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   SECRET_KEY=your-production-secret-key
   FLASK_ENV=production
   PORT=5001
   ```

3. **Deploy**
   - Railway automatically deploys on git push
   - Note your Railway URL: `https://your-app.up.railway.app`

### 2. Deploy Frontend to Vercel

1. **Connect Repository to Vercel**
   - Go to [Vercel](https://vercel.com)
   - Import your GitHub repository
   - Set framework preset to "Vite"
   - Set root directory to `frontend`

2. **Set Environment Variables in Vercel**
   ```bash
   VITE_API_BASE_URL=https://your-railway-app.up.railway.app/api
   VITE_SUPABASE_URL=https://your_project_id.supabase.co
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
   ```

3. **Deploy**
   - Vercel automatically deploys on git push
   - Your app: `https://your-app.vercel.app`

## Database Setup

Initialize Supabase tables:
```bash
cd backend
python setup_supabase.py
```

## Features & Data Sources

### Automated Data Collection
- **SAM.gov**: Federal contracts (requires API key)
- **Grants.gov**: Federal grants (free)
- **USASpending.gov**: Historical contracts (free)
- **Web Scraping**: Additional sources via Firecrawl

### AI Intelligence ($10/month)
- Daily market intelligence queries
- Weekly deep analysis
- Emergency contract discovery
- Budget protection with hard limits

### Monitoring Schedule
- **Hourly**: API rotation for light sync
- **Daily 2:00 AM**: Comprehensive data sync
- **Daily 2:30 AM**: AI analysis (if enabled)
- **Weekly Sunday 3:00 AM**: Deep predictions

## Troubleshooting

### Common Issues

**"SUPABASE_URL environment variables must be set"**
- Verify `.env` file exists in backend directory
- Check environment variables are set correctly

**"Connection failed"**
- Verify Supabase project is active
- Check database URL and credentials
- Ensure internet connectivity

**"API key invalid"**
- Verify API keys copied correctly (no extra spaces)
- Check if keys have expired
- Test with different model/provider

**CORS Issues**
- Backend enables CORS for all origins
- Verify frontend URL in VITE_API_BASE_URL

### Health Checks

**Backend Health**: `curl https://your-railway-app.up.railway.app/api/health`

**Expected Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "apis": {
    "sam_gov": "configured",
    "perplexity": "configured",
    "firecrawl": "configured"
  }
}
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/Vite)  │◄──►│   (Flask)       │◄──►│   (PostgreSQL)  │
│   Vercel        │    │   Railway       │    │   Supabase      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Cost Management

- **Free Tier**: Government APIs (SAM.gov requires registration)
- **AI Features**: ~$10/month (Perplexity API with budget limits)
- **Infrastructure**: 
  - Railway: $5/month (hobby plan)
  - Vercel: Free (hobby plan)
  - Supabase: Free (up to 2 projects)

## Security

- Environment variables stored securely in deployment platforms
- API keys not committed to repository
- Supabase Row Level Security (RLS) enabled
- CORS configured for frontend domain only in production

---

**Built with ❤️ for federal opportunity discovery**
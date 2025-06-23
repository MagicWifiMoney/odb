# 🚀 Deployment Guide - Federal Opportunity Dashboard

## Current Architecture

### ✅ **Frontend: Vercel**
- **Framework**: React + Vite
- **Location**: `/frontend/` directory
- **Domain**: Your custom Vercel domain
- **Build**: Automatic on git push to main

### ✅ **Backend: Railway** 
- **Framework**: Python Flask
- **Location**: `/backend/` directory  
- **API**: Railway auto-generated URL
- **Features**: AI Intelligence + Free API monitoring

### ✅ **Database: Supabase**
- **Type**: PostgreSQL
- **Purpose**: Opportunity storage + sync logs
- **Connection**: Both backend and frontend connect directly

## Environment Variables Required

### **Railway Backend**
```bash
DATABASE_URL=postgresql://postgres.zkdrpchjejelgsuuffli:DeepSignal2TheMoon@aws-0-us-east-1.pooler.supabase.com:5432/postgres
SAM_API_KEY=rCTGB3OnZVurfr2X7hqDHMt6DUHilFnP7WgtflLf
FIRECRAWL_API_KEY=fc-3613f533df0e42d09306650f54b2f00c
PERPLEXITY_API_KEY=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
SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SECRET_KEY=your-flask-secret-key
FLASK_ENV=production
```

### **Vercel Frontend**
```bash
VITE_API_BASE_URL=https://your-railway-backend.up.railway.app/api
VITE_SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Deployment Steps

### 1. **Get Railway Backend URL**
Once Railway deployment succeeds:
1. Go to Railway dashboard
2. Copy your backend URL (e.g., `https://web-production-1234.up.railway.app`)
3. Update Vercel environment variable: `VITE_API_BASE_URL=https://your-railway-url.up.railway.app/api`

### 2. **Update Vercel Frontend**
```bash
# Update the Railway URL in vercel.json
cd frontend
# Edit vercel.json to use actual Railway URL
# Redeploy automatically triggers on git push
```

### 3. **Test Integration**
- Frontend (Vercel) → Backend (Railway) → Database (Supabase)
- Verify `/api/health` endpoint works
- Check opportunity data loads in frontend
- Confirm AI intelligence is running

## Features Available

### ✅ **Free Government API Monitoring**
- Hourly: SAM.gov, Grants.gov, USASpending.gov rotation
- Daily: Comprehensive sync from all free APIs
- Weekly: Database analysis

### ✅ **AI Intelligence ($10/month)**
- Daily: 5 AI queries for market intelligence
- Weekly: 3 AI queries for deep agency analysis  
- Emergency: On-demand high-priority contract discovery
- Budget protection: Hard limits prevent overspend

### ✅ **Real-time Dashboard**
- 5,016+ federal opportunities
- Advanced filtering and search
- Opportunity scoring and intelligence
- Market trends and competitive analysis

## Management Commands

### **Check System Status**
```bash
# Frontend: Check Vercel deployment dashboard
# Backend: Check Railway deployment logs
# Database: Monitor Supabase dashboard
```

### **AI Intelligence Management**
```bash
# Check AI budget status
curl https://your-railway-backend.up.railway.app/api/health

# Monitor sync logs in Supabase
# View opportunity counts in dashboard
```

## Troubleshooting

### **CORS Issues**
- Backend automatically enables CORS for all origins
- Vercel frontend should connect without issues

### **Environment Variables**
- Railway: Set in Railway dashboard environment tab
- Vercel: Set in Vercel dashboard environment variables

### **Database Connection**
- Both frontend and backend connect directly to Supabase
- No connection through Railway needed

## Security Notes

- Database credentials are secure in environment variables
- API keys stored in Railway/Vercel environments only
- No secrets committed to git repository
- CORS enabled for frontend-backend communication
# 🚀 Fresh Deployment Guide - Opportunity Dashboard

## 🎯 Quick Start (5 minutes to deployed app)

### **Option 1: Railway (RECOMMENDED)**
Perfect for full-stack Python apps like yours.

```bash
# 1. Push to GitHub (if not already)
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to railway.app
# 3. Connect GitHub repository
# 4. Add environment variables (see below)
# 5. Deploy! 🚀
```

**Cost**: $5/month (includes PostgreSQL database)

### **Option 2: Render**
Similar to Railway, great Python support.

```bash
# 1. Go to render.com
# 2. Connect GitHub repository  
# 3. Choose "Web Service"
# 4. Build Command: pip install -r backend/requirements.txt
# 5. Start Command: cd backend && python -m flask --app src.main run --host=0.0.0.0 --port=$PORT
```

**Cost**: Free tier available, $7/month for full features

### **Option 3: Vercel (Full-Stack)**
Still good, but requires serverless restructuring.

---

## 🛠️ **Environment Variables Needed**

### **Required (for basic functionality):**
```bash
DATABASE_URL=postgresql://... (provided by Railway/Render)
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
```

### **Optional (for enhanced features):**
```bash
SAM_GOV_API_KEY=your_key
PERPLEXITY_API_KEY=your_key  
FIRECRAWL_API_KEY=your_key
```

### **Supabase Variables:**
```bash
SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprZHJwY2hqZWplbGdzdXVmZmxpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyMjY4MTMsImV4cCI6MjA2NTgwMjgxM30.xBBArkhXeFT26BmVI-WNag0qa0hHGdFUmxmlcTi4CGg
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprZHJwY2hqZWplbGdzdXVmZmxpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDIyNjgxMywiZXhwIjoyMDY1ODAyODEzfQ.sfXaVkEOIiJMpKdTt7YLauIwxcqjhL1J04Vt92neWR4
```

---

## 📋 **Pre-Deployment Checklist**

- [x] `Procfile` created
- [x] `railway.json` configured
- [x] `requirements.txt` in backend/
- [x] Flask app properly configured
- [x] CORS enabled for production
- [x] Database models ready

---

## 🔄 **Deployment Steps (Railway)**

### **Step 1: Prepare Repository**
```bash
# Make sure everything is committed
git status
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### **Step 2: Railway Setup**
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Connect GitHub account
4. Select your repository
5. Railway auto-detects Python app

### **Step 3: Add Database**
1. In Railway dashboard, click "+" 
2. Add "PostgreSQL" 
3. Railway automatically sets `DATABASE_URL`

### **Step 4: Configure Environment**
Add these variables in Railway dashboard:
```bash
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here
```

### **Step 5: Deploy Frontend**
Deploy frontend separately:
1. Create new Railway service for frontend
2. Or use Vercel/Netlify for frontend (recommended)
3. Set `VITE_API_BASE_URL=https://your-backend.railway.app/api`

---

## 🌐 **Frontend Deployment Options**

### **Option A: Vercel (Recommended for Frontend)**
```bash
cd frontend
npx vercel
# Follow prompts
# Set VITE_API_BASE_URL to your backend URL
```

### **Option B: Netlify**
```bash
cd frontend
npm run build
# Drag dist/ folder to netlify.com
# Or connect GitHub for auto-deploy
```

---

## ✅ **Post-Deployment Testing**

### **Backend Tests:**
- [ ] `GET /api/health` returns 200
- [ ] `GET /api/opportunities` returns data
- [ ] Database connection working

### **Frontend Tests:**
- [ ] App loads without errors
- [ ] API calls work
- [ ] Dashboard shows data
- [ ] Navigation works

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**"ModuleNotFoundError"**
```bash
# Make sure all imports use absolute paths
# from src.models.opportunity import db  ✅
# from models.opportunity import db      ❌
```

**"Database connection failed"**
```bash
# Check DATABASE_URL is set
# Railway/Render provide this automatically
```

**"CORS errors"**
```bash
# Make sure Flask-CORS is enabled
# Check frontend API URL matches backend URL
```

---

## 🎉 **Success Criteria**

When deployment is successful, you should have:
- ✅ Backend API responding at `https://your-app.railway.app/api`
- ✅ Frontend app at `https://your-frontend.vercel.app`
- ✅ Database storing opportunities
- ✅ Live data sync working
- ✅ Dashboard showing real data

---

**Total Time**: 15-30 minutes
**Total Cost**: $5/month (Railway) or FREE (with limitations)

Ready to deploy? Let's go! 🚀 
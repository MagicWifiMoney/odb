# Vercel Deployment Guide for ODB

## Quick Setup

### 1. Connect to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project" and import your GitHub repository
3. **IMPORTANT: Set Root Directory to `frontend`** in the project configuration
4. Vercel will auto-detect the configuration from `vercel.json`

### 2. Configure Root Directory (CRITICAL STEP)
In your Vercel project settings:
- Go to **Settings** > **General**
- Find **Root Directory** setting
- Set it to: `frontend`
- Click **Save**

This tells Vercel to treat the frontend folder as the project root.

### 3. Configure Environment Variables
In your Vercel project dashboard, go to Settings > Environment Variables and add:

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Configuration (if using external API)
VITE_API_BASE_URL=https://your-backend-api.com/api

# PostHog Analytics (Optional)
VITE_POSTHOG_KEY=your_posthog_project_key
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_POSTHOG_ENABLED=true
```

### 3. Deploy
- Click "Deploy" in Vercel
- Your app will be available at `https://your-project.vercel.app`

## Configuration Files

### vercel.json
- Configures build commands for the frontend
- Sets output directory to `frontend/dist`
- Handles SPA routing with rewrites

### Project Structure
```
odb/
├── frontend/          # React/Vite application
├── backend/           # Python Flask API (for Railway)
├── vercel.json        # Vercel configuration
├── package.json       # Root package.json for Vercel
└── VERCEL_DEPLOYMENT.md # This file
```

## Architecture Options

### Option 1: Frontend Only (Recommended for MVP)
- Deploy frontend to Vercel
- Use Supabase directly from frontend
- No backend API needed

### Option 2: Hybrid (Current Setup)
- Frontend: Vercel
- Backend: Railway (existing setup)
- Database: Supabase

## Troubleshooting

### Build Failures
- Check that `frontend/package.json` has correct dependencies
- Verify Node.js version compatibility
- Check build logs in Vercel dashboard

### Environment Variable Issues
- Make sure all VITE_ prefixed variables are set
- Check that Supabase URL and keys are correct
- Test locally first with `.env.local`

### API Connection Issues
- If using external backend, verify CORS settings
- Check VITE_API_BASE_URL points to correct domain
- Test API endpoints independently

## Local Development
```bash
cd frontend
npm install --legacy-peer-deps
cp .env.local.template .env.local
# Edit .env.local with your variables
npm run dev
```

## Production Checklist
- [ ] Environment variables configured in Vercel
- [ ] Supabase project active and accessible
- [ ] Build completes successfully
- [ ] App loads without console errors
- [ ] API connections working (if applicable)
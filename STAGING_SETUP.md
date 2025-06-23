# 🧪 Staging Environment Setup

## Quick Setup (5 minutes)

### 1. Create Staging Branch
```bash
git checkout -b staging
git push origin staging
```

### 2. Configure Auto-Deployments

#### Railway (Backend)
1. Go to your Railway project dashboard
2. Click "Settings" → "Deployments"
3. Enable "Deploy on push" for `staging` branch
4. Set environment to "staging"

#### Vercel (Frontend)
1. Go to your Vercel project dashboard
2. Click "Settings" → "Git"
3. Enable "Deploy on push" for `staging` branch
4. Set environment to "staging"

### 3. Your Workflow

#### Testing Changes
```bash
git checkout staging
# Make your changes
git add .
git commit -m "Testing new feature"
git push origin staging
# Auto-deploys to staging
```

#### Deploy to Production
```bash
git checkout main
git merge staging
git push origin main
# Auto-deploys to production
```

### 4. Visual Indicators

- **Staging**: Orange banner shows "🧪 STAGING ENVIRONMENT"
- **Production**: Clean, normal appearance

### 5. Environment URLs

- **Production**: `https://www.rfptracking.com`
- **Staging**: Same URL, but with staging banner

## Benefits

✅ **Safe Testing**: Test without affecting production
✅ **Visual Feedback**: Clear staging indicator
✅ **Easy Workflow**: Simple git commands
✅ **No Extra Costs**: Uses existing infrastructure
✅ **Automatic Deployments**: No manual work needed 
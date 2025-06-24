# 🚀 Opportunity Dashboard - Production Deployment Setup

## 📋 Environment Configuration

Your API keys and Supabase configuration have been prepared for production deployment. Follow these steps to set up your environment files.

### 🔧 Step 1: Backend Environment Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Copy the production configuration:**
   ```bash
   cp production_config.txt .env
   ```

3. **Verify the .env file contains all your keys:**
   - ✅ Supabase configuration (URL, anon key, service role key)
   - ✅ Database URL (PostgreSQL connection)
   - ✅ SAM.gov API key
   - ✅ Perplexity AI API key  
   - ✅ Firecrawl API key
   - ✅ Feature flags and cost tracking settings

### 🎨 Step 2: Frontend Environment Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Copy the frontend configuration:**
   ```bash
   cp production_config.txt .env
   ```

3. **Update the backend API URL:**
   - Edit the `VITE_API_URL` in `frontend/.env`
   - Replace `https://your-backend-domain.com/api` with your actual backend URL

### 🔍 Step 3: Verify Configuration

Run this verification script to ensure everything is configured correctly:

```bash
cd backend
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('🔍 Verifying Production Configuration...')
print('=' * 50)

# Check all required environment variables
required_vars = {
    'SUPABASE_URL': 'Supabase Project URL',
    'SUPABASE_ANON_KEY': 'Supabase Anonymous Key',
    'SUPABASE_SERVICE_ROLE_KEY': 'Supabase Service Role Key',
    'DATABASE_URL': 'PostgreSQL Database Connection',
    'SAM_GOV_API_KEY': 'SAM.gov API Key',
    'PERPLEXITY_API_KEY': 'Perplexity AI API Key',
    'FIRECRAWL_API_KEY': 'Firecrawl API Key',
    'SECRET_KEY': 'Flask Secret Key'
}

all_good = True
for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        # Show partial value for security
        if 'KEY' in var or 'SECRET' in var:
            display_value = value[:10] + '...' + value[-5:] if len(value) > 15 else '***'
        else:
            display_value = value[:40] + '...' if len(value) > 40 else value
        print(f'✅ {var}: {display_value}')
    else:
        print(f'❌ {var}: MISSING')
        all_good = False

if all_good:
    print('\n🎉 All environment variables are configured!')
    print('✅ Ready for production deployment')
else:
    print('\n❌ Some environment variables are missing')
    print('Please check your .env file')
"
```

### 🗄️ Step 4: Database Setup

Initialize your Supabase database with the required schema:

```bash
cd backend
python3 setup_supabase.py
```

### 🚀 Step 5: Start the Application

1. **Start the backend:**
   ```bash
   cd backend
   python3 src/main.py
   ```

2. **Start the frontend (in a new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

### 🌐 Step 6: Production Deployment

For production deployment on platforms like Railway, Heroku, or Vercel:

1. **Set environment variables in your deployment platform:**
   - Copy all variables from `backend/.env` to your platform's environment settings
   - Copy all variables from `frontend/.env` to your frontend deployment settings

2. **Update the frontend API URL:**
   - Set `VITE_API_URL` to your deployed backend URL
   - Example: `VITE_API_URL=https://your-app.railway.app/api`

## 📊 Your Configuration Summary

### 🏗️ **Project Details:**
- **Project Name:** opportunity-dashboard
- **Supabase Username:** MagicWifiMoney
- **Project Reference:** zkdrpchjejelgsuuffli
- **Database:** PostgreSQL (Supabase)

### 🔑 **API Keys Configured:**
- ✅ **SAM.gov API:** `rCTGB3OnZVurfr2X7hqDHMt6DUHilFnP7WgtflLf`
- ✅ **Perplexity AI:** `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`
- ✅ **Firecrawl:** `fc-3613f533df0e42d09306650f54b2f00c`
- ✅ **Supabase:** All keys configured

### 🚀 **Features Enabled:**
- ✅ Real-time government contracting data
- ✅ AI-powered market intelligence
- ✅ Web scraping capabilities
- ✅ Cost tracking and budget management
- ✅ Performance monitoring
- ✅ Intelligent caching

## 🔒 Security Notes

1. **Never commit `.env` files** to version control
2. **Rotate API keys regularly** for security
3. **Monitor API usage** to stay within budget limits
4. **Use strong SECRET_KEY** for production (already generated)

## 🆘 Troubleshooting

### Common Issues:

1. **"SUPABASE_URL environment variables must be set"**
   - Ensure your `.env` file is in the correct directory
   - Verify the file contains all Supabase variables

2. **"Connection failed"**
   - Check your internet connection
   - Verify Supabase project is active
   - Confirm database URL is correct

3. **"API key invalid"**
   - Verify API keys are copied correctly
   - Check for extra spaces or characters
   - Ensure keys haven't expired

### Getting Help:

If you encounter issues:
1. Run the verification script above
2. Check the console logs for specific error messages
3. Verify all environment variables are set correctly

## 🎯 Next Steps

Once your environment is configured:

1. **Test the Supabase connection:**
   ```bash
   cd backend
   python3 test_connection.py
   ```

2. **Populate with real data:**
   ```bash
   python3 clear_and_sync.py
   ```

3. **Access your dashboard:**
   - Backend API: `http://localhost:5001/api/health`
   - Frontend: `http://localhost:5173`

Your Opportunity Dashboard is now configured for production deployment! 🎉 
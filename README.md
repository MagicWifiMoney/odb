# ODB - Opportunity Discovery Bot

> **Status**: 🚀 Production Ready | **Latest Version**: v2.1.0 | **Live Demo**: [https://odb-frontend.vercel.app](https://odb-frontend.vercel.app)

An intelligent system for discovering and tracking government contracting opportunities using AI-powered analysis with automated data collection and real-time insights.

---

## 🚀 Quick Start

### Live Deployment
- **Frontend**: [https://odb-frontend.vercel.app](https://odb-frontend.vercel.app) (Vercel)
- **Backend API**: [https://odb-production.up.railway.app](https://odb-production.up.railway.app) (Railway)
- **Health Check**: [https://odb-production.up.railway.app/health](https://odb-production.up.railway.app/health)

### ⚙️ Environment Setup for Real Data

**Required for SAM.gov federal contracts:**
```bash
SAM_API_KEY=rCTGB3OnZVurfr2X7hqDHMt6DUHilFnP7WgtflLf
```

**Optional for enhanced features:**
```bash
PERPLEXITY_API_KEY=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
FIRECRAWL_API_KEY=fc-3613f533df0e42d09306650f54b2f00c
```

### 🔄 Automated Data Sync System

The system includes a Railway worker service that automatically:
- **Hourly**: Rotates through APIs for light sync
- **Daily 2:00 AM**: Comprehensive sync from all sources
- **Daily 2:30 AM**: AI intelligence analysis (if enabled)
- **Weekly Sunday 3:00 AM**: Deep analysis and predictions

### Data Sources
1. **SAM.gov** (requires API key) - Federal contracts and solicitations
2. **Grants.gov** (free) - Federal grant opportunities
3. **USASpending.gov** (free) - Historical contract awards
4. **Web Scraping** (optional) - Additional sources via Firecrawl

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/Vite)  │◄──►│   (Flask)       │◄──►│   (PostgreSQL)  │
│   Port: 5173    │    │   Port: 5000    │    │   Supabase      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel        │    │   Railway       │    │   Supabase      │
│   (Production)  │    │   (Production)  │    │   (Production)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 18+ and npm/pnpm
- Python 3.9+
- PostgreSQL (or use Supabase)

### **Local Development Setup**

```bash
# 1. Clone the repository
git clone https://github.com/MagicWifiMoney/odb.git
cd odb

# 2. Backend Setup
cd backend
pip install -r requirements.txt
cp ../env.example .env  # Configure your environment variables

# 3. Start Backend API
python -m flask --app src.main run --debug
# API will be available at http://localhost:5000

# 4. Frontend Setup (in new terminal)
cd frontend
npm install --legacy-peer-deps
npm run dev
# Frontend will be available at http://localhost:5173
```

### **Environment Configuration**

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/opportunity_db
# Or use Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Flask
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development

# API Keys (Optional)
SAM_GOV_API_KEY=your_sam_gov_key
PERPLEXITY_API_KEY=your_perplexity_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

---

## 🎨 **Features & Capabilities**

### **🏠 Dashboard**
- **Real-time Analytics**: Live opportunity metrics and trends
- **Interactive Charts**: Score distributions, agency breakdowns, due date analysis
- **Key Performance Indicators**: Total opportunities, high-score opportunities, urgent deadlines
- **Recent Activity Feed**: Latest opportunities with detailed previews

### **🔍 Search & Discovery**
- **Advanced Filtering**: By agency, value, score, due date, source type
- **Full-text Search**: Search across titles, descriptions, and agencies
- **Smart Sorting**: Multiple sorting options with relevance scoring
- **Bulk Operations**: Export and manage multiple opportunities

### **🧠 AI-Powered Intelligence**
- **Opportunity Scoring**: Proprietary algorithm considering multiple factors
- **Relevance Analysis**: AI-powered relevance scoring based on user preferences
- **Competitive Intelligence**: Market analysis and competitor identification
- **Strategic Insights**: Key requirements and risk factor analysis

### **📊 Opportunity Management**
- **Detailed Views**: Comprehensive opportunity information
- **Status Tracking**: Review, pursue, submit status management
- **Contact Information**: Direct access to opportunity contacts
- **Document Links**: Easy access to solicitation documents

### **🔗 Data Integration**
- **SAM.gov Integration**: Government contract opportunities
- **Grants.gov**: Federal grant opportunities
- **Perplexity AI**: Enhanced opportunity research
- **Firecrawl**: Web scraping for additional sources
- **Automated Sync**: Scheduled data synchronization

### **👤 User Management**
- **Authentication**: Secure login/register system
- **User Profiles**: Customizable preferences and keywords
- **Dashboard Personalization**: Tailored views based on user interests
- **Activity Tracking**: User interaction history

---

## 🛠️ **Technology Stack**

### **Frontend**
- **Framework**: React 19 with Vite
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **State Management**: React Hooks + Context
- **Routing**: React Router v7
- **HTTP Client**: Fetch API with custom wrapper

### **Backend**
- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: Flask sessions + Supabase Auth
- **API Documentation**: OpenAPI/Swagger ready
- **Background Tasks**: Python Schedule
- **External APIs**: SAM.gov, Perplexity, Firecrawl

### **Database Schema**
- **Opportunities**: Core opportunity data with scoring
- **Users**: User profiles and preferences
- **Opportunity Tracking**: User-opportunity relationships
- **Audit Logs**: Data sync and user activity tracking

### **Deployment**
- **Backend**: Railway (Python app + PostgreSQL)
- **Frontend**: Vercel (Static site deployment)
- **Database**: Supabase (PostgreSQL as a Service)
- **CI/CD**: GitHub Actions integration

---

## 🚀 **Deployment**

### **Production Deployment**

**Backend (Railway)**
```bash
# Repository is configured for Railway deployment
# 1. Push to GitHub
git push origin main

# 2. Connect to Railway
# 3. Add environment variables
# 4. Railway auto-deploys using railway.json
```

**Frontend (Vercel)**
```bash
cd frontend
npm run build
npx vercel --prod
# Set VITE_API_BASE_URL to your Railway backend URL
```

### **Environment Variables for Production**

**Railway (Backend)**
```bash
DATABASE_URL=postgresql://... (auto-provided by Railway)
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cC...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cC...
```

**Vercel (Frontend)**
```bash
VITE_API_BASE_URL=https://your-app.railway.app/api
VITE_SUPABASE_URL=https://zkdrpchjejelgsuuffli.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cC...
```

---

## 📈 **Roadmap**

### **🎯 Version 2.1.0 (Next 30 Days)**
- [ ] Enhanced AI recommendations engine
- [ ] Email notification system
- [ ] Advanced compliance analysis
- [ ] Performance monitoring dashboard
- [ ] Mobile app (React Native)

### **🚀 Version 2.2.0 (Next 60 Days)**
- [ ] Multi-tenant support
- [ ] Advanced analytics and reporting
- [ ] Integration with CRM systems
- [ ] API rate limiting and caching
- [ ] Automated proposal generation

### **🌟 Version 3.0.0 (Next 90 Days)**
- [ ] Machine learning-based opportunity matching
- [ ] Collaborative team features
- [ ] Advanced competitive intelligence
- [ ] Document analysis with AI
- [ ] Enterprise SSO integration

---

## 🧪 **Testing**

### **Backend Tests**
```bash
cd backend
python -m pytest test_*.py -v
```

### **Running the Test Suite**
Run all unit tests from the repository root:

```bash
pip install -r requirements.txt
pytest
```

### **Frontend Tests**
```bash
cd frontend
npm run test
```

### **API Health Check**
```bash
curl http://localhost:5000/api/health
```

---

## 📊 **Performance Metrics**

- **API Response Time**: < 200ms average
- **Database Queries**: Optimized with indexes
- **Frontend Bundle Size**: < 2MB compressed
- **Lighthouse Score**: 95+ (Performance, Accessibility, SEO)
- **Uptime Target**: 99.9%

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### **Development Guidelines**
- Follow React/Flask best practices
- Write tests for new features
- Update documentation
- Use conventional commit messages

---

## 📞 **Support & Contact**

- **Issues**: [GitHub Issues](https://github.com/MagicWifiMoney/odb/issues)
- **Documentation**: [Wiki](https://github.com/MagicWifiMoney/odb/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/MagicWifiMoney/odb/discussions)

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 **Acknowledgments**

- **shadcn/ui** for the beautiful component library
- **Supabase** for the backend infrastructure
- **Railway** for seamless deployment
- **Radix UI** for accessible primitives

---

**Built with ❤️ for the business development community**

> Last Updated: June 21, 2025 | Status: Production Ready 🚀

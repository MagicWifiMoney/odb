# 🐳 Opportunity Dashboard - Docker Deployment

## Quick Start (1 Command!)

```bash
docker-compose up
```

That's it! Your opportunity dashboard will be running on:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000  
- **Redis UI**: http://localhost:8081 (admin/admin123)

## What You Get

### ✅ Complete Application Stack
- **Flask Backend** with existing SQLite database (already has data!)
- **React Frontend** with Nginx serving
- **Redis Cache** for API optimization
- **Redis Commander** for cache management

### ✅ Real Data Flowing
- Uses your existing SQLite database at `backend/instance/opportunities.db`
- All your current data is preserved and accessible
- No migration required!

### ✅ Development & Production Ready
- Production builds with nginx
- Development mode with hot reload
- VS Code DevContainer support

## Environment Setup (Optional)

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys (optional)
nano .env
```

Most features work without any API keys using the existing SQLite data!

## Development Mode

```bash
# Start with development frontend (hot reload)
docker-compose --profile dev up

# Access development server
# Frontend Dev: http://localhost:5173 (hot reload)
# Frontend Prod: http://localhost:3000 (nginx)
```

## VS Code Integration

Open project in VS Code and it will prompt to:
1. **Reopen in Container** - Full development environment
2. **Auto-install extensions** - Python, React, Docker tools
3. **Port forwarding** - All services accessible

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   SQLite DB     │
│   (React/Nginx) │◄──►│   (Flask)       │◄──►│   (Local File)  │
│   Port 3000     │    │   Port 5000     │    │   Real Data!    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   Port 6379     │
                       └─────────────────┘
```

## Commands

```bash
# Start everything
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after changes
docker-compose up --build

# Development mode with hot reload
docker-compose --profile dev up
```

## Troubleshooting

### Frontend Build Issues
If the frontend container fails to build, you can use development mode:
```bash
docker-compose --profile dev up
```

### Port Conflicts
If ports are in use:
```bash
# Edit docker-compose.yml to change ports
# Example: Change "3000:80" to "3001:80"
```

### Data Reset
Your data is in `backend/instance/opportunities.db` - it's preserved between runs!

## Production Deployment

This same Docker setup works on any cloud provider:
- **Railway**: Connect GitHub repo, auto-deploy
- **DigitalOcean**: Use Docker droplet
- **AWS**: ECS or Lightsail containers
- **Google Cloud**: Cloud Run
- **Azure**: Container Instances

No changes needed - same docker-compose.yml works everywhere!

## Cost Breakdown
- **Infrastructure**: $0-5/month (many free tiers)
- **API Usage**: $0-10/month (most government APIs are free)
- **Total**: Under $15/month for full production setup

---

🎉 **You now have a production-ready deployment with real data flowing!**
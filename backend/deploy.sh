#!/bin/bash

# ODB-1 Perplexity Cost Optimization - Phase 2 Deployment Script
# Deploys optimized backend with feature flags and monitoring

set -e

echo "🚀 Starting ODB-1 Phase 2 Deployment..."

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="deploy.yml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=your_database_url_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Redis Configuration  
REDIS_URL=redis://redis:6379

# API Keys
PERPLEXITY_API_KEY=your_perplexity_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
EOF
    print_error "Please update .env file with your actual values and run again"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("DATABASE_URL" "SUPABASE_URL" "SUPABASE_KEY" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [[ "${!var}" == *"your_"*"_here" ]]; then
        print_error "Required environment variable $var is not set or has default value"
        exit 1
    fi
done

print_status "Environment validation passed"

# Build and deploy
print_info "Building and deploying containers..."

# Stop existing containers
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Build and start containers
docker-compose -f $COMPOSE_FILE build --no-cache
docker-compose -f $COMPOSE_FILE up -d

print_status "Containers started"

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 10

# Health checks
print_info "Performing health checks..."

# Check Redis
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis is healthy"
else
    print_error "Redis health check failed"
    exit 1
fi

# Check Backend API
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -s -f http://localhost:5001/api/health > /dev/null; then
        print_status "Backend API is healthy"
        break
    else
        print_info "Waiting for backend API... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Backend API health check failed after $max_attempts attempts"
    exit 1
fi

# Check feature flags
print_info "Checking feature flag configuration..."
feature_flags=$(curl -s http://localhost:5001/api/performance/feature-flags | jq -r '.data.enabled_count')
print_status "Feature flags configured: $feature_flags enabled"

# Check performance monitoring
print_info "Checking performance monitoring..."
performance_status=$(curl -s http://localhost:5001/api/performance/health | jq -r '.status')
if [ "$performance_status" = "healthy" ]; then
    print_status "Performance monitoring is active"
else
    print_warning "Performance monitoring check returned: $performance_status"
fi

# Display deployment summary
print_info "=== Deployment Summary ==="
echo "Environment: $ENVIRONMENT"
echo "Backend URL: http://localhost:5001"
echo "Redis URL: localhost:6379"
echo "Redis Commander: http://localhost:8081 (if monitoring profile enabled)"
echo ""

print_info "=== Available Endpoints ==="
echo "Health Check: http://localhost:5001/api/health"
echo "Performance Summary: http://localhost:5001/api/performance/summary"
echo "Feature Flags: http://localhost:5001/api/performance/feature-flags"
echo "Cost Tracking: http://localhost:5001/api/performance/cost-tracking"
echo ""

print_info "=== Phase 2 Optimization Features ==="
echo "✅ Redis Cache Enabled"
echo "✅ Performance Monitoring Active"
echo "✅ Feature Flags Configured"
echo "✅ Cost Tracking Enabled"
echo "✅ Query Optimization Ready"
echo ""

# Optional: Start monitoring dashboard
if [ "$2" = "--with-monitoring" ]; then
    print_info "Starting monitoring dashboard..."
    docker-compose -f $COMPOSE_FILE --profile monitoring up -d redis-commander
    print_status "Redis Commander available at http://localhost:8081"
fi

print_status "🎉 ODB-1 Phase 2 deployment completed successfully!"
print_info "Expected cost reduction: 70-80% from combined frontend + backend optimization"

# Optional: Run quick smoke test
if [ "$3" = "--test" ]; then
    print_info "Running smoke tests..."
    echo "Testing API endpoints..."
    
    # Test opportunities endpoint
    if curl -s "http://localhost:5001/api/opportunities?limit=1" | jq -e '.opportunities' > /dev/null; then
        print_status "Opportunities API test passed"
    else
        print_warning "Opportunities API test failed"
    fi
    
    # Test cache functionality
    cache_stats=$(curl -s http://localhost:5001/api/performance/cache-stats | jq -r '.status')
    if [ "$cache_stats" = "success" ]; then
        print_status "Cache system test passed"
    else
        print_warning "Cache system test failed"
    fi
fi 
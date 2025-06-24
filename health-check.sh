#!/bin/bash

# 🔍 ODB Health Check Script
# Usage: ./health-check.sh [backend-url] [frontend-url]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default URLs (can be overridden)
BACKEND_URL=${1:-"http://localhost:5000"}
FRONTEND_URL=${2:-"http://localhost:5173"}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to check if URL is reachable
check_url() {
    local url=$1
    local name=$2
    local timeout=${3:-10}
    
    if curl -s --max-time $timeout "$url" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check backend health
check_backend() {
    print_header "Backend Health Check"
    
    local health_url="${BACKEND_URL}/api/health"
    
    print_status "Checking backend at: $BACKEND_URL"
    
    if check_url "$BACKEND_URL" "Backend" 5; then
        print_success "Backend is reachable ✓"
    else
        print_error "Backend is not reachable ✗"
        return 1
    fi
    
    print_status "Checking health endpoint: $health_url"
    
    local health_response
    if health_response=$(curl -s --max-time 10 "$health_url" 2>/dev/null); then
        print_success "Health endpoint responding ✓"
        
        # Try to parse JSON response
        if echo "$health_response" | python3 -m json.tool > /dev/null 2>&1; then
            print_success "Health endpoint returns valid JSON ✓"
            
            # Check for status field
            if echo "$health_response" | grep -q '"status"'; then
                local status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
                if [ "$status" = "healthy" ]; then
                    print_success "Backend reports healthy status ✓"
                else
                    print_warning "Backend status: $status"
                fi
            else
                print_warning "Health response missing status field"
            fi
            
            echo "Health Response:"
            echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
        else
            print_warning "Health endpoint response is not valid JSON"
            echo "Response: $health_response"
        fi
    else
        print_error "Health endpoint not responding ✗"
        return 1
    fi
}

# Function to check frontend
check_frontend() {
    print_header "Frontend Health Check"
    
    print_status "Checking frontend at: $FRONTEND_URL"
    
    if check_url "$FRONTEND_URL" "Frontend" 5; then
        print_success "Frontend is reachable ✓"
        
        # Check if it returns HTML
        local content
        if content=$(curl -s --max-time 10 "$FRONTEND_URL" 2>/dev/null); then
            if echo "$content" | grep -q "<html\|<!DOCTYPE"; then
                print_success "Frontend returns HTML content ✓"
                
                # Check for common React/Vite indicators
                if echo "$content" | grep -q "react\|vite"; then
                    print_success "Frontend appears to be React/Vite app ✓"
                fi
                
                # Check for app title
                if echo "$content" | grep -q "<title>"; then
                    local title=$(echo "$content" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
                    print_success "Page title: $title"
                fi
            else
                print_warning "Frontend doesn't return HTML content"
            fi
        else
            print_warning "Could not fetch frontend content"
        fi
    else
        print_error "Frontend is not reachable ✗"
        return 1
    fi
}

# Function to check database connectivity (through backend)
check_database() {
    print_header "Database Connectivity Check"
    
    local db_url="${BACKEND_URL}/api/opportunities"
    
    print_status "Checking database through API: $db_url"
    
    if check_url "$db_url" "Database API" 10; then
        print_success "Database API endpoint is reachable ✓"
        
        # Try to get response
        local response
        if response=$(curl -s --max-time 15 "$db_url" 2>/dev/null); then
            if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
                print_success "Database API returns valid JSON ✓"
                
                # Check if it's an array or has data field
                if echo "$response" | grep -q '\[\|\{.*"data"'; then
                    print_success "Database appears to be connected and responding ✓"
                else
                    print_warning "Database response format unexpected"
                fi
            else
                print_warning "Database API response is not valid JSON"
            fi
        else
            print_warning "Could not fetch data from database API"
        fi
    else
        print_error "Database API endpoint not reachable ✗"
        return 1
    fi
}

# Function to run all checks
run_all_checks() {
    local backend_ok=true
    local frontend_ok=true
    local database_ok=true
    
    # Run checks
    check_backend || backend_ok=false
    check_frontend || frontend_ok=false
    check_database || database_ok=false
    
    # Summary
    print_header "Health Check Summary"
    
    if $backend_ok; then
        print_success "Backend: Healthy ✓"
    else
        print_error "Backend: Issues detected ✗"
    fi
    
    if $frontend_ok; then
        print_success "Frontend: Healthy ✓"
    else
        print_error "Frontend: Issues detected ✗"
    fi
    
    if $database_ok; then
        print_success "Database: Healthy ✓"
    else
        print_error "Database: Issues detected ✗"
    fi
    
    if $backend_ok && $frontend_ok && $database_ok; then
        echo
        print_success "🎉 All systems healthy!"
        return 0
    else
        echo
        print_error "❌ Some systems have issues"
        return 1
    fi
}

# Function to show help
show_help() {
    echo "🔍 ODB Health Check Script"
    echo
    echo "Usage: $0 [backend-url] [frontend-url]"
    echo
    echo "Parameters:"
    echo "  backend-url   - Backend URL (default: http://localhost:5000)"
    echo "  frontend-url  - Frontend URL (default: http://localhost:5173)"
    echo
    echo "Examples:"
    echo "  $0                                                    # Check local development"
    echo "  $0 https://your-app.railway.app                      # Check Railway backend only"
    echo "  $0 https://your-app.railway.app https://your-app.vercel.app  # Check production"
    echo
}

# Main execution
main() {
    if [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    echo "🔍 ODB Health Check"
    echo "Backend URL: $BACKEND_URL"
    echo "Frontend URL: $FRONTEND_URL"
    
    run_all_checks
}

# Run main function with all arguments
main "$@"
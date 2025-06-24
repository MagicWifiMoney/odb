#!/bin/bash

# 🚀 ODB - One-Command Setup & Deployment Script
# Usage: ./setup.sh [local|verify|help]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check required tools
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    if ! command_exists node; then
        missing_tools+=("Node.js 18+")
    else
        node_version=$(node --version | cut -d 'v' -f 2 | cut -d '.' -f 1)
        if [ "$node_version" -lt 18 ]; then
            missing_tools+=("Node.js 18+ (current: $(node --version))")
        else
            print_success "Node.js $(node --version) ✓"
        fi
    fi
    
    if ! command_exists python3; then
        missing_tools+=("Python 3.9+")
    else
        python_version=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
        print_success "Python $(python3 --version | cut -d ' ' -f 2) ✓"
    fi
    
    if ! command_exists pip && ! command_exists pip3; then
        missing_tools+=("pip")
    else
        if command_exists pip3; then
            print_success "pip3 $(pip3 --version | cut -d ' ' -f 2) ✓"
        else
            print_success "pip $(pip --version | cut -d ' ' -f 2) ✓"
        fi
    fi
    
    if ! command_exists npm; then
        missing_tools+=("npm")
    else
        print_success "npm $(npm --version) ✓"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo
        echo "Please install the missing tools and run this script again."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Function to setup environment files
setup_environment() {
    print_header "Setting Up Environment Files"
    
    # Backend environment
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            print_success "Created backend/.env from template"
            print_warning "Please edit backend/.env with your actual API keys and database credentials"
        else
            print_error "backend/.env.example not found"
            return 1
        fi
    else
        print_success "backend/.env already exists"
    fi
    
    # Frontend environment
    if [ ! -f "frontend/.env.local" ]; then
        if [ -f "frontend/.env.local.template" ]; then
            cp frontend/.env.local.template frontend/.env.local
            print_success "Created frontend/.env.local from template"
            print_warning "Please edit frontend/.env.local with your API URLs"
        else
            print_error "frontend/.env.local.template not found"
            return 1
        fi
    else
        print_success "frontend/.env.local already exists"
    fi
}

# Function to install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    # Install backend dependencies
    print_status "Installing Python dependencies..."
    cd backend
    if command_exists pip3; then
        pip_cmd="pip3"
    else
        pip_cmd="pip"
    fi
    if $pip_cmd install -r requirements.txt; then
        print_success "Backend dependencies installed"
    else
        print_error "Failed to install backend dependencies"
        exit 1
    fi
    cd ..
    
    # Install frontend dependencies
    print_status "Installing Node.js dependencies..."
    cd frontend
    if npm install --legacy-peer-deps; then
        print_success "Frontend dependencies installed"
    else
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
    cd ..
}

# Function to verify environment variables
verify_environment() {
    print_header "Verifying Environment Configuration"
    
    local backend_vars=(
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY" 
        "SUPABASE_SERVICE_ROLE_KEY"
        "DATABASE_URL"
        "SAM_API_KEY"
        "SECRET_KEY"
    )
    
    local missing_vars=()
    
    if [ -f "backend/.env" ]; then
        source backend/.env
        for var in "${backend_vars[@]}"; do
            if [ -z "${!var}" ]; then
                missing_vars+=("$var")
            else
                print_success "$var: configured ✓"
            fi
        done
    else
        print_error "backend/.env file not found"
        return 1
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_warning "Missing environment variables in backend/.env:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_warning "Please configure these variables for full functionality"
    fi
    
    # Check frontend environment
    if [ -f "frontend/.env.local" ]; then
        print_success "frontend/.env.local exists ✓"
    else
        print_warning "frontend/.env.local not found"
    fi
}

# Function to test local setup
test_local_setup() {
    print_header "Testing Local Setup"
    
    # Test backend
    print_status "Testing backend setup..."
    cd backend
    if python3 -c "
import sys
sys.path.append('src')
try:
    from main import app
    print('✓ Backend imports successful')
except Exception as e:
    print(f'✗ Backend import failed: {e}')
    sys.exit(1)
"; then
        print_success "Backend configuration valid"
    else
        print_error "Backend configuration has issues"
        cd ..
        return 1
    fi
    cd ..
    
    # Test frontend
    print_status "Testing frontend setup..."
    cd frontend
    if npm run build --silent; then
        print_success "Frontend builds successfully"
    else
        print_error "Frontend build failed"
        cd ..
        return 1
    fi
    cd ..
}

# Function to start local development
start_local_dev() {
    print_header "Starting Local Development Servers"
    
    print_status "Starting backend server on http://localhost:5000..."
    cd backend
    python3 src/main.py &
    BACKEND_PID=$!
    cd ..
    
    sleep 3
    
    print_status "Starting frontend server on http://localhost:5173..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    sleep 2
    
    print_success "Servers started!"
    print_status "Backend: http://localhost:5000"
    print_status "Frontend: http://localhost:5173"
    print_status "Health check: http://localhost:5000/api/health"
    
    echo
    print_warning "Press Ctrl+C to stop both servers"
    
    # Wait for user interrupt
    trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; print_status "Servers stopped"; exit 0' INT
    wait
}

# Function to show help
show_help() {
    echo "🚀 ODB Setup & Deployment Script"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  local    - Set up and start local development environment"
    echo "  verify   - Verify environment configuration and dependencies"
    echo "  help     - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 local    # Full local setup and start servers"
    echo "  $0 verify   # Just verify configuration"
    echo "  $0          # Same as 'local'"
    echo
}

# Main execution
main() {
    local command=${1:-local}
    
    case $command in
        "local")
            check_prerequisites
            setup_environment
            install_dependencies
            verify_environment
            test_local_setup
            start_local_dev
            ;;
        "verify")
            check_prerequisites
            verify_environment
            test_local_setup
            print_success "Verification complete!"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
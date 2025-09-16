#!/bin/bash

# DBX AI Aviation System - Local Development Setup Script
# This script sets up the complete local development environment

set -e  # Exit on any error

echo "🚀 Setting up DBX AI Aviation System for local development..."

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

# Check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data/{models,training_data,uploads,results,cache}
    mkdir -p logs
    mkdir -p docker/{postgres/init-scripts,pgadmin}
    
    print_success "Directories created"
}

# Copy environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.local .env
        print_success "Environment file created (.env)"
        print_warning "Please edit .env file to configure your settings (especially GEMINI_API_KEY)"
    else
        print_warning ".env file already exists, skipping..."
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Use docker-compose or docker compose based on availability
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    print_status "Stopping any existing services..."
    $DOCKER_COMPOSE -f docker-compose.local.yml down
    
    print_status "Building application image..."
    $DOCKER_COMPOSE -f docker-compose.local.yml build dbx-app
    
    print_status "Starting database and cache services..."
    $DOCKER_COMPOSE -f docker-compose.local.yml up -d dbx-postgres dbx-redis
    
    print_status "Waiting for database to be ready..."
    sleep 30
    
    print_status "Starting application..."
    $DOCKER_COMPOSE -f docker-compose.local.yml up -d dbx-app
    
    print_success "All services started successfully"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker exec dbx-postgres pg_isready -U postgres -d dbx_aviation &> /dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "PostgreSQL failed to start within 60 seconds"
        exit 1
    fi
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker exec dbx-redis redis-cli ping &> /dev/null; then
            print_success "Redis is ready"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Redis failed to start within 30 seconds"
        exit 1
    fi
    
    # Wait for application
    print_status "Waiting for application..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Application is ready"
            break
        fi
        sleep 3
        timeout=$((timeout-3))
    done
    
    if [ $timeout -le 0 ]; then
        print_warning "Application may not be fully ready yet, but continuing..."
    fi
}

# Display connection information
show_info() {
    echo ""
    echo "🎉 DBX AI Aviation System is now running locally!"
    echo ""
    echo "📊 Service URLs:"
    echo "   • Application API: http://localhost:8000"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo ""
    echo "🗄️  Database Connections:"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Database: dbx_aviation"
    echo "   • Username: postgres"
    echo "   • Password: password"
    echo ""
    echo "🔄 Cache:"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "🔧 Management Tools (optional):"
    echo "   • Start pgAdmin: docker-compose -f docker-compose.local.yml --profile tools up -d dbx-pgadmin"
    echo "   • pgAdmin URL: http://localhost:5050 (admin@dbx-ai.com / admin123)"
    echo "   • Start Redis Commander: docker-compose -f docker-compose.local.yml --profile tools up -d dbx-redis-commander"
    echo "   • Redis Commander URL: http://localhost:8081"
    echo ""
    echo "📝 Default Credentials:"
    echo "   • Admin User: admin@dbx-ai.com / admin123"
    echo "   • Sample Aircraft: TEST-001, TEST-002, TEST-003"
    echo ""
    echo "🛠️  Useful Commands:"
    echo "   • View logs: docker-compose -f docker-compose.local.yml logs -f"
    echo "   • Stop services: docker-compose -f docker-compose.local.yml down"
    echo "   • Restart app: docker-compose -f docker-compose.local.yml restart dbx-app"
    echo "   • Database shell: docker exec -it dbx-postgres psql -U postgres -d dbx_aviation"
    echo "   • Redis shell: docker exec -it dbx-redis redis-cli"
    echo ""
    echo "⚠️  Important Notes:"
    echo "   • Edit .env file to configure your Gemini API key"
    echo "   • This is a development setup - not for production use"
    echo "   • Default passwords should be changed for any non-local use"
    echo ""
}

# Main execution
main() {
    echo "🔧 DBX AI Aviation System - Local Development Setup"
    echo "=================================================="
    
    check_docker
    create_directories
    setup_environment
    start_services
    wait_for_services
    show_info
    
    print_success "Setup completed successfully! 🎉"
}

# Run main function
main "$@"
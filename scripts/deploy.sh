#!/bin/bash
set -e

echo "========================================="
echo " SCHOOL MANAGEMENT SYSTEM - QUICK DEPLOY"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose is installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_info "Creating .env file from .env.example..."

    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created from .env.example"
        print_info "Please edit .env file with your configuration"
        echo ""
        echo "Important settings to change:"
        echo "  - SECRET_KEY (generate a new one)"
        echo "  - DB_PASSWORD (set a strong password)"
        echo "  - DJANGO_SUPERUSER_PASSWORD (change default password)"
        echo ""
        read -p "Press Enter to continue after editing .env file..."
    else
        print_info "Creating default .env file..."
        cat > .env <<EOF
DEBUG=False
SECRET_KEY=django-insecure-$(openssl rand -base64 32)
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=school_management
DB_USER=postgres
DB_PASSWORD=postgres_$(openssl rand -base64 12)

REDIS_HOST=redis
REDIS_PORT=6379

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@school.com
DJANGO_SUPERUSER_PASSWORD=admin123

FLOWER_USER=admin
FLOWER_PASSWORD=flower_$(openssl rand -base64 12)
EOF
        print_success "Default .env file created"
        print_info "Please review and edit .env file before proceeding"
        read -p "Press Enter to continue..."
    fi
else
    print_success ".env file exists"
fi

echo ""
print_info "Starting deployment..."
echo ""

# Stop any existing containers
print_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true
print_success "Existing containers stopped"

# Build containers
print_info "Building Docker images (this may take a few minutes)..."
docker-compose build --no-cache
print_success "Docker images built"

# Start services
print_info "Starting services..."
docker-compose up -d
print_success "Services started"

echo ""
print_info "Waiting for services to be ready..."

# Wait for web service to be healthy
max_wait=120
wait_time=0

while [ $wait_time -lt $max_wait ]; do
    if docker-compose ps web | grep -q "healthy"; then
        print_success "Web service is healthy!"
        break
    fi

    echo -n "."
    sleep 5
    wait_time=$((wait_time + 5))
done

echo ""

if [ $wait_time -ge $max_wait ]; then
    print_error "Services did not become healthy in time"
    print_info "Check logs with: docker-compose logs"
    exit 1
fi

# Show service status
echo ""
print_info "Service Status:"
docker-compose ps

# Show logs
echo ""
print_info "Recent Logs:"
docker-compose logs --tail=50 web | grep -E "\[OK\]|\[FAIL\]|VERIFICATION|Celery|Gunicorn" || true

echo ""
echo "========================================="
print_success "DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Access your application:"
echo "  Web Application:    http://localhost:8000"
echo "  Admin Panel:        http://localhost:8000/admin"
echo "  Celery Monitoring:  http://localhost:5555"
echo ""
echo "Default Credentials:"
echo "  Admin User: admin / admin123 (CHANGE THIS!)"
echo "  Flower:     admin / (check .env for password)"
echo ""
echo "Useful Commands:"
echo "  View logs:          docker-compose logs -f"
echo "  Stop services:      docker-compose down"
echo "  Restart services:   docker-compose restart"
echo "  Run tests:          docker-compose exec web python manage.py test"
echo "  Django shell:       docker-compose exec web python manage.py shell"
echo ""
print_info "Read DOCKER_DEPLOYMENT.md for more information"
echo ""

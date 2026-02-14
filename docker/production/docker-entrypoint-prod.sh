#!/bin/bash
set -e

echo "========================================"
echo "  AURELIUS - School Management System"
echo "  'Shaping Tomorrow's Leaders Today'"
echo "========================================"
echo ""
echo "Starting production entrypoint script..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
python scripts/wait_for_db.py

# Run shared schema migrations first (django-tenants)
echo "Running shared schema migrations..."
python manage.py migrate_schemas --shared --noinput || echo "[WARN] Shared migrations had errors (may be expected on first run)"

# Run tenant schema migrations
echo "Running tenant schema migrations..."
python manage.py migrate_schemas --tenant --noinput || echo "[WARN] Tenant migrations had errors (may be expected if no tenants exist)"

# Create superuser if none exists (only for initial setup)
if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    echo "Creating superuser..."
    python scripts/create_superuser_if_none.py
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table if it doesn't exist
echo "Creating cache table..."
python manage.py createcachetable || true

# Compile messages for internationalization
if [ -d "locale" ]; then
    echo "Compiling translation messages..."
    python manage.py compilemessages || true
fi

# Create demo tenant if it doesn't exist
# Demo tenant: demo.aurelius.rhematek-solutions.com
echo "Checking for demo tenant..."
python manage.py shell -c "
from core.models import Domain
if not Domain.objects.filter(domain='demo.aurelius.rhematek-solutions.com').exists():
    print('Creating demo tenant...')
    import os
    os.system('python manage.py create_tenant --name \"Aurelius Demo School\" --domain demo.aurelius.rhematek-solutions.com --admin demo@rhematek-solutions.com --admin-password \"${DEMO_ADMIN_PASSWORD:-AureliusDemo2026!}\" --email demo@rhematek-solutions.com --phone \"+1-555-DEMO\" --address \"Demo Street\" --city \"Demo City\" --country \"USA\" --subscription-type yearly --max-students 1000')
else:
    print('Demo tenant already exists')
" || true

# Check for configuration issues
echo "Running system checks..."
python manage.py check --deploy || true

# Warm up cache (optional)
if [ "${WARM_CACHE:-false}" = "true" ]; then
    echo "Warming up cache..."
    python manage.py warm_cache || true
fi

echo ""
echo "========================================"
echo "  AURELIUS Production Ready!"
echo "========================================"
echo "Base Domain: aurelius.rhematek-solutions.com"
echo "Demo Tenant: demo.aurelius.rhematek-solutions.com"
echo "Health check: http://localhost:8000/health/"
echo "========================================"

# Execute the main command
exec "$@"

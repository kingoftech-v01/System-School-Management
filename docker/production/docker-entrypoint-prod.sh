#!/bin/bash
set -e

echo "Starting production entrypoint script..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
python wait_for_db.py

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if none exists (only for initial setup)
if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    echo "Creating superuser..."
    python create_superuser_if_none.py
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

# Check for configuration issues
echo "Running system checks..."
python manage.py check --deploy

# Warm up cache (optional)
if [ "${WARM_CACHE:-false}" = "true" ]; then
    echo "Warming up cache..."
    python manage.py warm_cache || true
fi

echo "Production environment ready!"
echo "----------------------------------------"
echo "Application starting with Gunicorn..."
echo "Health check: http://localhost:8000/health/"
echo "----------------------------------------"

# Execute the main command
exec "$@"

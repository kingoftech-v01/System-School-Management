#!/bin/bash
set -e

echo "Starting development entrypoint script..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
python wait_for_db.py

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if none exists
echo "Creating superuser if needed..."
python create_superuser_if_none.py

# Collect static files (optional in development, but useful)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Create cache table if it doesn't exist
echo "Creating cache table..."
python manage.py createcachetable || true

# Load initial data if fixtures exist
if [ -d "fixtures" ]; then
    echo "Loading fixtures..."
    python manage.py loaddata fixtures/*.json || true
fi

echo "Development environment ready!"
echo "----------------------------------------"
echo "Django Admin: http://localhost:8000/admin/"
echo "API Docs: http://localhost:8000/api/docs/"
echo "Flower (Celery Monitor): http://localhost:5555/"
echo "Debug Port: 5678"
echo "----------------------------------------"

# Execute the main command
exec "$@"

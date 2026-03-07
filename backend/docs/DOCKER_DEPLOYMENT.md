# Docker Deployment Guide
**Multi-Tenant School Management System - Automated Deployment**

---

## Quick Start (TL;DR)

```bash
# 1. Clone repository
git clone <repository-url>
cd System-School-Management

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Deploy everything automatically
docker-compose up -d

# 4. Access the application
# Web: http://localhost:8000
# Admin: http://localhost:8000/admin (admin/admin123)
# Flower: http://localhost:5555 (admin/admin)
```

---

## What Happens Automatically

When you run `docker-compose up`, the system **automatically executes**:

### ✅ Step 1: Database Setup
- Waits for PostgreSQL to be ready
- Checks database connection (up to 30 retries)

### ✅ Step 2: Cache Setup
- Waits for Redis to be ready
- Verifies Redis connection (up to 30 retries)

### ✅ Step 3: Database Migrations
- Runs shared schema migrations
- Runs tenant schema migrations
- Creates all database tables

### ✅ Step 4: Static Files
- Collects all static files (CSS, JS, images)
- Clears old static files
- Organizes files in staticfiles directory

### ✅ Step 5: Superuser Creation
- Creates admin user if none exists
- Username: admin (configurable)
- Email: admin@school.com (configurable)
- Password: admin123 (configurable - **CHANGE IN PRODUCTION!**)

### ✅ Step 6: Initial Data (Optional)
- Loads fixtures/initial_data.json if exists
- Skips if file not found

### ✅ Step 7: System Verification
- Runs comprehensive system check
- Verifies cache configuration
- Verifies Celery configuration
- Checks all 33 scheduled tasks
- Verifies static files
- Checks components

### ✅ Step 8: Cache Tables
- Creates database cache tables if needed
- Skips if using Redis (recommended)

### ✅ Step 9: Translations (Optional)
- Compiles translation messages
- Skips if no locale directory

### ✅ Step 10: Session Cleanup
- Clears expired sessions

### ✅ Step 11: Security Check
- Runs Django security checks
- Warns about potential issues

### ✅ Step 12: Start Services
- **Web**: Gunicorn server (4 workers)
- **Celery Worker**: Background task processor (4 workers)
- **Celery Beat**: Scheduled task scheduler (33 tasks)
- **Flower**: Celery monitoring dashboard
- **Nginx**: Reverse proxy (optional)

---

## Docker Services

### 1. PostgreSQL Database (`db`)
- **Image**: postgres:16-alpine
- **Port**: 5432
- **Volume**: postgres_data
- **Health Check**: Every 10s
- **Auto-restarts**: Yes

### 2. Redis Cache (`redis`)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis_data (persistent)
- **Max Memory**: 512MB
- **Health Check**: Every 10s
- **Auto-restarts**: Yes

### 3. Django Web (`web`)
- **Port**: 8000
- **Workers**: 4 (Gunicorn)
- **Threads**: 2 per worker
- **Timeout**: 120s
- **Health Check**: Every 30s (starts after 60s)
- **Volumes**: Code, static files, media
- **Auto-restarts**: Yes

### 4. Celery Worker (`celery`)
- **Concurrency**: 4 workers
- **Max Tasks**: 1000 per worker
- **Task Timeout**: 3600s (1 hour)
- **Soft Timeout**: 3000s (50 min)
- **Auto-restarts**: Yes

### 5. Celery Beat (`celery-beat`)
- **Scheduler**: Database-backed
- **Tasks**: 33 scheduled tasks
- **PID File**: /tmp/celerybeat.pid
- **Auto-restarts**: Yes

### 6. Flower Monitor (`flower`)
- **Port**: 5555
- **Auth**: Basic (admin/admin)
- **Features**: Real-time monitoring
- **Auto-restarts**: Yes

### 7. Nginx Proxy (`nginx`)
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Static Files**: Served directly
- **Media Files**: Served directly
- **SSL**: Ready (add certs to nginx/ssl/)
- **Auto-restarts**: Yes

---

## Environment Variables

Create a `.env` file with these settings:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here-change-me
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_NAME=school_management
DB_USER=postgres
DB_PASSWORD=secure_password_here
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_CONCURRENCY=4
CELERY_MAX_TASKS_PER_CHILD=1000
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3000

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120

# Superuser (First Run)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@school.com
DJANGO_SUPERUSER_PASSWORD=admin123

# Flower Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=admin
FLOWER_PORT=5555

# Logging
LOG_LEVEL=info
CELERY_LOG_LEVEL=info
```

---

## Docker Commands

### Start All Services
```bash
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Reset)
```bash
docker-compose down -v
```

### Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Run Django Management Commands
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Create app
docker-compose exec web python manage.py startapp myapp

# Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test

# Bash shell
docker-compose exec web bash
```

### Monitor Services
```bash
# Service status
docker-compose ps

# Resource usage
docker stats

# Flower monitoring
# Open http://localhost:5555 in browser
```

### Database Operations
```bash
# Backup database
docker-compose exec db pg_dump -U postgres school_management > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres school_management < backup.sql

# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d school_management
```

### Redis Operations
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check Redis info
docker-compose exec redis redis-cli info

# Monitor Redis commands
docker-compose exec redis redis-cli monitor
```

---

## Service Types

The entrypoint script supports multiple service types via `SERVICE_TYPE` environment variable:

### Available Service Types:

1. **web** (default) - Django Gunicorn server
2. **celery_worker** - Celery background worker
3. **celery_beat** - Celery task scheduler
4. **celery_flower** - Celery monitoring
5. **test** - Run test suite
6. **shell** - Django shell
7. **bash** - Bash shell

### Example: Run Tests
```yaml
test:
  build: .
  environment:
    - SERVICE_TYPE=test
  depends_on:
    - db
    - redis
```

```bash
docker-compose run --rm test
```

---

## Health Checks

### Web Service Health Check
- **URL**: http://localhost:8000/admin/
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 60 seconds (allows startup time)

### Database Health Check
- **Command**: `pg_isready -U postgres`
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Retries**: 5

### Redis Health Check
- **Command**: `redis-cli ping`
- **Interval**: 10 seconds
- **Timeout**: 3 seconds
- **Retries**: 5

---

## Production Deployment

### 1. Security Checklist

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Change all default passwords
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Enable HTTPS (add SSL certs)
- [ ] Change Flower authentication
- [ ] Set strong database password
- [ ] Set Redis password
- [ ] Review Django security settings

### 2. SSL/HTTPS Setup

Add SSL certificates to `nginx/ssl/`:
```
nginx/ssl/
├── cert.pem
└── key.pem
```

Update `nginx/nginx.conf` to use HTTPS.

### 3. Performance Tuning

```bash
# Increase workers for production
GUNICORN_WORKERS=8
GUNICORN_THREADS=4
CELERY_CONCURRENCY=8

# Database connections
DB_MAX_CONNECTIONS=100

# Redis memory
# Edit redis command in docker-compose.yml
--maxmemory 2gb
```

### 4. Monitoring

- **Web**: http://yourdomain.com
- **Admin**: http://yourdomain.com/admin
- **Flower**: http://yourdomain.com:5555
- **Logs**: `docker-compose logs -f`

### 5. Backups

Set up automated backups:

```bash
# Create backup script
cat > backup.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres school_management > backup_${DATE}.sql
docker-compose exec redis redis-cli BGSAVE
EOF

chmod +x backup.sh

# Add to cron (daily at 2 AM)
0 2 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check service status
docker-compose ps

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection manually
docker-compose exec db psql -U postgres -d school_management
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

### Celery Tasks Not Running

```bash
# Check Celery worker status
docker-compose logs celery

# Check Celery beat status
docker-compose logs celery-beat

# Check Flower
# Open http://localhost:5555

# Restart Celery services
docker-compose restart celery celery-beat
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix volume permissions
docker-compose exec web chown -R appuser:appuser /app
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery=4

# Scale web workers
docker-compose up -d --scale web=3
```

Add load balancer (nginx) configuration for multiple web instances.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to server
        run: |
          ssh user@server 'cd /app && git pull && docker-compose up -d --build'
```

---

## Support

### Logs Location
- **Application**: Docker container logs
- **Database**: Container logs
- **Nginx**: Container logs
- **Celery**: Container logs

### Useful Commands
```bash
# View all container IDs
docker-compose ps -q

# Restart specific service
docker-compose restart web

# Update images
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -a
```

---

**Generated**: January 5, 2026
**System**: Multi-Tenant School Management
**Docker Version**: 3.8
**Services**: 7 containers (db, redis, web, celery, celery-beat, flower, nginx)

---

# Docker Deployment Guide

This directory contains Docker configurations for the School Management System, supporting both development and production environments.

## Directory Structure

```
docker/
├── development/
│   ├── Dockerfile                    # Development Docker image
│   └── docker-entrypoint-dev.sh     # Development startup script
├── production/
│   ├── Dockerfile                    # Production Docker image
│   ├── docker-entrypoint-prod.sh    # Production startup script
│   ├── nginx.conf                    # Nginx reverse proxy configuration
│   └── ssl/                          # SSL certificates (create this)
└── README.md                         # This file
```

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Quick Start - Development

### 1. Clone the repository
```bash
git clone <repository-url>
cd System-School-Management
```

### 2. Create environment file
```bash
cp .env.example .env
# Edit .env with your development settings
```

### 3. Start development environment
```bash
docker-compose -f docker-compose-dev.yml up -d
```

### 4. Access the application
- Django Admin: http://localhost:8000/admin/
- API Documentation: http://localhost:8000/api/docs/
- Flower (Celery Monitor): http://localhost:5555/

### 5. Create superuser (first time only)
```bash
docker-compose -f docker-compose-dev.yml exec web python manage.py createsuperuser
```

### 6. View logs
```bash
docker-compose -f docker-compose-dev.yml logs -f web
```

### 7. Stop the environment
```bash
docker-compose -f docker-compose-dev.yml down
```

## Production Deployment

### 1. Prepare environment variables
```bash
cp .env.production.example .env.production
# IMPORTANT: Edit .env.production with secure production values
```

**Critical settings to update:**
- `SECRET_KEY` - Generate a strong 50+ character key
- `DEBUG=False`
- `ALLOWED_HOSTS` - Your domain name(s)
- `DB_PASSWORD` - Strong database password
- `REDIS_PASSWORD` - Strong Redis password
- `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD`
- `STRIPE_SECRET_KEY` & `STRIPE_PUBLISHABLE_KEY`
- `SENTRY_DSN` (for error tracking)

### 2. Setup SSL certificates

**Option A: Let's Encrypt (Recommended)**
```bash
# Create SSL directory
mkdir -p docker/production/ssl

# Install certbot
sudo apt-get update && sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/production/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/production/ssl/key.pem
```

**Option B: Self-signed (Testing only)**
```bash
mkdir -p docker/production/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/production/ssl/key.pem \
  -out docker/production/ssl/cert.pem
```

### 3. Build and start production services
```bash
# Load environment variables
export $(cat .env.production | xargs)

# Build images
docker-compose -f docker-compose-prod.yml build

# Start services
docker-compose -f docker-compose-prod.yml up -d
```

### 4. Run database migrations
```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py migrate
```

### 5. Create superuser (first deployment)
```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py createsuperuser
```

### 6. Collect static files
```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py collectstatic --noinput
```

### 7. Verify deployment
- HTTPS: https://your-domain.com/
- Health check: https://your-domain.com/health/
- Admin: https://your-domain.com/admin/

## Service Management

### View running containers
```bash
docker-compose -f docker-compose-prod.yml ps
```

### View logs
```bash
# All services
docker-compose -f docker-compose-prod.yml logs -f

# Specific service
docker-compose -f docker-compose-prod.yml logs -f web
docker-compose -f docker-compose-prod.yml logs -f celery
```

### Restart services
```bash
# Restart all
docker-compose -f docker-compose-prod.yml restart

# Restart specific service
docker-compose -f docker-compose-prod.yml restart web
```

### Stop services
```bash
docker-compose -f docker-compose-prod.yml down
```

### Stop and remove volumes (CAUTION: Deletes data)
```bash
docker-compose -f docker-compose-prod.yml down -v
```

## Database Backup & Restore

### Backup database
```bash
docker-compose -f docker-compose-prod.yml exec db pg_dump -U school_admin school_management > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore database
```bash
docker-compose -f docker-compose-prod.yml exec -T db psql -U school_admin school_management < backup_20240101_120000.sql
```

### Automated backups (cron job)
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/System-School-Management && docker-compose -f docker-compose-prod.yml exec db pg_dump -U school_admin school_management > backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

## Scaling Services

### Scale Celery workers
```bash
docker-compose -f docker-compose-prod.yml up -d --scale celery=4
```

### Scale web application
```bash
# Update docker-compose-prod.yml to add more web instances
# Then restart
docker-compose -f docker-compose-prod.yml up -d --scale web=3
```

## Monitoring

### Flower (Celery Monitoring)
Access Flower at: http://your-domain.com:5555/ (requires FLOWER_USER and FLOWER_PASSWORD)

### Container health
```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py check --deploy
```

### Resource usage
```bash
docker stats
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker-compose-prod.yml logs web

# Check container status
docker-compose -f docker-compose-prod.yml ps
```

### Database connection errors
```bash
# Verify database is running
docker-compose -f docker-compose-prod.yml exec db pg_isready

# Check environment variables
docker-compose -f docker-compose-prod.yml exec web env | grep DATABASE
```

### Permission errors
```bash
# Fix ownership
docker-compose -f docker-compose-prod.yml exec web chown -R appuser:appuser /app
```

### Clear cache
```bash
docker-compose -f docker-compose-prod.yml exec web python manage.py clear_cache
docker-compose -f docker-compose-prod.yml exec redis redis-cli FLUSHALL
```

### Rebuild images
```bash
docker-compose -f docker-compose-prod.yml build --no-cache
docker-compose -f docker-compose-prod.yml up -d
```

## Environment Variables Reference

### Essential Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (50+ chars) | `your-random-secret-key-here` |
| `DEBUG` | Debug mode (False in production) | `False` |
| `ALLOWED_HOSTS` | Comma-separated domains | `example.com,www.example.com` |
| `DB_PASSWORD` | PostgreSQL password | `secure_password_123` |
| `REDIS_PASSWORD` | Redis password | `redis_secure_456` |
| `EMAIL_HOST_USER` | SMTP username | `noreply@example.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `email_app_password` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_S3` | Enable AWS S3 storage | `False` |
| `SENTRY_DSN` | Sentry error tracking | (empty) |
| `CREATE_SUPERUSER` | Auto-create admin on first run | `false` |
| `WARM_CACHE` | Warm cache on startup | `false` |

## Security Best Practices

1. **Never commit `.env` or `.env.production` files**
   - Add to `.gitignore`
   - Store securely (e.g., password manager, secrets manager)

2. **Use strong passwords**
   - Database password: 20+ characters
   - Redis password: 20+ characters
   - Secret key: 50+ characters

3. **Enable SSL/TLS**
   - Use Let's Encrypt certificates
   - Set `SECURE_SSL_REDIRECT=True`

4. **Regular updates**
   ```bash
   # Update Docker images
   docker-compose -f docker-compose-prod.yml pull
   docker-compose -f docker-compose-prod.yml up -d
   ```

5. **Monitor logs**
   - Setup centralized logging (ELK, Datadog, etc.)
   - Configure Sentry for error tracking

6. **Firewall configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

## Performance Optimization

### Nginx caching
Edit `docker/production/nginx.conf` to add caching rules.

### Database connection pooling
Already configured in Django settings with `CONN_MAX_AGE`.

### Redis caching
Redis is configured as cache backend. Monitor with:
```bash
docker-compose -f docker-compose-prod.yml exec redis redis-cli INFO stats
```

## Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- Docker Documentation: https://docs.docker.com/
- Project Issues: [GitHub Issues Link]

## License

[Your License Here]

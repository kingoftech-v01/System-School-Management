# Production Deployment Guide

This guide provides step-by-step instructions for deploying the School Management System to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Server Setup](#server-setup)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Nginx Configuration](#nginx-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup Strategy](#backup-strategy)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

**Minimum (up to 5 schools, 500 users)**
- 2 CPU cores
- 4 GB RAM
- 50 GB SSD storage
- 100 Mbps network

**Recommended (up to 20 schools, 2000 users)**
- 4 CPU cores
- 8 GB RAM
- 200 GB SSD storage
- 1 Gbps network

**High Traffic (50+ schools, 10000+ users)**
- 8+ CPU cores
- 16+ GB RAM
- 500+ GB SSD storage
- 1+ Gbps network
- Load balancer

### Software Requirements

- Ubuntu 22.04 LTS or similar Linux distribution
- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 14+ (if not using Docker)
- Redis 7+ (if not using Docker)
- nginx 1.18+
- Python 3.11+ (if not using Docker)
- Git

### Domain & DNS

- Registered domain name
- DNS A records pointing to your server IP
- Wildcard DNS support (for multi-tenant subdomains)

Example DNS setup:
```
example.com           A    203.0.113.10
*.example.com         A    203.0.113.10
school1.example.com   A    203.0.113.10
school2.example.com   A    203.0.113.10
```

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl git vim ufw fail2ban

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Configure fail2ban for SSH protection
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Create Application User

```bash
# Create a dedicated user for the application
sudo adduser --system --group --home /opt/school_system school_app

# Add your user to the school_app group
sudo usermod -aG school_app $USER
```

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker school_app
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Docker Deployment

### 1. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/school_system
sudo chown school_app:school_app /opt/school_system

# Clone repository
cd /opt/school_system
git clone <repository-url> .
```

### 2. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit environment configuration
nano .env
```

**Critical Production Settings:**

```env
# Django Settings
DEBUG=False
SECRET_KEY=<generate-50+-char-random-string>
ALLOWED_HOSTS=example.com,*.example.com,203.0.113.10

# Database
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=school_production_db
DATABASE_USER=school_db_user
DATABASE_PASSWORD=<strong-password-here>
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-redis-password>

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Email (Production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=<app-specific-password>
DEFAULT_FROM_EMAIL=noreply@example.com

# File Storage (S3)
USE_S3=True
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_STORAGE_BUCKET_NAME=school-management-prod
AWS_S3_REGION_NAME=us-east-1

# Monitoring
SENTRY_DSN=<your-sentry-dsn>

# Payment
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### 3. Generate Secret Key

```bash
# Generate a secure SECRET_KEY
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Build and Start Services

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps
```

### 5. Initialize Database

```bash
# Run migrations for shared schema
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate_schemas --shared

# Run migrations for all tenant schemas
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate_schemas

# Create superuser (public schema)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 6. Create First Tenant

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py create_tenant \
  --name "Demo School" \
  --domain demo.example.com \
  --admin admin@demo.example.com \
  --admin-password "SecurePassword123!" \
  --email info@demo.example.com \
  --phone "+1-555-0100" \
  --address "123 School Street" \
  --city "New York" \
  --country "USA" \
  --subscription-type yearly \
  --max-students 1000
```

## Manual Deployment

For deployment without Docker:

### 1. Install System Dependencies

```bash
# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
  postgresql postgresql-contrib libpq-dev \
  redis-server nginx \
  build-essential libssl-dev libffi-dev

# Install Node.js (for frontend assets if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Setup PostgreSQL

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE school_production_db;
CREATE USER school_db_user WITH PASSWORD 'strong_password_here';
ALTER ROLE school_db_user SET client_encoding TO 'utf8';
ALTER ROLE school_db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE school_db_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE school_production_db TO school_db_user;
\q

# Configure PostgreSQL for remote connections (if needed)
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: local   all   school_db_user   md5

sudo systemctl restart postgresql
```

### 3. Setup Redis

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Set the following:
# bind 127.0.0.1
# requirepass strong_redis_password
# maxmemory 256mb
# maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4. Setup Python Application

```bash
# Clone repository
cd /opt/school_system
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.example .env
nano .env  # Edit with production settings

# Run migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 5. Setup Gunicorn

Create systemd service file:

```bash
sudo nano /etc/systemd/system/school-management.service
```

```ini
[Unit]
Description=School Management System Gunicorn
After=network.target

[Service]
Type=notify
User=school_app
Group=school_app
WorkingDirectory=/opt/school_system
Environment="PATH=/opt/school_system/venv/bin"
EnvironmentFile=/opt/school_system/.env
ExecStart=/opt/school_system/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    --bind unix:/opt/school_system/school.sock \
    --access-logfile /var/log/school_system/access.log \
    --error-logfile /var/log/school_system/error.log \
    --log-level info \
    School_System.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start Gunicorn:

```bash
# Create log directory
sudo mkdir -p /var/log/school_system
sudo chown school_app:school_app /var/log/school_system

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable school-management
sudo systemctl start school-management
sudo systemctl status school-management
```

### 6. Setup Celery Workers

Create Celery systemd service:

```bash
sudo nano /etc/systemd/system/celery.service
```

```ini
[Unit]
Description=Celery Service
After=network.target redis.target

[Service]
Type=forking
User=school_app
Group=school_app
WorkingDirectory=/opt/school_system
Environment="PATH=/opt/school_system/venv/bin"
EnvironmentFile=/opt/school_system/.env
ExecStart=/opt/school_system/venv/bin/celery -A School_System worker \
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid

[Install]
WantedBy=multi-user.target
```

Create Celery Beat service:

```bash
sudo nano /etc/systemd/system/celery-beat.service
```

```ini
[Unit]
Description=Celery Beat Service
After=network.target redis.target

[Service]
Type=simple
User=school_app
Group=school_app
WorkingDirectory=/opt/school_system
Environment="PATH=/opt/school_system/venv/bin"
EnvironmentFile=/opt/school_system/.env
ExecStart=/opt/school_system/venv/bin/celery -A School_System beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid

[Install]
WantedBy=multi-user.target
```

Start Celery:

```bash
# Create directories
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown school_app:school_app /var/log/celery /var/run/celery

# Start services
sudo systemctl daemon-reload
sudo systemctl enable celery celery-beat
sudo systemctl start celery celery-beat
sudo systemctl status celery celery-beat
```

## SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com -d *.example.com

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is set up via cron/systemd timer automatically
```

### Manual SSL Certificate

If you have SSL certificates from a provider:

```bash
# Copy certificates
sudo mkdir -p /etc/nginx/ssl
sudo cp your-domain.crt /etc/nginx/ssl/
sudo cp your-domain.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/your-domain.key
```

## Nginx Configuration

### Main Configuration

```bash
sudo nano /etc/nginx/sites-available/school-management
```

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

# Upstream Django application
upstream django_app {
    server unix:/opt/school_system/school.sock fail_timeout=0;
    # Or for Docker:
    # server web:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name example.com *.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com *.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Logging
    access_log /var/log/nginx/school-access.log;
    error_log /var/log/nginx/school-error.log;

    # Client upload size
    client_max_body_size 100M;
    client_body_buffer_size 1M;

    # Timeouts
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # Static files
    location /static/ {
        alias /opt/school_system/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/school_system/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Login endpoint with rate limiting
    location /accounts/login/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # All other requests
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

Enable site and restart nginx:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/school-management /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Monitoring & Logging

### Application Monitoring with Sentry

1. Sign up for Sentry at https://sentry.io
2. Create a new project
3. Add DSN to `.env`:
   ```env
   SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
   ```

### Log Rotation

```bash
sudo nano /etc/logrotate.d/school-management
```

```
/var/log/school_system/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload school-management > /dev/null 2>&1 || true
    endscript
}

/var/log/celery/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload celery > /dev/null 2>&1 || true
    endscript
}
```

### System Monitoring

Install monitoring tools:

```bash
# Install htop and nethogs
sudo apt install -y htop nethogs iotop

# Optional: Install Prometheus and Grafana for advanced monitoring
```

## Backup Strategy

### Automated Database Backups

Create backup script:

```bash
sudo nano /usr/local/bin/backup-school-db.sh
```

```bash
#!/bin/bash
# School Management System Database Backup Script

BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="school_production_db"
DB_USER="school_db_user"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup all schemas
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/full_backup_$DATE.sql.gz

# Backup each tenant schema separately
for schema in $(psql -U $DB_USER -d $DB_NAME -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'school_%'"); do
    pg_dump -U $DB_USER -h localhost -n $schema $DB_NAME | gzip > $BACKUP_DIR/tenant_${schema}_$DATE.sql.gz
done

# Remove old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/database/

echo "Backup completed: $DATE"
```

Make executable and schedule:

```bash
sudo chmod +x /usr/local/bin/backup-school-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-school-db.sh >> /var/log/backup.log 2>&1
```

### Media Files Backup

```bash
# Sync media to S3 daily
0 3 * * * aws s3 sync /opt/school_system/media s3://your-bucket/media/ --delete
```

## Maintenance

### Update Application

```bash
# Pull latest code
cd /opt/school_system
git pull origin main

# For Docker deployment
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# For manual deployment
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate_schemas
python manage.py collectstatic --noinput
sudo systemctl restart school-management celery celery-beat
```

### Database Maintenance

```bash
# Vacuum database
sudo -u postgres psql -d school_production_db -c "VACUUM ANALYZE;"

# Check database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('school_production_db'));"
```

### Clear Cache

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Or for manual deployment
redis-cli -a your_redis_password FLUSHALL
```

## Troubleshooting

### Check Service Status

```bash
# Check all services
sudo systemctl status school-management
sudo systemctl status celery
sudo systemctl status celery-beat
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### View Logs

```bash
# Application logs
tail -f /var/log/school_system/error.log

# Nginx logs
tail -f /var/log/nginx/school-error.log

# Celery logs
tail -f /var/log/celery/worker.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Common Issues

#### 502 Bad Gateway
- Check if Django/Gunicorn is running: `sudo systemctl status school-management`
- Check socket file permissions
- Review Gunicorn error logs

#### Database Connection Errors
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Test connection: `psql -U school_db_user -d school_production_db -h localhost`

#### Static Files Not Loading
- Run `collectstatic` again
- Check nginx static file configuration
- Verify file permissions

#### SSL Certificate Issues
- Renew certificate: `sudo certbot renew`
- Check certificate validity: `sudo certbot certificates`

### Performance Optimization

```bash
# Check slow queries
sudo -u postgres psql -d school_production_db
SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# Monitor connections
SELECT count(*) FROM pg_stat_activity;
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Configure firewall (UFW)
- [ ] Enable fail2ban
- [ ] Configure SSL/TLS
- [ ] Enable HSTS
- [ ] Configure secure headers
- [ ] Disable DEBUG mode
- [ ] Use strong SECRET_KEY
- [ ] Configure rate limiting
- [ ] Regular security updates
- [ ] Monitor error logs
- [ ] Set up automated backups
- [ ] Configure Sentry monitoring
- [ ] Restrict database access
- [ ] Use environment variables for secrets
- [ ] Enable audit logging

## Post-Deployment

1. Test all critical functionality
2. Verify email sending works
3. Test payment processing
4. Check SSL certificate
5. Monitor error logs for 24-48 hours
6. Set up monitoring alerts
7. Document any custom configurations

---

**For support:** support@rhematek-solutions.com
**Last Updated:** December 24, 2025

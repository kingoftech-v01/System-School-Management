# Deployment Guide - School Management System (SMS)

This guide covers deploying the SMS application with Docker on a production server.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Domain pointed to server (e.g., `sms.yourdomain.com`)
- Nginx installed on host for SSL termination
- Certbot for SSL certificates

## Quick Deploy

```bash
# 1. Clone the repository
git clone <repo-url>
cd System-School-Management

# 2. Create environment file
cp .env.example .env
# Edit .env with your settings (see Environment Variables below)

# 3. Build and start containers
docker compose build
docker compose up -d

# 4. Check container status
docker ps
```

The entrypoint script automatically handles:
- Waiting for database to be ready
- Running migrations
- Collecting static files

## Environment Variables

Create a `.env` file with these required variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=sms.yourdomain.com,localhost

# Database
POSTGRES_DB=sms_production
POSTGRES_USER=sms_user
POSTGRES_PASSWORD=secure-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis-password-here

# Email (optional - defaults to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# For SMTP:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email
# EMAIL_HOST_PASSWORD=your-app-password

# Security
CSRF_TRUSTED_ORIGINS=https://sms.yourdomain.com
SECURE_SSL_REDIRECT=True
```

## Nginx Configuration (Host)

Create `/etc/nginx/sites-available/sms.yourdomain.com`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name sms.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sms.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/sms.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sms.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    client_max_body_size 100M;

    # Proxy to Docker container
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
    }
}
```

Enable the site and get SSL certificate:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sms.yourdomain.com /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Get SSL certificate
sudo certbot certonly --webroot -w /var/www/html -d sms.yourdomain.com

# Reload nginx
sudo systemctl reload nginx
```

## Docker Container Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| web     | 8000          | -             |
| nginx   | 80            | 8081          |
| db      | 5432          | -             |
| redis   | 6379          | -             |

## Common Commands

```bash
# View logs
docker compose logs -f web

# Restart containers
docker compose restart

# Rebuild after code changes
docker compose build web
docker compose up -d web

# Run Django management commands
docker compose exec web python manage.py <command>

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access Django shell
docker compose exec web python manage.py shell

# Database backup
docker compose exec db pg_dump -U sms_user sms_production > backup.sql
```

## Multi-Tenant Setup

After deployment, create tenants:

```bash
# Create public tenant (required first)
docker compose exec web python manage.py create_tenant --schema=public --name="Public" --domain=sms.yourdomain.com

# Create school tenant
docker compose exec web python manage.py create_tenant --schema=school1 --name="School Name" --domain=school1.sms.yourdomain.com
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs web

# Check if ports are in use
sudo lsof -i :8081
```

### Database connection errors
```bash
# Verify database is running
docker compose ps db

# Check database logs
docker compose logs db
```

### Static files not loading
```bash
# Manually collect static files
docker compose exec web python manage.py collectstatic --noinput
```

### CSRF errors
Ensure `CSRF_TRUSTED_ORIGINS` in `.env` includes your domain with `https://` prefix.

## Updating

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose build
docker compose up -d

# Run new migrations (if any)
docker compose exec web python manage.py migrate
```

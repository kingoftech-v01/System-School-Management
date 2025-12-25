# School Management System

A comprehensive, multi-tenant school management system built with Django, PostgreSQL, Redis, and Docker. This system enables multiple schools to manage students, staff, courses, attendance, payments, results, and more under a single platform with complete data isolation.

[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Latest-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)](LICENSE)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Applications](#applications)
- [User Roles & Permissions](#user-roles--permissions)
- [Installation](#installation)
- [Configuration](#configuration)
- [Management Commands](#management-commands)
- [API Documentation](#api-documentation)
- [Security Features](#security-features)
- [Deployment](#deployment)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

### Multi-Tenancy
- **Complete data isolation** using django-tenants with PostgreSQL schemas
- Each school has its own database schema
- Shared infrastructure with tenant-specific data
- Easy onboarding of new schools with single command
- License-based subscription management (monthly/yearly)

### Core Functionality
- User management for Students, Parents, Professors, and Direction/Admin
- Course and program (filiere) management
- Attendance tracking with automated parent notifications
- Grade and result management with GPA/CGPA calculation
- Payment processing and invoice generation
- Real-time search across all student records
- News and events publishing
- Academic year and semester management
- File uploads for course materials

### Security
- Two-Factor Authentication (2FA) for all staff using django-allauth
- Argon2 password hashing
- Role-based access control (RBAC)
- HTTPS enforcement in production
- Content Security Policy (CSP)
- Session security with secure cookies
- Rate limiting and login attempt throttling
- Audit logging for sensitive operations
- CSRF protection
- XSS protection

### Performance
- Redis caching for frequently accessed data
- Celery for background tasks (email sending, report generation)
- Database query optimization
- Static file compression with WhiteNoise
- Pagination on all list views
- Asynchronous task processing

### Additional Features
- Multi-language support (i18n) - 9 languages
- PDF report card generation
- Email notifications (attendance, payments, grades)
- Responsive UI based on W3 CRM design
- REST API with JWT authentication
- Import/Export functionality for admin
- File storage (local or S3-compatible)
- Comprehensive audit logs

## Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "System School Management"
   ```

2. **Copy environment configuration**
   ```bash
   cp .env.example .env
   ```

3. **Update `.env` file with your settings**
   - Set a strong `SECRET_KEY` (minimum 50 characters)
   - Configure database credentials
   - Set email configuration for notifications
   - Update Redis password

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   docker-compose exec web python manage.py migrate_schemas --shared
   docker-compose exec web python manage.py migrate_schemas
   ```

6. **Create your first school tenant**
   ```bash
   docker-compose exec web python manage.py create_tenant \
     --name "St. Mary High School" \
     --domain stmary.localhost \
     --admin admin@stmary.edu \
     --email info@stmary.edu \
     --phone "+1-555-0100" \
     --address "123 School Street" \
     --city "New York" \
     --country "USA"
   ```

7. **Access the application**
   - Main application: http://stmary.localhost:8000
   - Admin panel: http://stmary.localhost:8000/admin

8. **(Optional) Create demo data**
   ```bash
   docker-compose exec web python manage.py create_demo_data \
     --tenant "St. Mary High School" \
     --professors 5 \
     --students 10 \
     --parents 5
   ```

## Architecture Overview

### Multi-Tenancy Model

This system uses **django-tenants** to implement multi-tenancy at the database schema level:

```
PostgreSQL Database
├── public schema (shared)
│   ├── School (tenant) table
│   ├── Domain mapping table
│   └── Shared configuration
├── school_stmary schema (tenant 1)
│   ├── Users
│   ├── Students
│   ├── Courses
│   ├── Attendance
│   └── ... (all tenant-specific data)
└── school_riverside schema (tenant 2)
    ├── Users
    ├── Students
    └── ... (isolated data)
```

**Benefits:**
- Complete data isolation between schools
- No risk of cross-tenant data leakage
- Efficient multi-tenant queries
- Easy backup/restore per school
- Scalable to hundreds of tenants

### Technology Stack

```
┌─────────────────────────────────────────┐
│           Frontend (Templates)           │
│    Bootstrap 5 + W3 CRM Design          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│              nginx Proxy                 │
│  SSL Termination + Static Files         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Django Application              │
│  Gunicorn + Django 5.1.4 + DRF          │
└─────────────────────────────────────────┘
         ↓                    ↓
┌──────────────────┐  ┌─────────────────┐
│   PostgreSQL     │  │   Redis Cache   │
│  (Tenant DBs)    │  │  + Celery Queue │
└──────────────────┘  └─────────────────┘
         ↓
┌──────────────────┐
│  Celery Workers  │
│  Background Tasks │
└──────────────────┘
```

### Request Flow

1. Client requests `http://stmary.example.com`
2. nginx receives request and forwards to Django
3. Django middleware identifies tenant by domain
4. Switches to tenant's PostgreSQL schema
5. Processes request with tenant-specific data
6. Returns response

## Applications

The system consists of 10 core Django applications:

### 1. **core** - Core Functionality
- Tenant (School) model and domain routing
- Session (Academic Year) management
- Semester management
- News and events publishing
- Activity logging
- Shared utilities and helpers

### 2. **accounts** - User Management
- Custom User model with multiple roles
- Student profiles with program/level
- Parent profiles linked to students
- Department Head (Direction) management
- User authentication and authorization
- Profile picture management
- User search functionality

### 3. **authentication** - Advanced Authentication
- Two-Factor Authentication (2FA)
- OAuth social login (Google, GitHub, Facebook, LinkedIn)
- Password reset and email verification
- Session management
- Login attempt tracking and throttling
- Security middleware

### 4. **course** - Academic Courses
- Program (Filiere) management
- Course creation and management
- Course allocation to professors
- File uploads (PDFs, documents)
- Video uploads for courses
- Course offering by department heads
- Elective course support

### 5. **attendance** - Attendance Tracking
- Daily attendance recording by professors
- Subject-specific attendance
- Student attendance reports
- Automatic email notifications to parents
- Attendance statistics and analytics
- Export attendance data

### 6. **result** - Grades & Results
- Grade recording (A+, A, A-, B+, etc.)
- GPA and CGPA calculation
- Semester-wise results
- PDF report card generation
- Grade point mapping
- Pass/Fail determination
- Academic transcript generation

### 7. **payments** - Fee Management
- Invoice creation and management
- Payment tracking
- Payment completion status
- Invoice code generation
- Payment history
- Automated payment reminders
- Integration with payment gateways (Stripe)

### 8. **quiz** - Assessments & Quizzes
- Online quiz creation
- Question bank management
- Student quiz attempts
- Automatic grading
- Quiz analytics
- Time-limited assessments

### 9. **search** - Global Search
- Search students by name, email, ID
- Search parents and their children
- Search courses and programs
- Full academic record retrieval
- Direction-only access
- Advanced filtering

### 10. **dailystat** - Analytics & Statistics
- Student enrollment statistics
- Attendance trends
- Performance analytics
- Gender distribution reports
- Program-wise statistics
- Payment collection reports
- Custom date range reports

## User Roles & Permissions

### RBAC Matrix

| Feature | Student | Parent | Professor | Direction | Admin |
|---------|---------|--------|-----------|-----------|-------|
| View own profile | ✓ | ✓ | ✓ | ✓ | ✓ |
| View own courses | ✓ | - | ✓ | ✓ | ✓ |
| View own grades | ✓ | ✓* | - | ✓ | ✓ |
| View own attendance | ✓ | ✓* | - | ✓ | ✓ |
| Record attendance | - | - | ✓ | ✓ | ✓ |
| Record grades | - | - | ✓ | ✓ | ✓ |
| Create courses | - | - | - | ✓ | ✓ |
| Manage programs | - | - | - | ✓ | ✓ |
| View payments | ✓ | ✓* | - | ✓ | ✓ |
| Create invoices | - | - | - | ✓ | ✓ |
| Global search | - | - | - | ✓ | ✓ |
| Create users | - | - | - | ✓ | ✓ |
| Manage sessions | - | - | - | ✓ | ✓ |
| View analytics | - | - | ✓** | ✓ | ✓ |
| System settings | - | - | - | - | ✓ |
| Create tenants | - | - | - | - | ✓ |

*Parents can only view their linked student's data
**Professors can only view analytics for their courses

### Role Descriptions

#### Student
- View their own courses, grades, and attendance
- Download report cards
- Access course materials
- View payment invoices
- Update their profile

#### Parent
- View linked student's complete academic record
- Receive email notifications for attendance and grades
- View payment invoices for their child
- Communicate with professors and direction

#### Professor (Lecturer)
- Create and manage courses
- Record attendance for their classes
- Record grades for students in their courses
- Upload course materials and videos
- View course-specific analytics
- Manage course allocations

#### Direction Member (Department Head)
- All professor permissions
- Create and manage programs (filieres)
- Create and manage users (students, parents, professors)
- View all students and academic records
- Global search across all data
- Manage payments and invoices
- Create sessions and semesters
- View comprehensive analytics
- Offer courses for semesters

#### System Administrator (Superuser)
- All permissions across all tenants
- Create new school tenants
- Manage license and subscriptions
- Configure system-wide settings
- Access all tenant data (for support)
- Manage security settings

## Installation

### Development Setup (Without Docker)

1. **Install Python 3.11+**
   ```bash
   python --version  # Ensure 3.11+
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install PostgreSQL and Redis**
   - PostgreSQL 14+
   - Redis 7+

5. **Create database**
   ```sql
   CREATE DATABASE school_db;
   CREATE USER school_user WITH PASSWORD 'school_pass_2024';
   GRANT ALL PRIVILEGES ON DATABASE school_db TO school_user;
   ```

6. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

7. **Run migrations**
   ```bash
   python manage.py migrate_schemas --shared
   python manage.py migrate_schemas
   ```

8. **Create superuser (public schema)**
   ```bash
   python manage.py createsuperuser
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Production Setup (With Docker)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment instructions.

## Configuration

### Environment Variables

Key environment variables in `.env`:

#### Django Settings
```env
DJANGO_SETTINGS_MODULE=School_System.settings
SECRET_KEY=your-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
```

#### Database
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=school_db
DATABASE_USER=school_user
DATABASE_PASSWORD=strong_password_here
DATABASE_HOST=db
DATABASE_PORT=5432
```

#### Redis & Celery
```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password
CELERY_BROKER_URL=redis://:redis_secure_password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:redis_secure_password@redis:6379/0
```

#### Security (Production)
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

#### Email
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@schoolsystem.com
```

#### File Storage (Optional S3)
```env
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=school-management
AWS_S3_REGION_NAME=us-east-1
```

#### Payment Gateway (Stripe)
```env
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

#### Monitoring (Sentry)
```env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

See `.env.example` for complete configuration options.

## Management Commands

### Create Tenant
```bash
python manage.py create_tenant \
  --name "School Name" \
  --domain school.example.com \
  --admin admin@school.com \
  --admin-password "SecurePassword123!" \
  --email info@school.com \
  --phone "+1-555-0100" \
  --address "123 Main St" \
  --city "Boston" \
  --country "USA" \
  --subscription-type yearly \
  --max-students 1000
```

### Create Demo Data
```bash
python manage.py create_demo_data \
  --tenant "School Name" \
  --professors 10 \
  --students 50 \
  --parents 25 \
  --direction-members 5
```

### Setup 2FA
```bash
# Enable 2FA for all staff
python manage.py setup_2fa --role staff

# Enable for specific tenant
python manage.py setup_2fa \
  --tenant "School Name" \
  --role professors \
  --send-email

# Disable 2FA
python manage.py setup_2fa --disable --role all
```

### Standard Django Commands
```bash
# Run migrations for all tenants
python manage.py migrate_schemas

# Run migrations for shared apps only
python manage.py migrate_schemas --shared

# Create superuser (public schema)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run tests
python manage.py test

# Create translations
python manage.py makemessages -a
python manage.py compilemessages
```

## API Documentation

### Authentication

All API endpoints require authentication using JWT tokens.

#### Obtain Token
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Using Token
```bash
GET /api/students/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Key Endpoints

See [API.md](API.md) for complete API documentation.

#### Students
- `GET /api/students/` - List students
- `GET /api/students/{id}/` - Student detail
- `POST /api/students/` - Create student
- `PUT /api/students/{id}/` - Update student
- `DELETE /api/students/{id}/` - Delete student

#### Courses
- `GET /api/courses/` - List courses
- `GET /api/courses/{slug}/` - Course detail
- `POST /api/courses/` - Create course

#### Attendance
- `GET /api/attendance/` - List attendance records
- `POST /api/attendance/` - Record attendance

#### Results
- `GET /api/results/` - List results
- `GET /api/results/{student_id}/` - Student results
- `POST /api/results/` - Record grades

### Rate Limiting

API endpoints are rate-limited:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Admin users: No limit

## Security Features

### Authentication & Authorization
- Django-allauth for authentication
- Two-Factor Authentication (2FA) mandatory for staff
- OAuth social login (Google, GitHub, Facebook, LinkedIn)
- Argon2 password hashing
- Password strength validation
- Session timeout after 14 days

### Protection Mechanisms
- CSRF protection enabled
- XSS protection with auto-escaping
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- HTTP Strict Transport Security (HSTS)
- SQL injection protection (ORM)
- Rate limiting on all endpoints
- Login attempt throttling (django-axes)

### Data Security
- Tenant data isolation at schema level
- Encrypted database connections
- Secure password storage (Argon2)
- Sensitive data never logged
- Audit logs for critical operations
- Backup encryption

### Network Security
- HTTPS enforced in production
- Secure cookies (httpOnly, secure, sameSite)
- CORS configuration
- Database not exposed to public
- Redis authentication

See [SECURITY.md](SECURITY.md) for comprehensive security documentation.

## Deployment

### Production Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY` (50+ characters)
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS and SSL redirects
- [ ] Set secure cookie flags
- [ ] Configure email backend (SMTP)
- [ ] Set up PostgreSQL with backups
- [ ] Configure Redis with password
- [ ] Set up Celery workers
- [ ] Configure file storage (S3 or CDN)
- [ ] Set up monitoring (Sentry)
- [ ] Configure logging
- [ ] Run security checks
- [ ] Set up automated backups
- [ ] Configure firewall rules
- [ ] Set up SSL certificates
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Run migrations
- [ ] Collect static files
- [ ] Test all critical flows

### Docker Production Deployment

```bash
# Use production Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate_schemas

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### SSL Certificate Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Run all checks
black . && isort . && flake8
```

### Security Scanning

```bash
# Check for security vulnerabilities
bandit -r .

# Check dependencies
safety check

# Django security check
python manage.py check --deploy
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Development Workflow

1. Create feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes and test
   ```bash
   python manage.py test
   black .
   isort .
   ```

3. Commit changes
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. Push and create PR
   ```bash
   git push origin feature/my-feature
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Troubleshooting

### Common Issues

#### Docker containers won't start
```bash
# Check logs
docker-compose logs web
docker-compose logs db

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Database connection errors
```bash
# Verify PostgreSQL is running
docker-compose ps

# Check database settings in .env
# Ensure DATABASE_HOST matches service name in docker-compose.yml
```

#### Migrations fail
```bash
# Run shared migrations first
python manage.py migrate_schemas --shared

# Then run tenant migrations
python manage.py migrate_schemas

# Check for migration conflicts
python manage.py showmigrations
```

#### Static files not loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify STATIC_ROOT in settings
# Check nginx configuration
```

#### Email not sending
```bash
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])

# Check EMAIL_BACKEND in .env
# Verify SMTP credentials
```

#### Redis connection failed
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Verify REDIS_HOST and REDIS_PASSWORD in .env
```

#### 2FA not working
```bash
# Ensure django-allauth MFA is configured
# Check ALLAUTH_2FA_FORCE_2FA setting
# Verify user email is verified
```

### Debug Mode

Enable debug mode for development:

```env
DEBUG=True
```

View detailed error pages and SQL queries.

**Never enable DEBUG in production!**

### Logging

Logs are located at:
- Application logs: `/var/log/django/`
- nginx logs: `/var/log/nginx/`
- PostgreSQL logs: `/var/log/postgresql/`

View logs:
```bash
# Django logs
docker-compose logs -f web

# nginx logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f db
```

## Performance Optimization

### Database
- Use database indexes on frequently queried fields
- Enable connection pooling
- Use select_related() and prefetch_related()
- Regular VACUUM and ANALYZE

### Caching
- Redis caching for frequently accessed data
- Template fragment caching
- Database query caching
- Static file caching with far-future expires

### Media Files
- Use CDN for media files
- Optimize images before upload
- Lazy loading for images
- Use S3 or compatible object storage

## Backup Strategy

### Database Backups
```bash
# Backup all schemas
docker-compose exec db pg_dump -U school_user school_db > backup.sql

# Backup specific tenant
docker-compose exec db pg_dump -U school_user -n school_stmary school_db > tenant_backup.sql

# Automated daily backups (cron)
0 2 * * * /usr/local/bin/backup_db.sh
```

### Media Files Backup
```bash
# Backup media directory
tar -czf media_backup.tar.gz media/

# Sync to S3
aws s3 sync media/ s3://bucket-name/media/ --delete
```

### Restore
```bash
# Restore database
docker-compose exec -T db psql -U school_user school_db < backup.sql

# Restore media
tar -xzf media_backup.tar.gz
```

## Monitoring

### Application Monitoring
- Sentry for error tracking
- Custom logging for critical operations
- Performance monitoring with Django Debug Toolbar (dev only)

### Infrastructure Monitoring
- Docker container health checks
- Database connection monitoring
- Redis availability monitoring
- Disk space monitoring
- CPU and memory usage

### Metrics
- User activity metrics
- API request metrics
- Database query performance
- Cache hit rates
- Error rates

## License

This is proprietary software. Each school requires a valid license to use this system.

**License Types:**
- Monthly Subscription
- Yearly Subscription

Contact: support@rhematek-solutions.com

## Credits

**Developed by:** Rhematek Solutions
**Project Lead:** Stephane Arthur Victor
**Framework:** Django 5.1.4
**Design:** Based on W3 CRM

## Support

For technical support or license inquiries:
- Email: support@rhematek-solutions.com
- Documentation: [GitHub Wiki](wiki-url)
- Issue Tracker: [GitHub Issues](issues-url)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Version:** 1.0.0
**Last Updated:** December 24, 2025

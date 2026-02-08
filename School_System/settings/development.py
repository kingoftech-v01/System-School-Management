"""
Django development settings for School Management System.
Uses SQLite without multi-tenancy for easy local development.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development allowed hosts
ALLOWED_HOSTS = ['*']

# Development email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# DEVELOPMENT DATABASE - SQLite (no multi-tenancy)
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Remove django-tenants database router for development
DATABASE_ROUTERS = []

# ==============================================================================
# REMOVE MULTI-TENANCY FOR DEVELOPMENT
# ==============================================================================

# Combine all apps into a single INSTALLED_APPS (no tenant separation)
# Remove django_tenants from the list
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_tenants']

# Remove TenantMainMiddleware from MIDDLEWARE
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'TenantMainMiddleware' not in mw]

# Disable 2FA enforcement in development
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'Enforce2FAMiddleware' not in mw]

# Disable tenant-specific settings
TENANT_MODEL = None
TENANT_DOMAIN_MODEL = None

# Development CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# DEVELOPMENT CACHE - Use Local Memory Cache instead of Redis
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Disable HTTPS redirects in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Add development-specific apps
INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

# Add debug toolbar middleware
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'IS_RUNNING_TESTS': False,
}

# Relaxed CSP for development (django-csp 4.0+ format)
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'"),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"),
        'style-src': ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'",),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
    }
}

# Logging - more verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['accounts']['level'] = 'DEBUG'

# Development-specific settings
CELERY_TASK_ALWAYS_EAGER = False  # Set to True to run tasks synchronously in development
CELERY_TASK_EAGER_PROPAGATES = True

# Disable some security checks for development
AXES_ENABLED = config('AXES_ENABLED', default=True, cast=bool)

# Allow login without email verification in development
ACCOUNT_EMAIL_VERIFICATION = 'optional'


# Stripe placeholder keys for development
STRIPE_PUBLISHABLE_KEY = 'pk_test_placeholder'
STRIPE_SECRET_KEY = 'sk_test_placeholder'

# Development file storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Use simple static files storage (no manifest needed, no collectstatic required)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

print("=" * 80)
print("DEVELOPMENT MODE ACTIVE")
print("=" * 80)

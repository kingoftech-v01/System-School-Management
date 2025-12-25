"""
Django development settings for School Management System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development allowed hosts
ALLOWED_HOSTS = ['*']

# Development email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development database (override if needed)
# Keep the same postgres config for multi-tenancy

# Development CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# Development cache (can use dummy cache for development if needed)
# Keeping Redis for consistency with production

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
}

# Relaxed CSP for development
CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")

# Logging - more verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['accounts']['level'] = 'DEBUG'

# Development-specific settings
CELERY_TASK_ALWAYS_EAGER = False  # Set to True to run tasks synchronously in development
CELERY_TASK_EAGER_PROPAGATES = True

# Disable some security checks for development
AXES_ENABLED = config('AXES_ENABLED', default=True, cast=bool)

# Development file storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

print("=" * 80)
print("DEVELOPMENT MODE ACTIVE")
print("=" * 80)

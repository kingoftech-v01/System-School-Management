"""
Django production settings for School Management System.
Security hardened for production deployment.
"""

from .base import *

try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False

# SECURITY
DEBUG = False

# Strict allowed hosts from environment
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://sms.jhpetitfrere.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Production logging - ship to external service
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Sentry configuration for error tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN and HAS_SENTRY:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
        release=config('RELEASE_VERSION', default='1.0.0'),
    )

# AWS S3 Storage for media files (production)
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_FILE_OVERWRITE = False

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

    # Static files (optional - can still use WhiteNoise)
    # STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Celery production settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_POOL_LIMIT = 10

# Cache production settings
CACHES['default']['OPTIONS']['CONNECTION_POOL_CLASS_KWARGS']['max_connections'] = 100

# Database production optimizations
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 second query timeout
}

# Admin honeypot for production
ADMIN_URL = config('ADMIN_URL', default='admin/')

# Rate limiting - stricter in production
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '50/hour',
    'user': '500/hour',
    'search': '30/hour',
    'pdf_generation': '10/hour',
}

# Session security
SESSION_COOKIE_AGE = 3600  # 1 hour in production
SESSION_SAVE_EVERY_REQUEST = True

# CORS - whitelist only
CORS_ALLOW_ALL_ORIGINS = False

# Content Security Policy (django-csp 4.0+ format)
# Allow unsafe-inline/eval needed by templates and vendor JS libraries
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'",
                       "https://cdn.jsdelivr.net", "https://cdn.datatables.net",
                       "https://cdnjs.cloudflare.com"),
        'style-src': ("'self'", "'unsafe-inline'",
                      "https://cdn.jsdelivr.net", "https://cdn.datatables.net",
                      "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'", "https://fonts.gstatic.com", "https://fonts.googleapis.com"),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
    }
}

# Static files - use non-manifest storage to avoid source map reference errors
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Trust X-Forwarded-* headers from nginx
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

print("=" * 80)
print("PRODUCTION MODE ACTIVE - All security features enabled")
print("=" * 80)

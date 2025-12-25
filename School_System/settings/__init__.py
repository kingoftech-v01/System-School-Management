"""
Settings package initialization.
Automatically loads the appropriate settings module based on DJANGO_ENV.
"""

import os

# Determine which settings to use based on environment
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'development':
    from .development import *
else:
    from .base import *

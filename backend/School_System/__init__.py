"""
School Management System Django Project.
Multi-tenant school management platform with django-tenants.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
__version__ = '1.0.0'

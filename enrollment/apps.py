"""
Enrollment app configuration.
"""

from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enrollment'
    verbose_name = 'Student Enrollment Management'

    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import enrollment.signals  # noqa
        except ImportError:
            pass

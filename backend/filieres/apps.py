"""
Filieres app configuration.
"""

from django.apps import AppConfig


class FilieresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'filieres'
    verbose_name = 'Academic Programs (Filieres)'

    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import filieres.signals  # noqa
        except ImportError:
            pass

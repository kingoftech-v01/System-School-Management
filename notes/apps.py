"""
Notes app configuration.
"""

from django.apps import AppConfig


class NotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notes'
    verbose_name = 'Professor Notes Management'

    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import notes.signals  # noqa
        except ImportError:
            pass

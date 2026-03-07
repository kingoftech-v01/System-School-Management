from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduling'
    verbose_name = 'Scheduling & Timetable'

    def ready(self):
        import scheduling.signals  # noqa: F401

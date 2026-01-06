from django.apps import AppConfig


class CourseConfig(AppConfig):
    name = "course"

    def ready(self):
        """Import translation module before admin autodiscovery."""
        try:
            import course.translation  # noqa: F401
        except ImportError:
            pass

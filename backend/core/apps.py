from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        """Import translation module before admin autodiscovery."""
        try:
            import core.translation  # noqa: F401
        except ImportError:
            pass

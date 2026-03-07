from django.apps import AppConfig


class QuizConfig(AppConfig):
    name = "quiz"

    def ready(self):
        """Import translation module before admin autodiscovery."""
        try:
            import quiz.translation  # noqa: F401
        except ImportError:
            pass

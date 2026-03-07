from django.apps import AppConfig


class AnomalyDetectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'anomaly_detection'
    verbose_name = 'Anomaly Detection'

    def ready(self):
        import anomaly_detection.signals  # noqa: F401

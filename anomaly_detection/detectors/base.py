import logging
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from anomaly_detection.models import AnomalyType, AnomalyAlert

logger = logging.getLogger(__name__)


class BaseDetector:
    """Base class for all anomaly detectors."""

    anomaly_code = None  # Subclass must set this

    def get_anomaly_type(self):
        """Fetch the enabled AnomalyType by code, with short cache."""
        cache_key = f'anomaly_type_{self.anomaly_code}'
        anomaly_type = cache.get(cache_key)
        if anomaly_type is None:
            anomaly_type = AnomalyType.objects.filter(
                code=self.anomaly_code, is_enabled=True
            ).first()
            if anomaly_type:
                cache.set(cache_key, anomaly_type, timeout=300)
        return anomaly_type

    def get_threshold(self, key, default):
        """Get a configurable threshold value, falling back to default."""
        anomaly_type = self.get_anomaly_type()
        if not anomaly_type:
            return Decimal(str(default))
        threshold = anomaly_type.thresholds.filter(key=key).first()
        if threshold:
            return threshold.value
        return Decimal(str(default))

    def create_alert(self, title, details, severity=None, user=None, related_obj=None):
        """Create an AnomalyAlert and trigger notifications."""
        anomaly_type = self.get_anomaly_type()
        if not anomaly_type:
            logger.warning(
                "Anomaly type '%s' not found or disabled, skipping alert: %s",
                self.anomaly_code, title
            )
            return None

        alert_severity = severity or anomaly_type.severity

        kwargs = {
            'anomaly_type': anomaly_type,
            'severity': alert_severity,
            'title': title[:300],
            'details': details,
            'user': user,
        }

        if related_obj is not None:
            kwargs['content_type'] = ContentType.objects.get_for_model(related_obj)
            kwargs['object_id'] = related_obj.pk

        alert = AnomalyAlert.objects.create(**kwargs)

        # Trigger async notification (imported here to avoid circular imports)
        try:
            from anomaly_detection.notifications import notify_anomaly
            notify_anomaly(alert)
        except Exception:
            logger.exception("Failed to send notification for alert %s", alert.pk)

        return alert

    def check(self, instance):
        """Run the detection logic. Subclasses must implement this."""
        raise NotImplementedError

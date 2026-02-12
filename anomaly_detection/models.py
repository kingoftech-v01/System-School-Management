from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class AnomalyType(models.Model):
    """Admin-configurable anomaly type definitions."""

    DOMAIN_CHOICES = [
        ('grade', _('Grade')),
        ('payment', _('Payment')),
        ('enrollment', _('Enrollment')),
        ('login', _('Login')),
        ('academic', _('Academic Integrity')),
    ]
    SEVERITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    code = models.CharField(max_length=50, unique=True, help_text=_('Unique identifier, e.g. grade_sudden_jump'))
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=True)
    notify_roles = models.JSONField(
        default=list, blank=True,
        help_text=_('Roles to notify, e.g. ["direction","admin","professor"]'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Anomaly Type')
        verbose_name_plural = _('Anomaly Types')
        ordering = ['domain', 'severity', 'code']

    def __str__(self):
        return f"[{self.get_domain_display()}] {self.name}"


class AnomalyThreshold(models.Model):
    """Configurable thresholds per anomaly type."""

    anomaly_type = models.ForeignKey(
        AnomalyType, on_delete=models.CASCADE, related_name='thresholds',
    )
    key = models.CharField(max_length=50, help_text=_('Threshold key, e.g. std_dev_multiplier'))
    value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _('Anomaly Threshold')
        verbose_name_plural = _('Anomaly Thresholds')
        unique_together = ['anomaly_type', 'key']

    def __str__(self):
        return f"{self.anomaly_type.code}.{self.key} = {self.value}"


class AnomalyAlert(models.Model):
    """Individual detected anomaly instances."""

    STATUS_CHOICES = [
        ('new', _('New')),
        ('acknowledged', _('Acknowledged')),
        ('resolved', _('Resolved')),
        ('false_positive', _('False Positive')),
    ]

    anomaly_type = models.ForeignKey(
        AnomalyType, on_delete=models.CASCADE, related_name='alerts',
    )
    severity = models.CharField(max_length=10, choices=AnomalyType.SEVERITY_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new')
    title = models.CharField(max_length=300)
    details = models.JSONField(default=dict, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='anomaly_alerts',
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    detected_at = models.DateTimeField(auto_now_add=True)

    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acknowledged_anomalies',
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_anomalies',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    email_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Anomaly Alert')
        verbose_name_plural = _('Anomaly Alerts')
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['status', '-detected_at']),
            models.Index(fields=['anomaly_type', '-detected_at']),
            models.Index(fields=['user', '-detected_at']),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"

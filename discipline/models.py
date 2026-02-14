from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from audit.mixins import AuditedModelMixin


class DisciplinaryAction(AuditedModelMixin, models.Model):
    """Disciplinary actions with immutable audit trail."""

    AUDITED_FIELDS = [
        'incident_type', 'description', 'action_taken', 'severity',
        'is_resolved', 'parent_acknowledged', 'parent_response',
    ]

    SEVERITY_CHOICES = (
        ('minor', _('Minor')),
        ('moderate', _('Moderate')),
        ('serious', _('Serious')),
        ('critical', _('Critical')),
    )

    tenant = models.ForeignKey('core.School', on_delete=models.CASCADE)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disciplinary_actions'
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_filed'
    )
    incident_type = models.CharField(max_length=100, verbose_name=_('Incident Type'))
    description = models.TextField(verbose_name=_('Description'))
    action_taken = models.TextField(verbose_name=_('Action Taken'))
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    incident_date = models.DateField(verbose_name=_('Incident Date'))
    resolution_date = models.DateField(null=True, blank=True, verbose_name=_('Resolution Date'))
    is_resolved = models.BooleanField(default=False, verbose_name=_('Is Resolved'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='discipline_updates'
    )

    # Parent acknowledgment fields
    parent_acknowledged = models.BooleanField(
        default=False, verbose_name=_('Parent Acknowledged')
    )
    parent_acknowledged_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Acknowledged At')
    )
    parent_response = models.TextField(
        blank=True, verbose_name=_('Parent Response')
    )

    class Meta:
        ordering = ['-incident_date']
        verbose_name = _('Disciplinary Action')
        verbose_name_plural = _('Disciplinary Actions')
        permissions = [
            ('view_all_disciplinary_actions', 'Can view all disciplinary actions'),
        ]

    def __str__(self):
        return f"{self.student} - {self.incident_type} ({self.severity})"

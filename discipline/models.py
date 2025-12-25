from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DisciplinaryAction(models.Model):
    """Disciplinary actions with immutable audit trail."""

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

    class Meta:
        ordering = ['-incident_date']
        verbose_name = _('Disciplinary Action')
        verbose_name_plural = _('Disciplinary Actions')
        permissions = [
            ('view_all_disciplinary_actions', 'Can view all disciplinary actions'),
        ]

    def __str__(self):
        return f"{self.student} - {self.incident_type} ({self.severity})"

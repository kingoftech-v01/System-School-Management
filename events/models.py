from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Event(models.Model):
    """School events and calendar."""

    EVENT_TYPE_CHOICES = (
        ('exam', _('Exam')),
        ('holiday', _('Holiday')),
        ('meeting', _('Meeting')),
        ('activity', _('Extra-curricular Activity')),
        ('ceremony', _('Ceremony')),
        ('deadline', _('Deadline')),
    )

    AUDIENCE_CHOICES = (
        ('all', _('All')),
        ('students', _('Students')),
        ('parents', _('Parents')),
        ('staff', _('Staff/Professors')),
    )

    tenant = models.ForeignKey('core.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    target_audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    send_reminder = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __str__(self):
        return f"{self.title} ({self.start_date.date()})"

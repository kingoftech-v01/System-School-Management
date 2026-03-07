"""
Notices app models for announcements with document attachments.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from ckeditor.fields import RichTextField

User = get_user_model()


class NotifyGroup(models.Model):
    """Groups for targeted notifications."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, related_name='notify_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Notice(models.Model):
    """Notice/Announcement model."""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    title = models.CharField(max_length=200)
    content = RichTextField()
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notices'
    )

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    notify_groups = models.ManyToManyField(NotifyGroup, related_name='notices', blank=True)

    expires_at = models.DateField(null=True, blank=True, help_text="Notice will be hidden after this date")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
        permissions = [
            ('can_send_urgent_notice', 'Can send urgent notices'),
        ]

    def __str__(self):
        return self.title

    def is_expired(self):
        """Check if notice is expired."""
        if self.expires_at:
            return timezone.now().date() > self.expires_at
        return False


class NoticeDocument(models.Model):
    """Attachments for notices."""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='notices/documents/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return self.filename


class NoticeResponse(models.Model):
    """Track notice acknowledgments/reads."""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notice_responses')
    read_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['notice', 'user']
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['notice', 'user']),
            models.Index(fields=['acknowledged']),
        ]

    def __str__(self):
        return f"{self.user} - {self.notice.title}"

    def acknowledge(self):
        """Mark as acknowledged."""
        if not self.acknowledged:
            self.acknowledged = True
            self.acknowledged_at = timezone.now()
            self.save(update_fields=['acknowledged', 'acknowledged_at'])

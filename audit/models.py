import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class FieldChangeRecord(models.Model):
    """
    Generic field-level audit trail entry.
    Tracks individual field changes on any model via ContentType.
    """

    ACTION_CHOICES = (
        ('create', _('Created')),
        ('update', _('Updated')),
        ('delete', _('Deleted')),
    )

    # Generic relation to any tracked model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        help_text=_('The model type that was changed')
    )
    object_id = models.PositiveIntegerField(
        help_text=_('The PK of the object that was changed')
    )
    tracked_object = GenericForeignKey('content_type', 'object_id')

    # What changed
    field_name = models.CharField(
        max_length=100,
        help_text=_('Name of the field that changed')
    )
    field_verbose_name = models.CharField(
        max_length=200, blank=True,
        help_text=_('Human-readable field name')
    )
    old_value = models.TextField(
        blank=True, null=True,
        help_text=_('Previous field value as string')
    )
    new_value = models.TextField(
        blank=True, null=True,
        help_text=_('New field value as string')
    )

    # Who and when
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_changes_made'
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Optional context
    change_reason = models.TextField(
        blank=True,
        help_text=_('Optional reason for the change')
    )

    # Grouping: all field changes from a single save() get the same batch_id
    batch_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        help_text=_('Groups field changes from a single save operation')
    )

    # Action type
    action = models.CharField(
        max_length=10, choices=ACTION_CHOICES, default='update'
    )

    class Meta:
        ordering = ['-changed_at']
        verbose_name = _('Field Change Record')
        verbose_name_plural = _('Field Change Records')
        indexes = [
            models.Index(
                fields=['content_type', 'object_id', '-changed_at'],
                name='audit_ct_obj_date_idx',
            ),
            models.Index(
                fields=['changed_by', '-changed_at'],
                name='audit_user_date_idx',
            ),
        ]

    def __str__(self):
        return (
            f"{self.content_type.model}.{self.field_name}: "
            f"{self.old_value} -> {self.new_value}"
        )

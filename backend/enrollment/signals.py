"""
Signal handlers for enrollment app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=RegistrationForm)
def track_status_change(sender, instance, **kwargs):
    """Track status changes in registration form."""
    if instance.pk:
        try:
            old_instance = RegistrationForm.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed, will be logged by the view or admin
                logger.info(
                    f"Registration {instance.id} status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )
        except RegistrationForm.DoesNotExist:
            pass


@receiver(post_save, sender=EnrollmentDocument)
def notify_document_upload(sender, instance, created, **kwargs):
    """Notify when a new document is uploaded."""
    if created:
        logger.info(
            f"New document uploaded for registration {instance.registration.id}: "
            f"{instance.get_document_type_display()}"
        )
        # You could send an email notification here if needed


@receiver(post_save, sender=RegistrationForm)
def send_status_notification(sender, instance, created, **kwargs):
    """Send notification email when status changes (if not triggered from view)."""
    # This is handled in views and tasks, but kept here as backup
    if not created and instance.status in ['approved', 'rejected', 'enrolled']:
        # Check if notification was already sent (by checking if there's a recent history entry)
        recent_history = EnrollmentStatusHistory.objects.filter(
            registration=instance,
            new_status=instance.status
        ).order_by('-changed_at').first()

        if not recent_history or (
            instance.reviewed_at and
            recent_history.changed_at < instance.reviewed_at
        ):
            # Notification might not have been sent yet
            logger.info(f"Triggering status notification for registration {instance.id}")

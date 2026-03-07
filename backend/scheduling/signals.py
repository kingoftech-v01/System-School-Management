from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ScheduleException, SubstitutionRequest


@receiver(post_save, sender=ScheduleException)
def notify_schedule_exception(sender, instance, created, **kwargs):
    """Create notifications when a schedule exception is created."""
    if not created:
        return
    if not instance.notify_students:
        return

    from .services import create_exception_notifications
    create_exception_notifications(instance)


@receiver(post_save, sender=SubstitutionRequest)
def notify_substitution_status(sender, instance, created, **kwargs):
    """Notify relevant parties when substitution request status changes."""
    if created:
        from .services import notify_substitution_created
        notify_substitution_created(instance)
    elif instance.status in ('approved', 'rejected', 'fulfilled'):
        from .services import notify_substitution_updated
        notify_substitution_updated(instance)

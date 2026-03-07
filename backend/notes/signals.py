from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import ProfessorNote, NoteHistory
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ProfessorNote)
def track_note_changes(sender, instance, **kwargs):
    """Track changes to professor notes."""
    if instance.pk:
        try:
            old_instance = ProfessorNote.objects.get(pk=instance.pk)

            # Create history record if important fields changed
            if old_instance.score != instance.score or old_instance.status != instance.status:
                # Get the user who made the change (if available from context)
                changed_by = getattr(instance, '_changed_by', None)

                NoteHistory.objects.create(
                    note=instance,
                    action='updated',
                    changed_by=changed_by,
                    old_values={'score': str(old_instance.score), 'status': old_instance.status},
                    new_values={'score': str(instance.score), 'status': instance.status},
                    change_summary=f'Score changed from {old_instance.score} to {instance.score}'
                )
        except ProfessorNote.DoesNotExist:
            pass


@receiver(post_save, sender=ProfessorNote)
def log_note_creation(sender, instance, created, **kwargs):
    """Log when a new note is created."""
    if created:
        logger.info(
            f"New note created: Professor {instance.professor.username} "
            f"created note for {instance.student.username} in {instance.subject}"
        )

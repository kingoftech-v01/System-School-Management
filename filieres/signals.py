"""
Signal handlers for filieres app.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Filiere, FiliereSubject
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Filiere)
def log_filiere_creation(sender, instance, created, **kwargs):
    """Log when a new filiere is created."""
    if created:
        logger.info(f"New filiere created: {instance.name} ({instance.code}) for {instance.tenant}")


@receiver(post_save, sender=FiliereSubject)
def log_subject_added(sender, instance, created, **kwargs):
    """Log when a subject is added to a filiere."""
    if created:
        logger.info(
            f"Subject {instance.subject.title} added to {instance.filiere.name} "
            f"(Year {instance.year}, Semester {instance.semester}, Coefficient: {instance.coefficient})"
        )


@receiver(pre_delete, sender=FiliereSubject)
def log_subject_removed(sender, instance, **kwargs):
    """Log when a subject is removed from a filiere."""
    logger.info(f"Subject {instance.subject.title} removed from {instance.filiere.name}")

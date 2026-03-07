"""Celery tasks for the scheduling app."""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0, time_limit=120)
def generate_timetable_task(self, generation_id):
    """Async timetable generation triggered from the web UI."""
    from .models import TimetableGeneration
    from .engine.generator import TimetableGenerator

    generation = TimetableGeneration.objects.get(id=generation_id)

    logger.info(f"Starting timetable generation #{generation_id}")
    generator = TimetableGenerator(generation)
    generator.generate()
    logger.info(f"Timetable generation #{generation_id} finished: {generation.status}")


@shared_task
def send_schedule_change_notifications():
    """Send email notifications for pending schedule changes (every 5 min)."""
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import ScheduleNotification

    pending = ScheduleNotification.objects.filter(
        email_sent=False,
    ).select_related('recipient')[:50]  # Batch of 50

    for notification in pending:
        try:
            if notification.recipient.email:
                send_mail(
                    subject=notification.title,
                    message=notification.message,
                    from_email=getattr(settings, 'EMAIL_FROM_ADDRESS', 'noreply@school.local'),
                    recipient_list=[notification.recipient.email],
                    fail_silently=True,
                )
            notification.email_sent = True
            notification.save(update_fields=['email_sent'])
        except Exception as e:
            logger.warning(f"Failed to send notification email: {e}")


@shared_task
def send_daily_schedule_reminder():
    """Send tomorrow's schedule to students and professors at 8 PM."""
    from datetime import date, timedelta
    from django.core.mail import send_mail
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from .models import ScheduleEntry

    User = get_user_model()
    tomorrow = date.today() + timedelta(days=1)
    day_of_week = tomorrow.weekday()

    # Get all active entries for tomorrow
    entries = ScheduleEntry.objects.filter(
        status='active',
        effective_from__lte=tomorrow,
        effective_until__gte=tomorrow,
        time_slot__day_of_week=day_of_week,
    ).select_related('course', 'professor', 'room', 'time_slot', 'filiere')

    # Group by professor
    prof_entries = {}
    for entry in entries:
        if entry.is_active_on(tomorrow):
            prof_entries.setdefault(entry.professor_id, []).append(entry)

    # Send to professors
    for prof_id, prof_schedule in prof_entries.items():
        try:
            prof = User.objects.get(id=prof_id)
            if not prof.email:
                continue

            lines = [f"Your schedule for {tomorrow.strftime('%A, %B %d')}:\n"]
            for entry in sorted(prof_schedule, key=lambda e: e.time_slot.start_time):
                room = entry.room.name if entry.room else 'TBD'
                lines.append(
                    f"  {entry.time_slot.start_time:%H:%M}-{entry.time_slot.end_time:%H:%M}: "
                    f"{entry.course.title} ({room})"
                )

            send_mail(
                subject=f"Tomorrow's Schedule - {tomorrow.strftime('%B %d')}",
                message='\n'.join(lines),
                from_email=getattr(settings, 'EMAIL_FROM_ADDRESS', 'noreply@school.local'),
                recipient_list=[prof.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Failed to send schedule reminder to prof {prof_id}: {e}")

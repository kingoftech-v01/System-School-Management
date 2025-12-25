from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import ProfessorNote


@shared_task
def notify_note_status_change(note_id, status):
    """Send notification when note status changes."""
    try:
        note = ProfessorNote.objects.get(id=note_id)

        # Notify professor
        send_mail(
            subject=f'[{note.tenant.name}] Note {status.title()}',
            message=f'Your note for {note.student.get_full_name()} has been {status}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[note.professor.email],
            fail_silently=True
        )

        # Notify student if approved
        if status == 'approved':
            send_mail(
                subject=f'[{note.tenant.name}] New Grade Posted',
                message=f'A new grade has been posted for {note.subject}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[note.student.email],
                fail_silently=True
            )

    except ProfessorNote.DoesNotExist:
        pass

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from .models import BorrowRecord


@shared_task
def send_overdue_reminders():
    """Send email reminders for overdue books."""
    overdue_records = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lt=date.today()
    )

    for record in overdue_records:
        record.status = 'overdue'
        record.save()

        send_mail(
            subject=f'[{record.tenant.name}] Overdue Book Reminder',
            message=f'Dear {record.student.get_full_name()},\n\nThe book "{record.book.title}" is overdue. Please return it as soon as possible.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[record.student.email],
            fail_silently=True
        )

    return overdue_records.count()

"""
Celery tasks for payments app.
Handles payment reminders, failed payment processing, and invoice generation.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, Payment


@shared_task
def send_payment_reminders():
    """
    Send payment reminders for unpaid invoices.
    Runs on the 1st of each month at 9 AM.
    """
    from core.sms import send_sms_to_parent

    overdue_invoices = Invoice.objects.filter(
        payment_complete=False,
        due_date__lt=timezone.now().date()
    ).select_related('student', 'student__student')

    sent_count = 0
    for invoice in overdue_invoices:
        student = invoice.student
        name = student.student.get_full_name
        amount = invoice.balance

        # Email to student
        send_mail(
            subject=f'Payment Reminder: Invoice #{invoice.pk}',
            message=(
                f'Dear {name},\n\n'
                f'This is a reminder that your invoice #{invoice.pk} '
                f'has an outstanding balance of {amount}.\n'
                f'Due date: {invoice.due_date}\n\n'
                f'Please make your payment at your earliest convenience.\n\n'
                f'School Management System'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.student.email],
            fail_silently=True,
        )

        # SMS to parent
        sms_msg = (
            f'Payment reminder: {name} has an outstanding balance of '
            f'{amount} (Invoice #{invoice.pk}, due {invoice.due_date}). '
            f'Please contact the school for payment options.'
        )
        send_sms_to_parent(student, sms_msg)
        sent_count += 1

    return f'Sent {sent_count} payment reminders'


@shared_task
def process_failed_payments():
    """
    Retry processing of failed payments.
    Runs daily at 2 AM.
    """
    failed = Payment.objects.filter(
        status='failed',
        created_at__gte=timezone.now() - timedelta(days=7)
    )

    retried = 0
    for payment in failed:
        try:
            payment.status = 'pending'
            payment.save(update_fields=['status'])
            retried += 1
        except Exception:
            pass

    return f'Retried {retried} failed payments'


@shared_task
def generate_monthly_invoices():
    """
    Generate monthly invoices for recurring payments.
    Runs on the 1st of each month.
    """
    # TODO: Implement monthly invoice generation based on fee structures
    pass

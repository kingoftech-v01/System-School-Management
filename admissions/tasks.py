"""
Celery tasks for admissions app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_admission_confirmation_email(application_id):
    """Send email confirmation when application is submitted."""
    from .models import AdmissionStudent

    try:
        application = AdmissionStudent.objects.get(id=application_id)

        send_mail(
            subject=f"Application Received - {application.session.name}",
            message=f"""Dear {application.get_full_name()},

We have received your application for {application.program.title if application.program else 'the program'}.

Application Details:
- Application ID: {application.id}
- Session: {application.session.name}
- Status: {application.get_status_display()}

We will review your application and contact you soon.

Best regards,
Admissions Office""",
            from_email="admissions@school.com",
            recipient_list=[application.email],
            fail_silently=True
        )

        logger.info(f"Sent admission confirmation email to {application.email}")
        return f"Sent confirmation to {application.email}"

    except Exception as exc:
        logger.error(f"Error sending admission confirmation: {exc}")
        raise


@shared_task
def send_status_update_email(application_id):
    """Send email when application status changes."""
    from .models import AdmissionStudent

    try:
        application = AdmissionStudent.objects.get(id=application_id)

        status_messages = {
            'under_review': 'Your application is now under review.',
            'counseling': 'Your application has been moved to counseling stage. A counselor will contact you soon.',
            'payment_pending': 'Congratulations! Please complete the payment to finalize your admission.',
            'admitted': 'Congratulations! You have been admitted to the program.',
            'rejected': 'We regret to inform you that your application was not successful this time.'
        }

        message = status_messages.get(application.status, 'Your application status has been updated.')

        send_mail(
            subject=f"Application Status Update - {application.get_status_display()}",
            message=f"""Dear {application.get_full_name()},

{message}

Current Status: {application.get_status_display()}
Session: {application.session.name}

{'Reason: ' + application.rejection_reason if application.rejection_reason else ''}

For any questions, please contact our admissions office.

Best regards,
Admissions Office""",
            from_email="admissions@school.com",
            recipient_list=[application.email],
            fail_silently=True
        )

        logger.info(f"Sent status update email to {application.email} - Status: {application.status}")
        return f"Sent status update to {application.email}"

    except Exception as exc:
        logger.error(f"Error sending status update: {exc}")
        raise


@shared_task
def process_admission_payments():
    """Check and process pending admission payments."""
    from .models import AdmissionStudent, AdmissionPayment

    pending_payments = AdmissionStudent.objects.filter(
        status='payment_pending',
        application_fee_paid=False
    ).select_related('program', 'session')

    processed_count = 0
    for application in pending_payments:
        try:
            # Check if payment exists
            if hasattr(application, 'payment') and application.payment.verified:
                application.application_fee_paid = True
                application.status = 'admitted'
                application.admitted = True
                application.admission_date = timezone.now().date()
                application.save()

                # Send admission confirmation
                send_status_update_email.delay(application.id)
                processed_count += 1
        except Exception as exc:
            logger.error(f"Error processing payment for application {application.id}: {exc}")

    logger.info(f"Processed {processed_count} admission payments")
    return f"Processed {processed_count} payments"


@shared_task
def send_counseling_reminders():
    """Send reminders to counselors for pending counseling sessions."""
    from .models import AdmissionStudent
    from django.contrib.auth import get_user_model

    User = get_user_model()

    counseling_applications = AdmissionStudent.objects.filter(
        status='counseling',
        counselor__isnull=False
    ).select_related('counselor', 'session', 'program')

    # Group by counselor
    counselor_apps = {}
    for app in counseling_applications:
        if app.counselor.email:
            if app.counselor not in counselor_apps:
                counselor_apps[app.counselor] = []
            counselor_apps[app.counselor].append(app)

    sent_count = 0
    for counselor, applications in counselor_apps.items():
        app_list = '\n'.join([
            f"- {app.get_full_name()} (ID: {app.id}, Program: {app.program.title if app.program else 'N/A'})"
            for app in applications
        ])

        send_mail(
            subject=f"Counseling Reminder - {len(applications)} Pending Applications",
            message=f"""Dear {counselor.get_full_name},

You have {len(applications)} applications pending counseling:

{app_list}

Please review and provide your feedback at your earliest convenience.

Best regards,
Admissions Office""",
            from_email="admissions@school.com",
            recipient_list=[counselor.email],
            fail_silently=True
        )
        sent_count += 1

    logger.info(f"Sent counseling reminders to {sent_count} counselors")
    return f"Sent reminders to {sent_count} counselors"


@shared_task
def auto_archive_old_applications():
    """Archive applications from closed sessions."""
    from .models import AdmissionSession, AdmissionStudent

    closed_sessions = AdmissionSession.objects.filter(
        is_active=False,
        end_date__lt=timezone.now().date()
    )

    # You could add an 'archived' field to AdmissionStudent model
    # For now, just log the count
    old_apps_count = AdmissionStudent.objects.filter(
        session__in=closed_sessions,
        status__in=['pending', 'under_review']
    ).count()

    logger.info(f"Found {old_apps_count} old applications that could be archived")
    return f"Found {old_apps_count} old applications"

"""
Celery tasks for enrollment notifications and automation.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import RegistrationForm, EnrollmentStatusHistory
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_enrollment_status_email(self, registration_id, status):
    """
    Send email notification when enrollment status changes.

    Args:
        registration_id: ID of the registration form
        status: New status of the registration
    """
    try:
        registration = RegistrationForm.objects.get(id=registration_id)

        # Determine email template and subject based on status
        templates = {
            'submitted': {
                'subject': 'Registration Received',
                'template': 'enrollment/emails/registration_received.html',
                'to': [registration.email, registration.parent_email]
            },
            'under_review': {
                'subject': 'Application Under Review',
                'template': 'enrollment/emails/under_review.html',
                'to': [registration.email, registration.parent_email]
            },
            'approved': {
                'subject': 'Congratulations! Application Approved',
                'template': 'enrollment/emails/approved.html',
                'to': [registration.email, registration.parent_email]
            },
            'rejected': {
                'subject': 'Application Status Update',
                'template': 'enrollment/emails/rejected.html',
                'to': [registration.email, registration.parent_email]
            },
            'enrolled': {
                'subject': 'Welcome to {}'.format(registration.tenant.name),
                'template': 'enrollment/emails/enrolled.html',
                'to': [registration.email, registration.parent_email]
            },
        }

        config = templates.get(status)
        if not config:
            logger.warning(f"No email template for status: {status}")
            return

        # Render email content
        context = {
            'registration': registration,
            'student_name': registration.student_name,
            'parent_name': registration.parent_name,
            'school_name': registration.tenant.name,
            'filiere': registration.filiere.name if registration.filiere else 'N/A',
            'academic_year': registration.academic_year,
            'status': registration.get_status_display(),
            'rejection_reason': registration.rejection_reason,
            'review_notes': registration.review_notes,
        }

        html_message = render_to_string(config['template'], context)
        plain_message = f"""
        Dear {registration.parent_name},

        Your registration for {registration.student_name} has been {status}.

        Status: {registration.get_status_display()}

        {'Reason: ' + registration.rejection_reason if status == 'rejected' else ''}

        Thank you,
        {registration.tenant.name}
        """

        # Send email
        send_mail(
            subject=f"[{registration.tenant.name}] {config['subject']}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=config['to'],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Sent {status} email for registration {registration_id}")

    except RegistrationForm.DoesNotExist:
        logger.error(f"Registration {registration_id} not found")
    except Exception as exc:
        logger.error(f"Error sending enrollment email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_enrollment_reminders():
    """
    Send reminders for incomplete registrations.
    Runs daily to remind users to complete their registration.
    """
    from datetime import timedelta

    # Find registrations submitted more than 7 days ago but not completed
    seven_days_ago = timezone.now() - timedelta(days=7)
    incomplete_registrations = RegistrationForm.objects.filter(
        status='pending',
        submitted_at__lte=seven_days_ago,
        submitted_at__gte=seven_days_ago - timedelta(days=1)  # Only 7-day mark
    )

    count = 0
    for registration in incomplete_registrations:
        try:
            context = {
                'registration': registration,
                'student_name': registration.student_name,
                'parent_name': registration.parent_name,
                'school_name': registration.tenant.name,
                'days_pending': (timezone.now() - registration.submitted_at).days
            }

            html_message = render_to_string(
                'enrollment/emails/reminder_incomplete.html',
                context
            )

            send_mail(
                subject=f"[{registration.tenant.name}] Registration Reminder",
                message=f"Dear {registration.parent_name}, Your registration is still pending review.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.parent_email],
                html_message=html_message,
                fail_silently=True
            )
            count += 1
        except Exception as e:
            logger.error(f"Error sending reminder for registration {registration.id}: {e}")

    logger.info(f"Sent {count} enrollment reminders")
    return count


@shared_task
def cleanup_old_rejected_registrations():
    """
    Archive or delete old rejected registrations after 90 days.
    Runs weekly.
    """
    from datetime import timedelta

    ninety_days_ago = timezone.now() - timedelta(days=90)
    old_rejected = RegistrationForm.objects.filter(
        status='rejected',
        reviewed_at__lte=ninety_days_ago
    )

    count = old_rejected.count()
    # Instead of deleting, we could archive them
    # For now, just log the count
    logger.info(f"Found {count} old rejected registrations eligible for archival")

    # Uncomment to actually delete:
    # old_rejected.delete()

    return count


@shared_task
def generate_enrollment_report(tenant_id, academic_year):
    """
    Generate enrollment report for a specific academic year.

    Args:
        tenant_id: School tenant ID
        academic_year: Academic year (e.g., '2024-2025')
    """
    try:
        from core.models import School

        tenant = School.objects.get(id=tenant_id)
        registrations = RegistrationForm.objects.filter(
            tenant=tenant,
            academic_year=academic_year
        )

        # Generate statistics
        stats = {
            'total': registrations.count(),
            'pending': registrations.filter(status='pending').count(),
            'approved': registrations.filter(status='approved').count(),
            'rejected': registrations.filter(status='rejected').count(),
            'enrolled': registrations.filter(status='enrolled').count(),
        }

        # You could generate a PDF report here
        # For now, just return stats
        logger.info(f"Generated enrollment report for {tenant.name} - {academic_year}: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Error generating enrollment report: {e}")
        raise


@shared_task
def auto_approve_complete_registrations():
    """
    Auto-approve registrations that meet certain criteria.
    This is an example - you might want different logic.
    """
    # Find registrations with all documents uploaded and verified
    pending_registrations = RegistrationForm.objects.filter(
        status='pending'
    ).prefetch_related('documents')

    auto_approved = 0
    for registration in pending_registrations:
        # Check if all required documents are uploaded and verified
        docs = registration.documents.all()
        required_doc_types = ['birth_certificate', 'photo', 'id_card', 'parent_id']

        uploaded_types = set(doc.document_type for doc in docs if doc.is_verified)

        if all(doc_type in uploaded_types for doc_type in required_doc_types):
            # Auto-approve if 100% complete and all docs verified
            if registration.get_completion_percentage() == 100:
                registration.status = 'approved'
                registration.review_notes = 'Auto-approved: All requirements met'
                registration.save()

                # Send notification
                send_enrollment_status_email.delay(registration.id, 'approved')
                auto_approved += 1

    logger.info(f"Auto-approved {auto_approved} registrations")
    return auto_approved

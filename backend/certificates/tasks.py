"""
Celery tasks for certificates app.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from .models import (
    Certificate, BatchCertificateGeneration,
    CertificateTemplate, CertificateVerification
)
from accounts.models import Student
from result.models import Result


@shared_task(name='certificates.generate_batch_certificates')
def generate_batch_certificates(batch_id):
    """Generate certificates in batch (background task)."""
    try:
        batch = BatchCertificateGeneration.objects.get(pk=batch_id)

        # Get eligible students from course
        course = batch.course
        template = batch.template or course.default_certificate_template

        # Get students who passed the course
        passing_students = Result.objects.filter(
            course=course,
            grade__gte=course.passing_grade  # Assuming passing grade exists
        ).select_related('student')

        batch.total_students = passing_students.count()
        batch.save()

        success_count = 0
        failed_count = 0

        for result in passing_students:
            try:
                # Check if certificate already exists
                if Certificate.objects.filter(student=result.student, course=course).exists():
                    batch.processed_count += 1
                    batch.save()
                    continue

                # Create certificate
                certificate = Certificate.objects.create(
                    student=result.student,
                    course=course,
                    template=template,
                    issue_date=timezone.now().date(),
                    grade=result.grade,
                    honors=determine_honors(result.grade),  # Helper function
                )

                # Generate PDF (to be implemented)
                # certificate.generate_pdf()

                success_count += 1
                batch.processed_count += 1
                batch.success_count += 1
                batch.save()

            except Exception as e:
                failed_count += 1
                batch.processed_count += 1
                batch.failed_count += 1
                batch.save()

                # Log error
                print(f"Error generating certificate for {result.student}: {str(e)}")

        # Mark batch as completed
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()

        # Notify creator
        send_mail(
            subject=f'Certificate Batch Generation Complete',
            message=f'Batch generation for {course.name} is complete.\n\nSuccess: {success_count}\nFailed: {failed_count}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[batch.created_by.email],
            fail_silently=True,
        )

        return f'Generated {success_count} certificates, {failed_count} failed'

    except BatchCertificateGeneration.DoesNotExist:
        return f'Batch {batch_id} not found'


def determine_honors(grade):
    """Determine honors based on grade."""
    if grade >= 95:
        return 'Summa Cum Laude'
    elif grade >= 90:
        return 'Magna Cum Laude'
    elif grade >= 85:
        return 'Cum Laude'
    return ''


@shared_task(name='certificates.send_certificate_notification')
def send_certificate_notification(certificate_id):
    """Send notification when certificate is issued."""
    try:
        certificate = Certificate.objects.get(pk=certificate_id)

        send_mail(
            subject='Certificate Issued',
            message=f'Congratulations! Your certificate for {certificate.course.name} has been issued.\n\nCertificate Number: {certificate.certificate_number}\nIssue Date: {certificate.issue_date}\n\nYou can download it from your student portal.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[certificate.student.student.email],
            fail_silently=False,
        )

        return f'Sent notification for certificate {certificate_id}'
    except Certificate.DoesNotExist:
        return f'Certificate {certificate_id} not found'


@shared_task(name='certificates.verify_certificate_integrity')
def verify_certificate_integrity():
    """Verify integrity of all certificates (check hash signatures)."""
    certificates = Certificate.objects.filter(is_revoked=False)

    invalid_count = 0

    for certificate in certificates:
        calculated_hash = certificate.calculate_hash()

        if certificate.hash_signature != calculated_hash:
            invalid_count += 1
            # Log or notify about potential tampering
            print(f"Warning: Certificate {certificate.certificate_number} has invalid signature")

    return f'Verified {certificates.count()} certificates, found {invalid_count} with invalid signatures'


@shared_task(name='certificates.cleanup_expired_verifications')
def cleanup_expired_verifications():
    """Clean up old verification records."""
    # Delete verification records older than 2 years
    cutoff_date = timezone.now() - timedelta(days=730)

    deleted_count, _ = CertificateVerification.objects.filter(
        verified_at__lt=cutoff_date
    ).delete()

    return f'Deleted {deleted_count} old verification records'


@shared_task(name='certificates.send_expiring_certificate_reminders')
def send_expiring_certificate_reminders():
    """Send reminders for certificates expiring soon (if applicable)."""
    # This is for certificates with expiration dates
    # Only applicable if your system has expiring certificates

    # Example: Certificates expiring in 30 days
    expiry_date = timezone.now().date() + timedelta(days=30)

    expiring_certs = Certificate.objects.filter(
        expiry_date=expiry_date,  # Assuming this field exists
        is_revoked=False
    )

    for cert in expiring_certs:
        send_mail(
            subject='Certificate Expiring Soon',
            message=f'Your certificate for {cert.course.name} will expire on {cert.expiry_date}.\n\nPlease renew if required.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cert.student.student.email],
            fail_silently=True,
        )

    return f'Sent {expiring_certs.count()} expiry reminders'

"""
Email utility functions for sending templated emails.
Handles all email communication in the multi-tenant school management system.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
import logging

logger = logging.getLogger(__name__)


def send_templated_email(subject, template_name, context, recipient_list, from_email=None, fail_silently=False):
    """
    Send an email using a Django template.

    Args:
        subject (str): Email subject line
        template_name (str): Path to HTML template (e.g., 'emails/welcome.html')
        context (dict): Context dictionary for template rendering
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): Sender email (defaults to DEFAULT_FROM_EMAIL)
        fail_silently (bool): If False, raises exceptions on send failure

    Returns:
        int: Number of successfully sent emails
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Add default context variables if not present
    context.setdefault('tenant_name', getattr(context.get('tenant'), 'name', 'School Management System'))
    context.setdefault('support_email', settings.DEFAULT_FROM_EMAIL)
    context.setdefault('site_name', getattr(settings, 'SITE_NAME', 'School System'))

    try:
        # Render HTML email
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        result = email.send(fail_silently=fail_silently)

        logger.info(f"Email sent successfully: {subject} to {recipient_list}")
        return result

    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {recipient_list}: {str(e)}")
        if not fail_silently:
            raise
        return 0


def send_verification_email(user, verification_url, tenant):
    """
    Send email verification email to new users.

    Args:
        user: User instance
        verification_url (str): Full URL for email verification
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'user': user,
        'verification_url': verification_url,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
    }

    return send_templated_email(
        subject=f'Verify Your Email - {tenant.name}',
        template_name='emails/email_verification.html',
        context=context,
        recipient_list=[user.email]
    )


def send_welcome_email(user, tenant, request=None):
    """
    Send welcome email after successful registration and email verification.

    Args:
        user: User instance
        tenant: Tenant instance
        request: HTTP request object (optional, for building URLs)

    Returns:
        int: Number of successfully sent emails
    """
    # Build base URL
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
    else:
        base_url = f"https://{tenant.get_primary_domain().domain}"

    context = {
        'user': user,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
        'dashboard_url': base_url + '/dashboard/',
        'profile_url': base_url + '/accounts/profile/',
        'help_url': base_url + '/help/',
    }

    return send_templated_email(
        subject=f'Welcome to {tenant.name}!',
        template_name='emails/welcome.html',
        context=context,
        recipient_list=[user.email]
    )


def send_password_reset_email(user, reset_url, tenant):
    """
    Send password reset email.

    Args:
        user: User instance
        reset_url (str): Full URL for password reset
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'user': user,
        'reset_url': reset_url,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
    }

    return send_templated_email(
        subject=f'Password Reset Request - {tenant.name}',
        template_name='emails/password_reset.html',
        context=context,
        recipient_list=[user.email]
    )


def send_2fa_enabled_email(user, tenant):
    """
    Send notification email when 2FA is enabled.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'user': user,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
    }

    return send_templated_email(
        subject=f'Two-Factor Authentication Enabled - {tenant.name}',
        template_name='emails/2fa_enabled.html',
        context=context,
        recipient_list=[user.email]
    )


def send_2fa_disabled_email(user, tenant):
    """
    Send notification email when 2FA is disabled.

    Args:
        user: User instance
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'user': user,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
    }

    return send_templated_email(
        subject=f'Two-Factor Authentication Disabled - {tenant.name}',
        template_name='emails/2fa_disabled.html',
        context=context,
        recipient_list=[user.email]
    )


def send_enrollment_confirmation_email(student, course, tenant):
    """
    Send enrollment confirmation email to students.

    Args:
        student: Student instance
        course: Course instance
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'student': student,
        'course': course,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': student.student.email,
        'user_name': student.student.get_full_name(),
    }

    return send_templated_email(
        subject=f'Course Enrollment Confirmation - {tenant.name}',
        template_name='emails/enrollment_confirmation.html',
        context=context,
        recipient_list=[student.student.email]
    )


def send_grade_notification_email(student, course, grade, tenant):
    """
    Send grade notification email to students.

    Args:
        student: Student instance
        course: Course instance
        grade: Grade/score
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'student': student,
        'course': course,
        'grade': grade,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': student.student.email,
        'user_name': student.student.get_full_name(),
    }

    return send_templated_email(
        subject=f'New Grade Posted - {course.title}',
        template_name='emails/grade_notification.html',
        context=context,
        recipient_list=[student.student.email]
    )


def send_payment_receipt_email(student, payment, tenant):
    """
    Send payment receipt email to students/parents.

    Args:
        student: Student instance
        payment: Payment/Invoice instance
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'student': student,
        'payment': payment,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': student.student.email,
        'user_name': student.student.get_full_name(),
    }

    recipients = [student.student.email]

    # Also send to parent if exists
    try:
        from accounts.models import Parent
        parent = Parent.objects.filter(student=student).first()
        if parent:
            recipients.append(parent.user.email)
    except:
        pass

    return send_templated_email(
        subject=f'Payment Receipt - {tenant.name}',
        template_name='emails/payment_receipt.html',
        context=context,
        recipient_list=recipients
    )


def send_bulk_notification_email(recipients, subject, message, tenant, from_role='admin'):
    """
    Send bulk notification emails (for announcements, etc.).

    Args:
        recipients (list): List of email addresses
        subject (str): Email subject
        message (str): Email message body
        tenant: Tenant instance
        from_role (str): Role of sender (for template customization)

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'message': message,
        'subject': subject,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'from_role': from_role,
    }

    # Send to recipients in batches of 50 to avoid overwhelming the mail server
    batch_size = 50
    total_sent = 0

    for i in range(0, len(recipients), batch_size):
        batch = recipients[i:i + batch_size]
        sent = send_templated_email(
            subject=subject,
            template_name='emails/bulk_notification.html',
            context=context,
            recipient_list=batch,
            fail_silently=True
        )
        total_sent += sent

    return total_sent


def send_account_activation_email(user, activation_url, tenant):
    """
    Send account activation email for manual account approval systems.

    Args:
        user: User instance
        activation_url (str): Full URL for account activation
        tenant: Tenant instance

    Returns:
        int: Number of successfully sent emails
    """
    context = {
        'user': user,
        'activation_url': activation_url,
        'tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'recipient_email': user.email,
        'user_name': user.get_full_name() or user.username,
    }

    return send_templated_email(
        subject=f'Account Activated - {tenant.name}',
        template_name='emails/account_activation.html',
        context=context,
        recipient_list=[user.email]
    )

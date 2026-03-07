import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def notify_anomaly(alert):
    """Send email notifications for an anomaly alert to configured roles."""
    roles = alert.anomaly_type.notify_roles or ['direction', 'admin']
    recipients = User.objects.filter(
        role__in=roles,
        is_active=True,
    ).exclude(email='')

    # Scope notifications to the same tenant as the alert user
    if alert.user and getattr(alert.user, 'tenant_id', None):
        recipients = recipients.filter(tenant_id=alert.user.tenant_id)

    emails = list(recipients.values_list('email', flat=True))

    if not emails:
        logger.info("No recipients found for anomaly alert %s (roles: %s)", alert.pk, roles)
        return

    try:
        from core.utils import send_html_email
        send_html_email(
            subject=f"[{alert.severity.upper()}] Anomaly: {alert.title[:100]}",
            recipient_list=emails,
            template='anomaly_detection/email/alert_notification.html',
            context={'alert': alert},
        )
        alert.email_sent = True
        alert.save(update_fields=['email_sent'])
        logger.info("Anomaly alert email sent for alert %s to %d recipients", alert.pk, len(emails))
    except Exception:
        logger.exception("Failed to send anomaly alert email for alert %s", alert.pk)

"""
Celery tasks for notices app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notice_notifications(notice_id):
    """Send email notifications for a new notice."""
    from .models import Notice, NoticeResponse

    try:
        notice = Notice.objects.get(id=notice_id)

        # Get all users in notify groups
        users = set()
        for group in notice.notify_groups.all():
            users.update(group.users.all())

        # Create notice responses and send emails
        for user in users:
            NoticeResponse.objects.get_or_create(notice=notice, user=user)
            
            if user.email:
                send_mail(
                    subject=f"New Notice: {notice.title}",
                    message=notice.content,
                    from_email="notices@school.com",
                    recipient_list=[user.email],
                    fail_silently=True
                )

        logger.info(f"Sent notice {notice.id} to {len(users)} users")
        return f"Sent to {len(users)} users"

    except Exception as exc:
        logger.error(f"Error sending notice notifications: {exc}")
        raise


@shared_task
def check_notice_acknowledgments():
    """Send reminders for unacknowledged notices."""
    from .models import NoticeResponse

    unacknowledged = NoticeResponse.objects.filter(
        acknowledged=False,
        notice__is_active=True
    ).select_related("notice", "user")

    reminder_count = 0
    for response in unacknowledged:
        if response.user.email:
            send_mail(
                subject=f"Reminder: Acknowledge {response.notice.title}",
                message=f"Please acknowledge: {response.notice.title}",
                from_email="notices@school.com",
                recipient_list=[response.user.email],
                fail_silently=True
            )
            reminder_count += 1

    logger.info(f"Sent {reminder_count} acknowledgment reminders")
    return f"Sent {reminder_count} reminders"


@shared_task
def archive_expired_notices():
    """Archive notices that have expired."""
    from .models import Notice

    now = timezone.now()
    expired = Notice.objects.filter(is_active=True, expires_at__lt=now)
    count = expired.update(is_active=False)
    
    logger.info(f"Archived {count} expired notices")
    return f"Archived {count} notices"

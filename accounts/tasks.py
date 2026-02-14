"""
Celery tasks for accounts app.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def cleanup_inactive_parent_accounts():
    """Delete parent accounts with no active children after 15 days of inactivity.

    A parent account is deleted if:
    1. Never enrolled a child AND account is >15 days old.
    2. All enrollments were rejected AND last rejection was >15 days ago.

    Parents with at least one linked child or any active enrollment
    (pending/under_review/approved) are never deleted.
    """
    from accounts.models import Parent, User
    from enrollment.models import RegistrationForm

    cutoff = timezone.now() - timedelta(days=15)

    # All parent users with NO linked children (no Parent profile rows)
    childless_parents = User.objects.filter(
        is_parent=True, role='parent',
    ).exclude(
        parent_profiles__isnull=False
    )

    to_delete = []
    for parent in childless_parents:
        enrollments = RegistrationForm.objects.filter(parent_user=parent)

        if not enrollments.exists():
            # Case 1: Never enrolled — delete if account is >15 days old
            if parent.date_joined <= cutoff:
                to_delete.append(parent.pk)
        else:
            # Has enrollments — check if any are still active
            active = enrollments.filter(
                status__in=['pending', 'under_review', 'approved']
            )
            if active.exists():
                continue  # keep account — has active enrollment

            # All enrollments are rejected/closed
            # Delete if the most recent rejection is >15 days old
            latest = enrollments.order_by('-updated_at').first()
            if latest and latest.updated_at <= cutoff:
                to_delete.append(parent.pk)

    count = 0
    if to_delete:
        count = User.objects.filter(pk__in=to_delete).delete()[0]

    logger.info("Cleaned up %d inactive parent accounts (15-day rule)", count)
    return count

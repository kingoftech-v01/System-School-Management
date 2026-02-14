import logging
from datetime import timedelta

from django.utils import timezone

from .base import BaseDetector

logger = logging.getLogger(__name__)


class BruteForceDetector(BaseDetector):
    """Detect brute force login attempts using django-axes AccessAttempt."""

    anomaly_code = 'login_brute_force'

    def check(self, user, ip_address=None):
        try:
            from axes.models import AccessAttempt
        except ImportError:
            logger.debug("django-axes not installed, skipping brute force detection")
            return

        failure_threshold = int(self.get_threshold('failure_threshold', 5))
        window_minutes = int(self.get_threshold('window_minutes', 30))
        since = timezone.now() - timedelta(minutes=window_minutes)

        filters = {'attempt_time__gte': since}
        if ip_address:
            filters['ip_address'] = ip_address
        elif user:
            filters['username'] = user.username

        recent_failures = AccessAttempt.objects.filter(**filters).count()

        if recent_failures >= failure_threshold:
            identifier = ip_address or (user.username if user else 'unknown')
            self.create_alert(
                title=f"Brute force detected: {recent_failures} failed attempts "
                      f"from {identifier} in {window_minutes}min",
                details={
                    'failed_attempts': recent_failures,
                    'threshold': failure_threshold,
                    'window_minutes': window_minutes,
                    'ip_address': ip_address or '',
                    'username': user.username if user else '',
                },
                user=user,
            )


class UnusualLoginTimeDetector(BaseDetector):
    """Detect logins outside of normal operating hours."""

    anomaly_code = 'login_unusual_time'

    def check(self, user, login_time=None):
        if login_time is None:
            login_time = timezone.now()

        # Use localtime for hour comparison
        local_time = timezone.localtime(login_time)
        current_hour = local_time.hour

        start_hour = int(self.get_threshold('start_hour', 6))
        end_hour = int(self.get_threshold('end_hour', 23))

        if current_hour < start_hour or current_hour >= end_hour:
            self.create_alert(
                title=f"Unusual login time: {user.get_full_name} logged in at "
                      f"{local_time.strftime('%H:%M')}",
                details={
                    'username': user.username,
                    'login_time': local_time.isoformat(),
                    'hour': current_hour,
                    'normal_start': start_hour,
                    'normal_end': end_hour,
                },
                severity='low',
                user=user,
            )


class DeviceChangeDetector(BaseDetector):
    """Detect user agent changes between consecutive login sessions."""

    anomaly_code = 'login_device_change'

    def check(self, user, current_user_agent=''):
        if not current_user_agent:
            return

        try:
            from analytics.models import ActivityLog
        except ImportError:
            return

        # Get the previous login entry for this user
        previous_login = (
            ActivityLog.objects.filter(
                student__student=user,
                activity_type='login',
            )
            .exclude(user_agent=current_user_agent)
            .order_by('-created_at')
            .first()
        )

        if not previous_login or not previous_login.user_agent:
            return

        # Only alert if the previous login was recent (within 24h)
        if previous_login.created_at < timezone.now() - timedelta(hours=24):
            return

        self.create_alert(
            title=f"Device change detected for {user.get_full_name}",
            details={
                'username': user.username,
                'previous_user_agent': previous_login.user_agent[:500],
                'current_user_agent': current_user_agent[:500],
                'previous_login_at': previous_login.created_at.isoformat(),
                'previous_ip': previous_login.ip_address or '',
            },
            user=user,
        )

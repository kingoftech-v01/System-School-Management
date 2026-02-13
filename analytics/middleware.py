"""
ActivityLog Middleware - Tracks student activity across the platform.

This middleware writes to analytics.ActivityLog on every request made by
an authenticated student user. It feeds the engagement scoring pipeline,
at-risk student detection, and all analytics dashboards.
"""

import logging
import time

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Paths to skip entirely (static assets, admin, API health checks)
SKIP_PREFIXES = (
    '/static/',
    '/media/',
    '/admin/',
    '/favicon',
    '/__debug__/',
    '/api/token/',
)

# URL pattern → activity_type mapping (checked in order, first match wins)
ACTIVITY_TYPE_MAP = [
    # Login/logout
    ('/accounts/login/', 'login'),
    ('/accounts/logout/', 'logout'),
    # Quiz
    ('/quiz/', 'quiz_start'),
    # Forums
    ('/forums/', 'forum_post'),
    # Search
    ('/search/', 'search'),
    # Downloads / media viewing
    ('/download/', 'download'),
    # Course content (video views matched by checking metadata later)
    ('/course/', 'page_view'),
]


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Tracks student activity by writing to analytics.ActivityLog.

    Runs after AuthenticationMiddleware so request.user is available.
    Only tracks authenticated student users. Wraps everything in
    try/except to never break the request.
    """

    def process_request(self, request):
        """Record request start time for duration calculation."""
        request._activity_start_time = time.monotonic()
        return None

    def process_response(self, request, response):
        """Create ActivityLog entry for student requests."""
        try:
            self._log_activity(request, response)
        except Exception:
            logger.debug("ActivityLog middleware error (non-fatal)", exc_info=True)
        return response

    def _log_activity(self, request, response):
        """Internal method that does the actual logging."""
        # Skip if user not authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return

        # Only track students
        user = request.user
        if not getattr(user, 'is_student', False) and getattr(user, 'role', '') != 'student':
            return

        # Skip non-success responses (4xx, 5xx)
        if response.status_code >= 400:
            return

        # Skip excluded paths
        path = request.path
        if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            return

        # Skip AJAX/API requests to avoid noise (JSON responses)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return
        content_type = response.get('Content-Type', '')
        if 'application/json' in content_type:
            return

        # Determine activity type
        activity_type = self._get_activity_type(request)

        # For POST on quiz, it's quiz_submit not quiz_start
        if activity_type == 'quiz_start' and request.method == 'POST':
            activity_type = 'quiz_submit'

        # For POST on forums, it's forum_post; GET is just page_view
        if activity_type == 'forum_post' and request.method == 'GET':
            activity_type = 'page_view'

        # Calculate duration
        start_time = getattr(request, '_activity_start_time', None)
        duration = None
        if start_time is not None:
            duration = max(1, int(time.monotonic() - start_time))

        # Get student object (lazy import to avoid circular imports)
        from accounts.models import Student
        try:
            student = Student.objects.select_related('student').get(student=user)
        except Student.DoesNotExist:
            return

        # Try to extract course from URL resolver
        course = self._extract_course(request)

        # Get client IP
        ip_address = self._get_client_ip(request)

        # Create the log entry
        from analytics.models import ActivityLog
        ActivityLog.objects.create(
            student=student,
            course=course,
            activity_type=activity_type,
            activity_description=f"{request.method} {path}",
            url=request.build_absolute_uri()[:200],
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            duration_seconds=duration,
            metadata={
                'method': request.method,
                'status_code': response.status_code,
            },
        )

    def _get_activity_type(self, request):
        """Map the request URL to an activity type."""
        path = request.path.lower()
        for url_prefix, act_type in ACTIVITY_TYPE_MAP:
            if url_prefix in path:
                return act_type
        return 'page_view'

    def _extract_course(self, request):
        """Try to extract a Course object from the resolved URL kwargs."""
        try:
            resolver_match = request.resolver_match
            if resolver_match and resolver_match.kwargs:
                # Common patterns: slug, course_slug, pk, course_id
                from course.models import Course
                kwargs = resolver_match.kwargs

                slug = kwargs.get('slug') or kwargs.get('course_slug')
                if slug:
                    return Course.objects.filter(slug=slug).first()

                course_id = kwargs.get('course_id') or kwargs.get('course_pk')
                if course_id:
                    return Course.objects.filter(pk=course_id).first()
        except Exception:
            pass
        return None

    @staticmethod
    def _get_client_ip(request):
        """Get client IP, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

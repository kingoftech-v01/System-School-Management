"""
Celery configuration for School Management System.
Handles async tasks like emails, PDF generation, and scheduled jobs.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'School_System.settings')

# Create Celery app
app = Celery('School_System')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    # ===== Attendance Tasks =====
    'send-attendance-reminders': {
        'task': 'attendance.tasks.send_attendance_reminders',
        'schedule': crontab(hour=18, minute=0),  # 6 PM daily
    },
    'generate-daily-attendance-stats': {
        'task': 'attendance.tasks.generate_daily_attendance_stats',
        'schedule': crontab(hour=0, minute=5),  # Daily at 12:05 AM
    },
    'send-low-attendance-alerts': {
        'task': 'attendance.tasks.send_low_attendance_alerts',
        'schedule': crontab(hour=10, minute=0, day_of_week='friday'),  # Friday at 10 AM
    },

    # ===== Payment Tasks =====
    'send-payment-reminders': {
        'task': 'payments.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),  # 1st of each month at 9 AM
    },
    'process-failed-payments': {
        'task': 'payments.tasks.process_failed_payments',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },

    # ===== Event Tasks =====
    'send-event-reminders': {
        'task': 'events.tasks.send_event_reminders',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },

    # ===== Library Tasks =====
    'send-overdue-book-reminders': {
        'task': 'library.tasks.send_overdue_reminders',
        'schedule': crontab(hour=10, minute=0, day_of_week='1,3,5'),  # Mon, Wed, Fri at 10 AM
    },

    # ===== Articles Tasks =====
    'send-latest-article-newsletter': {
        'task': 'articles.tasks.send_latest_article_newsletter',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),  # Monday at 9 AM
    },
    'cleanup-old-article-drafts': {
        'task': 'articles.tasks.cleanup_old_drafts',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 1st of month at 3 AM
    },

    # ===== Notices Tasks =====
    'check-notice-acknowledgments': {
        'task': 'notices.tasks.check_notice_acknowledgments',
        'schedule': crontab(hour=14, minute=0),  # Daily at 2 PM
    },
    'archive-expired-notices': {
        'task': 'notices.tasks.archive_expired_notices',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },

    # ===== Admissions Tasks =====
    'process-admission-payments': {
        'task': 'admissions.tasks.process_admission_payments',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'send-counseling-reminders': {
        'task': 'admissions.tasks.send_counseling_reminders',
        'schedule': crontab(hour=9, minute=30, day_of_week='1,4'),  # Mon & Thu at 9:30 AM
    },
    'auto-archive-old-applications': {
        'task': 'admissions.tasks.auto_archive_old_applications',
        'schedule': crontab(hour=3, minute=30, day_of_week='sunday'),  # Sunday at 3:30 AM
    },

    # ===== Alumni Tasks =====
    'send-alumni-newsletter': {
        'task': 'alumni.tasks.send_alumni_newsletter',
        'schedule': crontab(hour=10, minute=0, day_of_month=15),  # 15th of month at 10 AM
    },
    'send-upcoming-alumni-event-notifications': {
        'task': 'alumni.tasks.send_upcoming_event_notifications',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),  # Monday at 9 AM
    },
    'generate-donation-receipts': {
        'task': 'alumni.tasks.generate_donation_receipts',
        'schedule': crontab(hour=4, minute=0, day_of_week='tuesday'),  # Tuesday at 4 AM
    },
    'update-alumni-career-data-reminders': {
        'task': 'alumni.tasks.update_alumni_career_data',
        'schedule': crontab(hour=10, minute=0, day_of_month=1),  # 1st of month at 10 AM
    },

    # ===== Forums Tasks =====
    'process-flagged-content': {
        'task': 'forums.tasks.process_flagged_content',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'cleanup-old-threads': {
        'task': 'forums.tasks.cleanup_old_threads',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),  # Sunday at 3 AM
    },
    'update-thread-view-counts': {
        'task': 'forums.tasks.update_thread_view_counts',
        'schedule': crontab(hour=1, minute=30),  # Daily at 1:30 AM
    },

    # ===== Certificates Tasks =====
    'verify-certificate-integrity': {
        'task': 'certificates.tasks.verify_certificate_integrity',
        'schedule': crontab(hour=2, minute=30, day_of_week='sunday'),  # Sunday at 2:30 AM
    },
    'cleanup-expired-verifications': {
        'task': 'certificates.tasks.cleanup_expired_verifications',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 1st of month at 3 AM
    },

    # ===== Grading Tasks =====
    'send-peer-review-reminders': {
        'task': 'grading.tasks.send_peer_review_reminders',
        'schedule': crontab(hour=10, minute=0, day_of_week='3,5'),  # Wed & Fri at 10 AM
    },
    'calculate-rubric-statistics': {
        'task': 'grading.tasks.calculate_rubric_statistics',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    'notify-low-scores': {
        'task': 'grading.tasks.notify_low_scores',
        'schedule': crontab(hour=9, minute=0, day_of_week='friday'),  # Friday at 9 AM
    },

    # ===== Analytics Tasks =====
    'calculate-daily-engagement': {
        'task': 'analytics.tasks.calculate_daily_engagement',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'update-course-completion': {
        'task': 'analytics.tasks.update_course_completion',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'identify-at-risk-students': {
        'task': 'analytics.tasks.identify_at_risk_students',
        'schedule': crontab(hour=5, minute=0, day_of_week='monday,thursday'),  # Mon & Thu at 5 AM
    },
    'send-at-risk-notifications': {
        'task': 'analytics.tasks.send_at_risk_notifications',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),  # Monday at 9 AM
    },
    'generate-engagement-reports': {
        'task': 'analytics.tasks.generate_engagement_reports',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),  # Monday at 8 AM
    },
    'cleanup-old-activity-logs': {
        'task': 'analytics.tasks.cleanup_old_activity_logs',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 1st of month at 3 AM
    },
    'measure-learning-outcomes': {
        'task': 'analytics.tasks.measure_learning_outcomes',
        'schedule': crontab(hour=6, minute=0, day_of_week='sunday'),  # Sunday at 6 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')

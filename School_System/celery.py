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
    # Daily attendance email reminders
    'send-attendance-reminders': {
        'task': 'attendance.tasks.send_attendance_reminders',
        'schedule': crontab(hour=18, minute=0),  # 6 PM daily
    },
    # Payment due reminders
    'send-payment-reminders': {
        'task': 'payments.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0, day_of_month=1),  # 1st of each month
    },
    # Event reminders
    'send-event-reminders': {
        'task': 'events.tasks.send_event_reminders',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    # Library overdue book notifications
    'send-overdue-book-reminders': {
        'task': 'library.tasks.send_overdue_reminders',
        'schedule': crontab(hour=10, minute=0, day_of_week='1,3,5'),  # Mon, Wed, Fri
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')

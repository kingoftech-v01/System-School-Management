"""Tests for events app Celery tasks."""

from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from events.models import Event
from events.tasks import send_event_reminders
from tests.helpers import TestDataMixin


class SendEventRemindersTest(TestDataMixin, TestCase):
    def _create_event(self, **kwargs):
        tenant = kwargs.pop('tenant', None) or self.create_school()
        user = kwargs.pop('created_by', None) or self.create_user(role='direction')
        # Use datetime.now() to match what the task uses
        tomorrow = datetime.now() + timedelta(days=1)
        defaults = {
            'tenant': tenant,
            'title': 'Test Event',
            'description': 'Event description',
            'event_type': 'meeting',
            'start_date': tomorrow,
            'end_date': tomorrow + timedelta(hours=2),
            'target_audience': 'all',
            'created_by': user,
            'send_reminder': True,
            'reminder_sent': False,
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    @patch('events.tasks.send_mail')
    def test_marks_reminder_sent(self, mock_mail):
        event = self._create_event()
        send_event_reminders()
        event.refresh_from_db()
        self.assertTrue(event.reminder_sent)

    @patch('events.tasks.send_mail')
    def test_skips_already_sent(self, mock_mail):
        event = self._create_event(reminder_sent=True)
        send_event_reminders()
        self.assertEqual(mock_mail.call_count, 0)

    @patch('events.tasks.send_mail')
    def test_skips_send_reminder_false(self, mock_mail):
        event = self._create_event(send_reminder=False)
        send_event_reminders()
        self.assertEqual(mock_mail.call_count, 0)

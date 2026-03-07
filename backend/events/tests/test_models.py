"""Tests for events app models."""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from tests.helpers import TestDataMixin


class EventTest(TestDataMixin, TestCase):
    def _create_event(self, **kwargs):
        tenant = kwargs.pop('tenant', None) or self.create_school()
        user = kwargs.pop('created_by', None) or self.create_user(role='direction')
        now = timezone.now()
        defaults = {
            'tenant': tenant,
            'title': 'Test Event',
            'description': 'Event description',
            'event_type': 'meeting',
            'start_date': now + timedelta(days=1),
            'end_date': now + timedelta(days=1, hours=2),
            'target_audience': 'all',
            'created_by': user,
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    def test_create_and_str(self):
        event = self._create_event(title='School Meeting')
        self.assertIn('School Meeting', str(event))

    def test_defaults(self):
        event = self._create_event()
        self.assertTrue(event.send_reminder)
        self.assertFalse(event.reminder_sent)

    def test_event_types(self):
        for etype in ['exam', 'holiday', 'meeting', 'activity', 'ceremony', 'deadline']:
            event = self._create_event(event_type=etype)
            self.assertEqual(event.event_type, etype)

    def test_audience_choices(self):
        for audience in ['all', 'students', 'parents', 'staff']:
            event = self._create_event(target_audience=audience)
            self.assertEqual(event.target_audience, audience)

    def test_location_optional(self):
        event = self._create_event(location='')
        self.assertEqual(event.location, '')

    def test_location_provided(self):
        event = self._create_event(location='Room 101')
        self.assertEqual(event.location, 'Room 101')

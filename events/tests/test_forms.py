"""Tests for events app forms."""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from events.forms import EventForm
from tests.helpers import TestDataMixin


class EventFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        now = timezone.now()
        form = EventForm(data={
            'title': 'Exam Week',
            'description': 'Mid-term exams',
            'event_type': 'exam',
            'start_date': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (now + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'target_audience': 'students',
            'send_reminder': True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = EventForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)

    def test_all_event_types(self):
        now = timezone.now()
        for etype in ['exam', 'holiday', 'meeting', 'activity', 'ceremony', 'deadline']:
            form = EventForm(data={
                'title': f'{etype} event',
                'description': 'Desc',
                'event_type': etype,
                'start_date': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
                'end_date': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
                'target_audience': 'all',
            })
            self.assertTrue(form.is_valid(), f'{etype}: {form.errors}')

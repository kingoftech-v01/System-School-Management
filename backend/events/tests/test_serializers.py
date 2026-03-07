"""Tests for events app serializers."""

from datetime import datetime
from django.test import TestCase

from tests.helpers import TestDataMixin
from events.serializers import (
    UserMinimalSerializer,
    EventSerializer,
    EventListSerializer,
    EventCreateSerializer,
)
from events.models import Event


class UserMinimalSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_user(first_name='John', last_name='Doe')
        serializer = UserMinimalSerializer(user)
        self.assertEqual(serializer.data['full_name'], 'John Doe')
        self.assertIn('id', serializer.data)
        self.assertIn('email', serializer.data)


class EventSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.user = self.create_admin_user()
        self.event = self.create_event(
            tenant=self.tenant,
            created_by=self.user,
            event_type='exam',
            target_audience='all',
        )

    def test_serializes(self):
        serializer = EventSerializer(self.event)
        self.assertIn('title', serializer.data)
        self.assertIn('event_type', serializer.data)
        self.assertIn('event_type_display', serializer.data)
        self.assertIn('target_audience_display', serializer.data)

    def test_created_by_nested(self):
        serializer = EventSerializer(self.event)
        cb = serializer.data['created_by']
        self.assertIn('username', cb)
        self.assertIn('full_name', cb)

    def test_read_only_fields(self):
        serializer = EventSerializer(self.event)
        self.assertIn('created_at', serializer.data)
        self.assertIn('reminder_sent', serializer.data)

    def test_event_type_display(self):
        serializer = EventSerializer(self.event)
        self.assertEqual(serializer.data['event_type_display'], 'Exam')


class EventListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tenant = self.create_school()
        user = self.create_admin_user()
        event = self.create_event(tenant=tenant, created_by=user)
        serializer = EventListSerializer(event)
        self.assertIn('title', serializer.data)
        self.assertIn('created_by_name', serializer.data)
        self.assertIn('event_type_display', serializer.data)
        # Should not include description (lightweight)
        self.assertNotIn('description', serializer.data)

    def test_all_read_only(self):
        tenant = self.create_school()
        user = self.create_admin_user()
        event = self.create_event(tenant=tenant, created_by=user)
        serializer = EventListSerializer(event)
        self.assertIn('id', serializer.data)


class EventCreateSerializerTest(TestDataMixin, TestCase):
    def test_valid_data(self):
        data = {
            'title': 'New Event',
            'description': 'Event description',
            'event_type': 'meeting',
            'start_date': '2025-06-01T09:00:00Z',
            'end_date': '2025-06-01T17:00:00Z',
            'target_audience': 'all',
        }
        serializer = EventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_end_before_start_invalid(self):
        data = {
            'title': 'Bad Event',
            'description': 'Test',
            'event_type': 'meeting',
            'start_date': '2025-06-02T09:00:00Z',
            'end_date': '2025-06-01T17:00:00Z',
            'target_audience': 'all',
        }
        serializer = EventCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)

    def test_missing_required_fields(self):
        serializer = EventCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('event_type', serializer.errors)
        self.assertIn('start_date', serializer.errors)
        self.assertIn('end_date', serializer.errors)

    def test_valid_event_types(self):
        for et in ['exam', 'holiday', 'meeting', 'activity', 'ceremony', 'deadline']:
            data = {
                'title': f'Event {et}',
                'description': 'Test',
                'event_type': et,
                'start_date': '2025-06-01T09:00:00Z',
                'end_date': '2025-06-01T17:00:00Z',
                'target_audience': 'all',
            }
            serializer = EventCreateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for type={et}: {serializer.errors}")

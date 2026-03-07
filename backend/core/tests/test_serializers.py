"""Tests for core app serializers."""

from django.test import TestCase

from core.models import Session, Semester, NewsAndEvents, ActivityLog
from core.serializers import (
    SessionSerializer,
    SemesterSerializer,
    NewsAndEventsSerializer,
    ActivityLogSerializer,
)
from tests.helpers import TestDataMixin


class SessionSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        session = self.create_session()
        data = SessionSerializer(session).data
        self.assertEqual(data['session'], session.session)
        self.assertIn('is_current_session', data)
        self.assertIn('id', data)

    def test_deserialization_valid(self):
        serializer = SessionSerializer(data={
            'session': '2026/2027',
            'is_current_session': False,
        })
        self.assertTrue(serializer.is_valid())

    def test_deserialization_invalid(self):
        serializer = SessionSerializer(data={'session': ''})
        self.assertFalse(serializer.is_valid())


class SemesterSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        semester = self.create_semester()
        data = SemesterSerializer(semester).data
        self.assertEqual(data['semester'], semester.semester)
        self.assertIn('session', data)

    def test_deserialization_valid(self):
        session = self.create_session()
        serializer = SemesterSerializer(data={
            'semester': 'Second',
            'is_current_semester': False,
            'session': session.pk,
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)


class NewsAndEventsSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        item = NewsAndEvents.objects.create(
            title='Serialized News', posted_as='News'
        )
        data = NewsAndEventsSerializer(item).data
        self.assertEqual(data['title'], 'Serialized News')
        self.assertIn('posted_as', data)

    def test_deserialization_valid(self):
        serializer = NewsAndEventsSerializer(data={
            'title': 'New Item',
            'posted_as': 'Event',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ActivityLogSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        log = ActivityLog.objects.create(message='Serialized log')
        data = ActivityLogSerializer(log).data
        self.assertEqual(data['message'], 'Serialized log')
        self.assertIn('created_at', data)

    def test_created_at_read_only(self):
        serializer = ActivityLogSerializer(data={
            'message': 'Test',
            'created_at': '2025-01-01T00:00:00Z',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

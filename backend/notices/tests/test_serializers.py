"""Tests for notices app serializers."""

from django.test import TestCase

from tests.helpers import TestDataMixin
from notices.serializers import (
    UserMinimalSerializer,
    NoticeSerializer,
    NoticeListSerializer,
    NoticeCreateSerializer,
)
from notices.models import Notice


class UserMinimalSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_user(first_name='Alice', last_name='Smith')
        serializer = UserMinimalSerializer(user)
        self.assertEqual(serializer.data['full_name'], 'Alice Smith')
        self.assertIn('id', serializer.data)
        self.assertIn('email', serializer.data)


class NoticeSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_admin_user()
        self.notice = Notice.objects.create(
            title='Test Notice', content='Content here',
            uploaded_by=self.user, priority='high',
        )

    def test_serializes(self):
        serializer = NoticeSerializer(self.notice)
        self.assertIn('title', serializer.data)
        self.assertIn('content', serializer.data)
        self.assertIn('priority_display', serializer.data)
        self.assertIn('uploaded_by', serializer.data)

    def test_uploaded_by_nested(self):
        serializer = NoticeSerializer(self.notice)
        uploader = serializer.data['uploaded_by']
        self.assertIn('username', uploader)
        self.assertIn('full_name', uploader)

    def test_read_only_fields(self):
        serializer = NoticeSerializer(self.notice)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)


class NoticeListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_admin_user()
        notice = Notice.objects.create(
            title='List Notice', content='Content',
            uploaded_by=user, priority='normal',
        )
        serializer = NoticeListSerializer(notice)
        self.assertIn('title', serializer.data)
        self.assertIn('uploaded_by_name', serializer.data)
        self.assertIn('priority_display', serializer.data)
        # Should not include content (lightweight)
        self.assertNotIn('content', serializer.data)


class NoticeCreateSerializerTest(TestDataMixin, TestCase):
    def test_valid_data(self):
        data = {
            'title': 'New Notice',
            'content': 'Important announcement',
            'priority': 'high',
            'is_active': True,
        }
        serializer = NoticeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_title(self):
        data = {'content': 'Content', 'priority': 'normal'}
        serializer = NoticeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_missing_content(self):
        data = {'title': 'Title', 'priority': 'normal'}
        serializer = NoticeCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

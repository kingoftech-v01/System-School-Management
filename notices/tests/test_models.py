"""Tests for notices app models."""

from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from notices.models import NotifyGroup, Notice, NoticeDocument, NoticeResponse
from tests.helpers import TestDataMixin


class NotifyGroupTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        group = NotifyGroup.objects.create(name='Students')
        self.assertEqual(str(group), 'Students')

    def test_unique_name(self):
        NotifyGroup.objects.create(name='Staff')
        with self.assertRaises(Exception):
            NotifyGroup.objects.create(name='Staff')


class NoticeTest(TestDataMixin, TestCase):
    def _create_notice(self, **kwargs):
        user = kwargs.pop('uploaded_by', None) or self.create_user(role='direction')
        defaults = {
            'title': 'Test Notice',
            'content': 'Notice content here',
            'uploaded_by': user,
        }
        defaults.update(kwargs)
        return Notice.objects.create(**defaults)

    def test_create_and_str(self):
        notice = self._create_notice(title='Holiday')
        self.assertEqual(str(notice), 'Holiday')

    def test_defaults(self):
        notice = self._create_notice()
        self.assertEqual(notice.priority, 'normal')
        self.assertTrue(notice.is_active)
        self.assertIsNone(notice.expires_at)

    def test_is_expired_no_date(self):
        notice = self._create_notice()
        self.assertFalse(notice.is_expired())

    def test_is_expired_future(self):
        notice = self._create_notice(expires_at=date.today() + timedelta(days=7))
        self.assertFalse(notice.is_expired())

    def test_is_expired_past(self):
        notice = self._create_notice(expires_at=date.today() - timedelta(days=1))
        self.assertTrue(notice.is_expired())

    def test_priority_choices(self):
        for priority in ['low', 'normal', 'high', 'urgent']:
            notice = self._create_notice(priority=priority)
            self.assertEqual(notice.priority, priority)


class NoticeDocumentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        user = self.create_user(role='direction')
        notice = Notice.objects.create(
            title='Doc Notice', content='Content', uploaded_by=user,
        )
        doc = NoticeDocument.objects.create(
            notice=notice, filename='test.pdf', file_size=1024,
            file='notices/test.pdf',
        )
        self.assertEqual(str(doc), 'test.pdf')


class NoticeResponseTest(TestDataMixin, TestCase):
    def _create_response(self):
        user = self.create_user(role='direction')
        notice = Notice.objects.create(
            title='Resp Notice', content='Content', uploaded_by=user,
        )
        reader = self.create_user(role='student')
        return NoticeResponse.objects.create(notice=notice, user=reader)

    def test_create_and_str(self):
        resp = self._create_response()
        self.assertIn('Resp Notice', str(resp))

    def test_defaults(self):
        resp = self._create_response()
        self.assertFalse(resp.acknowledged)
        self.assertIsNone(resp.acknowledged_at)

    def test_acknowledge(self):
        resp = self._create_response()
        resp.acknowledge()
        resp.refresh_from_db()
        self.assertTrue(resp.acknowledged)
        self.assertIsNotNone(resp.acknowledged_at)

    def test_acknowledge_idempotent(self):
        resp = self._create_response()
        resp.acknowledge()
        first_ack = resp.acknowledged_at
        resp.acknowledge()
        resp.refresh_from_db()
        self.assertEqual(resp.acknowledged_at, first_ack)

"""Tests for notices app Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from notices.models import Notice, NotifyGroup, NoticeResponse
from notices.tasks import (
    send_notice_notifications,
    check_notice_acknowledgments,
    archive_expired_notices,
)
from tests.helpers import TestDataMixin


class ArchiveExpiredNoticesTest(TestDataMixin, TestCase):
    def _create_notice(self, **kwargs):
        author = kwargs.pop('uploaded_by', None) or self.create_user(role='direction')
        defaults = {
            'title': 'Test Notice',
            'content': 'Notice content',
            'priority': 'normal',
            'uploaded_by': author,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Notice.objects.create(**defaults)

    def test_archives_expired(self):
        notice = self._create_notice(
            expires_at=timezone.now() - timedelta(days=1),
        )
        result = archive_expired_notices()
        notice.refresh_from_db()
        self.assertFalse(notice.is_active)
        self.assertIn('1', result)

    def test_does_not_archive_future(self):
        notice = self._create_notice(
            expires_at=timezone.now() + timedelta(days=1),
        )
        archive_expired_notices()
        notice.refresh_from_db()
        self.assertTrue(notice.is_active)

    def test_does_not_archive_no_expiry(self):
        notice = self._create_notice(expires_at=None)
        archive_expired_notices()
        notice.refresh_from_db()
        self.assertTrue(notice.is_active)

    def test_already_inactive(self):
        notice = self._create_notice(
            is_active=False,
            expires_at=timezone.now() - timedelta(days=1),
        )
        result = archive_expired_notices()
        self.assertIn('0', result)


class SendNoticeNotificationsTest(TestDataMixin, TestCase):
    @patch('notices.tasks.send_mail')
    def test_sends_to_group_users(self, mock_mail):
        author = self.create_user(role='direction')
        user1 = self.create_user(role='student')
        user2 = self.create_user(role='student')
        group = NotifyGroup.objects.create(name='Students')
        group.users.add(user1, user2)
        notice = Notice.objects.create(
            title='Test', content='Content',
            priority='normal', uploaded_by=author,
        )
        notice.notify_groups.add(group)

        result = send_notice_notifications(notice.pk)
        self.assertEqual(mock_mail.call_count, 2)
        self.assertEqual(NoticeResponse.objects.count(), 2)

    @patch('notices.tasks.send_mail')
    def test_creates_responses(self, mock_mail):
        author = self.create_user(role='direction')
        user = self.create_user(role='student')
        group = NotifyGroup.objects.create(name='All')
        group.users.add(user)
        notice = Notice.objects.create(
            title='Test', content='Content',
            priority='normal', uploaded_by=author,
        )
        notice.notify_groups.add(group)

        send_notice_notifications(notice.pk)
        self.assertTrue(NoticeResponse.objects.filter(notice=notice, user=user).exists())


class CheckNoticeAcknowledgmentsTest(TestDataMixin, TestCase):
    @patch('notices.tasks.send_mail')
    def test_sends_reminders(self, mock_mail):
        author = self.create_user(role='direction')
        user = self.create_user(role='student')
        notice = Notice.objects.create(
            title='Ack Me', content='Content',
            priority='normal', uploaded_by=author, is_active=True,
        )
        NoticeResponse.objects.create(
            notice=notice, user=user, acknowledged=False,
        )
        result = check_notice_acknowledgments()
        self.assertEqual(mock_mail.call_count, 1)
        self.assertIn('1', result)

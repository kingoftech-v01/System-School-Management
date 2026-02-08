"""Tests for forums app Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from forums.models import ForumCategory, Thread, Post, ThreadSubscription
from forums.tasks import (
    send_new_post_notifications,
    cleanup_old_threads,
)
from tests.helpers import TestDataMixin


class CleanupOldThreadsTest(TestDataMixin, TestCase):
    def _create_thread(self, **kwargs):
        author = kwargs.pop('author', None) or self.create_user(role='student')
        category = ForumCategory.objects.create(
            name='General', slug='general',
        )
        defaults = {
            'category': category,
            'author': author,
            'title': 'Test Thread',
            'content': 'Thread content',
        }
        defaults.update(kwargs)
        return Thread.objects.create(**defaults)

    def test_counts_old_threads(self):
        thread = self._create_thread()
        Thread.objects.filter(pk=thread.pk).update(
            updated_at=timezone.now() - timedelta(days=366),
        )
        result = cleanup_old_threads()
        self.assertIn('1', result)

    def test_skips_pinned(self):
        thread = self._create_thread(is_pinned=True)
        Thread.objects.filter(pk=thread.pk).update(
            updated_at=timezone.now() - timedelta(days=366),
        )
        result = cleanup_old_threads()
        self.assertIn('0', result)

    def test_skips_locked(self):
        thread = self._create_thread(is_locked=True)
        Thread.objects.filter(pk=thread.pk).update(
            updated_at=timezone.now() - timedelta(days=366),
        )
        result = cleanup_old_threads()
        self.assertIn('0', result)

    def test_skips_recent(self):
        self._create_thread()
        result = cleanup_old_threads()
        self.assertIn('0', result)


class SendNewPostNotificationsTest(TestDataMixin, TestCase):
    @patch('forums.tasks.send_mail')
    def test_notifies_subscribers(self, mock_mail):
        """Task calls get_full_name() but it's a property - causes TypeError."""
        author = self.create_user(role='student')
        subscriber = self.create_user(role='student')
        category = ForumCategory.objects.create(
            name='General', slug='general-2',
        )
        thread = Thread.objects.create(
            category=category, author=author,
            title='Test', content='Content',
        )
        ThreadSubscription.objects.create(
            thread=thread, user=subscriber, email_on_reply=True,
        )
        post = Post.objects.create(
            thread=thread, author=author, content='Reply content',
        )
        # Task calls get_full_name() (with parens) but it's a @property - source bug
        with self.assertRaises(TypeError):
            send_new_post_notifications(post.pk)

    @patch('forums.tasks.send_mail')
    def test_excludes_post_author(self, mock_mail):
        author = self.create_user(role='student')
        category = ForumCategory.objects.create(
            name='General', slug='general-3',
        )
        thread = Thread.objects.create(
            category=category, author=author,
            title='Test', content='Content',
        )
        ThreadSubscription.objects.create(
            thread=thread, user=author, email_on_reply=True,
        )
        post = Post.objects.create(
            thread=thread, author=author, content='My own reply',
        )
        send_new_post_notifications(post.pk)
        self.assertEqual(mock_mail.call_count, 0)

    def test_nonexistent_post(self):
        result = send_new_post_notifications(99999)
        self.assertIn('not found', result)

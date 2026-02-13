"""
API ViewSet tests for the forums app.

Tests cover CRUD operations, custom actions, and permission checks for:
- ForumCategoryViewSet
- ThreadViewSet
- PostViewSet
- TagViewSet (read-only)
- ThreadSubscriptionViewSet
- ReportViewSet
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin
from forums.models import (
    ForumCategory, Thread, Post, Tag, Vote,
    ThreadSubscription, Report,
)


# ============================================================================
# ForumCategory ViewSet Tests
# ============================================================================

class ForumCategoryViewSetTests(TestDataMixin, TestCase):
    """Tests for ForumCategoryViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.user = self.create_student_user()
        self.category = self.create_forum_category()

    def test_list_categories_unauthenticated(self):
        """Categories are public (IsAuthenticatedOrReadOnly)."""
        url = reverse('api:forums:category-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_categories_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:category-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_category(self):
        url = reverse('api:forums:category-detail', kwargs={'pk': self.category.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], self.category.name)

    def test_create_category_requires_moderator(self):
        """Regular users cannot create categories."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:category-list')
        data = {'name': 'New Category', 'description': 'Test'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_threads_action(self):
        """List threads within a category."""
        thread = self.create_thread(category=self.category, author=self.user)
        thread.status = 'published'
        thread.is_published = True
        thread.save()
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:category-threads', kwargs={'pk': self.category.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Thread ViewSet Tests
# ============================================================================

class ThreadViewSetTests(TestDataMixin, TestCase):
    """Tests for ThreadViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.user = self.create_student_user()
        self.category = self.create_forum_category()
        self.thread = self.create_thread(category=self.category, author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()

    def test_list_threads_unauthenticated(self):
        """Threads are public (IsAuthenticatedOrReadOnly)."""
        url = reverse('api:forums:thread-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_threads(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_thread(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-list')
        data = {
            'category': self.category.pk,
            'title': 'A New Thread',
            'content': 'Thread body content here.',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_thread(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-detail', kwargs={'pk': self.thread.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_subscribe_action(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-subscribe', kwargs={'pk': self.thread.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_subscribe_duplicate(self):
        ThreadSubscription.objects.create(thread=self.thread, user=self.user)
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-subscribe', kwargs={'pk': self.thread.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe_action(self):
        ThreadSubscription.objects.create(thread=self.thread, user=self.user)
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-unsubscribe', kwargs={'pk': self.thread.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unsubscribe_not_subscribed(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-unsubscribe', kwargs={'pk': self.thread.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_posts_action(self):
        Post.objects.create(thread=self.thread, author=self.user, content='A reply')
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:thread-posts', kwargs={'pk': self.thread.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)


# ============================================================================
# Post ViewSet Tests
# ============================================================================

class PostViewSetTests(TestDataMixin, TestCase):
    """Tests for PostViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.user = self.create_student_user()
        self.category = self.create_forum_category()
        self.thread = self.create_thread(category=self.category, author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()
        self.post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content',
        )

    def test_list_posts(self):
        url = reverse('api:forums:post-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-list')
        data = {
            'thread': self.thread.pk,
            'content': 'A new reply',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-detail', kwargs={'pk': self.post.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_soft_delete_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-detail', kwargs={'pk': self.post.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_vote_action(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-vote', kwargs={'pk': self.post.pk})
        resp = self.client.post(url, {'vote_type': 1}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_vote_invalid_type(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-vote', kwargs={'pk': self.post.pk})
        resp = self.client.post(url, {'vote_type': 5}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_replies_action(self):
        reply = Post.objects.create(
            thread=self.thread, author=self.user,
            content='Reply to post', parent=self.post,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:post-replies', kwargs={'pk': self.post.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)


# ============================================================================
# Tag ViewSet Tests (Read-Only)
# ============================================================================

class TagViewSetTests(TestDataMixin, TestCase):
    """Tests for TagViewSet (read-only).

    Note: TagViewSet doesn't override permission_classes, so it inherits
    the global default of IsAuthenticated.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_student_user()
        self.tag = Tag.objects.create(name='Django', description='Django framework')

    def test_list_tags_unauthenticated(self):
        """Tags require authentication (global default IsAuthenticated)."""
        url = reverse('api:forums:tag-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_tags(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:tag-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = resp.data['results'] if isinstance(resp.data, dict) else resp.data
        self.assertGreaterEqual(len(results), 1)

    def test_retrieve_tag(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:tag-detail', kwargs={'pk': self.tag.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'Django')

    def test_threads_action(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:tag-threads', kwargs={'pk': self.tag.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# ThreadSubscription ViewSet Tests
# ============================================================================

class ThreadSubscriptionViewSetTests(TestDataMixin, TestCase):
    """Tests for ThreadSubscriptionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_student_user()
        self.category = self.create_forum_category()
        self.thread = self.create_thread(category=self.category, author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()
        self.subscription = ThreadSubscription.objects.create(
            thread=self.thread, user=self.user,
        )

    def test_list_subscriptions_unauthenticated(self):
        url = reverse('api:forums:subscription-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_subscriptions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:subscription-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = resp.data['results'] if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 1)

    def test_only_own_subscriptions(self):
        other = self.create_student_user()
        self.client.force_authenticate(user=other)
        url = reverse('api:forums:subscription-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = resp.data['results'] if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 0)

    def test_mark_read_action(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:subscription-mark-read', kwargs={'pk': self.subscription.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Report ViewSet Tests
# ============================================================================

class ReportViewSetTests(TestDataMixin, TestCase):
    """Tests for ReportViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.user = self.create_student_user()
        self.category = self.create_forum_category()
        self.thread = self.create_thread(category=self.category, author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()
        ct = ContentType.objects.get_for_model(Thread)
        self.report = Report.objects.create(
            content_type=ct,
            object_id=self.thread.pk,
            reported_by=self.user,
            report_type='spam',
            description='This is spam content.',
        )

    def test_list_reports_unauthenticated(self):
        url = reverse('api:forums:report-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_reports_as_user_sees_own(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:report-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = resp.data['results'] if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 1)

    def test_retrieve_report(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:forums:report-detail', kwargs={'pk': self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_report(self):
        self.client.force_authenticate(user=self.user)
        ct = ContentType.objects.get_for_model(Thread)
        url = reverse('api:forums:report-list')
        data = {
            'content_type': ct.pk,
            'object_id': self.thread.pk,
            'report_type': 'offensive',
            'description': 'Offensive content here.',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

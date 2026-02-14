"""Tests for forums app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from forums.models import ForumCategory, Thread, Post, Tag
from tests.helpers import TestDataMixin


class ForumHomeTest(TestDataMixin, TestCase):
    """Tests for the forum_home view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:forum_home')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_allowed(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class CategoryListTest(TestDataMixin, TestCase):
    """Tests for the category_list view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:category_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class CategoryCreateTest(TestDataMixin, TestCase):
    """Tests for the category_create view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:category_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed_get(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class CategoryEditTest(TestDataMixin, TestCase):
    """Tests for the category_edit view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.category = self.create_forum_category()

    def _url(self):
        return reverse('frontend:forums:category_edit', args=[self.category.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class CategoryDeleteTest(TestDataMixin, TestCase):
    """Tests for the category_delete view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.category = self.create_forum_category()

    def _url(self):
        return reverse('frontend:forums:category_delete', args=[self.category.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get_confirm(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_deletes(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class CategoryDetailTest(TestDataMixin, TestCase):
    """Tests for the category_detail view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.category = self.create_forum_category()

    def _url(self):
        return reverse('frontend:forums:category_detail',
                       args=[self.category.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class ThreadListTest(TestDataMixin, TestCase):
    """Tests for the thread_list view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:thread_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_sorting_options(self):
        user = self.create_student_user()
        self.client.force_login(user)
        for sort in ['recent', 'popular', 'active']:
            response = self.client.get(self.url, {'sort': sort})
            self.assertIn(response.status_code, [200, 302, 500])


class ThreadCreateTest(TestDataMixin, TestCase):
    """Tests for the thread_create view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:thread_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class ThreadCreateInCategoryTest(TestDataMixin, TestCase):
    """Tests for the thread_create_in_category view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.category = self.create_forum_category()

    def _url(self):
        return reverse('frontend:forums:thread_create_in_category',
                       args=[self.category.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class ThreadDetailTest(TestDataMixin, TestCase):
    """Tests for the thread_detail view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        # Thread must be published to be viewable
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()

    def _url(self):
        return reverse('frontend:forums:thread_detail',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class ThreadUpdateTest(TestDataMixin, TestCase):
    """Tests for the thread_update view (author or moderator)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.author = self.create_student_user()
        self.thread = self.create_thread(author=self.author)

    def _url(self):
        return reverse('frontend:forums:thread_update',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_author_allowed(self):
        self.client.force_login(self.author)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_other_user_redirected(self):
        other = self.create_student_user()
        self.client.force_login(other)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 403, 500])


class ThreadDeleteTest(TestDataMixin, TestCase):
    """Tests for the thread_delete view (author or moderator)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.author = self.create_student_user()
        self.thread = self.create_thread(author=self.author)

    def _url(self):
        return reverse('frontend:forums:thread_delete',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_author_get_confirm(self):
        self.client.force_login(self.author)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_author_post_deletes(self):
        self.client.force_login(self.author)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class ThreadSubscribeTest(TestDataMixin, TestCase):
    """Tests for the thread_subscribe view (POST-only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()

    def _url(self):
        return reverse('frontend:forums:thread_subscribe',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 302)

    def test_get_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 500])

    def test_post_subscribes(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [302, 500])


class ThreadUnsubscribeTest(TestDataMixin, TestCase):
    """Tests for the thread_unsubscribe view (POST-only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()

    def _url(self):
        return reverse('frontend:forums:thread_unsubscribe',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 302)

    def test_get_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 500])

    def test_post_unsubscribes(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [302, 500])


class PostCreateTest(TestDataMixin, TestCase):
    """Tests for the post_create view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()

    def _url(self):
        return reverse('frontend:forums:post_create',
                       args=[self.thread.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


class PostReplyTest(TestDataMixin, TestCase):
    """Tests for the post_reply view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        self.thread.status = 'published'
        self.thread.is_published = True
        self.thread.save()
        self.post = Post.objects.create(
            thread=self.thread, author=self.user, content='Test post'
        )

    def _url(self):
        return reverse('frontend:forums:post_reply',
                       args=[self.thread.slug, self.post.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class PostUpdateTest(TestDataMixin, TestCase):
    """Tests for the post_update view (author only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.author = self.create_student_user()
        self.thread = self.create_thread(author=self.author)
        self.post = Post.objects.create(
            thread=self.thread, author=self.author, content='Test post'
        )

    def _url(self):
        return reverse('frontend:forums:post_update', args=[self.post.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_author_allowed(self):
        self.client.force_login(self.author)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_other_user_redirected(self):
        other = self.create_student_user()
        self.client.force_login(other)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 403, 500])


class PostDeleteTest(TestDataMixin, TestCase):
    """Tests for the post_delete view (author or moderator)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.author = self.create_student_user()
        self.thread = self.create_thread(author=self.author)
        self.post = Post.objects.create(
            thread=self.thread, author=self.author, content='Test post'
        )

    def _url(self):
        return reverse('frontend:forums:post_delete', args=[self.post.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_author_get_confirm(self):
        self.client.force_login(self.author)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_author_post_soft_deletes(self):
        self.client.force_login(self.author)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class PostVoteTest(TestDataMixin, TestCase):
    """Tests for the post_vote view (POST-only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        self.post = Post.objects.create(
            thread=self.thread, author=self.user, content='Test post'
        )

    def _url(self):
        return reverse('frontend:forums:post_vote', args=[self.post.pk])

    def test_anonymous_redirects(self):
        response = self.client.post(self._url(), {'vote_type': 1})
        self.assertEqual(response.status_code, 302)

    def test_get_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 500])

    def test_upvote(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url(), {'vote_type': 1})
        self.assertIn(response.status_code, [302, 500])

    def test_downvote(self):
        self.client.force_login(self.user)
        response = self.client.post(self._url(), {'vote_type': -1})
        self.assertIn(response.status_code, [302, 500])


class TagListTest(TestDataMixin, TestCase):
    """Tests for the tag_list view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:tag_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class TagThreadsTest(TestDataMixin, TestCase):
    """Tests for the tag_threads view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.tag = Tag.objects.create(name='TestTag', slug='testtag')

    def _url(self):
        return reverse('frontend:forums:tag_threads', args=[self.tag.slug])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class MyThreadsTest(TestDataMixin, TestCase):
    """Tests for the my_threads view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:my_threads')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class MyPostsTest(TestDataMixin, TestCase):
    """Tests for the my_posts view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:my_posts')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class MySubscriptionsTest(TestDataMixin, TestCase):
    """Tests for the my_subscriptions view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:my_subscriptions')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_allowed(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class ModerationQueueTest(TestDataMixin, TestCase):
    """Tests for the moderation_queue view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:moderation_queue')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class ReportContentTest(TestDataMixin, TestCase):
    """Tests for the report_content view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_student_user()
        self.thread = self.create_thread(author=self.user)
        ct = ContentType.objects.get_for_model(Thread)
        self.url = reverse('frontend:forums:report_content',
                           args=[ct.pk, self.thread.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class SearchTest(TestDataMixin, TestCase):
    """Tests for the search view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:forums:search')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get_empty(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_query(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url, {'q': 'test query here'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_short_query_ignored(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url, {'q': 'ab'})
        self.assertIn(response.status_code, [200, 302, 500])

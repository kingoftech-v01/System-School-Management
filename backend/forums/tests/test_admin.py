"""Tests for forums admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from forums.models import ForumCategory, Thread, Post, Vote, Tag, ThreadSubscription, Report
from forums.admin import (
    ForumCategoryAdmin, ThreadAdmin, PostAdmin,
    VoteAdmin, TagAdmin, ThreadSubscriptionAdmin, ReportAdmin,
)


class ForumsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all forums models are registered in the admin."""

    def test_forum_category_registered(self):
        self.assertIn(ForumCategory, admin.site._registry)

    def test_thread_registered(self):
        self.assertIn(Thread, admin.site._registry)

    def test_post_registered(self):
        self.assertIn(Post, admin.site._registry)

    def test_vote_registered(self):
        self.assertIn(Vote, admin.site._registry)

    def test_tag_registered(self):
        self.assertIn(Tag, admin.site._registry)

    def test_thread_subscription_registered(self):
        self.assertIn(ThreadSubscription, admin.site._registry)

    def test_report_registered(self):
        self.assertIn(Report, admin.site._registry)


class ForumCategoryAdminTest(TestDataMixin, TestCase):
    """Test ForumCategoryAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ForumCategoryAdmin(ForumCategory, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('name', 'order', 'is_active', 'requires_approval', 'get_thread_count', 'get_post_count', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_active', 'requires_approval', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('name', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('name',)})

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'activate_categories'))
        self.assertTrue(hasattr(self.admin, 'deactivate_categories'))

    def test_get_thread_count(self):
        category = self.create_forum_category()
        count = self.admin.get_thread_count(category)
        self.assertEqual(count, 0)


class ThreadAdminTest(TestDataMixin, TestCase):
    """Test ThreadAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ThreadAdmin(Thread, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = (
            'title', 'category', 'author', 'status', 'is_pinned', 'is_locked', 'is_featured',
            'view_count', 'reply_count', 'last_activity_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'is_published', 'is_pinned', 'is_locked', 'is_featured', 'category', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'content', 'author__username', 'author__email')
        self.assertEqual(self.admin.search_fields, expected)

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('title',)})

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')

    def test_actions_exist(self):
        action_names = [
            'publish_threads', 'pin_threads', 'unpin_threads',
            'lock_threads', 'unlock_threads', 'feature_threads', 'archive_threads',
        ]
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_pin_threads_action(self):
        thread = self.create_thread()
        qs = Thread.objects.filter(pk=thread.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.pin_threads(request, qs)
        thread.refresh_from_db()
        self.assertTrue(thread.is_pinned)


class PostAdminTest(TestDataMixin, TestCase):
    """Test PostAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = PostAdmin(Post, self.site)

    def test_list_display(self):
        expected = (
            'get_short_content', 'thread', 'author', 'parent', 'upvotes', 'downvotes',
            'get_score', 'is_deleted', 'is_edited', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_deleted', 'is_edited', 'created_at', 'thread__category')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'soft_delete_posts'))
        self.assertTrue(hasattr(self.admin, 'restore_posts'))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')


class VoteAdminTest(TestDataMixin, TestCase):
    """Test VoteAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = VoteAdmin(Vote, self.site)

    def test_list_display(self):
        expected = ('user', 'post', 'get_vote_display', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('vote_type', 'created_at'))


class TagAdminTest(TestDataMixin, TestCase):
    """Test TagAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = TagAdmin(Tag, self.site)

    def test_list_display(self):
        expected = ('name', 'get_color_badge', 'use_count', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        expected = ('name', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('name',)})


class ThreadSubscriptionAdminTest(TestDataMixin, TestCase):
    """Test ThreadSubscriptionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ThreadSubscriptionAdmin(ThreadSubscription, self.site)

    def test_list_display(self):
        expected = ('user', 'thread', 'email_on_reply', 'has_unread', 'subscribed_at', 'last_read_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('email_on_reply', 'subscribed_at'))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'subscribed_at')


class ReportAdminTest(TestDataMixin, TestCase):
    """Test ReportAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ReportAdmin(Report, self.site)

    def test_list_display(self):
        expected = ('get_content_type', 'reported_by', 'report_type', 'status', 'reviewed_by', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('report_type', 'status', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        action_names = ['mark_reviewing', 'mark_resolved', 'mark_dismissed']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')

"""Tests for articles admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from articles.models import Category, Article, Comment, Like, Newsletter, NewsletterSent
from articles.admin import (
    CategoryAdmin, ArticleAdmin, CommentAdmin,
    LikeAdmin, NewsletterAdmin, NewsletterSentAdmin,
)


class ArticlesAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all articles models are registered in the admin."""

    def test_category_registered(self):
        self.assertIn(Category, admin.site._registry)

    def test_article_registered(self):
        self.assertIn(Article, admin.site._registry)

    def test_comment_registered(self):
        self.assertIn(Comment, admin.site._registry)

    def test_like_registered(self):
        self.assertIn(Like, admin.site._registry)

    def test_newsletter_registered(self):
        self.assertIn(Newsletter, admin.site._registry)

    def test_newsletter_sent_registered(self):
        self.assertIn(NewsletterSent, admin.site._registry)


class CategoryAdminTest(TestDataMixin, TestCase):
    """Test CategoryAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CategoryAdmin(Category, self.site)

    def test_list_display(self):
        expected = ['name', 'parent', 'is_active', 'get_article_count', 'created_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ['is_active', 'created_at'])

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ['name', 'description'])

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('name',)})


class ArticleAdminTest(TestDataMixin, TestCase):
    """Test ArticleAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ArticleAdmin(Article, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ['title', 'author', 'status', 'is_featured', 'is_pinned', 'views_count', 'published_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ['status', 'is_featured', 'is_pinned', 'created_at', 'categories']
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ['title', 'summary', 'content']
        self.assertEqual(self.admin.search_fields, expected)

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('title',)})

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')

    def test_actions_exist(self):
        action_names = ['publish_articles', 'feature_articles', 'archive_articles']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_publish_articles_action(self):
        article = self.create_article()
        qs = Article.objects.filter(pk=article.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.publish_articles(request, qs)
        article.refresh_from_db()
        self.assertEqual(article.status, 'published')

    def test_archive_articles_action(self):
        article = self.create_article()
        qs = Article.objects.filter(pk=article.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.archive_articles(request, qs)
        article.refresh_from_db()
        self.assertEqual(article.status, 'archived')


class CommentAdminTest(TestDataMixin, TestCase):
    """Test CommentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CommentAdmin(Comment, self.site)

    def test_list_display(self):
        expected = ['article', 'author', 'status', 'created_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ['status', 'created_at'])

    def test_search_fields(self):
        expected = ['content', 'author__username', 'article__title']
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        action_names = ['approve_comments', 'reject_comments', 'mark_as_spam']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))


class LikeAdminTest(TestDataMixin, TestCase):
    """Test LikeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = LikeAdmin(Like, self.site)

    def test_list_display(self):
        expected = ['user', 'article', 'created_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ['created_at'])


class NewsletterAdminTest(TestDataMixin, TestCase):
    """Test NewsletterAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NewsletterAdmin(Newsletter, self.site)

    def test_list_display(self):
        expected = ['email', 'is_subscribed', 'is_verified', 'frequency', 'subscribed_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ['is_subscribed', 'is_verified', 'frequency', 'subscribed_at']
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'verify_subscriptions'))
        self.assertTrue(hasattr(self.admin, 'unsubscribe_users'))


class NewsletterSentAdminTest(TestDataMixin, TestCase):
    """Test NewsletterSentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NewsletterSentAdmin(NewsletterSent, self.site)

    def test_list_display(self):
        expected = ['subject', 'recipients_count', 'sent_by', 'sent_at']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ['sent_at'])

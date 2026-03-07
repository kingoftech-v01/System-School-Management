"""Tests for articles app Celery tasks."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from articles.models import Article, Category, Comment, Like
from articles.tasks import (
    cleanup_draft_articles,
    moderate_pending_comments,
    update_article_statistics,
)
from tests.helpers import TestDataMixin


class CleanupDraftArticlesTest(TestDataMixin, TestCase):
    def _create_article(self, **kwargs):
        author = kwargs.pop('author', None) or self.create_user(role='direction')
        category = kwargs.pop('category', None) or Category.objects.create(
            name='Test Cat', slug='test-cat',
        )
        defaults = {
            'title': 'Test Article',
            'content': 'Content',
            'author': author,
            'status': 'draft',
        }
        defaults.update(kwargs)
        article = Article.objects.create(**defaults)
        article.categories.add(category)
        return article

    def test_deletes_old_drafts(self):
        article = self._create_article()
        Article.objects.filter(pk=article.pk).update(
            created_at=timezone.now() - timedelta(days=91),
        )
        result = cleanup_draft_articles()
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())
        self.assertIn('1', result)

    def test_keeps_recent_drafts(self):
        article = self._create_article()
        cleanup_draft_articles()
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())

    def test_keeps_published(self):
        article = self._create_article(status='published')
        Article.objects.filter(pk=article.pk).update(
            created_at=timezone.now() - timedelta(days=91),
        )
        cleanup_draft_articles()
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())


class ModeratePendingCommentsTest(TestDataMixin, TestCase):
    def _make_article(self):
        author = self.create_user(role='direction')
        category = Category.objects.create(name='C', slug='c')
        article = Article.objects.create(
            title='A', content='Content', author=author, status='published',
        )
        article.categories.add(category)
        return article

    def test_auto_approves_trusted_user(self):
        article = self._make_article()
        user = self.create_user(role='student')
        for i in range(5):
            Comment.objects.create(
                article=article, author=user,
                content=f'Comment {i}', status='approved',
            )
        pending = Comment.objects.create(
            article=article, author=user,
            content='New comment', status='pending',
        )
        moderate_pending_comments()
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'approved')

    def test_flags_spam(self):
        article = self._make_article()
        user = self.create_user(role='student')
        comment = Comment.objects.create(
            article=article, author=user,
            content='Buy cheap viagra now', status='pending',
        )
        moderate_pending_comments()
        comment.refresh_from_db()
        self.assertEqual(comment.status, 'spam')

    def test_flags_casino_spam(self):
        article = self._make_article()
        user = self.create_user(role='student')
        comment = Comment.objects.create(
            article=article, author=user,
            content='Best casino deals online', status='pending',
        )
        moderate_pending_comments()
        comment.refresh_from_db()
        self.assertEqual(comment.status, 'spam')

    def test_leaves_unknown_pending(self):
        article = self._make_article()
        user = self.create_user(role='student')
        comment = Comment.objects.create(
            article=article, author=user,
            content='Regular comment here', status='pending',
        )
        moderate_pending_comments()
        comment.refresh_from_db()
        self.assertEqual(comment.status, 'pending')


class UpdateArticleStatisticsTest(TestDataMixin, TestCase):
    def test_updates_counts(self):
        author = self.create_user(role='direction')
        category = Category.objects.create(name='C', slug='c')
        article = Article.objects.create(
            title='A', content='Content', author=author, status='published',
        )
        article.categories.add(category)
        user = self.create_user(role='student')
        Like.objects.create(article=article, user=user)
        Comment.objects.create(
            article=article, author=user,
            content='Nice', status='approved',
        )
        Comment.objects.create(
            article=article, author=user,
            content='Spam', status='pending',
        )
        update_article_statistics()
        article.refresh_from_db()
        self.assertEqual(article.likes_count, 1)
        self.assertEqual(article.comments_count, 1)

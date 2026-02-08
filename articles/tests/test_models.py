"""Tests for articles app models."""

from django.test import TestCase
from django.utils import timezone

from articles.models import Category, Article, Comment, Like, Newsletter, NewsletterSent
from tests.helpers import TestDataMixin


class CategoryTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        cat = Category.objects.create(name='Technology')
        self.assertEqual(str(cat), 'Technology')

    def test_defaults(self):
        cat = Category.objects.create(name='Test')
        self.assertTrue(cat.is_active)

    def test_parent_child(self):
        parent = Category.objects.create(name='Science')
        child = Category.objects.create(name='Physics', parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.get_children())


class ArticleTest(TestDataMixin, TestCase):
    def _create_article(self, **kwargs):
        user = kwargs.pop('author', None) or self.create_user(role='direction')
        defaults = {
            'title': 'Test Article',
            'summary': 'A brief summary of the article content.',
            'content': 'Full article content with enough words for reading time calc.',
            'author': user,
        }
        defaults.update(kwargs)
        return Article.objects.create(**defaults)

    def test_create_and_str(self):
        article = self._create_article(title='My Article')
        self.assertEqual(str(article), 'My Article')

    def test_defaults(self):
        article = self._create_article()
        self.assertEqual(article.status, 'draft')
        self.assertFalse(article.is_featured)
        self.assertFalse(article.is_pinned)
        self.assertEqual(article.views_count, 0)
        self.assertEqual(article.likes_count, 0)
        self.assertEqual(article.comments_count, 0)

    def test_published_at_set_on_publish(self):
        article = self._create_article(status='published')
        self.assertIsNotNone(article.published_at)

    def test_published_at_not_set_for_draft(self):
        article = self._create_article(status='draft')
        self.assertIsNone(article.published_at)

    def test_get_reading_time(self):
        # 200 words = 1 minute
        content = ' '.join(['word'] * 400)
        article = self._create_article(content=content)
        self.assertEqual(article.get_reading_time(), 2)

    def test_get_reading_time_min_1(self):
        article = self._create_article(content='short')
        self.assertEqual(article.get_reading_time(), 1)

    def test_queryset_published(self):
        user = self.create_user(role='direction')
        self._create_article(author=user, status='published')
        self._create_article(author=user, status='draft')
        self.assertEqual(Article.objects.get_queryset().published().count(), 1)

    def test_queryset_draft(self):
        user = self.create_user(role='direction')
        self._create_article(author=user, status='draft')
        self.assertEqual(Article.objects.get_queryset().draft().count(), 1)


class CommentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        user = self.create_user(role='direction')
        article = Article.objects.create(
            title='Art', summary='Sum', content='Content', author=user,
        )
        comment = Comment.objects.create(
            article=article, author=user, content='Nice article!',
        )
        self.assertIn('Comment by', str(comment))

    def test_defaults(self):
        user = self.create_user(role='direction')
        article = Article.objects.create(
            title='Art2', summary='Sum', content='Content', author=user,
        )
        comment = Comment.objects.create(
            article=article, author=user, content='Good',
        )
        self.assertEqual(comment.status, 'pending')


class LikeTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        user = self.create_user(role='direction')
        article = Article.objects.create(
            title='Liked', summary='Sum', content='Content', author=user,
        )
        like = Like.objects.create(article=article, user=user)
        self.assertIn('likes', str(like))

    def test_unique_together(self):
        user = self.create_user(role='direction')
        article = Article.objects.create(
            title='Unique', summary='Sum', content='Content', author=user,
        )
        Like.objects.create(article=article, user=user)
        with self.assertRaises(Exception):
            Like.objects.create(article=article, user=user)


class NewsletterTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        nl = Newsletter.objects.create(email='test@example.com')
        self.assertEqual(str(nl), 'test@example.com')

    def test_defaults(self):
        nl = Newsletter.objects.create(email='test2@example.com')
        self.assertTrue(nl.is_subscribed)
        self.assertFalse(nl.is_verified)
        self.assertEqual(nl.frequency, 'weekly')

    def test_unsubscribe(self):
        nl = Newsletter.objects.create(email='unsub@example.com')
        nl.unsubscribe()
        nl.refresh_from_db()
        self.assertFalse(nl.is_subscribed)
        self.assertIsNotNone(nl.unsubscribed_at)

    def test_unique_email(self):
        Newsletter.objects.create(email='dup@example.com')
        with self.assertRaises(Exception):
            Newsletter.objects.create(email='dup@example.com')


class NewsletterSentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        user = self.create_user(role='direction')
        ns = NewsletterSent.objects.create(
            subject='Weekly Update', recipients_count=50, sent_by=user,
        )
        self.assertIn('Weekly Update', str(ns))

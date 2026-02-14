"""
Deep tests for articles tasks.
Calls tasks directly (not .delay()), mocks external dependencies.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from articles.models import Article, Newsletter, NewsletterSent, Comment, Like, Category
from tests.helpers import TestDataMixin


class ArticlesTaskMixin(TestDataMixin):
    """Shared helpers for articles task tests."""

    def _make_newsletter_subscriber(self, **kwargs):
        defaults = {
            'email': f'sub{id(kwargs)}@test.com',
            'is_subscribed': True,
            'is_verified': True,
            'frequency': 'weekly',
        }
        defaults.update(kwargs)
        return Newsletter.objects.create(**defaults)


class TestSendArticleNotification(ArticlesTaskMixin, TestCase):
    """Tests for send_article_notification task."""

    @patch('articles.tasks.render_to_string', return_value='<html>Test</html>')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_sends_to_subscribers(self, mock_email_cls, mock_render):
        from articles.tasks import send_article_notification

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        # Set published_at
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        article.refresh_from_db()

        sub = self._make_newsletter_subscriber(email='test1@test.com')

        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        result = send_article_notification(article.pk)
        self.assertIn('Sent 1 notifications', result)
        mock_msg.send.assert_called_once()

    @patch('articles.tasks.render_to_string', return_value='<html>Test</html>')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_no_subscribers(self, mock_email_cls, mock_render):
        from articles.tasks import send_article_notification

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        result = send_article_notification(article.pk)
        self.assertIsNone(result)

    def test_article_not_found_raises(self):
        from articles.tasks import send_article_notification

        with self.assertRaises(Article.DoesNotExist):
            send_article_notification(99999)

    @patch('articles.tasks.render_to_string', return_value='<html>Test</html>')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_draft_article_not_found(self, mock_email_cls, mock_render):
        from articles.tasks import send_article_notification

        author = self.create_user()
        article = self.create_article(author=author, status='draft')
        with self.assertRaises(Article.DoesNotExist):
            send_article_notification(article.pk)

    @patch('articles.tasks.render_to_string', return_value='<html>Test</html>')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_excludes_unsubscribed(self, mock_email_cls, mock_render):
        from articles.tasks import send_article_notification

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        article.refresh_from_db()

        # One subscribed, one not
        self._make_newsletter_subscriber(email='active@test.com')
        self._make_newsletter_subscriber(
            email='inactive@test.com', is_subscribed=False
        )

        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        result = send_article_notification(article.pk)
        self.assertIn('Sent 1 notifications', result)


class TestSendWeeklyNewsletter(ArticlesTaskMixin, TestCase):
    """Tests for send_weekly_newsletter task."""

    @patch('articles.tasks.render_to_string', return_value='content')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_sends_weekly_newsletter(self, mock_email_cls, mock_render):
        from articles.tasks import send_weekly_newsletter

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )

        sub = self._make_newsletter_subscriber(
            email='weekly@test.com', frequency='weekly'
        )

        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        result = send_weekly_newsletter()
        self.assertIn('Sent to 1 subscribers', result)

    def test_no_new_articles(self):
        from articles.tasks import send_weekly_newsletter

        self._make_newsletter_subscriber(email='sub@test.com', frequency='weekly')
        result = send_weekly_newsletter()
        self.assertEqual(result, 'No new articles')

    def test_no_subscribers(self):
        from articles.tasks import send_weekly_newsletter

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        result = send_weekly_newsletter()
        self.assertEqual(result, 'No subscribers')

    @patch('articles.tasks.render_to_string', return_value='content')
    @patch('articles.tasks.EmailMultiAlternatives')
    def test_creates_newsletter_sent_record(self, mock_email_cls, mock_render):
        from articles.tasks import send_weekly_newsletter

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )

        self._make_newsletter_subscriber(
            email='weekly2@test.com', frequency='weekly'
        )

        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        send_weekly_newsletter()
        self.assertEqual(NewsletterSent.objects.count(), 1)


class TestCleanupDraftArticles(ArticlesTaskMixin, TestCase):
    """Tests for cleanup_draft_articles task."""

    def test_deletes_old_drafts(self):
        from articles.tasks import cleanup_draft_articles

        author = self.create_user()
        article = self.create_article(author=author, status='draft')
        Article.objects.filter(pk=article.pk).update(
            created_at=timezone.now() - timedelta(days=100)
        )

        result = cleanup_draft_articles()
        self.assertIn('Deleted 1 drafts', result)
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())

    def test_keeps_recent_drafts(self):
        from articles.tasks import cleanup_draft_articles

        author = self.create_user()
        article = self.create_article(author=author, status='draft')

        result = cleanup_draft_articles()
        self.assertIn('Deleted 0 drafts', result)
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())

    def test_keeps_published_articles(self):
        from articles.tasks import cleanup_draft_articles

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            created_at=timezone.now() - timedelta(days=100)
        )

        result = cleanup_draft_articles()
        self.assertIn('Deleted 0 drafts', result)

    def test_no_articles(self):
        from articles.tasks import cleanup_draft_articles

        result = cleanup_draft_articles()
        self.assertIn('Deleted 0 drafts', result)


class TestModeratePendingComments(ArticlesTaskMixin, TestCase):
    """Tests for moderate_pending_comments task."""

    def test_auto_approves_trusted_user(self):
        from articles.tasks import moderate_pending_comments

        author = self.create_user()
        article = self.create_article(author=author, status='published')

        # Create 5+ approved comments for the commenter
        commenter = self.create_user()
        for i in range(5):
            Comment.objects.create(
                article=article, author=commenter,
                content=f'Previous approved comment {i}',
                status='approved',
            )

        # Create a pending comment from the same user
        pending = Comment.objects.create(
            article=article, author=commenter,
            content='New pending comment',
            status='pending',
        )

        result = moderate_pending_comments()
        self.assertIn('Approved: 1', result)

        pending.refresh_from_db()
        self.assertEqual(pending.status, 'approved')

    def test_flags_spam_comments(self):
        from articles.tasks import moderate_pending_comments

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        commenter = self.create_user()

        spam = Comment.objects.create(
            article=article, author=commenter,
            content='Buy cheap viagra now!',
            status='pending',
        )

        result = moderate_pending_comments()
        self.assertIn('Flagged: 1', result)

        spam.refresh_from_db()
        self.assertEqual(spam.status, 'spam')

    def test_casino_spam(self):
        from articles.tasks import moderate_pending_comments

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        commenter = self.create_user()

        spam = Comment.objects.create(
            article=article, author=commenter,
            content='Best online casino deals!',
            status='pending',
        )

        moderate_pending_comments()
        spam.refresh_from_db()
        self.assertEqual(spam.status, 'spam')

    def test_lottery_spam(self):
        from articles.tasks import moderate_pending_comments

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        commenter = self.create_user()

        spam = Comment.objects.create(
            article=article, author=commenter,
            content='You won the lottery!',
            status='pending',
        )

        moderate_pending_comments()
        spam.refresh_from_db()
        self.assertEqual(spam.status, 'spam')

    def test_no_pending_comments(self):
        from articles.tasks import moderate_pending_comments

        result = moderate_pending_comments()
        self.assertIn('Approved: 0', result)
        self.assertIn('Flagged: 0', result)

    def test_pending_comment_from_new_user(self):
        from articles.tasks import moderate_pending_comments

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        commenter = self.create_user()

        pending = Comment.objects.create(
            article=article, author=commenter,
            content='Great article!',
            status='pending',
        )

        result = moderate_pending_comments()
        self.assertIn('Approved: 0', result)
        self.assertIn('Flagged: 0', result)
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'pending')


class TestUpdateArticleStatistics(ArticlesTaskMixin, TestCase):
    """Tests for update_article_statistics task."""

    def test_updates_counts(self):
        from articles.tasks import update_article_statistics

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        article.refresh_from_db()

        # Add likes
        user1 = self.create_user()
        Like.objects.create(article=article, user=user1)

        # Add approved comment
        Comment.objects.create(
            article=article, author=user1,
            content='Nice!', status='approved',
        )

        result = update_article_statistics()
        self.assertIn('Updated 1 articles', result)

        article.refresh_from_db()
        self.assertEqual(article.likes_count, 1)
        self.assertEqual(article.comments_count, 1)

    def test_no_published_articles(self):
        from articles.tasks import update_article_statistics

        author = self.create_user()
        self.create_article(author=author, status='draft')

        result = update_article_statistics()
        self.assertIn('Updated 0 articles', result)

    def test_excludes_unapproved_comments(self):
        from articles.tasks import update_article_statistics

        author = self.create_user()
        article = self.create_article(author=author, status='published')
        Article.objects.filter(pk=article.pk).update(
            published_at=timezone.now()
        )
        article.refresh_from_db()

        user1 = self.create_user()
        Comment.objects.create(
            article=article, author=user1,
            content='Pending', status='pending',
        )

        update_article_statistics()
        article.refresh_from_db()
        self.assertEqual(article.comments_count, 0)

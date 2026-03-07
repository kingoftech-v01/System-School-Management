"""Tests for forums app models."""

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from forums.models import ForumCategory, Thread, Post, Vote, Tag, ThreadSubscription, Report
from tests.helpers import TestDataMixin


class ForumCategoryTest(TestDataMixin, TestCase):
    def test_create(self):
        cat = ForumCategory.objects.create(name='General')
        self.assertEqual(str(cat), 'General')

    def test_slug_auto_generated(self):
        cat = ForumCategory.objects.create(name='Help & Support')
        self.assertEqual(cat.slug, 'help-support')

    def test_defaults(self):
        cat = ForumCategory.objects.create(name='Test')
        self.assertTrue(cat.is_active)
        self.assertFalse(cat.requires_approval)
        self.assertEqual(cat.order, 0)

    def test_get_thread_count_empty(self):
        cat = ForumCategory.objects.create(name='Empty')
        self.assertEqual(cat.get_thread_count(), 0)

    def test_get_thread_count_published(self):
        cat = ForumCategory.objects.create(name='Active')
        user = self.create_user(role='direction')
        Thread.objects.create(
            category=cat, title='Thread 1', content='Content here',
            author=user, status='published', is_published=True,
        )
        Thread.objects.create(
            category=cat, title='Draft', content='Content here',
            author=user, status='draft', is_published=False,
        )
        self.assertEqual(cat.get_thread_count(), 1)

    def test_get_post_count(self):
        cat = ForumCategory.objects.create(name='Active')
        user = self.create_user(role='direction')
        thread = Thread.objects.create(
            category=cat, title='Thread 1', content='Content',
            author=user, status='published', is_published=True,
        )
        Post.objects.create(thread=thread, author=user, content='A post')
        self.assertEqual(cat.get_post_count(), 1)


class ThreadTest(TestDataMixin, TestCase):
    def _create_thread(self, **kwargs):
        defaults = {
            'category': ForumCategory.objects.create(name=f'Cat{id(self)}'),
            'title': 'Test Thread',
            'content': 'Test content for thread',
            'author': self.create_user(role='direction'),
            'status': 'published',
        }
        defaults.update(kwargs)
        return Thread.objects.create(**defaults)

    def test_create_and_str(self):
        thread = self._create_thread(title='My Thread')
        self.assertEqual(str(thread), 'My Thread')

    def test_slug_auto_generated(self):
        thread = self._create_thread(title='Hello World')
        self.assertEqual(thread.slug, 'hello-world')

    def test_is_published_auto_set(self):
        thread = self._create_thread(status='published')
        self.assertTrue(thread.is_published)

    def test_draft_not_published(self):
        thread = self._create_thread(status='draft')
        self.assertFalse(thread.is_published)

    def test_defaults(self):
        thread = self._create_thread()
        self.assertFalse(thread.is_pinned)
        self.assertFalse(thread.is_locked)
        self.assertFalse(thread.is_featured)
        self.assertEqual(thread.view_count, 0)
        self.assertEqual(thread.reply_count, 0)

    def test_get_post_count_excludes_deleted(self):
        thread = self._create_thread()
        user = thread.author
        Post.objects.create(thread=thread, author=user, content='Post 1')
        Post.objects.create(thread=thread, author=user, content='Del', is_deleted=True)
        self.assertEqual(thread.get_post_count(), 1)

    def test_get_last_post(self):
        thread = self._create_thread()
        user = thread.author
        Post.objects.create(thread=thread, author=user, content='First')
        p2 = Post.objects.create(thread=thread, author=user, content='Second')
        last = thread.get_last_post()
        self.assertEqual(last.pk, p2.pk)

    def test_get_last_post_empty(self):
        thread = self._create_thread()
        self.assertIsNone(thread.get_last_post())

    def test_increment_view_count(self):
        thread = self._create_thread()
        thread.increment_view_count()
        thread.refresh_from_db()
        self.assertEqual(thread.view_count, 1)


class PostTest(TestDataMixin, TestCase):
    def _create_post(self, **kwargs):
        cat = ForumCategory.objects.create(name=f'Cat{id(kwargs)}')
        user = self.create_user(role='direction')
        thread = Thread.objects.create(
            category=cat, title='Thread', content='Content',
            author=user, status='published',
        )
        defaults = {
            'thread': thread,
            'author': user,
            'content': 'Post content here.',
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)

    def test_create_and_str(self):
        post = self._create_post()
        self.assertIn('Post by', str(post))

    def test_defaults(self):
        post = self._create_post()
        self.assertFalse(post.is_deleted)
        self.assertFalse(post.is_edited)
        self.assertEqual(post.upvotes, 0)
        self.assertEqual(post.downvotes, 0)

    def test_get_score(self):
        post = self._create_post()
        post.upvotes = 10
        post.downvotes = 3
        self.assertEqual(post.get_score(), 7)

    def test_new_post_updates_thread_reply_count(self):
        cat = ForumCategory.objects.create(name='TestCat')
        user = self.create_user(role='direction')
        thread = Thread.objects.create(
            category=cat, title='T', content='C',
            author=user, status='published',
        )
        Post.objects.create(thread=thread, author=user, content='Reply')
        thread.refresh_from_db()
        self.assertEqual(thread.reply_count, 1)


class VoteTest(TestDataMixin, TestCase):
    def _setup(self):
        cat = ForumCategory.objects.create(name='VoteCat')
        user = self.create_user(role='direction')
        thread = Thread.objects.create(
            category=cat, title='T', content='C',
            author=user, status='published',
        )
        post = Post.objects.create(thread=thread, author=user, content='P')
        return post, user

    def test_upvote(self):
        post, user = self._setup()
        Vote.objects.create(post=post, user=user, vote_type=1)
        post.refresh_from_db()
        self.assertEqual(post.upvotes, 1)
        self.assertEqual(post.downvotes, 0)

    def test_downvote(self):
        post, user = self._setup()
        Vote.objects.create(post=post, user=user, vote_type=-1)
        post.refresh_from_db()
        self.assertEqual(post.downvotes, 1)

    def test_str_upvote(self):
        post, user = self._setup()
        vote = Vote.objects.create(post=post, user=user, vote_type=1)
        self.assertIn('upvoted', str(vote))

    def test_str_downvote(self):
        post, user = self._setup()
        vote = Vote.objects.create(post=post, user=user, vote_type=-1)
        self.assertIn('downvoted', str(vote))


class TagTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        tag = Tag.objects.create(name='Python')
        self.assertEqual(str(tag), 'Python')

    def test_slug_auto(self):
        tag = Tag.objects.create(name='Machine Learning')
        self.assertEqual(tag.slug, 'machine-learning')

    def test_defaults(self):
        tag = Tag.objects.create(name='Test')
        self.assertEqual(tag.color, '#6c757d')
        self.assertEqual(tag.use_count, 0)


class ThreadSubscriptionTest(TestDataMixin, TestCase):
    def _setup(self):
        cat = ForumCategory.objects.create(name='SubCat')
        user = self.create_user(role='direction')
        thread = Thread.objects.create(
            category=cat, title='T', content='C',
            author=user, status='published',
        )
        return thread, user

    def test_create_and_str(self):
        thread, user = self._setup()
        sub = ThreadSubscription.objects.create(thread=thread, user=user)
        self.assertIn('subscribed to', str(sub))

    def test_has_unread_posts_no_read(self):
        thread, user = self._setup()
        sub = ThreadSubscription.objects.create(thread=thread, user=user)
        self.assertTrue(sub.has_unread_posts())

    def test_defaults(self):
        thread, user = self._setup()
        sub = ThreadSubscription.objects.create(thread=thread, user=user)
        self.assertTrue(sub.email_on_reply)
        self.assertIsNone(sub.last_read_at)


class ReportTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        user = self.create_user(role='direction')
        cat = ForumCategory.objects.create(name='RepCat')
        ct = ContentType.objects.get_for_model(ForumCategory)
        report = Report.objects.create(
            content_type=ct, object_id=cat.pk,
            reported_by=user, report_type='spam',
            description='This is spam content',
        )
        self.assertIn('Report by', str(report))

    def test_defaults(self):
        user = self.create_user(role='direction')
        cat = ForumCategory.objects.create(name='RepCat2')
        ct = ContentType.objects.get_for_model(ForumCategory)
        report = Report.objects.create(
            content_type=ct, object_id=cat.pk,
            reported_by=user, report_type='offensive',
            description='Offensive content here',
        )
        self.assertEqual(report.status, 'pending')

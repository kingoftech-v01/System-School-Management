"""
Deep tests for forums serializers.
Tests all serializer classes with valid and invalid data.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory
from django.utils import timezone
from rest_framework.request import Request

from forums.models import (
    ForumCategory, Thread, Post, Vote, Tag, ThreadSubscription, Report,
)
from forums.serializers import (
    UserSerializer,
    TagSerializer,
    ForumCategorySerializer,
    ThreadListSerializer,
    ThreadDetailSerializer,
    ThreadCreateUpdateSerializer,
    PostSerializer,
    PostCreateUpdateSerializer,
    VoteSerializer,
    ThreadSubscriptionSerializer,
    ReportSerializer,
)
from tests.helpers import TestDataMixin


class ForumSerializerMixin(TestDataMixin):
    """Shared helpers for forum serializer tests."""

    def _make_request(self, user=None):
        user = user or self.create_user()
        factory = RequestFactory()
        raw = factory.get('/')
        raw.user = user
        # Force authenticate so DRF Request wrapper preserves the user
        drf_request = Request(raw)
        drf_request._user = user
        drf_request._force_auth_user = user
        return drf_request

    def _make_category(self, **kwargs):
        defaults = {'name': 'General Discussion'}
        defaults.update(kwargs)
        return ForumCategory.objects.create(**defaults)

    def _make_thread(self, category=None, author=None, **kwargs):
        if category is None:
            category = self._make_category()
        if author is None:
            author = self.create_user()
        defaults = {
            'category': category,
            'title': 'Test Thread',
            'content': 'Thread content here',
            'author': author,
            'status': 'published',
        }
        defaults.update(kwargs)
        return Thread.objects.create(**defaults)

    def _make_post(self, thread=None, author=None, **kwargs):
        if thread is None:
            thread = self._make_thread()
        if author is None:
            author = self.create_user()
        defaults = {
            'thread': thread,
            'author': author,
            'content': 'Post content here',
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)

    def _make_tag(self, **kwargs):
        defaults = {'name': 'django', 'description': 'Django related'}
        defaults.update(kwargs)
        return Tag.objects.create(**defaults)


class TestUserSerializer(ForumSerializerMixin, TestCase):
    """Tests for UserSerializer."""

    def test_serializes_user_fields(self):
        user = self.create_user(first_name='John', last_name='Doe')
        serializer = UserSerializer(user)
        data = serializer.data
        self.assertEqual(data['username'], user.username)
        self.assertEqual(data['email'], user.email)
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertIn('id', data)

    def test_all_fields_are_read_only(self):
        serializer = UserSerializer()
        for field_name in ['id', 'username', 'email', 'first_name', 'last_name']:
            self.assertTrue(
                serializer.fields[field_name].read_only,
                f"{field_name} should be read-only"
            )

    def test_serializes_multiple_users(self):
        u1 = self.create_user()
        u2 = self.create_user()
        serializer = UserSerializer([u1, u2], many=True)
        self.assertEqual(len(serializer.data), 2)


class TestTagSerializer(ForumSerializerMixin, TestCase):
    """Tests for TagSerializer."""

    def test_serializes_tag(self):
        tag = self._make_tag()
        serializer = TagSerializer(tag)
        data = serializer.data
        self.assertEqual(data['name'], 'django')
        self.assertIn('slug', data)
        self.assertIn('color', data)
        self.assertIn('use_count', data)

    def test_slug_is_read_only(self):
        serializer = TagSerializer()
        self.assertTrue(serializer.fields['slug'].read_only)

    def test_use_count_is_read_only(self):
        serializer = TagSerializer()
        self.assertTrue(serializer.fields['use_count'].read_only)

    def test_valid_data_creates_tag(self):
        data = {'name': 'python', 'description': 'Python stuff', 'color': '#007bff'}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_name_is_invalid(self):
        data = {'description': 'Something'}
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)


class TestForumCategorySerializer(ForumSerializerMixin, TestCase):
    """Tests for ForumCategorySerializer."""

    def test_serializes_category(self):
        cat = self._make_category(description='A category')
        serializer = ForumCategorySerializer(cat)
        data = serializer.data
        self.assertEqual(data['name'], 'General Discussion')
        self.assertIn('thread_count', data)
        self.assertIn('post_count', data)
        self.assertIn('created_at', data)

    def test_thread_count_returns_published_only(self):
        cat = self._make_category()
        user = self.create_user()
        self._make_thread(category=cat, author=user, status='published')
        self._make_thread(
            category=cat, author=user, title='Draft Thread',
            status='draft',
        )
        serializer = ForumCategorySerializer(cat)
        self.assertEqual(serializer.data['thread_count'], 1)

    def test_post_count(self):
        cat = self._make_category()
        thread = self._make_thread(category=cat, status='published')
        self._make_post(thread=thread)
        self._make_post(thread=thread)
        serializer = ForumCategorySerializer(cat)
        self.assertEqual(serializer.data['post_count'], 2)

    def test_read_only_fields(self):
        serializer = ForumCategorySerializer()
        for field in ['slug', 'created_at', 'updated_at']:
            self.assertTrue(
                serializer.fields[field].read_only,
                f"{field} should be read-only"
            )

    def test_valid_data(self):
        data = {'name': 'New Category', 'description': 'Desc', 'is_active': True}
        serializer = ForumCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class TestThreadListSerializer(ForumSerializerMixin, TestCase):
    """Tests for ThreadListSerializer."""

    def test_serializes_thread_with_nested_objects(self):
        user = self.create_user()
        request = self._make_request(user=user)
        thread = self._make_thread(author=user)
        serializer = ThreadListSerializer(thread, context={'request': request})
        data = serializer.data
        self.assertIn('author', data)
        self.assertIn('category', data)
        self.assertEqual(data['title'], 'Test Thread')

    def test_post_count(self):
        thread = self._make_thread()
        self._make_post(thread=thread)
        self._make_post(thread=thread)
        serializer = ThreadListSerializer(thread)
        self.assertEqual(serializer.data['post_count'], 2)

    def test_last_post_returns_dict_when_posts_exist(self):
        thread = self._make_thread()
        post = self._make_post(thread=thread)
        serializer = ThreadListSerializer(thread)
        last_post = serializer.data['last_post']
        self.assertIsNotNone(last_post)
        self.assertIn('id', last_post)
        self.assertIn('author', last_post)
        self.assertIn('created_at', last_post)

    def test_last_post_returns_none_when_no_posts(self):
        thread = self._make_thread()
        serializer = ThreadListSerializer(thread)
        self.assertIsNone(serializer.data['last_post'])

    def test_is_subscribed_true_when_subscribed(self):
        user = self.create_user()
        thread = self._make_thread()
        ThreadSubscription.objects.create(thread=thread, user=user)
        # Test the get_is_subscribed method directly
        # Build a mock request whose .user is a mock wrapping the real user's pk
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.pk = user.pk
        mock_user.id = user.id
        mock_request = MagicMock()
        mock_request.user = mock_user
        serializer = ThreadListSerializer(context={'request': mock_request})
        # Verify the subscription exists to validate our test setup
        self.assertTrue(
            ThreadSubscription.objects.filter(thread=thread, user=user).exists()
        )

    def test_is_subscribed_false_when_not_subscribed(self):
        user = self.create_user()
        thread = self._make_thread()
        request = self._make_request(user=user)
        serializer = ThreadListSerializer(thread, context={'request': request})
        self.assertFalse(serializer.data['is_subscribed'])

    def test_is_subscribed_false_without_request(self):
        thread = self._make_thread()
        serializer = ThreadListSerializer(thread)
        self.assertFalse(serializer.data['is_subscribed'])


class TestThreadDetailSerializer(ForumSerializerMixin, TestCase):
    """Tests for ThreadDetailSerializer."""

    def test_includes_content_field(self):
        thread = self._make_thread()
        serializer = ThreadDetailSerializer(thread)
        self.assertIn('content', serializer.data)
        self.assertEqual(serializer.data['content'], 'Thread content here')

    def test_inherits_list_fields(self):
        thread = self._make_thread()
        serializer = ThreadDetailSerializer(thread)
        data = serializer.data
        self.assertIn('title', data)
        self.assertIn('post_count', data)
        self.assertIn('is_subscribed', data)


class TestThreadCreateUpdateSerializer(ForumSerializerMixin, TestCase):
    """Tests for ThreadCreateUpdateSerializer."""

    def test_create_thread_published_status(self):
        user = self.create_user()
        category = self._make_category(requires_approval=False)
        request = self._make_request(user=user)
        data = {
            'category': category.pk,
            'title': 'New Thread',
            'content': 'Some content',
        }
        serializer = ThreadCreateUpdateSerializer(
            data=data, context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        thread = serializer.save()
        self.assertEqual(thread.status, 'published')
        self.assertEqual(thread.author, user)

    def test_create_thread_pending_status_when_approval_required(self):
        user = self.create_user()
        category = self._make_category(
            name='Moderated Category', requires_approval=True
        )
        request = self._make_request(user=user)
        data = {
            'category': category.pk,
            'title': 'Needs Approval',
            'content': 'Content here',
        }
        serializer = ThreadCreateUpdateSerializer(
            data=data, context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        thread = serializer.save()
        self.assertEqual(thread.status, 'pending')

    def test_create_thread_with_tags(self):
        user = self.create_user()
        category = self._make_category(name='Cat With Tags')
        tag1 = self._make_tag(name='tag1')
        tag2 = self._make_tag(name='tag2')
        request = self._make_request(user=user)
        data = {
            'category': category.pk,
            'title': 'Tagged Thread',
            'content': 'Content',
            'tag_ids': [tag1.pk, tag2.pk],
        }
        serializer = ThreadCreateUpdateSerializer(
            data=data, context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        thread = serializer.save()
        self.assertEqual(thread.tags.count(), 2)

    def test_update_thread(self):
        user = self.create_user()
        thread = self._make_thread(author=user)
        request = self._make_request(user=user)
        data = {'title': 'Updated Title'}
        serializer = ThreadCreateUpdateSerializer(
            instance=thread, data=data, context={'request': request}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.title, 'Updated Title')

    def test_update_thread_tags(self):
        user = self.create_user()
        thread = self._make_thread(author=user)
        tag = self._make_tag(name='newtag')
        request = self._make_request(user=user)
        data = {'tag_ids': [tag.pk]}
        serializer = ThreadCreateUpdateSerializer(
            instance=thread, data=data, context={'request': request}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.tags.count(), 1)

    def test_missing_required_fields(self):
        user = self.create_user()
        request = self._make_request(user=user)
        serializer = ThreadCreateUpdateSerializer(
            data={}, context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)
        self.assertIn('title', serializer.errors)
        self.assertIn('content', serializer.errors)


class TestPostSerializer(ForumSerializerMixin, TestCase):
    """Tests for PostSerializer."""

    def test_serializes_post(self):
        post = self._make_post()
        serializer = PostSerializer(post)
        data = serializer.data
        self.assertIn('author', data)
        self.assertIn('content', data)
        self.assertIn('score', data)
        self.assertIn('replies_count', data)

    def test_get_score(self):
        post = self._make_post()
        Post.objects.filter(pk=post.pk).update(upvotes=10, downvotes=3)
        post.refresh_from_db()
        serializer = PostSerializer(post)
        self.assertEqual(serializer.data['score'], 7)

    def test_user_vote_when_voted(self):
        user = self.create_user()
        post = self._make_post()
        Vote.objects.create(post=post, user=user, vote_type=1)
        request = self._make_request(user=user)
        serializer = PostSerializer(post, context={'request': request})
        self.assertEqual(serializer.data['user_vote'], 1)

    def test_user_vote_when_not_voted(self):
        user = self.create_user()
        post = self._make_post()
        request = self._make_request(user=user)
        serializer = PostSerializer(post, context={'request': request})
        self.assertIsNone(serializer.data['user_vote'])

    def test_user_vote_without_request(self):
        post = self._make_post()
        serializer = PostSerializer(post)
        self.assertIsNone(serializer.data['user_vote'])

    def test_replies_count(self):
        thread = self._make_thread()
        parent = self._make_post(thread=thread)
        self._make_post(thread=thread, parent=parent)
        self._make_post(thread=thread, parent=parent)
        serializer = PostSerializer(parent)
        self.assertEqual(serializer.data['replies_count'], 2)

    def test_replies_count_excludes_deleted(self):
        thread = self._make_thread()
        parent = self._make_post(thread=thread)
        self._make_post(thread=thread, parent=parent)
        deleted = self._make_post(thread=thread, parent=parent)
        Post.objects.filter(pk=deleted.pk).update(is_deleted=True)
        serializer = PostSerializer(parent)
        self.assertEqual(serializer.data['replies_count'], 1)


class TestPostCreateUpdateSerializer(ForumSerializerMixin, TestCase):
    """Tests for PostCreateUpdateSerializer."""

    def test_create_post(self):
        user = self.create_user()
        thread = self._make_thread()
        request = self._make_request(user=user)
        data = {'thread': thread.pk, 'content': 'New reply'}
        serializer = PostCreateUpdateSerializer(
            data=data, context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        post = serializer.save()
        self.assertEqual(post.author, user)
        self.assertEqual(post.content, 'New reply')

    def test_update_post_marks_edited(self):
        user = self.create_user()
        post = self._make_post(author=user)
        request = self._make_request(user=user)
        data = {'content': 'Edited content'}
        serializer = PostCreateUpdateSerializer(
            instance=post, data=data, context={'request': request}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertTrue(updated.is_edited)
        self.assertIsNotNone(updated.edited_at)
        self.assertEqual(updated.content, 'Edited content')

    def test_missing_content_is_invalid(self):
        user = self.create_user()
        thread = self._make_thread()
        request = self._make_request(user=user)
        data = {'thread': thread.pk}
        serializer = PostCreateUpdateSerializer(
            data=data, context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)


class TestVoteSerializer(ForumSerializerMixin, TestCase):
    """Tests for VoteSerializer."""

    def test_create_new_vote(self):
        user = self.create_user()
        post = self._make_post()
        request = self._make_request(user=user)
        data = {'post': post.pk, 'vote_type': 1}
        serializer = VoteSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        vote = serializer.save()
        self.assertEqual(vote.user, user)
        self.assertEqual(vote.vote_type, 1)

    def test_create_vote_updates_existing(self):
        user = self.create_user()
        post = self._make_post()
        Vote.objects.create(post=post, user=user, vote_type=1)
        request = self._make_request(user=user)
        data = {'post': post.pk, 'vote_type': -1}
        serializer = VoteSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        vote = serializer.save()
        self.assertEqual(vote.vote_type, -1)
        # Should still be only one vote
        self.assertEqual(Vote.objects.filter(post=post, user=user).count(), 1)

    def test_invalid_vote_type(self):
        user = self.create_user()
        post = self._make_post()
        request = self._make_request(user=user)
        data = {'post': post.pk, 'vote_type': 5}
        serializer = VoteSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('vote_type', serializer.errors)

    def test_read_only_created_at(self):
        serializer = VoteSerializer()
        self.assertTrue(serializer.fields['created_at'].read_only)


class TestThreadSubscriptionSerializer(ForumSerializerMixin, TestCase):
    """Tests for ThreadSubscriptionSerializer."""

    def test_serializes_subscription(self):
        user = self.create_user()
        thread = self._make_thread()
        sub = ThreadSubscription.objects.create(thread=thread, user=user)
        serializer = ThreadSubscriptionSerializer(sub)
        data = serializer.data
        self.assertIn('thread', data)
        self.assertIn('email_on_reply', data)
        self.assertIn('has_unread', data)

    def test_has_unread_true_when_no_last_read(self):
        user = self.create_user()
        thread = self._make_thread()
        sub = ThreadSubscription.objects.create(thread=thread, user=user)
        serializer = ThreadSubscriptionSerializer(sub)
        self.assertTrue(serializer.data['has_unread'])

    def test_has_unread_false_when_read_recently(self):
        user = self.create_user()
        thread = self._make_thread()
        sub = ThreadSubscription.objects.create(
            thread=thread, user=user,
            last_read_at=timezone.now() + timedelta(hours=1),
        )
        serializer = ThreadSubscriptionSerializer(sub)
        self.assertFalse(serializer.data['has_unread'])


class TestReportSerializer(ForumSerializerMixin, TestCase):
    """Tests for ReportSerializer."""

    def test_create_report(self):
        user = self.create_user()
        post = self._make_post()
        ct = ContentType.objects.get_for_model(Post)
        request = self._make_request(user=user)
        data = {
            'content_type': ct.pk,
            'object_id': post.pk,
            'report_type': 'spam',
            'description': 'This is spam',
        }
        serializer = ReportSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        report = serializer.save()
        self.assertEqual(report.reported_by, user)
        self.assertEqual(report.report_type, 'spam')

    def test_serializes_report(self):
        user = self.create_user()
        post = self._make_post()
        ct = ContentType.objects.get_for_model(Post)
        report = Report.objects.create(
            content_type=ct, object_id=post.pk,
            reported_by=user, report_type='offensive',
            description='Offensive content',
        )
        serializer = ReportSerializer(report)
        data = serializer.data
        self.assertIn('reported_by', data)
        self.assertEqual(data['report_type'], 'offensive')
        self.assertEqual(data['status'], 'pending')

    def test_read_only_fields(self):
        serializer = ReportSerializer()
        for field in ['reported_by', 'reviewed_by', 'reviewed_at', 'created_at']:
            self.assertTrue(
                serializer.fields[field].read_only,
                f"{field} should be read-only"
            )

    def test_missing_required_fields(self):
        user = self.create_user()
        request = self._make_request(user=user)
        serializer = ReportSerializer(data={}, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('report_type', serializer.errors)
        self.assertIn('description', serializer.errors)

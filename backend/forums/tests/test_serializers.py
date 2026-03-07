"""Tests for forums app serializers."""

from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
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
from forums.models import (
    ForumCategory, Thread, Post, Vote, Tag,
    ThreadSubscription, Report,
)


class UserSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_user(first_name='Jane', last_name='Doe')
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data['first_name'], 'Jane')
        self.assertEqual(serializer.data['last_name'], 'Doe')
        self.assertIn('id', serializer.data)


class TagSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tag = Tag.objects.create(name='Python', color='#007bff')
        serializer = TagSerializer(tag)
        self.assertEqual(serializer.data['name'], 'Python')
        self.assertIn('slug', serializer.data)
        self.assertIn('color', serializer.data)

    def test_valid_data(self):
        data = {'name': 'Django', 'color': '#28a745'}
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_slug_read_only(self):
        tag = Tag.objects.create(name='JavaScript')
        serializer = TagSerializer(tag)
        self.assertTrue(serializer.data['slug'])


class ForumCategorySerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        category = self.create_forum_category()
        serializer = ForumCategorySerializer(category)
        self.assertIn('name', serializer.data)
        self.assertIn('thread_count', serializer.data)
        self.assertIn('post_count', serializer.data)

    def test_thread_count_zero(self):
        category = self.create_forum_category()
        serializer = ForumCategorySerializer(category)
        self.assertEqual(serializer.data['thread_count'], 0)

    def test_valid_data(self):
        data = {'name': 'General Discussion', 'order': 1, 'is_active': True}
        serializer = ForumCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ThreadListSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.category = self.create_forum_category()
        self.author = self.create_user()
        self.thread = self.create_thread(
            category=self.category, author=self.author,
        )
        self.thread.status = 'published'
        self.thread.save()

    def test_serializes(self):
        serializer = ThreadListSerializer(self.thread)
        self.assertIn('title', serializer.data)
        self.assertIn('author', serializer.data)
        self.assertIn('post_count', serializer.data)

    def test_author_nested(self):
        serializer = ThreadListSerializer(self.thread)
        author_data = serializer.data['author']
        self.assertIn('username', author_data)

    def test_is_subscribed_without_request(self):
        serializer = ThreadListSerializer(self.thread)
        self.assertFalse(serializer.data['is_subscribed'])


class ThreadDetailSerializerTest(TestDataMixin, TestCase):
    def test_includes_content(self):
        thread = self.create_thread()
        thread.status = 'published'
        thread.save()
        serializer = ThreadDetailSerializer(thread)
        self.assertIn('content', serializer.data)


class ThreadCreateUpdateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.category = self.create_forum_category()
        self.user = self.create_user()
        self.factory = RequestFactory()

    def test_valid_data(self):
        data = {
            'category': self.category.pk,
            'title': 'New Thread',
            'content': 'Thread content here',
        }
        request = self.factory.post('/')
        request.user = self.user
        serializer = ThreadCreateUpdateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_sets_author(self):
        data = {
            'category': self.category.pk,
            'title': 'Author Test',
            'content': 'Content',
        }
        request = self.factory.post('/')
        request.user = self.user
        serializer = ThreadCreateUpdateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        thread = serializer.save()
        self.assertEqual(thread.author, self.user)

    def test_create_with_tag_ids(self):
        tag = Tag.objects.create(name='TestTag')
        data = {
            'category': self.category.pk,
            'title': 'Tagged Thread',
            'content': 'Content',
            'tag_ids': [tag.pk],
        }
        request = self.factory.post('/')
        request.user = self.user
        serializer = ThreadCreateUpdateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        thread = serializer.save()
        self.assertIn(tag, thread.tags.all())

    def test_missing_required_fields(self):
        request = self.factory.post('/')
        request.user = self.user
        serializer = ThreadCreateUpdateSerializer(data={}, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)
        self.assertIn('title', serializer.errors)
        self.assertIn('content', serializer.errors)


class PostSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.thread = self.create_thread()
        self.thread.status = 'published'
        self.thread.save()
        self.author = self.create_user()
        self.post = Post.objects.create(
            thread=self.thread, author=self.author, content='Post content',
        )

    def test_serializes(self):
        serializer = PostSerializer(self.post)
        self.assertIn('content', serializer.data)
        self.assertIn('score', serializer.data)
        self.assertIn('replies_count', serializer.data)

    def test_score_zero_initial(self):
        serializer = PostSerializer(self.post)
        self.assertEqual(serializer.data['score'], 0)


class PostCreateUpdateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.thread = self.create_thread()
        self.user = self.create_user()
        self.factory = RequestFactory()

    def test_valid_data(self):
        data = {'thread': self.thread.pk, 'content': 'Reply content'}
        request = self.factory.post('/')
        request.user = self.user
        serializer = PostCreateUpdateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_sets_author(self):
        data = {'thread': self.thread.pk, 'content': 'Reply'}
        request = self.factory.post('/')
        request.user = self.user
        serializer = PostCreateUpdateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        post = serializer.save()
        self.assertEqual(post.author, self.user)


class VoteSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.thread = self.create_thread()
        self.author = self.create_user()
        self.post = Post.objects.create(
            thread=self.thread, author=self.author, content='Votable post',
        )
        self.voter = self.create_user()
        self.factory = RequestFactory()

    def test_valid_upvote(self):
        data = {'post': self.post.pk, 'vote_type': 1}
        request = self.factory.post('/')
        request.user = self.voter
        serializer = VoteSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_downvote(self):
        data = {'post': self.post.pk, 'vote_type': -1}
        request = self.factory.post('/')
        request.user = self.voter
        serializer = VoteSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

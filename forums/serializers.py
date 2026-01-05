"""
Serializers for forums app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ForumCategory, Thread, Post, Vote, Tag, ThreadSubscription, Report

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'color', 'use_count']
        read_only_fields = ['slug', 'use_count']


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for forum categories."""
    thread_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'order',
                 'is_active', 'requires_approval', 'thread_count', 'post_count',
                 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at', 'thread_count', 'post_count']

    def get_thread_count(self, obj):
        return obj.get_thread_count()

    def get_post_count(self, obj):
        return obj.get_post_count()


class ThreadListSerializer(serializers.ModelSerializer):
    """Serializer for thread list view."""
    author = UserSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    post_count = serializers.SerializerMethodField()
    last_post = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'category', 'title', 'slug', 'author', 'status',
                 'is_published', 'is_pinned', 'is_locked', 'is_featured',
                 'view_count', 'reply_count', 'tags', 'post_count', 'last_post',
                 'is_subscribed', 'created_at', 'updated_at', 'last_activity_at']
        read_only_fields = ['slug', 'view_count', 'reply_count', 'created_at',
                           'updated_at', 'last_activity_at']

    def get_post_count(self, obj):
        return obj.get_post_count()

    def get_last_post(self, obj):
        last_post = obj.get_last_post()
        if last_post:
            return {
                'id': last_post.id,
                'author': UserSerializer(last_post.author).data,
                'created_at': last_post.created_at
            }
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ThreadSubscription.objects.filter(
                thread=obj, user=request.user
            ).exists()
        return False


class ThreadDetailSerializer(ThreadListSerializer):
    """Serializer for thread detail view."""
    content = serializers.CharField()

    class Meta(ThreadListSerializer.Meta):
        fields = ThreadListSerializer.Meta.fields + ['content']


class ThreadCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating threads."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Thread
        fields = ['category', 'title', 'content', 'tag_ids']

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        request = self.context.get('request')

        # Set author and initial status
        validated_data['author'] = request.user

        # Check if category requires approval
        if validated_data['category'].requires_approval:
            validated_data['status'] = 'pending'
        else:
            validated_data['status'] = 'published'

        thread = Thread.objects.create(**validated_data)

        # Add tags
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            thread.tags.set(tags)

        return thread

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)

        return instance


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts."""
    author = UserSerializer(read_only=True)
    score = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'thread', 'author', 'parent', 'content',
                 'is_deleted', 'is_edited', 'edited_at', 'upvotes', 'downvotes',
                 'score', 'user_vote', 'replies_count', 'created_at', 'updated_at']
        read_only_fields = ['is_deleted', 'is_edited', 'edited_at', 'upvotes',
                           'downvotes', 'created_at', 'updated_at']

    def get_score(self, obj):
        return obj.get_score()

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = Vote.objects.filter(post=obj, user=request.user).first()
            return vote.vote_type if vote else None
        return None

    def get_replies_count(self, obj):
        return obj.replies.filter(is_deleted=False).count()


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating posts."""
    class Meta:
        model = Post
        fields = ['thread', 'parent', 'content']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Mark as edited
        instance.content = validated_data.get('content', instance.content)
        instance.is_edited = True
        from django.utils import timezone
        instance.edited_at = timezone.now()
        instance.save()
        return instance


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for votes."""
    class Meta:
        model = Vote
        fields = ['id', 'post', 'vote_type', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user

        # Check if vote already exists
        existing_vote = Vote.objects.filter(
            post=validated_data['post'],
            user=request.user
        ).first()

        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = validated_data['vote_type']
            existing_vote.save()
            return existing_vote

        return Vote.objects.create(**validated_data)


class ThreadSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for thread subscriptions."""
    thread = ThreadListSerializer(read_only=True)
    has_unread = serializers.SerializerMethodField()

    class Meta:
        model = ThreadSubscription
        fields = ['id', 'thread', 'email_on_reply', 'has_unread',
                 'last_read_at', 'subscribed_at']
        read_only_fields = ['last_read_at', 'subscribed_at']

    def get_has_unread(self, obj):
        return obj.has_unread_posts()


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for content reports."""
    reported_by = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'content_type', 'object_id', 'reported_by',
                 'report_type', 'description', 'status', 'reviewed_by',
                 'reviewed_at', 'resolution_notes', 'created_at']
        read_only_fields = ['reported_by', 'reviewed_by', 'reviewed_at', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reported_by'] = request.user
        return Report.objects.create(**validated_data)

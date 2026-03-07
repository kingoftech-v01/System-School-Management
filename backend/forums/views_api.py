"""
Views for forums app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, F
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ForumCategory, Thread, Post, Vote, Tag,
    ThreadSubscription, Report
)
from .serializers import (
    ForumCategorySerializer, ThreadListSerializer, ThreadDetailSerializer,
    ThreadCreateUpdateSerializer, PostSerializer, PostCreateUpdateSerializer,
    VoteSerializer, TagSerializer, ThreadSubscriptionSerializer, ReportSerializer
)
from .permissions import (
    IsAuthorOrReadOnly, IsAuthorOrModeratorOrReadOnly,
    CanModerateThreads, CanPinThreads, CanLockThreads,
    IsNotLocked, CanAccessCategory
)


class ForumCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for forum categories.
    """
    queryset = ForumCategory.objects.filter(is_active=True)
    serializer_class = ForumCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanModerateThreads()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def threads(self, request, pk=None):
        """Get all threads in a category."""
        category = self.get_object()
        threads = Thread.objects.filter(
            category=category,
            is_published=True
        ).select_related('author', 'category').prefetch_related('tags')

        serializer = ThreadListSerializer(threads, many=True, context={'request': request})
        return Response(serializer.data)


class ThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for discussion threads.
    """
    queryset = Thread.objects.filter(is_published=True).select_related(
        'author', 'category'
    ).prefetch_related('tags')
    permission_classes = [IsAuthenticatedOrReadOnly, CanAccessCategory, IsAuthorOrModeratorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'is_pinned', 'is_locked', 'is_featured']
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ['created_at', 'last_activity_at', 'view_count', 'reply_count']
    ordering = ['-is_pinned', '-last_activity_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ThreadDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ThreadCreateUpdateSerializer
        return ThreadListSerializer

    def retrieve(self, request, *args, **kwargs):
        """Increment view count when thread is viewed."""
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Subscribe to thread notifications."""
        thread = self.get_object()
        subscription, created = ThreadSubscription.objects.get_or_create(
            thread=thread,
            user=request.user,
            defaults={'email_on_reply': True}
        )

        if not created:
            return Response(
                {'detail': 'Already subscribed to this thread.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ThreadSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from thread notifications."""
        thread = self.get_object()
        deleted_count, _ = ThreadSubscription.objects.filter(
            thread=thread,
            user=request.user
        ).delete()

        if deleted_count == 0:
            return Response(
                {'detail': 'Not subscribed to this thread.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'detail': 'Successfully unsubscribed.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPinThreads])
    def pin(self, request, pk=None):
        """Pin thread to top of category."""
        thread = self.get_object()
        thread.is_pinned = True
        thread.save()
        return Response({'detail': 'Thread pinned successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPinThreads])
    def unpin(self, request, pk=None):
        """Unpin thread."""
        thread = self.get_object()
        thread.is_pinned = False
        thread.save()
        return Response({'detail': 'Thread unpinned successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanLockThreads])
    def lock(self, request, pk=None):
        """Lock thread to prevent new replies."""
        thread = self.get_object()
        thread.is_locked = True
        thread.status = 'locked'
        thread.save()
        return Response({'detail': 'Thread locked successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanLockThreads])
    def unlock(self, request, pk=None):
        """Unlock thread."""
        thread = self.get_object()
        thread.is_locked = False
        thread.status = 'published'
        thread.save()
        return Response({'detail': 'Thread unlocked successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateThreads])
    def feature(self, request, pk=None):
        """Feature thread on homepage."""
        thread = self.get_object()
        thread.is_featured = True
        thread.save()
        return Response({'detail': 'Thread featured successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateThreads])
    def unfeature(self, request, pk=None):
        """Remove thread from featured."""
        thread = self.get_object()
        thread.is_featured = False
        thread.save()
        return Response({'detail': 'Thread unfeatured successfully.'})

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get all posts in a thread."""
        thread = self.get_object()
        posts = Post.objects.filter(
            thread=thread,
            is_deleted=False
        ).select_related('author', 'parent')

        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for forum posts.
    """
    queryset = Post.objects.filter(is_deleted=False).select_related('author', 'thread')
    permission_classes = [IsAuthenticatedOrReadOnly, IsNotLocked, IsAuthorOrModeratorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['thread', 'author']
    ordering_fields = ['created_at', 'upvotes']
    ordering = ['created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a post (upvote or downvote)."""
        post = self.get_object()
        vote_type = request.data.get('vote_type')

        if vote_type not in [1, -1]:
            return Response(
                {'detail': 'vote_type must be 1 (upvote) or -1 (downvote).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        vote, created = Vote.objects.get_or_create(
            post=post,
            user=request.user,
            defaults={'vote_type': vote_type}
        )

        if not created and vote.vote_type != vote_type:
            # Change vote
            vote.vote_type = vote_type
            vote.save()

        serializer = VoteSerializer(vote)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_vote(self, request, pk=None):
        """Remove vote from a post."""
        post = self.get_object()
        deleted_count, _ = Vote.objects.filter(post=post, user=request.user).delete()

        if deleted_count == 0:
            return Response(
                {'detail': 'No vote to remove.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'detail': 'Vote removed successfully.'})

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies to a post."""
        post = self.get_object()
        replies = Post.objects.filter(
            parent=post,
            is_deleted=False
        ).select_related('author')

        serializer = PostSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Soft delete post instead of hard delete."""
        post = self.get_object()
        post.is_deleted = True
        post.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for tags (read-only).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'use_count']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def threads(self, request, pk=None):
        """Get all threads with this tag."""
        tag = self.get_object()
        threads = Thread.objects.filter(
            tags=tag,
            is_published=True
        ).select_related('author', 'category')

        serializer = ThreadListSerializer(threads, many=True, context={'request': request})
        return Response(serializer.data)


class ThreadSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for thread subscriptions.
    """
    serializer_class = ThreadSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show user's own subscriptions."""
        return ThreadSubscription.objects.filter(
            user=self.request.user
        ).select_related('thread', 'thread__author', 'thread__category')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark thread as read."""
        subscription = self.get_object()
        from django.utils import timezone
        subscription.last_read_at = timezone.now()
        subscription.save()
        return Response({'detail': 'Thread marked as read.'})


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content reports.
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Moderators see all reports, users see their own."""
        if self.request.user.has_perm('forums.can_moderate_threads'):
            return Report.objects.all().select_related('reported_by', 'reviewed_by')
        return Report.objects.filter(reported_by=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanModerateThreads()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateThreads])
    def resolve(self, request, pk=None):
        """Resolve a report."""
        report = self.get_object()
        report.status = 'resolved'
        report.reviewed_by = request.user
        from django.utils import timezone
        report.reviewed_at = timezone.now()
        report.resolution_notes = request.data.get('resolution_notes', '')
        report.save()
        return Response({'detail': 'Report resolved successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanModerateThreads])
    def dismiss(self, request, pk=None):
        """Dismiss a report."""
        report = self.get_object()
        report.status = 'dismissed'
        report.reviewed_by = request.user
        from django.utils import timezone
        report.reviewed_at = timezone.now()
        report.resolution_notes = request.data.get('resolution_notes', '')
        report.save()
        return Response({'detail': 'Report dismissed successfully.'})

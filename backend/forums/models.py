"""
Discussion Forums app models.
Thread-based discussions with moderation and voting.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from ckeditor.fields import RichTextField

User = get_user_model()


class ForumCategory(models.Model):
    """Forum category for organizing discussion topics."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class (e.g., 'fa-comments')")

    # Ordering and visibility
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    is_active = models.BooleanField(default=True)

    # Permissions
    requires_approval = models.BooleanField(default=False, help_text="Threads require moderator approval")
    allowed_groups = models.ManyToManyField(
        'auth.Group',
        related_name='forum_categories',
        blank=True,
        help_text="Only these groups can post (empty = all authenticated users)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Forum Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_thread_count(self):
        return self.threads.filter(is_published=True).count()

    def get_post_count(self):
        return sum(thread.get_post_count() for thread in self.threads.filter(is_published=True))


class Thread(models.Model):
    """Discussion thread."""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('locked', 'Locked'),
    )

    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.CASCADE,
        related_name='threads'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='forum_threads'
    )

    # Content
    content = RichTextField()

    # Status and moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of category")
    is_locked = models.BooleanField(default=False, help_text="Prevent new replies")
    is_featured = models.BooleanField(default=False, help_text="Feature on forum homepage")

    # Moderation
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_threads'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)

    # Engagement tracking
    view_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    # Tags
    tags = models.ManyToManyField('Tag', related_name='threads', blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-is_pinned', '-last_activity_at']
        indexes = [
            models.Index(fields=['category', '-is_pinned', '-last_activity_at']),
            models.Index(fields=['is_published', '-last_activity_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
        ]
        permissions = [
            ('can_moderate_threads', 'Can moderate threads'),
            ('can_pin_threads', 'Can pin threads'),
            ('can_lock_threads', 'Can lock threads'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-set is_published based on status
        self.is_published = self.status == 'published'

        super().save(*args, **kwargs)

    def get_post_count(self):
        """Get number of posts (excluding deleted)."""
        return self.posts.filter(is_deleted=False).count()

    def get_last_post(self):
        """Get the most recent post."""
        return self.posts.filter(is_deleted=False).order_by('-created_at').first()

    def increment_view_count(self):
        """Increment view count atomically."""
        Thread.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])


class Post(models.Model):
    """Forum post/reply."""
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='forum_posts'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent post for nested replies"
    )

    # Content
    content = RichTextField()

    # Moderation
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_posts'
    )
    moderation_reason = models.TextField(blank=True)

    # Engagement
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author} on {self.thread.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update thread activity
        if is_new and not self.is_deleted:
            self.thread.update_activity()
            # Update reply count
            Thread.objects.filter(pk=self.thread.pk).update(
                reply_count=models.F('reply_count') + 1
            )

    def get_score(self):
        """Calculate post score (upvotes - downvotes)."""
        return self.upvotes - self.downvotes


class Vote(models.Model):
    """Vote on a post (upvote/downvote)."""
    VOTE_CHOICES = (
        (1, 'Upvote'),
        (-1, 'Downvote'),
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_votes'
    )
    vote_type = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['post', 'vote_type']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} {'upvoted' if self.vote_type == 1 else 'downvoted'} {self.post}"

    def save(self, *args, **kwargs):
        # Update post vote counts
        if self.pk:  # Existing vote
            old_vote = Vote.objects.get(pk=self.pk)
            if old_vote.vote_type != self.vote_type:
                # Vote changed
                if old_vote.vote_type == 1:
                    Post.objects.filter(pk=self.post.pk).update(
                        upvotes=models.F('upvotes') - 1,
                        downvotes=models.F('downvotes') + 1
                    )
                else:
                    Post.objects.filter(pk=self.post.pk).update(
                        upvotes=models.F('upvotes') + 1,
                        downvotes=models.F('downvotes') - 1
                    )
        else:  # New vote
            if self.vote_type == 1:
                Post.objects.filter(pk=self.post.pk).update(
                    upvotes=models.F('upvotes') + 1
                )
            else:
                Post.objects.filter(pk=self.post.pk).update(
                    downvotes=models.F('downvotes') + 1
                )

        super().save(*args, **kwargs)


class Tag(models.Model):
    """Tag for categorizing threads."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text="Hex color code (e.g., #007bff)"
    )

    use_count = models.PositiveIntegerField(default=0, help_text="Number of threads using this tag")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ThreadSubscription(models.Model):
    """User subscription to thread for notifications."""
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='thread_subscriptions'
    )

    # Notification preferences
    email_on_reply = models.BooleanField(default=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['thread', 'user']
        indexes = [
            models.Index(fields=['user', '-subscribed_at']),
        ]

    def __str__(self):
        return f"{self.user} subscribed to {self.thread.title}"

    def has_unread_posts(self):
        """Check if there are unread posts."""
        if not self.last_read_at:
            return True
        return self.thread.posts.filter(
            created_at__gt=self.last_read_at,
            is_deleted=False
        ).exists()


class Report(models.Model):
    """Report inappropriate content."""
    REPORT_TYPE_CHOICES = (
        ('spam', 'Spam'),
        ('offensive', 'Offensive Content'),
        ('harassment', 'Harassment'),
        ('misinformation', 'Misinformation'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )

    # Content being reported (use GenericForeignKey for flexibility)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Report details
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_reports'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField()

    # Moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reported_by', '-created_at']),
        ]

    def __str__(self):
        return f"Report by {self.reported_by} - {self.get_report_type_display()}"

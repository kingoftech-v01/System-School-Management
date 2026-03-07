"""
Articles app models for news, blogs, and announcements.
Includes MPTT hierarchical categories, comments, likes, and newsletter management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField
from autoslug import AutoSlugField

User = get_user_model()


class Category(MPTTModel):
    """Hierarchical category structure using MPTT."""

    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True, always_update=False)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['tree_id', 'lft']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def get_article_count(self):
        """Count published articles in this category and descendants."""
        return Article.published.filter(
            categories__in=self.get_descendants(include_self=True)
        ).distinct().count()


class ArticleQuerySet(models.QuerySet):
    """Custom queryset for Article model."""

    def published(self):
        return self.filter(status='published', published_at__lte=timezone.now())

    def draft(self):
        return self.filter(status='draft')

    def pending(self):
        return self.filter(status='pending')

    def featured(self):
        return self.published().filter(is_featured=True)

    def by_author(self, author):
        return self.filter(author=author)

    def by_category(self, category):
        return self.filter(categories=category)


class ArticleManager(models.Manager):
    """Custom manager for Article model."""

    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()


class Article(models.Model):
    """Article model for news, blogs, and announcements."""

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles'
    )
    categories = models.ManyToManyField(Category, related_name='articles', blank=True)
    tags = TaggableManager(blank=True)

    summary = models.TextField(max_length=500, help_text="Brief summary for previews")
    content = RichTextField()

    featured_image = models.ImageField(
        upload_to='articles/images/%Y/%m/%d/',
        null=True,
        blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Feature on homepage")
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of list")

    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO fields
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    objects = ArticleManager()
    published = ArticleManager()  # Convenience manager

    class Meta:
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['-is_featured', '-published_at']),
        ]
        permissions = [
            ('can_publish_article', 'Can publish articles'),
            ('can_feature_article', 'Can feature articles'),
            ('can_moderate_comments', 'Can moderate comments'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-set published_at on first publish
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def increment_views(self):
        """Increment view counter."""
        self.views_count = models.F('views_count') + 1
        self.save(update_fields=['views_count'])

    def get_reading_time(self):
        """Estimate reading time in minutes (200 words per minute)."""
        from django.utils.html import strip_tags
        word_count = len(strip_tags(self.content).split())
        return max(1, round(word_count / 200))


class Comment(models.Model):
    """Comments on articles."""

    STATUS_CHOICES = (
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('spam', 'Spam'),
    )

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='article_comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    content = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.article.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update article comment count
        if is_new and self.status == 'approved':
            self.article.comments_count = models.F('comments_count') + 1
            self.article.save(update_fields=['comments_count'])


class Like(models.Model):
    """Article likes/favorites."""

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='article_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']
        indexes = [
            models.Index(fields=['article', 'user']),
        ]

    def __str__(self):
        return f"{self.user} likes {self.article.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update article like count
        if is_new:
            self.article.likes_count = models.F('likes_count') + 1
            self.article.save(update_fields=['likes_count'])


class Newsletter(models.Model):
    """Newsletter subscription management."""

    email = models.EmailField(unique=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='newsletter_subscription'
    )

    is_subscribed = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    frequency = models.CharField(
        max_length=20,
        choices=(
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
            ('monthly', 'Monthly Digest'),
        ),
        default='weekly'
    )

    class Meta:
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_subscribed', 'is_verified']),
        ]

    def __str__(self):
        return self.email

    def unsubscribe(self):
        """Unsubscribe from newsletter."""
        self.is_subscribed = False
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['is_subscribed', 'unsubscribed_at'])


class NewsletterSent(models.Model):
    """Track sent newsletters."""

    subject = models.CharField(max_length=200)
    articles = models.ManyToManyField(Article, related_name='newsletters')
    recipients_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_newsletters'
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Newsletter Sent'
        verbose_name_plural = 'Newsletters Sent'

    def __str__(self):
        return f"{self.subject} - {self.sent_at.date()}"

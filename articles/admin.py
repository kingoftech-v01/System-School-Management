"""
Admin configuration for articles app.
"""

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Category, Article, Comment, Like, Newsletter, NewsletterSent


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    """Admin for hierarchical categories."""
    list_display = ['name', 'parent', 'is_active', 'get_article_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin for articles."""
    list_display = ['title', 'author', 'status', 'is_featured', 'is_pinned', 'views_count', 'published_at']
    list_filter = ['status', 'is_featured', 'is_pinned', 'created_at', 'categories']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views_count', 'likes_count', 'comments_count', 'created_at', 'updated_at']
    filter_horizontal = ['categories']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'categories', 'tags')
        }),
        ('Content', {
            'fields': ('summary', 'content', 'featured_image')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_pinned', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'likes_count', 'comments_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_articles', 'feature_articles', 'archive_articles']

    def publish_articles(self, request, queryset):
        queryset.update(status='published')
    publish_articles.short_description = "Publish selected articles"

    def feature_articles(self, request, queryset):
        queryset.update(is_featured=True)
    feature_articles.short_description = "Feature selected articles"

    def archive_articles(self, request, queryset):
        queryset.update(status='archived')
    archive_articles.short_description = "Archive selected articles"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for comments."""
    list_display = ['article', 'author', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['content', 'author__username', 'article__title']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['approve_comments', 'reject_comments', 'mark_as_spam']

    def approve_comments(self, request, queryset):
        queryset.update(status='approved')
    approve_comments.short_description = "Approve selected comments"

    def reject_comments(self, request, queryset):
        queryset.update(status='rejected')
    reject_comments.short_description = "Reject selected comments"

    def mark_as_spam(self, request, queryset):
        queryset.update(status='spam')
    mark_as_spam.short_description = "Mark selected comments as spam"


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin for likes."""
    list_display = ['user', 'article', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'article__title']
    readonly_fields = ['created_at']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin for newsletter subscriptions."""
    list_display = ['email', 'is_subscribed', 'is_verified', 'frequency', 'subscribed_at']
    list_filter = ['is_subscribed', 'is_verified', 'frequency', 'subscribed_at']
    search_fields = ['email', 'user__username']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']

    actions = ['verify_subscriptions', 'unsubscribe_users']

    def verify_subscriptions(self, request, queryset):
        queryset.update(is_verified=True)
    verify_subscriptions.short_description = "Verify selected subscriptions"

    def unsubscribe_users(self, request, queryset):
        for subscription in queryset:
            subscription.unsubscribe()
    unsubscribe_users.short_description = "Unsubscribe selected users"


@admin.register(NewsletterSent)
class NewsletterSentAdmin(admin.ModelAdmin):
    """Admin for sent newsletters."""
    list_display = ['subject', 'recipients_count', 'sent_by', 'sent_at']
    list_filter = ['sent_at']
    search_fields = ['subject']
    readonly_fields = ['sent_at']
    filter_horizontal = ['articles']

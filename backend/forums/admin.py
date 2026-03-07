"""
Admin configuration for forums app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ForumCategory, Thread, Post, Vote, Tag, ThreadSubscription, Report


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    """Admin for forum categories."""
    list_display = ('name', 'order', 'is_active', 'requires_approval', 'get_thread_count', 'get_post_count', 'created_at')
    list_filter = ('is_active', 'requires_approval', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('allowed_groups',)
    readonly_fields = ('created_at', 'updated_at', 'get_thread_count', 'get_post_count')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon', 'order')
        }),
        ('Permissions', {
            'fields': ('is_active', 'requires_approval', 'allowed_groups')
        }),
        ('Statistics', {
            'fields': ('get_thread_count', 'get_post_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_categories', 'deactivate_categories']

    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)
    activate_categories.short_description = "Activate selected categories"

    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_categories.short_description = "Deactivate selected categories"

    def get_thread_count(self, obj):
        return obj.get_thread_count()
    get_thread_count.short_description = 'Threads'

    def get_post_count(self, obj):
        return obj.get_post_count()
    get_post_count.short_description = 'Posts'


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Admin for discussion threads."""
    list_display = ('title', 'category', 'author', 'status', 'is_pinned', 'is_locked', 'is_featured',
                    'view_count', 'reply_count', 'last_activity_at')
    list_filter = ('status', 'is_published', 'is_pinned', 'is_locked', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username', 'author__email')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('view_count', 'reply_count', 'created_at', 'updated_at', 'last_activity_at',
                      'moderated_at', 'get_post_count', 'get_last_post')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Thread Information', {
            'fields': ('category', 'title', 'slug', 'author', 'content', 'tags')
        }),
        ('Status & Moderation', {
            'fields': ('status', 'is_published', 'is_pinned', 'is_locked', 'is_featured')
        }),
        ('Moderation Details', {
            'fields': ('moderated_by', 'moderated_at', 'moderation_notes'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('view_count', 'reply_count', 'get_post_count', 'get_last_post'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_threads', 'pin_threads', 'unpin_threads', 'lock_threads',
               'unlock_threads', 'feature_threads', 'archive_threads']

    def publish_threads(self, request, queryset):
        queryset.update(status='published', is_published=True)
    publish_threads.short_description = "Publish selected threads"

    def pin_threads(self, request, queryset):
        queryset.update(is_pinned=True)
    pin_threads.short_description = "Pin selected threads"

    def unpin_threads(self, request, queryset):
        queryset.update(is_pinned=False)
    unpin_threads.short_description = "Unpin selected threads"

    def lock_threads(self, request, queryset):
        queryset.update(is_locked=True, status='locked')
    lock_threads.short_description = "Lock selected threads"

    def unlock_threads(self, request, queryset):
        queryset.update(is_locked=False, status='published')
    unlock_threads.short_description = "Unlock selected threads"

    def feature_threads(self, request, queryset):
        queryset.update(is_featured=True)
    feature_threads.short_description = "Feature selected threads"

    def archive_threads(self, request, queryset):
        queryset.update(status='archived')
    archive_threads.short_description = "Archive selected threads"

    def get_post_count(self, obj):
        return obj.get_post_count()
    get_post_count.short_description = 'Active Posts'

    def get_last_post(self, obj):
        last_post = obj.get_last_post()
        if last_post:
            return format_html(
                '{} by {} at {}',
                last_post.content[:50] + '...' if len(last_post.content) > 50 else last_post.content,
                last_post.author,
                last_post.created_at.strftime('%Y-%m-%d %H:%M')
            )
        return 'No posts'
    get_last_post.short_description = 'Last Post'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin for forum posts."""
    list_display = ('get_short_content', 'thread', 'author', 'parent', 'upvotes', 'downvotes',
                    'get_score', 'is_deleted', 'is_edited', 'created_at')
    list_filter = ('is_deleted', 'is_edited', 'created_at', 'thread__category')
    search_fields = ('content', 'author__username', 'thread__title')
    readonly_fields = ('upvotes', 'downvotes', 'created_at', 'updated_at', 'edited_at', 'get_score')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Post Information', {
            'fields': ('thread', 'author', 'parent', 'content')
        }),
        ('Moderation', {
            'fields': ('is_deleted', 'is_edited', 'edited_at', 'moderated_by', 'moderation_reason')
        }),
        ('Engagement', {
            'fields': ('upvotes', 'downvotes', 'get_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['soft_delete_posts', 'restore_posts']

    def soft_delete_posts(self, request, queryset):
        queryset.update(is_deleted=True)
    soft_delete_posts.short_description = "Soft delete selected posts"

    def restore_posts(self, request, queryset):
        queryset.update(is_deleted=False)
    restore_posts.short_description = "Restore selected posts"

    def get_short_content(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    get_short_content.short_description = 'Content'

    def get_score(self, obj):
        score = obj.get_score()
        color = 'green' if score > 0 else 'red' if score < 0 else 'gray'
        return format_html('<span style="color: {};">{:+d}</span>', color, score)
    get_score.short_description = 'Score'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin for post votes."""
    list_display = ('user', 'post', 'get_vote_display', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('user__username', 'post__content')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def get_vote_display(self, obj):
        if obj.vote_type == 1:
            return format_html('<span style="color: green;">⬆ Upvote</span>')
        else:
            return format_html('<span style="color: red;">⬇ Downvote</span>')
    get_vote_display.short_description = 'Vote Type'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for thread tags."""
    list_display = ('name', 'get_color_badge', 'use_count', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('use_count', 'created_at')

    fieldsets = (
        ('Tag Information', {
            'fields': ('name', 'slug', 'description', 'color')
        }),
        ('Statistics', {
            'fields': ('use_count',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.name
        )
    get_color_badge.short_description = 'Preview'


@admin.register(ThreadSubscription)
class ThreadSubscriptionAdmin(admin.ModelAdmin):
    """Admin for thread subscriptions."""
    list_display = ('user', 'thread', 'email_on_reply', 'has_unread', 'subscribed_at', 'last_read_at')
    list_filter = ('email_on_reply', 'subscribed_at')
    search_fields = ('user__username', 'thread__title')
    readonly_fields = ('subscribed_at', 'last_read_at', 'has_unread')
    date_hierarchy = 'subscribed_at'

    def has_unread(self, obj):
        return obj.has_unread_posts()
    has_unread.boolean = True
    has_unread.short_description = 'Has Unread'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin for content reports."""
    list_display = ('get_content_type', 'reported_by', 'report_type', 'status', 'reviewed_by', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reported_by__username', 'description', 'resolution_notes')
    readonly_fields = ('created_at', 'reviewed_at', 'content_type', 'object_id')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Report Information', {
            'fields': ('content_type', 'object_id', 'reported_by', 'report_type', 'description')
        }),
        ('Moderation', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'resolution_notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_reviewing', 'mark_resolved', 'mark_dismissed']

    def mark_reviewing(self, request, queryset):
        queryset.update(status='reviewing')
    mark_reviewing.short_description = "Mark as under review"

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_resolved.short_description = "Mark as resolved"

    def mark_dismissed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='dismissed', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_dismissed.short_description = "Dismiss selected reports"

    def get_content_type(self, obj):
        return f"{obj.content_type} (ID: {obj.object_id})"
    get_content_type.short_description = 'Reported Content'

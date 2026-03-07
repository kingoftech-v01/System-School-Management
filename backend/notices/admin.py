"""
Admin configuration for notices app.
"""

from django.contrib import admin
from .models import Notice, NoticeDocument, NotifyGroup, NoticeResponse


class NoticeDocumentInline(admin.TabularInline):
    """Inline admin for notice documents."""
    model = NoticeDocument
    extra = 1
    fields = ('filename', 'file', 'file_size')
    readonly_fields = ('file_size',)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    """Admin for notices with targeted delivery."""
    list_display = ('title', 'uploaded_by', 'priority', 'is_active', 'expires_at', 'created_at', 'get_read_count')
    list_filter = ('priority', 'is_active', 'created_at', 'expires_at')
    search_fields = ('title', 'content', 'uploaded_by__username')
    readonly_fields = ('created_at', 'updated_at', 'get_read_count', 'get_unread_count')
    filter_horizontal = ('notify_groups',)
    date_hierarchy = 'created_at'
    inlines = [NoticeDocumentInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'uploaded_by')
        }),
        ('Targeting', {
            'fields': ('notify_groups',)
        }),
        ('Settings', {
            'fields': ('priority', 'is_active', 'expires_at')
        }),
        ('Statistics', {
            'fields': ('get_read_count', 'get_unread_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_notices', 'deactivate_notices', 'mark_as_urgent']

    def activate_notices(self, request, queryset):
        queryset.update(is_active=True)
    activate_notices.short_description = "Activate selected notices"

    def deactivate_notices(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_notices.short_description = "Deactivate selected notices"

    def mark_as_urgent(self, request, queryset):
        queryset.update(priority='urgent')
    mark_as_urgent.short_description = "Mark as urgent"

    def get_read_count(self, obj):
        return obj.responses.filter(acknowledged=True).count()
    get_read_count.short_description = 'Read Count'

    def get_unread_count(self, obj):
        return obj.responses.filter(acknowledged=False).count()
    get_unread_count.short_description = 'Unread Count'


@admin.register(NoticeDocument)
class NoticeDocumentAdmin(admin.ModelAdmin):
    """Admin for notice attachments."""
    list_display = ('filename', 'notice', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'notice__title')
    readonly_fields = ('uploaded_at', 'file_size')


@admin.register(NotifyGroup)
class NotifyGroupAdmin(admin.ModelAdmin):
    """Admin for notice target groups."""
    list_display = ('name', 'description', 'get_member_count', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('users',)
    readonly_fields = ('created_at',)

    def get_member_count(self, obj):
        return obj.users.count()
    get_member_count.short_description = 'Members'


@admin.register(NoticeResponse)
class NoticeResponseAdmin(admin.ModelAdmin):
    """Admin for notice acknowledgments."""
    list_display = ('notice', 'user', 'acknowledged', 'acknowledged_at', 'read_at')
    list_filter = ('acknowledged', 'read_at', 'acknowledged_at')
    search_fields = ('notice__title', 'user__username')
    readonly_fields = ('read_at', 'acknowledged_at')

    actions = ['mark_as_acknowledged']

    def mark_as_acknowledged(self, request, queryset):
        from django.utils import timezone
        queryset.update(acknowledged=True, acknowledged_at=timezone.now())
    mark_as_acknowledged.short_description = "Mark as acknowledged"

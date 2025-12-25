"""
Admin configuration for core app.
Includes tenant management and shared models.
"""

from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from modeltranslation.admin import TranslationAdmin
from .models import School, Domain, Session, Semester, NewsAndEvents, ActivityLog


@admin.register(School)
class SchoolAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin for School (Tenant) model."""
    list_display = ('name', 'slug', 'email', 'subscription_type', 'subscription_end', 'is_active', 'is_subscription_valid')
    list_filter = ('is_active', 'subscription_type', 'country')
    search_fields = ('name', 'slug', 'email', 'license_key')
    readonly_fields = ('created_on', 'updated_on', 'schema_name')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'schema_name')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'country', 'postal_code')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color')
        }),
        ('Subscription & License', {
            'fields': ('license_key', 'subscription_type', 'subscription_start', 'subscription_end', 'is_active', 'max_students', 'max_staff')
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin for Domain model."""
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__name')


class NewsAndEventsAdmin(TranslationAdmin):
    list_display = ('title', 'posted_as', 'upload_time', 'updated_date')
    list_filter = ('posted_as', 'upload_time')
    search_fields = ('title', 'summary')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session', 'is_current_session', 'next_session_begins')
    list_filter = ('is_current_session',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('semester', 'session', 'is_current_semester', 'next_semester_begins')
    list_filter = ('is_current_semester', 'session')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('message',)
    readonly_fields = ('created_at',)


admin.site.register(NewsAndEvents, NewsAndEventsAdmin)

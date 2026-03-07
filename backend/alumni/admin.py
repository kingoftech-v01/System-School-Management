"""
Admin configuration for alumni app.
"""

from django.contrib import admin
from .models import Alumni, AlumniEvent, AlumniDonation, AlumniAchievement


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    """Admin for alumni records."""
    list_display = ('student', 'graduation_year', 'current_occupation', 'current_employer', 'is_active')
    list_filter = ('graduation_year', 'is_active', 'willing_to_mentor')
    search_fields = ('student__student__first_name', 'student__student__last_name', 'personal_email', 'current_employer')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'graduation_year', 'graduation_date')
        }),
        ('Career Information', {
            'fields': ('current_occupation', 'current_employer', 'industry', 'job_title')
        }),
        ('Contact Information', {
            'fields': ('personal_email', 'phone', 'linkedin_url', 'city', 'country')
        }),
        ('Engagement', {
            'fields': ('is_active', 'willing_to_mentor', 'newsletter_subscribed')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_alumni', 'deactivate_alumni']

    def activate_alumni(self, request, queryset):
        queryset.update(is_active=True)
    activate_alumni.short_description = "Activate selected alumni"

    def deactivate_alumni(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_alumni.short_description = "Deactivate selected alumni"


@admin.register(AlumniEvent)
class AlumniEventAdmin(admin.ModelAdmin):
    """Admin for alumni events."""
    list_display = ('title', 'event_type', 'event_date', 'location', 'get_attendee_count', 'is_active', 'created_at')
    list_filter = ('event_type', 'event_date', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location')
    filter_horizontal = ('attendees',)
    readonly_fields = ('created_at', 'updated_at', 'get_attendee_count')
    date_hierarchy = 'event_date'

    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'event_type', 'event_date', 'end_date', 'location', 'venue_details')
        }),
        ('Registration', {
            'fields': ('max_attendees', 'registration_deadline', 'registration_fee', 'attendees')
        }),
        ('Management', {
            'fields': ('organizer', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_attendee_count(self, obj):
        return obj.attendees.count()
    get_attendee_count.short_description = 'Attendees'


@admin.register(AlumniDonation)
class AlumniDonationAdmin(admin.ModelAdmin):
    """Admin for alumni donations."""
    list_display = ('alumni', 'amount', 'currency', 'purpose', 'is_anonymous', 'tax_receipt_sent', 'donated_at')
    list_filter = ('purpose', 'is_anonymous', 'currency', 'tax_receipt_sent', 'donated_at')
    search_fields = ('alumni__student__student__first_name', 'alumni__student__student__last_name', 'purpose_details', 'notes', 'transaction_id')
    readonly_fields = ('donated_at', 'thank_you_sent_at')
    date_hierarchy = 'donated_at'

    fieldsets = (
        ('Donation Information', {
            'fields': ('alumni', 'amount', 'currency', 'purpose', 'purpose_details')
        }),
        ('Payment Information', {
            'fields': ('transaction_id', 'payment_method')
        }),
        ('Recognition & Acknowledgment', {
            'fields': ('is_anonymous', 'tax_receipt_sent', 'tax_receipt_number', 'thank_you_sent', 'thank_you_sent_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('donated_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_receipt_sent', 'mark_thank_you_sent']

    def mark_receipt_sent(self, request, queryset):
        queryset.update(tax_receipt_sent=True)
    mark_receipt_sent.short_description = "Mark tax receipt as sent"

    def mark_thank_you_sent(self, request, queryset):
        from django.utils import timezone
        queryset.update(thank_you_sent=True, thank_you_sent_at=timezone.now())
    mark_thank_you_sent.short_description = "Mark thank you as sent"


@admin.register(AlumniAchievement)
class AlumniAchievementAdmin(admin.ModelAdmin):
    """Admin for alumni achievements."""
    list_display = ('alumni', 'title', 'achievement_type', 'is_featured', 'is_published', 'achievement_date', 'created_at')
    list_filter = ('achievement_type', 'is_featured', 'is_published', 'achievement_date')
    search_fields = ('title', 'description', 'alumni__student__student__first_name', 'alumni__student__student__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'achievement_date'

    fieldsets = (
        ('Achievement Information', {
            'fields': ('alumni', 'title', 'description', 'achievement_type', 'achievement_date')
        }),
        ('Media', {
            'fields': ('image', 'url')
        }),
        ('Display', {
            'fields': ('is_featured', 'is_published')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['feature_achievements', 'unfeature_achievements']

    def feature_achievements(self, request, queryset):
        queryset.update(is_featured=True)
    feature_achievements.short_description = "Feature selected achievements"

    def unfeature_achievements(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature_achievements.short_description = "Unfeature selected achievements"

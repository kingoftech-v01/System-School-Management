"""
Admin interface for filieres management.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Filiere, FiliereSubject, FiliereRequirement


class FiliereSubjectInline(admin.TabularInline):
    """Inline admin for filiere subjects."""
    model = FiliereSubject
    extra = 1
    fields = ('subject', 'coefficient', 'is_mandatory', 'year', 'semester', 'credits', 'hours_per_week')
    autocomplete_fields = ['subject']


class FiliereRequirementInline(admin.TabularInline):
    """Inline admin for filiere requirements."""
    model = FiliereRequirement
    extra = 1
    fields = ('requirement_type', 'description', 'is_mandatory', 'order')


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    """Admin interface for Filiere model."""

    list_display = (
        'code',
        'name',
        'level',
        'duration_years',
        'status_badge',
        'enrollment_info',
        'coordinator',
        'tenant'
    )
    list_filter = (
        'is_active',
        'level',
        'duration_years',
        'tenant',
        'created_at'
    )
    search_fields = (
        'name',
        'code',
        'description'
    )
    readonly_fields = ('created_at', 'updated_at', 'enrollment_info')
    fieldsets = (
        (_('Tenant Information'), {
            'fields': ('tenant',)
        }),
        (_('Basic Information'), {
            'fields': (
                'name',
                'code',
                'description',
                'level'
            )
        }),
        (_('Program Details'), {
            'fields': (
                'duration_years',
                'capacity',
                'coordinator'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'enrollment_info',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [FiliereSubjectInline, FiliereRequirementInline]
    list_per_page = 50

    def status_badge(self, obj):
        """Display status with color badge."""
        if obj.is_active:
            color = '#28a745'  # Green
            text = _('Active')
        else:
            color = '#dc3545'  # Red
            text = _('Inactive')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            text
        )
    status_badge.short_description = _('Status')

    def enrollment_info(self, obj):
        """Display enrollment statistics."""
        enrolled = obj.get_enrolled_students_count()
        capacity = obj.capacity if obj.capacity else '∞'
        total_subjects = obj.get_total_subjects()

        return format_html(
            '<strong>Students:</strong> {} / {}<br>'
            '<strong>Subjects:</strong> {}',
            enrolled,
            capacity,
            total_subjects
        )
    enrollment_info.short_description = _('Enrollment Info')

    def get_queryset(self, request):
        """Filter queryset by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs.select_related('tenant', 'coordinator').prefetch_related('subjects')

    def save_model(self, request, obj, form, change):
        """Set tenant automatically if not set."""
        if not obj.pk and not obj.tenant_id:
            if hasattr(request, 'tenant'):
                obj.tenant = request.tenant
        super().save_model(request, obj, form, change)


@admin.register(FiliereSubject)
class FiliereSubjectAdmin(admin.ModelAdmin):
    """Admin interface for FiliereSubject model."""

    list_display = (
        'filiere',
        'subject',
        'year',
        'semester',
        'coefficient',
        'credits',
        'is_mandatory',
        'hours_per_week'
    )
    list_filter = (
        'is_mandatory',
        'year',
        'semester',
        'filiere__tenant'
    )
    search_fields = (
        'filiere__name',
        'filiere__code',
        'subject__title'
    )
    list_editable = ('coefficient', 'is_mandatory')
    autocomplete_fields = ['filiere', 'subject']

    def get_queryset(self, request):
        """Filter by tenant."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(filiere__tenant=request.tenant)
        return qs.select_related('filiere', 'subject')


@admin.register(FiliereRequirement)
class FiliereRequirementAdmin(admin.ModelAdmin):
    """Admin interface for FiliereRequirement model."""

    list_display = (
        'filiere',
        'requirement_type',
        'is_mandatory',
        'order',
        'description_preview'
    )
    list_filter = (
        'requirement_type',
        'is_mandatory',
        'filiere__tenant'
    )
    search_fields = (
        'filiere__name',
        'description'
    )
    list_editable = ('order', 'is_mandatory')

    def description_preview(self, obj):
        """Show preview of description."""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = _('Description')

    def get_queryset(self, request):
        """Filter by tenant."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(filiere__tenant=request.tenant)
        return qs.select_related('filiere')

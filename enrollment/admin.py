"""
Admin interface for enrollment management.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory


class EnrollmentDocumentInline(admin.TabularInline):
    """Inline admin for enrollment documents."""
    model = EnrollmentDocument
    extra = 0
    readonly_fields = ('uploaded_at', 'verified_by', 'get_file_size')
    fields = ('document_type', 'file', 'description', 'is_verified', 'verified_by', 'get_file_size')

    def get_file_size(self, obj):
        if obj.file:
            return f"{obj.get_file_size()} MB"
        return "-"
    get_file_size.short_description = _('File Size')


class EnrollmentStatusHistoryInline(admin.TabularInline):
    """Inline admin for status history."""
    model = EnrollmentStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at', 'notes')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegistrationForm)
class RegistrationFormAdmin(admin.ModelAdmin):
    """Admin interface for registration forms."""

    list_display = (
        'student_name',
        'colored_status',
        'enrollment_type',
        'filiere',
        'academic_year',
        'submitted_at',
        'completion_badge',
        'reviewed_by',
        'tenant'
    )
    list_filter = (
        'status',
        'enrollment_type',
        'level',
        'academic_year',
        'gender',
        'filiere',
        'submitted_at',
        'tenant'
    )
    search_fields = (
        'student_name',
        'email',
        'phone',
        'parent_name',
        'parent_email'
    )
    readonly_fields = (
        'submitted_at',
        'updated_at',
        'reviewed_at',
        'completion_badge',
        'enrolled_user'
    )
    fieldsets = (
        (_('Tenant Information'), {
            'fields': ('tenant',)
        }),
        (_('Student Information'), {
            'fields': (
                'student_name',
                'date_of_birth',
                'gender',
                'nationality',
                'email',
                'phone',
                'address'
            )
        }),
        (_('Parent/Guardian Information'), {
            'fields': (
                'parent_name',
                'parent_email',
                'parent_phone',
                'parent_relationship'
            )
        }),
        (_('Academic Information'), {
            'fields': (
                'enrollment_type',
                'filiere',
                'academic_year',
                'level',
                'previous_school'
            )
        }),
        (_('Review & Status'), {
            'fields': (
                'status',
                'reviewed_by',
                'reviewed_at',
                'review_notes',
                'rejection_reason'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'special_needs',
                'medical_information'
            ),
            'classes': ('collapse',)
        }),
        (_('Enrollment Result'), {
            'fields': ('enrolled_user',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': (
                'submitted_at',
                'updated_at',
                'completion_badge'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [EnrollmentDocumentInline, EnrollmentStatusHistoryInline]
    actions = ['approve_registrations', 'reject_registrations', 'mark_under_review']
    date_hierarchy = 'submitted_at'
    list_per_page = 50

    def colored_status(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#FFA500',  # Orange
            'under_review': '#0000FF',  # Blue
            'approved': '#008000',  # Green
            'rejected': '#FF0000',  # Red
            'enrolled': '#800080',  # Purple
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = _('Status')
    colored_status.admin_order_field = 'status'

    def completion_badge(self, obj):
        """Display completion percentage as badge."""
        percentage = obj.get_completion_percentage()
        color = '#008000' if percentage == 100 else '#FFA500' if percentage >= 75 else '#FF0000'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} %</span>',
            color,
            percentage
        )
    completion_badge.short_description = _('Completion')

    def get_queryset(self, request):
        """Filter queryset by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs.select_related('tenant', 'filiere', 'reviewed_by', 'enrolled_user')

    def save_model(self, request, obj, form, change):
        """Set tenant and track status changes."""
        if not obj.pk and not obj.tenant_id:
            if hasattr(request, 'tenant'):
                obj.tenant = request.tenant

        # Track status change
        if change and 'status' in form.changed_data:
            old_obj = RegistrationForm.objects.get(pk=obj.pk)
            EnrollmentStatusHistory.objects.create(
                registration=obj,
                old_status=old_obj.status,
                new_status=obj.status,
                changed_by=request.user,
                notes=obj.review_notes
            )
            obj.reviewed_by = request.user

        super().save_model(request, obj, form, change)

    def approve_registrations(self, request, queryset):
        """Bulk approve registrations."""
        count = queryset.update(
            status='approved',
            reviewed_by=request.user
        )
        self.message_user(request, _(f'{count} registration(s) approved successfully.'))
    approve_registrations.short_description = _('Approve selected registrations')

    def reject_registrations(self, request, queryset):
        """Bulk reject registrations."""
        count = queryset.update(
            status='rejected',
            reviewed_by=request.user
        )
        self.message_user(request, _(f'{count} registration(s) rejected.'))
    reject_registrations.short_description = _('Reject selected registrations')

    def mark_under_review(self, request, queryset):
        """Mark registrations as under review."""
        count = queryset.update(status='under_review')
        self.message_user(request, _(f'{count} registration(s) marked as under review.'))
    mark_under_review.short_description = _('Mark as under review')


@admin.register(EnrollmentDocument)
class EnrollmentDocumentAdmin(admin.ModelAdmin):
    """Admin interface for enrollment documents."""

    list_display = (
        'document_type',
        'registration',
        'is_verified',
        'verified_by',
        'uploaded_at',
        'file_size_display'
    )
    list_filter = (
        'document_type',
        'is_verified',
        'uploaded_at',
        'registration__tenant'
    )
    search_fields = (
        'registration__student_name',
        'description'
    )
    readonly_fields = ('uploaded_at', 'file_size_display')
    date_hierarchy = 'uploaded_at'

    def file_size_display(self, obj):
        """Display file size."""
        return f"{obj.get_file_size()} MB"
    file_size_display.short_description = _('File Size')

    def get_queryset(self, request):
        """Filter by tenant."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(registration__tenant=request.tenant)
        return qs.select_related('registration', 'verified_by')


@admin.register(EnrollmentStatusHistory)
class EnrollmentStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for status history (read-only)."""

    list_display = (
        'registration',
        'old_status',
        'new_status',
        'changed_by',
        'changed_at'
    )
    list_filter = (
        'old_status',
        'new_status',
        'changed_at',
        'registration__tenant'
    )
    search_fields = (
        'registration__student_name',
        'notes'
    )
    readonly_fields = (
        'registration',
        'old_status',
        'new_status',
        'changed_by',
        'notes',
        'changed_at'
    )
    date_hierarchy = 'changed_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        """Filter by tenant."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(registration__tenant=request.tenant)
        return qs.select_related('registration', 'changed_by')

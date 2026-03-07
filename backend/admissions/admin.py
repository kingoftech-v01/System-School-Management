"""
Admin configuration for admissions app.
"""

from django.contrib import admin
from .models import AdmissionSession, AdmissionStudent, CounselingComment, AdmissionPayment


@admin.register(AdmissionSession)
class AdmissionSessionAdmin(admin.ModelAdmin):
    """Admin for admission sessions."""
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'get_application_count')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

    def get_application_count(self, obj):
        return obj.applications.count()
    get_application_count.short_description = 'Applications'


class CounselingCommentInline(admin.TabularInline):
    """Inline admin for counseling comments."""
    model = CounselingComment
    extra = 1
    fields = ('counselor', 'comment', 'is_recommendation', 'created_at')
    readonly_fields = ('created_at',)


class AdmissionPaymentInline(admin.TabularInline):
    """Inline admin for admission payments."""
    model = AdmissionPayment
    extra = 0
    fields = ('amount', 'transaction_id', 'payment_method', 'verified', 'verified_by', 'paid_at')
    readonly_fields = ('paid_at',)


@admin.register(AdmissionStudent)
class AdmissionStudentAdmin(admin.ModelAdmin):
    """Admin for admission applications."""
    list_display = ('get_full_name', 'email', 'program', 'status', 'created_at')
    list_filter = ('status', 'session', 'program', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CounselingCommentInline, AdmissionPaymentInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'nationality', 'address')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_email')
        }),
        ('Academic Information', {
            'fields': ('program', 'previous_school', 'previous_grade', 'exam_scores')
        }),
        ('Application Status', {
            'fields': ('session', 'status', 'reviewed_by', 'counselor', 'rejection_reason')
        }),
        ('Payment & Admission', {
            'fields': ('application_fee_paid', 'admitted', 'admission_date')
        }),
        ('Documents', {
            'fields': ('transcript', 'birth_certificate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_applications', 'reject_applications', 'move_to_counseling']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Name'

    def approve_applications(self, request, queryset):
        queryset.update(status='admitted')
    approve_applications.short_description = "Approve applications"

    def reject_applications(self, request, queryset):
        queryset.update(status='rejected')
    reject_applications.short_description = "Reject applications"

    def move_to_counseling(self, request, queryset):
        queryset.update(status='counseling')
    move_to_counseling.short_description = "Move to counseling"


@admin.register(CounselingComment)
class CounselingCommentAdmin(admin.ModelAdmin):
    """Admin for counseling comments."""
    list_display = ('application', 'counselor', 'is_recommendation', 'created_at')
    list_filter = ('created_at', 'counselor', 'is_recommendation')
    search_fields = ('application__first_name', 'application__last_name', 'comment')
    readonly_fields = ('created_at',)


@admin.register(AdmissionPayment)
class AdmissionPaymentAdmin(admin.ModelAdmin):
    """Admin for admission payments."""
    list_display = ('application', 'amount', 'payment_method', 'verified', 'verified_by', 'paid_at')
    list_filter = ('verified', 'payment_method', 'paid_at')
    search_fields = ('application__first_name', 'application__last_name', 'transaction_id')
    readonly_fields = ('paid_at', 'verified_at')

    actions = ['verify_payments']

    def verify_payments(self, request, queryset):
        from django.utils import timezone
        queryset.update(verified=True, verified_by=request.user, verified_at=timezone.now())
    verify_payments.short_description = "Verify selected payments"

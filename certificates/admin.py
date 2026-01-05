"""
Admin configuration for certificates app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import CertificateTemplate, Certificate, CertificateVerification, BatchCertificateGeneration


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    """Admin for certificate templates."""
    list_display = ('name', 'orientation', 'page_size', 'is_active', 'created_at')
    list_filter = ('is_active', 'orientation', 'page_size', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description')
        }),
        ('Template Design', {
            'fields': ('template_file', 'background_image', 'title_text', 'body_template')
        }),
        ('Signature Configuration', {
            'fields': (
                'signature_1_name', 'signature_1_title', 'signature_1_image',
                'signature_2_name', 'signature_2_title', 'signature_2_image'
            )
        }),
        ('Page Settings', {
            'fields': ('orientation', 'page_size')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_templates', 'deactivate_templates']

    def activate_templates(self, request, queryset):
        queryset.update(is_active=True)
    activate_templates.short_description = "Activate selected templates"

    def deactivate_templates(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_templates.short_description = "Deactivate selected templates"


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin for issued certificates."""
    list_display = ('certificate_number', 'student', 'course', 'template', 'issue_date',
                    'is_revoked', 'get_verification_status', 'created_at')
    list_filter = ('is_revoked', 'issue_date', 'created_at')
    search_fields = ('certificate_number', 'student__student__first_name', 'student__student__last_name',
                    'course__name', 'hash_signature', 'blockchain_hash')
    readonly_fields = ('certificate_number', 'hash_signature', 'blockchain_hash', 'qr_code',
                      'created_at', 'updated_at', 'get_verification_count', 'get_qr_preview')
    date_hierarchy = 'issue_date'

    fieldsets = (
        ('Certificate Information', {
            'fields': ('student', 'course', 'template', 'issue_date')
        }),
        ('Certificate Details', {
            'fields': ('certificate_number', 'grade', 'honors', 'additional_info')
        }),
        ('Digital Verification', {
            'fields': ('hash_signature', 'blockchain_hash', 'qr_code', 'get_qr_preview'),
            'classes': ('collapse',)
        }),
        ('Certificate File', {
            'fields': ('certificate_file',)
        }),
        ('Revocation', {
            'fields': ('is_revoked', 'revoked_at', 'revocation_reason'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('get_verification_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['revoke_certificates', 'unrevoke_certificates', 'regenerate_hash']

    def revoke_certificates(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_revoked=True, revoked_at=timezone.now())
    revoke_certificates.short_description = "Revoke selected certificates"

    def unrevoke_certificates(self, request, queryset):
        queryset.update(is_revoked=False, revoked_at=None, revocation_reason='')
    unrevoke_certificates.short_description = "Unrevoke selected certificates"

    def regenerate_hash(self, request, queryset):
        count = 0
        for cert in queryset:
            cert.hash_signature = cert.calculate_hash()
            cert.save(update_fields=['hash_signature'])
            count += 1
        self.message_user(request, f"Regenerated hash for {count} certificate(s)")
    regenerate_hash.short_description = "Regenerate hash signatures"

    def get_verification_status(self, obj):
        if obj.is_revoked:
            return format_html('<span style="color: red;">❌ Revoked</span>')
        elif obj.hash_signature:
            return format_html('<span style="color: green;">✓ Verified</span>')
        else:
            return format_html('<span style="color: orange;">⚠ No Hash</span>')
    get_verification_status.short_description = 'Status'

    def get_verification_count(self, obj):
        return obj.verifications.count()
    get_verification_count.short_description = 'Verification Count'

    def get_qr_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150"/>', obj.qr_code.url)
        return 'No QR code'
    get_qr_preview.short_description = 'QR Code Preview'


@admin.register(CertificateVerification)
class CertificateVerificationAdmin(admin.ModelAdmin):
    """Admin for certificate verifications."""
    list_display = ('certificate', 'get_verified_by', 'verification_method', 'is_valid', 'verified_at')
    list_filter = ('verification_method', 'is_valid', 'verified_at')
    search_fields = ('certificate__certificate_number', 'verified_by_email', 'ip_address', 'notes')
    readonly_fields = ('verified_at',)
    date_hierarchy = 'verified_at'

    fieldsets = (
        ('Verification Information', {
            'fields': ('certificate', 'verified_by_email', 'verification_method', 'is_valid')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('verified_at',),
            'classes': ('collapse',)
        }),
    )

    def get_verified_by(self, obj):
        return obj.verified_by_email or 'Anonymous'
    get_verified_by.short_description = 'Verified By'


@admin.register(BatchCertificateGeneration)
class BatchCertificateGenerationAdmin(admin.ModelAdmin):
    """Admin for batch certificate generation."""
    list_display = ('course', 'template', 'status', 'get_progress', 'success_count', 'get_failed_count',
                    'get_created_by', 'created_at')
    list_filter = ('status', 'created_at', 'completed_at')
    search_fields = ('course__name', 'created_by__username', 'error_log')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'get_progress', 'get_success_rate')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Batch Information', {
            'fields': ('course', 'template', 'created_by')
        }),
        ('Filter Criteria', {
            'fields': ('grade_threshold', 'include_honors_only'),
            'classes': ('collapse',)
        }),
        ('Progress Tracking', {
            'fields': ('status', 'total_students', 'processed_count', 'success_count', 'failed_count',
                      'get_progress', 'get_success_rate')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Error Details', {
            'fields': ('error_log',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_pending', 'mark_completed']

    def mark_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_pending.short_description = "Mark as pending"

    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', completed_at=timezone.now())
    mark_completed.short_description = "Mark as completed"

    def get_progress(self, obj):
        if obj.total_students == 0:
            percentage = 0
        else:
            percentage = (obj.processed_count / obj.total_students) * 100

        color = 'green' if percentage == 100 else 'orange' if percentage > 0 else 'gray'
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; border-radius:3px;">'
            '{:.0f}%</div></div>',
            percentage, color, percentage
        )
    get_progress.short_description = 'Progress'

    def get_success_rate(self, obj):
        if obj.processed_count == 0:
            return '0%'
        rate = (obj.success_count / obj.processed_count) * 100
        color = 'green' if rate > 90 else 'orange' if rate > 70 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    get_success_rate.short_description = 'Success Rate'

    def get_failed_count(self, obj):
        return obj.failed_count
    get_failed_count.short_description = 'Failed'

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else 'Unknown'
    get_created_by.short_description = 'Created By'

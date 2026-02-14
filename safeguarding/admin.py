from django.contrib import admin
from .models import Incident, IncidentAttachment, VisitorLog, StudentCaseNote


class IncidentAttachmentInline(admin.TabularInline):
    model = IncidentAttachment
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'incident_type', 'severity', 'status',
        'incident_date', 'reported_by', 'tenant',
    )
    list_filter = ('incident_type', 'severity', 'status', 'incident_date', 'tenant')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at', 'reported_by', 'updated_by')
    inlines = [IncidentAttachmentInline]
    filter_horizontal = ('students_involved', 'staff_involved')
    fieldsets = (
        ('Incident Information', {
            'fields': (
                'tenant', 'incident_type', 'title', 'description',
                'severity', 'status',
            )
        }),
        ('When & Where', {
            'fields': ('incident_date', 'incident_time', 'location')
        }),
        ('People Involved', {
            'fields': (
                'students_involved', 'staff_involved',
                'external_parties', 'witnesses',
            )
        }),
        ('Response', {
            'fields': (
                'actions_taken', 'follow_up_needed', 'follow_up_date',
                'follow_up_notes', 'resolution',
            )
        }),
        ('Links', {
            'fields': ('disciplinary_action',),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': (
                'reported_by', 'updated_by', 'created_at', 'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = (
        'visitor_name', 'visitor_type', 'organization',
        'time_in', 'time_out', 'host_staff', 'id_verified',
    )
    list_filter = ('visitor_type', 'id_verified', 'time_in', 'tenant')
    search_fields = ('visitor_name', 'organization', 'purpose')
    readonly_fields = ('created_at', 'updated_at', 'logged_by')
    filter_horizontal = ('students_involved',)


@admin.register(StudentCaseNote)
class StudentCaseNoteAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'title', 'category', 'confidentiality',
        'created_by', 'created_at', 'follow_up_date',
    )
    list_filter = ('category', 'confidentiality', 'follow_up_completed', 'tenant')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

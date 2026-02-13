from django.contrib import admin
from .models import ReportExportLog


@admin.register(ReportExportLog)
class ReportExportLogAdmin(admin.ModelAdmin):
    list_display = (
        'report_type', 'export_format', 'title',
        'exported_by', 'exported_at', 'ip_address',
    )
    list_filter = ('report_type', 'export_format', 'exported_at')
    search_fields = ('title', 'export_reason', 'exported_by__username')
    date_hierarchy = 'exported_at'
    readonly_fields = (
        'report_type', 'export_format', 'title',
        'exported_by', 'exported_at', 'export_reason',
        'student_id', 'incident_id', 'filter_params',
        'ip_address', 'user_agent', 'tenant',
    )
    ordering = ('-exported_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

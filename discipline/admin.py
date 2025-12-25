from django.contrib import admin
from .models import DisciplinaryAction


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ('student', 'incident_type', 'severity', 'incident_date', 'is_resolved', 'tenant')
    list_filter = ('severity', 'is_resolved', 'incident_date', 'tenant')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'incident_type', 'description')
    readonly_fields = ('created_at', 'updated_at', 'reported_by', 'updated_by')

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'student', 'reported_by', 'incident_type', 'severity')
        }),
        ('Details', {
            'fields': ('description', 'action_taken', 'incident_date', 'resolution_date', 'is_resolved')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)

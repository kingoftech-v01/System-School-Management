from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'target_audience', 'tenant')
    list_filter = ('event_type', 'target_audience', 'tenant', 'start_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'reminder_sent')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs

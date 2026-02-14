from django.contrib import admin
from .models import AnomalyType, AnomalyThreshold, AnomalyAlert


class AnomalyThresholdInline(admin.TabularInline):
    model = AnomalyThreshold
    extra = 1


@admin.register(AnomalyType)
class AnomalyTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'domain', 'severity', 'is_enabled']
    list_filter = ['domain', 'severity', 'is_enabled']
    search_fields = ['code', 'name']
    inlines = [AnomalyThresholdInline]


@admin.register(AnomalyAlert)
class AnomalyAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'anomaly_type', 'severity', 'status', 'user', 'detected_at', 'email_sent']
    list_filter = ['severity', 'status', 'anomaly_type__domain', 'email_sent']
    search_fields = ['title', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['detected_at', 'acknowledged_at', 'resolved_at', 'details']
    date_hierarchy = 'detected_at'

from django.contrib import admin
from .models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'building', 'floor', 'capacity', 'room_type', 'is_active', 'tenant')
    list_filter = ('room_type', 'is_active', 'building', 'tenant')
    search_fields = ('name', 'code', 'building')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'day_of_week', 'start_time', 'end_time', 'slot_type', 'order', 'is_active', 'tenant')
    list_filter = ('day_of_week', 'slot_type', 'is_active', 'tenant')
    ordering = ('day_of_week', 'order', 'start_time')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(ProfessorAvailability)
class ProfessorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('professor', 'time_slot', 'preference')
    list_filter = ('preference',)
    search_fields = ('professor__first_name', 'professor__last_name')


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = (
        'course', 'professor', 'room', 'time_slot', 'filiere',
        'recurrence', 'status', 'is_locked', 'tenant',
    )
    list_filter = ('status', 'recurrence', 'is_locked', 'semester', 'tenant')
    search_fields = ('course__title', 'professor__first_name', 'professor__last_name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('professor', 'created_by')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display = (
        'schedule_entry', 'exception_type', 'date',
        'is_approved', 'notification_sent', 'tenant',
    )
    list_filter = ('exception_type', 'is_approved', 'notification_sent', 'tenant')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(SubstitutionRequest)
class SubstitutionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'requesting_professor', 'schedule_entry', 'date',
        'status', 'assigned_substitute', 'tenant',
    )
    list_filter = ('status', 'tenant')
    search_fields = (
        'requesting_professor__first_name', 'requesting_professor__last_name',
    )
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(ScheduleNotification)
class ScheduleNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'email_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'email_sent', 'tenant')
    search_fields = ('title', 'recipient__first_name', 'recipient__last_name')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(TimetableGeneration)
class TimetableGenerationAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'session', 'semester', 'status',
        'entries_created', 'conflicts_found', 'is_published', 'tenant',
    )
    list_filter = ('status', 'is_published', 'tenant')
    readonly_fields = ('created_at', 'started_at', 'completed_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs

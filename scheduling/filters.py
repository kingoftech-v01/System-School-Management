import django_filters
from .models import (
    Room, TimeSlot, ScheduleEntry, ScheduleException,
    SubstitutionRequest, ScheduleNotification,
)


class RoomFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    building = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Room
        fields = ['room_type', 'is_active', 'building']


class TimeSlotFilter(django_filters.FilterSet):
    class Meta:
        model = TimeSlot
        fields = ['day_of_week', 'slot_type', 'is_active']


class ScheduleEntryFilter(django_filters.FilterSet):
    course_title = django_filters.CharFilter(
        field_name='course__title', lookup_expr='icontains'
    )
    professor_name = django_filters.CharFilter(
        method='filter_professor_name'
    )

    class Meta:
        model = ScheduleEntry
        fields = ['status', 'recurrence', 'filiere', 'semester', 'room']

    def filter_professor_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(professor__first_name__icontains=value) |
            models.Q(professor__last_name__icontains=value)
        )


class SubstitutionRequestFilter(django_filters.FilterSet):
    class Meta:
        model = SubstitutionRequest
        fields = ['status']


class ScheduleNotificationFilter(django_filters.FilterSet):
    class Meta:
        model = ScheduleNotification
        fields = ['notification_type', 'is_read']

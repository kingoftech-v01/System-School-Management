"""Template tags for the scheduling app."""

from datetime import date

from django import template

from scheduling.models import ScheduleEntry

register = template.Library()


@register.inclusion_tag(
    'scheduling/includes/todays_schedule_widget.html',
    takes_context=True,
)
def todays_schedule(context):
    """Render today's schedule widget for the current user."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return {'schedule_entries': []}

    user = request.user
    role = getattr(user, 'role', 'student')
    today = date.today()

    # Get tenant
    if hasattr(request, 'tenant') and request.tenant:
        tenant = request.tenant
    else:
        from core.models import School
        tenant, _ = School.objects.get_or_create(
            slug='default',
            defaults={'name': 'Default School', 'email': 'admin@school.local'},
        )

    entries = ScheduleEntry.objects.filter(
        tenant=tenant,
        status='active',
        effective_from__lte=today,
        effective_until__gte=today,
        time_slot__day_of_week=today.weekday(),
    ).select_related('course', 'professor', 'room', 'time_slot', 'filiere')

    if role == 'professor':
        entries = entries.filter(professor=user)
    elif role == 'student':
        student_profile = getattr(user, 'student', None)
        if student_profile and student_profile.program:
            entries = entries.filter(filiere=student_profile.program)
        else:
            entries = entries.none()
    elif role == 'parent':
        from accounts.models import Parent
        try:
            parent = Parent.objects.get(user=user)
            child_filieres = parent.students.values_list(
                'student__program', flat=True,
            ).distinct()
            entries = entries.filter(filiere_id__in=child_filieres)
        except Parent.DoesNotExist:
            entries = entries.none()

    # Filter for recurrence and sort
    todays_entries = [e for e in entries if e.is_active_on(today)]
    todays_entries.sort(key=lambda e: e.time_slot.start_time)

    return {'schedule_entries': todays_entries[:8]}

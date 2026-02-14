"""
Service functions for scheduling notifications and business logic.
"""
from django.utils import timezone

from .models import ScheduleNotification


def create_exception_notifications(exception):
    """Create notifications for all affected users when a schedule exception occurs."""
    entry = exception.schedule_entry
    tenant = exception.tenant

    # Build notification title and message based on exception type
    type_labels = {
        'cancellation': 'Class Cancelled',
        'room_change': 'Room Changed',
        'substitution': 'Substitute Teacher',
        'reschedule': 'Class Rescheduled',
        'extra_session': 'Extra Session Added',
    }
    title = f"{type_labels.get(exception.exception_type, 'Schedule Change')}: {entry.course.title}"
    message = _build_exception_message(exception)

    # Get recipients: students in the filiere + the professor
    recipients = _get_entry_recipients(entry)

    notifications = []
    for user in recipients:
        notifications.append(ScheduleNotification(
            tenant=tenant,
            recipient=user,
            notification_type=exception.exception_type,
            title=title,
            message=message,
            related_entry=entry,
            related_exception=exception,
        ))

    if notifications:
        ScheduleNotification.objects.bulk_create(notifications)


def notify_substitution_created(sub_request):
    """Notify direction when a professor requests a substitution."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    tenant = sub_request.tenant
    title = f"Substitution Request: {sub_request.schedule_entry.course.title}"
    message = (
        f"{sub_request.requesting_professor.get_full_name} has requested "
        f"a substitute for {sub_request.schedule_entry.course.title} "
        f"on {sub_request.date}. Reason: {sub_request.reason}"
    )

    # Notify direction/admin users
    direction_users = User.objects.filter(
        tenant=tenant,
        role__in=['direction', 'admin', 'secretary'],
    )
    notifications = []
    for user in direction_users:
        notifications.append(ScheduleNotification(
            tenant=tenant,
            recipient=user,
            notification_type='substitution',
            title=title,
            message=message,
            related_entry=sub_request.schedule_entry,
        ))

    # Also notify the suggested substitute if any
    if sub_request.suggested_substitute:
        notifications.append(ScheduleNotification(
            tenant=tenant,
            recipient=sub_request.suggested_substitute,
            notification_type='substitution',
            title=f"Substitution Suggested: {sub_request.schedule_entry.course.title}",
            message=(
                f"You have been suggested as a substitute for "
                f"{sub_request.schedule_entry.course.title} on {sub_request.date}."
            ),
            related_entry=sub_request.schedule_entry,
        ))

    if notifications:
        ScheduleNotification.objects.bulk_create(notifications)


def notify_substitution_updated(sub_request):
    """Notify the requesting professor when their substitution request is updated."""
    tenant = sub_request.tenant
    status_msg = sub_request.get_status_display()
    title = f"Substitution {status_msg}: {sub_request.schedule_entry.course.title}"

    if sub_request.status == 'approved' and sub_request.assigned_substitute:
        message = (
            f"Your substitution request for {sub_request.date} has been approved. "
            f"{sub_request.assigned_substitute.get_full_name} will cover your class."
        )
    elif sub_request.status == 'rejected':
        message = f"Your substitution request for {sub_request.date} has been rejected."
    else:
        message = f"Your substitution request for {sub_request.date} status: {status_msg}."

    ScheduleNotification.objects.create(
        tenant=tenant,
        recipient=sub_request.requesting_professor,
        notification_type='substitution',
        title=title,
        message=message,
        related_entry=sub_request.schedule_entry,
    )

    # If approved, also notify the assigned substitute and students
    if sub_request.status == 'approved' and sub_request.assigned_substitute:
        ScheduleNotification.objects.create(
            tenant=tenant,
            recipient=sub_request.assigned_substitute,
            notification_type='substitution',
            title=f"Substitution Assignment: {sub_request.schedule_entry.course.title}",
            message=(
                f"You have been assigned to cover {sub_request.schedule_entry.course.title} "
                f"on {sub_request.date}."
            ),
            related_entry=sub_request.schedule_entry,
        )


def _build_exception_message(exception):
    """Build a human-readable message for a schedule exception."""
    entry = exception.schedule_entry
    parts = [f"Course: {entry.course.title}", f"Date: {exception.date}"]

    if exception.exception_type == 'cancellation':
        parts.append("This class has been cancelled.")
    elif exception.exception_type == 'room_change' and exception.new_room:
        parts.append(f"New room: {exception.new_room.name}")
    elif exception.exception_type == 'substitution' and exception.substitute_professor:
        parts.append(f"Substitute: {exception.substitute_professor.get_full_name}")
    elif exception.exception_type == 'reschedule':
        if exception.new_start_time:
            parts.append(f"New time: {exception.new_start_time:%H:%M}-{exception.new_end_time:%H:%M}")

    if exception.reason:
        parts.append(f"Reason: {exception.reason}")

    return "\n".join(parts)


def _get_entry_recipients(entry):
    """Get all users who should be notified about changes to a schedule entry."""
    from django.contrib.auth import get_user_model
    from accounts.models import Student

    User = get_user_model()
    recipients = set()

    # The professor
    recipients.add(entry.professor)

    # Students in the filiere
    if entry.filiere:
        students = Student.objects.filter(
            program=entry.filiere,
        ).select_related('student')
        for s in students:
            recipients.add(s.student)

    return list(recipients)

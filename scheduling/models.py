from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


# ============================================================================
# CHOICES
# ============================================================================

DAY_OF_WEEK_CHOICES = (
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
)

ROOM_TYPE_CHOICES = (
    ('classroom', _('Classroom')),
    ('lab', _('Laboratory')),
    ('amphitheatre', _('Amphitheatre')),
    ('computer_room', _('Computer Room')),
    ('meeting', _('Meeting Room')),
    ('gym', _('Gymnasium')),
    ('online', _('Online/Virtual')),
)

SLOT_TYPE_CHOICES = (
    ('class', _('Class Period')),
    ('break', _('Break')),
    ('lunch', _('Lunch Break')),
)

RECURRENCE_CHOICES = (
    ('weekly', _('Weekly')),
    ('biweekly_odd', _('Bi-weekly (Odd weeks)')),
    ('biweekly_even', _('Bi-weekly (Even weeks)')),
)

SCHEDULE_STATUS_CHOICES = (
    ('active', _('Active')),
    ('cancelled', _('Cancelled')),
    ('substituted', _('Substituted')),
    ('rescheduled', _('Rescheduled')),
)

EXCEPTION_TYPE_CHOICES = (
    ('cancellation', _('Cancellation')),
    ('room_change', _('Room Change')),
    ('substitution', _('Substitution')),
    ('reschedule', _('Reschedule')),
    ('extra_session', _('Extra Session')),
)

PREFERENCE_CHOICES = (
    ('unavailable', _('Unavailable')),
    ('avoid', _('Prefer to Avoid')),
    ('neutral', _('Neutral')),
    ('preferred', _('Preferred')),
)

SUBSTITUTION_STATUS_CHOICES = (
    ('pending', _('Pending')),
    ('approved', _('Approved')),
    ('rejected', _('Rejected')),
    ('fulfilled', _('Fulfilled')),
)

NOTIFICATION_TYPE_CHOICES = (
    ('cancellation', _('Class Cancelled')),
    ('room_change', _('Room Changed')),
    ('substitution', _('Substitute Teacher')),
    ('reschedule', _('Class Rescheduled')),
    ('new_event', _('New Event')),
    ('reminder', _('Reminder')),
)

GENERATION_STATUS_CHOICES = (
    ('pending', _('Pending')),
    ('running', _('Running')),
    ('completed', _('Completed')),
    ('failed', _('Failed')),
    ('rolled_back', _('Rolled Back')),
)


# ============================================================================
# MODELS
# ============================================================================

class Room(models.Model):
    """Physical or virtual rooms available for scheduling."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='rooms'
    )
    name = models.CharField(_('Room Name'), max_length=100)
    code = models.CharField(_('Room Code'), max_length=20)
    building = models.CharField(_('Building'), max_length=100, blank=True)
    floor = models.IntegerField(_('Floor'), default=0)
    capacity = models.IntegerField(
        _('Capacity'), default=30, validators=[MinValueValidator(1)]
    )
    room_type = models.CharField(
        _('Room Type'), max_length=20, choices=ROOM_TYPE_CHOICES, default='classroom'
    )
    equipment = models.JSONField(
        _('Equipment'), default=list, blank=True,
        help_text=_('List of equipment: ["projector", "whiteboard", "computers"]')
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['tenant', 'code']]
        ordering = ['building', 'floor', 'name']
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')

    def __str__(self):
        if self.building:
            return f"{self.name} ({self.building}, Floor {self.floor})"
        return self.name


class TimeSlot(models.Model):
    """Configurable time slots for the school's scheduling grid."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='time_slots'
    )
    name = models.CharField(_('Slot Name'), max_length=50)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    day_of_week = models.IntegerField(_('Day of Week'), choices=DAY_OF_WEEK_CHOICES)
    slot_type = models.CharField(
        _('Slot Type'), max_length=10, choices=SLOT_TYPE_CHOICES, default='class'
    )
    order = models.IntegerField(_('Display Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        unique_together = [['tenant', 'day_of_week', 'start_time']]
        ordering = ['day_of_week', 'order', 'start_time']
        verbose_name = _('Time Slot')
        verbose_name_plural = _('Time Slots')

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    @property
    def duration_minutes(self):
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end += timedelta(days=1)
        return int((end - start).total_seconds() / 60)


class ProfessorAvailability(models.Model):
    """Professor availability preferences per time slot."""

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='availability_preferences'
    )
    time_slot = models.ForeignKey(
        TimeSlot, on_delete=models.CASCADE, related_name='professor_preferences'
    )
    preference = models.CharField(
        _('Preference'), max_length=20, choices=PREFERENCE_CHOICES, default='neutral'
    )

    class Meta:
        unique_together = [['professor', 'time_slot']]
        verbose_name = _('Professor Availability')
        verbose_name_plural = _('Professor Availabilities')

    def __str__(self):
        return f"{self.professor} - {self.time_slot}: {self.get_preference_display()}"


class ScheduleEntry(models.Model):
    """
    A single scheduled class on the timetable.
    One row = one recurring weekly (or bi-weekly) slot.
    """

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='schedule_entries'
    )
    course = models.ForeignKey(
        'course.Course', on_delete=models.CASCADE, related_name='schedule_entries'
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='teaching_schedule',
        limit_choices_to={'role': 'professor'}
    )
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='schedule_entries'
    )
    time_slot = models.ForeignKey(
        TimeSlot, on_delete=models.CASCADE, related_name='schedule_entries'
    )
    filiere = models.ForeignKey(
        'filieres.Filiere', on_delete=models.CASCADE, null=True, blank=True,
        related_name='schedule_entries'
    )
    group_name = models.CharField(
        _('Group'), max_length=50, blank=True,
        help_text=_('e.g. "Group A", "TD1"')
    )
    session = models.ForeignKey(
        'core.Session', on_delete=models.CASCADE, null=True, blank=True,
        related_name='schedule_entries'
    )
    semester = models.ForeignKey(
        'core.Semester', on_delete=models.CASCADE, null=True, blank=True,
        related_name='schedule_entries'
    )
    effective_from = models.DateField(_('Effective From'))
    effective_until = models.DateField(_('Effective Until'))
    recurrence = models.CharField(
        _('Recurrence'), max_length=20, choices=RECURRENCE_CHOICES, default='weekly'
    )
    status = models.CharField(
        _('Status'), max_length=20, choices=SCHEDULE_STATUS_CHOICES, default='active'
    )
    color = models.CharField(_('Color'), max_length=7, default='#3788d8')
    is_locked = models.BooleanField(
        _('Locked'), default=False,
        help_text=_('Locked entries are preserved during auto-regeneration')
    )
    generation = models.ForeignKey(
        'TimetableGeneration', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='entries',
        help_text=_('The generation run that created this entry')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_schedule_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['time_slot__day_of_week', 'time_slot__start_time']
        verbose_name = _('Schedule Entry')
        verbose_name_plural = _('Schedule Entries')
        indexes = [
            models.Index(fields=['tenant', 'professor']),
            models.Index(fields=['tenant', 'room']),
            models.Index(fields=['tenant', 'filiere', 'semester']),
            models.Index(fields=['effective_from', 'effective_until']),
        ]

    def __str__(self):
        return (
            f"{self.course} - {self.professor.get_full_name} "
            f"({self.time_slot})"
        )

    def is_active_on(self, date):
        """Check if this entry is active on a given date."""
        if self.status != 'active':
            return False
        if not (self.effective_from <= date <= self.effective_until):
            return False
        if date.weekday() != self.time_slot.day_of_week:
            return False
        if self.recurrence == 'weekly':
            return True
        # Bi-weekly: check ISO week number parity
        week_num = date.isocalendar()[1]
        if self.recurrence == 'biweekly_odd':
            return week_num % 2 == 1
        if self.recurrence == 'biweekly_even':
            return week_num % 2 == 0
        return True


class ScheduleException(models.Model):
    """One-off modifications to a ScheduleEntry for a specific date."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='schedule_exceptions'
    )
    schedule_entry = models.ForeignKey(
        ScheduleEntry, on_delete=models.CASCADE, related_name='exceptions'
    )
    exception_type = models.CharField(
        _('Exception Type'), max_length=20, choices=EXCEPTION_TYPE_CHOICES
    )
    date = models.DateField(_('Date'))
    new_room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exception_assignments',
        help_text=_('Override room for this date')
    )
    substitute_professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='substitution_entries',
        help_text=_('Substitute professor for this date')
    )
    new_start_time = models.TimeField(_('New Start Time'), null=True, blank=True)
    new_end_time = models.TimeField(_('New End Time'), null=True, blank=True)
    reason = models.TextField(_('Reason'), blank=True)
    is_approved = models.BooleanField(_('Approved'), default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_schedule_exceptions'
    )
    notify_students = models.BooleanField(_('Notify Students'), default=True)
    notification_sent = models.BooleanField(_('Notification Sent'), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_schedule_exceptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['schedule_entry', 'date', 'exception_type']]
        ordering = ['-date']
        verbose_name = _('Schedule Exception')
        verbose_name_plural = _('Schedule Exceptions')

    def __str__(self):
        return f"{self.get_exception_type_display()} - {self.schedule_entry} on {self.date}"


class SubstitutionRequest(models.Model):
    """Professor requests a substitute for a specific date."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='substitution_requests'
    )
    schedule_entry = models.ForeignKey(
        ScheduleEntry, on_delete=models.CASCADE, related_name='substitution_requests'
    )
    date = models.DateField(_('Date'))
    requesting_professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='substitution_requests_made'
    )
    suggested_substitute = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='substitution_requests_received'
    )
    assigned_substitute = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='substitution_assignments'
    )
    reason = models.TextField(_('Reason'))
    status = models.CharField(
        _('Status'), max_length=20, choices=SUBSTITUTION_STATUS_CHOICES, default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_substitution_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Substitution Request')
        verbose_name_plural = _('Substitution Requests')

    def __str__(self):
        return (
            f"{self.requesting_professor.get_full_name} - "
            f"{self.schedule_entry.course} on {self.date}"
        )


class ScheduleNotification(models.Model):
    """In-app notifications for schedule changes."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='schedule_notifications'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='schedule_notifications'
    )
    notification_type = models.CharField(
        _('Type'), max_length=20, choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(_('Title'), max_length=200)
    message = models.TextField(_('Message'))
    related_entry = models.ForeignKey(
        ScheduleEntry, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    related_exception = models.ForeignKey(
        ScheduleException, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(_('Read'), default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(_('Email Sent'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Schedule Notification')
        verbose_name_plural = _('Schedule Notifications')
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['tenant', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"


class TimetableGeneration(models.Model):
    """Tracks auto-generation runs for audit and rollback."""

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE, related_name='timetable_generations'
    )
    session = models.ForeignKey(
        'core.Session', on_delete=models.CASCADE, related_name='timetable_generations'
    )
    semester = models.ForeignKey(
        'core.Semester', on_delete=models.CASCADE, related_name='timetable_generations'
    )
    status = models.CharField(
        _('Status'), max_length=20, choices=GENERATION_STATUS_CHOICES, default='pending'
    )
    config = models.JSONField(
        _('Configuration'), default=dict, blank=True,
        help_text=_('Constraints and preferences used for generation')
    )
    entries_created = models.IntegerField(_('Entries Created'), default=0)
    conflicts_found = models.IntegerField(_('Conflicts Found'), default=0)
    conflict_details = models.JSONField(
        _('Conflict Details'), default=list, blank=True
    )
    is_published = models.BooleanField(
        _('Published'), default=False,
        help_text=_('Only one published generation per session+semester')
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Timetable Generation')
        verbose_name_plural = _('Timetable Generations')

    def __str__(self):
        return f"Generation #{self.pk} - {self.session} {self.semester} ({self.get_status_display()})"

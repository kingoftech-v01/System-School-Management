"""
Scheduling API ViewSets.

Provides REST endpoints for:
- Room CRUD + availability queries
- TimeSlot CRUD + weekly grid
- ScheduleEntry CRUD + calendar feed + conflict detection
- ScheduleException CRUD + approval
- SubstitutionRequest CRUD + approval/rejection
- ScheduleNotification (read-only) + mark read
- TimetableGeneration CRUD + run/rollback
"""

from datetime import datetime, date, timedelta
from collections import defaultdict

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)
from .serializers import (
    RoomSerializer, RoomListSerializer, TimeSlotSerializer,
    ScheduleEntrySerializer, ScheduleEntryCreateSerializer,
    CalendarEventSerializer, ScheduleExceptionSerializer,
    SubstitutionRequestSerializer, ScheduleNotificationSerializer,
    TimetableGenerationSerializer,
)


def get_tenant(request):
    """Get tenant from request, handling both multi-tenant and dev mode."""
    if hasattr(request, 'tenant'):
        return request.tenant
    return None


class RoomViewSet(viewsets.ModelViewSet):
    """Room CRUD with availability queries."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return RoomListSerializer
        return RoomSerializer

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = Room.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Find rooms available at a given date/time.

        Query params: date, start_time, end_time
        """
        target_date = request.query_params.get('date')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        if not all([target_date, start_time, end_time]):
            return Response(
                {'detail': 'date, start_time, and end_time are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = date.fromisoformat(target_date)
        day_of_week = target_date.weekday()
        tenant = get_tenant(request)

        # Find rooms that have no schedule entry at this day/time
        occupied_room_ids = ScheduleEntry.objects.filter(
            tenant=tenant,
            status='active',
            time_slot__day_of_week=day_of_week,
            time_slot__start_time__lt=end_time,
            time_slot__end_time__gt=start_time,
            effective_from__lte=target_date,
            effective_until__gte=target_date,
        ).values_list('room_id', flat=True).distinct()

        available_rooms = self.get_queryset().filter(
            is_active=True,
        ).exclude(id__in=occupied_room_ids)

        serializer = RoomListSerializer(available_rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def utilization(self, request, pk=None):
        """Room utilization stats for a given period.

        Query params: start_date, end_date (defaults to current month)
        """
        room = self.get_object()
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')

        today = date.today()
        start_date = date.fromisoformat(start_str) if start_str else today.replace(day=1)
        end_date = date.fromisoformat(end_str) if end_str else today

        entries = ScheduleEntry.objects.filter(
            room=room,
            status='active',
            effective_from__lte=end_date,
            effective_until__gte=start_date,
        ).select_related('time_slot')

        total_hours = 0
        for entry in entries:
            duration = entry.time_slot.duration_minutes / 60.0
            # Count weeks the entry is active within the period
            entry_start = max(entry.effective_from, start_date)
            entry_end = min(entry.effective_until, end_date)
            weeks = max(0, (entry_end - entry_start).days // 7 + 1)
            total_hours += duration * weeks

        # Total available hours (assuming 12h/day, Mon-Sat)
        total_days = (end_date - start_date).days + 1
        school_days = sum(1 for d in range(total_days) if (start_date + timedelta(days=d)).weekday() < 6)
        total_available = school_days * 12

        return Response({
            'room': RoomSerializer(room).data,
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'hours_used': round(total_hours, 1),
            'hours_available': total_available,
            'utilization_pct': round(total_hours / max(total_available, 1) * 100, 1),
        })


class TimeSlotViewSet(viewsets.ModelViewSet):
    """TimeSlot CRUD with weekly grid endpoint."""
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = TimeSlot.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant)

    @action(detail=False, methods=['get'])
    def grid(self, request):
        """Return the weekly time slot grid grouped by day."""
        slots = self.get_queryset().filter(is_active=True)
        grid = defaultdict(list)
        for slot in slots:
            grid[slot.day_of_week].append(TimeSlotSerializer(slot).data)

        return Response(dict(grid))


class ScheduleEntryViewSet(viewsets.ModelViewSet):
    """Schedule entry CRUD + calendar feed + conflict detection."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleEntryCreateSerializer
        return ScheduleEntrySerializer

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = ScheduleEntry.objects.select_related(
            'course', 'professor', 'room', 'time_slot', 'filiere',
            'session', 'semester',
        )
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def calendar_feed(self, request):
        """FullCalendar event source endpoint.

        FullCalendar sends ?start=YYYY-MM-DD&end=YYYY-MM-DD.
        Additional params: filiere_id, professor_id, room_id, include_events
        """
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')

        if not start_str or not end_str:
            return Response(
                {'detail': 'start and end parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        range_start = date.fromisoformat(start_str[:10])
        range_end = date.fromisoformat(end_str[:10])

        # Base queryset
        entries = self.get_queryset().filter(
            status='active',
            effective_from__lte=range_end,
            effective_until__gte=range_start,
        )

        # Role-based filtering
        user = request.user
        role = getattr(user, 'role', 'student')

        if role == 'student':
            # Student sees their filiere's schedule
            student_profile = getattr(user, 'student', None)
            if student_profile and student_profile.program:
                entries = entries.filter(filiere=student_profile.program)
            else:
                entries = entries.none()
        elif role == 'professor':
            entries = entries.filter(professor=user)
        elif role == 'parent':
            # Parent sees their children's schedule
            from accounts.models import Parent
            try:
                parent = Parent.objects.get(user=user)
                child_filieres = parent.students.values_list(
                    'student__program', flat=True
                ).distinct()
                entries = entries.filter(filiere_id__in=child_filieres)
            except Parent.DoesNotExist:
                entries = entries.none()
        # direction/admin/secretary see everything (no filter)
        elif role not in ('direction', 'admin', 'secretary'):
            # Other roles see only school events (handled below)
            entries = entries.none()

        # Additional filter params
        filiere_id = request.query_params.get('filiere_id')
        professor_id = request.query_params.get('professor_id')
        room_id = request.query_params.get('room_id')

        if filiere_id:
            entries = entries.filter(filiere_id=filiere_id)
        if professor_id:
            entries = entries.filter(professor_id=professor_id)
        if room_id:
            entries = entries.filter(room_id=room_id)

        # Load exceptions for the date range
        exceptions_map = {}
        exception_qs = ScheduleException.objects.filter(
            schedule_entry__in=entries,
            date__gte=range_start,
            date__lte=range_end,
        ).select_related('new_room', 'substitute_professor')
        for exc in exception_qs:
            exceptions_map[(exc.schedule_entry_id, exc.date)] = exc

        # Expand entries into calendar events
        events = self._expand_entries(entries, range_start, range_end, exceptions_map, user)

        # Optionally include school events
        include_events = request.query_params.get('include_events', 'true')
        if include_events.lower() == 'true':
            events.extend(self._get_school_events(request, range_start, range_end, role))

        return Response(events)

    def _expand_entries(self, entries, range_start, range_end, exceptions_map, user):
        """Expand recurring ScheduleEntries into individual FullCalendar events."""
        events = []
        is_editor = getattr(user, 'role', '') in ('direction', 'admin', 'secretary')

        for entry in entries:
            slot = entry.time_slot
            current = range_start

            while current <= range_end:
                if current.weekday() == slot.day_of_week and entry.is_active_on(current):
                    exception = exceptions_map.get((entry.id, current))
                    event = self._build_event(entry, current, slot, exception, is_editor)
                    events.append(event)
                current += timedelta(days=1)

        return events

    def _build_event(self, entry, current_date, slot, exception, is_editor):
        """Build a single FullCalendar event object."""
        start_dt = datetime.combine(current_date, slot.start_time)
        end_dt = datetime.combine(current_date, slot.end_time)

        title_parts = [entry.course.title]
        color = entry.color
        extra_props = {
            'type': 'class',
            'entryId': entry.id,
            'courseCode': entry.course.code,
            'courseName': entry.course.title,
            'professorName': entry.professor.get_full_name,
            'professorId': entry.professor_id,
            'roomName': entry.room.name if entry.room else '',
            'roomId': entry.room_id,
            'filiereName': entry.filiere.name if entry.filiere else '',
            'filiereId': entry.filiere_id,
            'groupName': entry.group_name,
            'status': 'active',
        }

        if exception:
            if exception.exception_type == 'cancellation':
                title_parts.insert(0, 'CANCELLED:')
                color = '#dc3545'
                extra_props['status'] = 'cancelled'
                extra_props['reason'] = exception.reason
            elif exception.exception_type == 'room_change' and exception.new_room:
                extra_props['roomName'] = exception.new_room.name
                extra_props['roomId'] = exception.new_room_id
                extra_props['status'] = 'room_changed'
                color = '#17a2b8'
            elif exception.exception_type == 'substitution' and exception.substitute_professor:
                extra_props['professorName'] = exception.substitute_professor.get_full_name
                extra_props['professorId'] = exception.substitute_professor_id
                extra_props['status'] = 'substituted'
                color = '#ffc107'
            elif exception.exception_type == 'reschedule':
                if exception.new_start_time:
                    start_dt = datetime.combine(current_date, exception.new_start_time)
                if exception.new_end_time:
                    end_dt = datetime.combine(current_date, exception.new_end_time)
                extra_props['status'] = 'rescheduled'
                color = '#17a2b8'

        # Build display title
        prof_name = extra_props['professorName']
        room_name = extra_props['roomName']
        if room_name:
            title_parts.append(f"({prof_name}) - {room_name}")
        else:
            title_parts.append(f"({prof_name})")

        return {
            'id': f"entry_{entry.id}_{current_date.isoformat()}",
            'title': ' '.join(title_parts),
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'color': color,
            'textColor': '#ffffff',
            'editable': is_editor,
            'extendedProps': extra_props,
        }

    def _get_school_events(self, request, range_start, range_end, role):
        """Fetch events from the events app and format for FullCalendar."""
        try:
            from events.models import Event
        except ImportError:
            return []

        tenant = get_tenant(request)
        qs = Event.objects.filter(
            start_date__date__lte=range_end,
            end_date__date__gte=range_start,
        )
        if tenant:
            qs = qs.filter(tenant=tenant)

        # Filter by audience
        audience_map = {
            'student': ['all', 'students'],
            'professor': ['all', 'staff'],
            'parent': ['all', 'parents'],
        }
        audiences = audience_map.get(role, ['all'])
        if role not in ('direction', 'admin', 'secretary'):
            qs = qs.filter(target_audience__in=audiences)

        event_colors = {
            'exam': '#dc3545',
            'holiday': '#6c757d',
            'meeting': '#6f42c1',
            'activity': '#28a745',
            'ceremony': '#28a745',
            'deadline': '#fd7e14',
        }

        events = []
        for evt in qs:
            events.append({
                'id': f"event_{evt.id}",
                'title': evt.title,
                'start': evt.start_date.isoformat(),
                'end': evt.end_date.isoformat(),
                'color': event_colors.get(evt.event_type, '#28a745'),
                'textColor': '#ffffff',
                'editable': False,
                'extendedProps': {
                    'type': 'event',
                    'eventType': evt.event_type,
                    'location': evt.location,
                    'description': evt.description,
                },
            })

        return events

    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        """Personal schedule for the authenticated user."""
        target_date_str = request.query_params.get('date', 'today')
        if target_date_str == 'today':
            target_date = date.today()
        else:
            target_date = date.fromisoformat(target_date_str)

        user = request.user
        role = getattr(user, 'role', 'student')

        entries = self.get_queryset().filter(
            status='active',
            effective_from__lte=target_date,
            effective_until__gte=target_date,
            time_slot__day_of_week=target_date.weekday(),
        )

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
                    'student__program', flat=True
                ).distinct()
                entries = entries.filter(filiere_id__in=child_filieres)
            except Parent.DoesNotExist:
                entries = entries.none()

        # Filter for recurrence
        entries = [e for e in entries if e.is_active_on(target_date)]

        schedule_items = []
        for entry in entries:
            schedule_items.append({
                'time': f"{entry.time_slot.start_time:%H:%M} - {entry.time_slot.end_time:%H:%M}",
                'title': entry.course.title,
                'room': entry.room.name if entry.room else '',
                'professor': entry.professor.get_full_name,
                'status': entry.status,
                'color': entry.color,
            })

        schedule_items.sort(key=lambda x: x['time'])

        return Response({
            'date': target_date.isoformat(),
            'entries': schedule_items,
        })

    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Detect scheduling conflicts for a proposed entry.

        Query params: day_of_week, start_time, end_time, professor_id,
                      room_id, filiere_id, exclude_entry_id
        """
        day = request.query_params.get('day_of_week')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        professor_id = request.query_params.get('professor_id')
        room_id = request.query_params.get('room_id')
        filiere_id = request.query_params.get('filiere_id')
        exclude_id = request.query_params.get('exclude_entry_id')

        if not all([day, start_time, end_time]):
            return Response(
                {'detail': 'day_of_week, start_time, and end_time are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_qs = self.get_queryset().filter(
            status='active',
            time_slot__day_of_week=int(day),
            time_slot__start_time__lt=end_time,
            time_slot__end_time__gt=start_time,
        )
        if exclude_id:
            base_qs = base_qs.exclude(id=int(exclude_id))

        conflicts = []

        # Professor conflict
        if professor_id:
            prof_conflicts = base_qs.filter(professor_id=int(professor_id))
            for e in prof_conflicts:
                conflicts.append({
                    'type': 'professor',
                    'message': f"Professor already teaching {e.course.title} at {e.time_slot}",
                    'entry_id': e.id,
                })

        # Room conflict
        if room_id:
            room_conflicts = base_qs.filter(room_id=int(room_id))
            for e in room_conflicts:
                conflicts.append({
                    'type': 'room',
                    'message': f"Room already occupied by {e.course.title} at {e.time_slot}",
                    'entry_id': e.id,
                })

        # Student group conflict
        if filiere_id:
            group_conflicts = base_qs.filter(filiere_id=int(filiere_id))
            for e in group_conflicts:
                conflicts.append({
                    'type': 'student_group',
                    'message': f"Students already have {e.course.title} at {e.time_slot}",
                    'entry_id': e.id,
                })

        return Response(conflicts)

    @action(detail=False, methods=['post'])
    def move(self, request):
        """Handle FullCalendar drag-and-drop event moves."""
        entry_id = request.data.get('entry_id')
        new_time_slot_id = request.data.get('time_slot_id')

        if not entry_id or not new_time_slot_id:
            return Response(
                {'detail': 'entry_id and time_slot_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entry = self.get_queryset().get(id=entry_id)
            new_slot = TimeSlot.objects.get(id=new_time_slot_id)
        except (ScheduleEntry.DoesNotExist, TimeSlot.DoesNotExist):
            return Response(
                {'detail': 'Entry or time slot not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        entry.time_slot = new_slot
        entry.save(update_fields=['time_slot', 'updated_at'])

        return Response(ScheduleEntrySerializer(entry).data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple entries at once (from auto-generation)."""
        entries_data = request.data.get('entries', [])
        tenant = get_tenant(request)

        created = []
        for data in entries_data:
            serializer = ScheduleEntryCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            entry = serializer.save(tenant=tenant, created_by=request.user)
            created.append(entry.id)

        return Response(
            {'created': len(created), 'ids': created},
            status=status.HTTP_201_CREATED,
        )


class ScheduleExceptionViewSet(viewsets.ModelViewSet):
    """Schedule exception CRUD with approval."""
    serializer_class = ScheduleExceptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = ScheduleException.objects.select_related(
            'schedule_entry', 'new_room', 'substitute_professor',
        )
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """List pending (unapproved) exceptions."""
        qs = self.get_queryset().filter(is_approved=False)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a schedule exception."""
        exception = self.get_object()
        exception.is_approved = True
        exception.approved_by = request.user
        exception.save(update_fields=['is_approved', 'approved_by', 'updated_at'])
        return Response(self.get_serializer(exception).data)


class SubstitutionRequestViewSet(viewsets.ModelViewSet):
    """Substitution request CRUD with approval/rejection."""
    serializer_class = SubstitutionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = SubstitutionRequest.objects.select_related(
            'schedule_entry__course', 'requesting_professor',
            'suggested_substitute', 'assigned_substitute',
        )
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(
            tenant=tenant,
            requesting_professor=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a substitution request."""
        sub = self.get_object()
        substitute_id = request.data.get('substitute_id')

        if substitute_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            sub.assigned_substitute = User.objects.get(id=substitute_id)
        elif sub.suggested_substitute:
            sub.assigned_substitute = sub.suggested_substitute

        sub.status = 'approved'
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.save()

        # Create the schedule exception
        ScheduleException.objects.create(
            tenant=sub.tenant,
            schedule_entry=sub.schedule_entry,
            exception_type='substitution',
            date=sub.date,
            substitute_professor=sub.assigned_substitute,
            reason=sub.reason,
            is_approved=True,
            approved_by=request.user,
            notify_students=True,
            created_by=request.user,
        )

        return Response(self.get_serializer(sub).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a substitution request."""
        sub = self.get_object()
        sub.status = 'rejected'
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.save()
        return Response(self.get_serializer(sub).data)

    @action(detail=False, methods=['get'])
    def available_professors(self, request):
        """Find professors available at a given date/time slot."""
        target_date = request.query_params.get('date')
        time_slot_id = request.query_params.get('timeslot_id')

        if not target_date or not time_slot_id:
            return Response(
                {'detail': 'date and timeslot_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = date.fromisoformat(target_date)
        tenant = get_tenant(request)

        # Professors who are NOT teaching at this time
        busy_prof_ids = ScheduleEntry.objects.filter(
            tenant=tenant,
            status='active',
            time_slot_id=int(time_slot_id),
            effective_from__lte=target_date,
            effective_until__gte=target_date,
        ).values_list('professor_id', flat=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        available = User.objects.filter(
            tenant=tenant,
            role='professor',
        ).exclude(id__in=busy_prof_ids)

        return Response([
            {'id': p.id, 'name': p.get_full_name}
            for p in available
        ])


class ScheduleNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only notifications for the current user."""
    serializer_class = ScheduleNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScheduleNotification.objects.filter(
            recipient=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Returns unread count for badge display."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})


class TimetableGenerationViewSet(viewsets.ModelViewSet):
    """Manage timetable auto-generation runs."""
    serializer_class = TimetableGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_tenant(self.request)
        qs = TimetableGeneration.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = get_tenant(self.request)
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Trigger timetable generation (async via Celery)."""
        generation = self.get_object()

        if generation.status not in ('pending', 'failed'):
            return Response(
                {'detail': f'Cannot run generation with status: {generation.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .tasks import generate_timetable_task
            generate_timetable_task.delay(generation.id)
            generation.status = 'running'
            generation.started_at = timezone.now()
            generation.save(update_fields=['status', 'started_at'])
        except Exception:
            # If Celery is not available, run synchronously
            from .engine.generator import TimetableGenerator
            generator = TimetableGenerator(generation)
            generator.generate()

        return Response(self.get_serializer(generation).data)

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback a generation (delete all its entries)."""
        generation = self.get_object()
        count = generation.entries.count()
        generation.entries.all().delete()
        generation.status = 'rolled_back'
        generation.save(update_fields=['status'])

        return Response({
            'detail': f'Rolled back {count} entries.',
            'generation': self.get_serializer(generation).data,
        })

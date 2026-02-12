"""
Scheduling frontend views.

All HTML template views for the scheduling system:
- Calendar views (all roles)
- Professor views (cancellation, substitution requests)
- Parent views (child schedule)
- Direction/Admin management views (rooms, time slots, editor, wizard)
- Notification views
"""

from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import (
    direction_only, tenant_required, professor_only, parent_only,
    role_required,
)
from django_ratelimit.decorators import ratelimit
from core.models import School

from .models import (
    Room, TimeSlot, ScheduleEntry, ScheduleException,
    SubstitutionRequest, ScheduleNotification, TimetableGeneration,
    ProfessorAvailability,
)
from .forms import (
    RoomForm, TimeSlotForm, ScheduleEntryForm, ScheduleExceptionForm,
    SubstitutionRequestForm, CancellationForm,
)


def get_current_tenant(request):
    """Get current tenant from request or return default for development."""
    if hasattr(request, 'tenant') and request.tenant:
        return request.tenant
    school, _ = School.objects.get_or_create(
        slug='default',
        defaults={'name': 'Default School', 'email': 'admin@school.local'}
    )
    return school


# ============================================================================
# CALENDAR VIEWS (All Roles)
# ============================================================================

@login_required
@tenant_required
def schedule_calendar(request):
    """Main FullCalendar page - all roles see their filtered schedule."""
    tenant = get_current_tenant(request)
    user = request.user
    role = getattr(user, 'role', 'student')

    # Get filieres and professors for filter dropdowns (direction only)
    filieres = []
    professors = []
    rooms = []
    if role in ('direction', 'admin', 'secretary'):
        from filieres.models import Filiere
        from django.contrib.auth import get_user_model
        User = get_user_model()
        filieres = Filiere.objects.filter(tenant=tenant, is_active=True)
        professors = User.objects.filter(tenant=tenant, role='professor')
        rooms = Room.objects.filter(tenant=tenant, is_active=True)

    return render(request, 'scheduling/calendar.html', {
        'title': _('Schedule Calendar'),
        'user_role': role,
        'filieres': filieres,
        'professors': professors,
        'rooms': rooms,
    })


@login_required
@tenant_required
def my_schedule(request):
    """Personal schedule summary view."""
    tenant = get_current_tenant(request)
    today = date.today()

    entries = ScheduleEntry.objects.filter(
        tenant=tenant,
        status='active',
        effective_from__lte=today,
        effective_until__gte=today,
        time_slot__day_of_week=today.weekday(),
    ).select_related('course', 'professor', 'room', 'time_slot', 'filiere')

    user = request.user
    role = getattr(user, 'role', 'student')

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
    todays_entries = [e for e in entries if e.is_active_on(today)]
    todays_entries.sort(key=lambda e: e.time_slot.start_time)

    return render(request, 'scheduling/my_schedule.html', {
        'title': _('My Schedule'),
        'today': today,
        'entries': todays_entries,
    })


# ============================================================================
# PROFESSOR VIEWS
# ============================================================================

@login_required
@professor_only
@tenant_required
def professor_schedule(request):
    """Professor's teaching schedule view."""
    tenant = get_current_tenant(request)
    entries = ScheduleEntry.objects.filter(
        tenant=tenant,
        professor=request.user,
        status='active',
    ).select_related('course', 'room', 'time_slot', 'filiere').order_by(
        'time_slot__day_of_week', 'time_slot__start_time'
    )

    return render(request, 'scheduling/professor_schedule.html', {
        'title': _('My Teaching Schedule'),
        'entries': entries,
    })


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def mark_cancellation(request, entry_id):
    """Professor cancels a class on a specific date."""
    tenant = get_current_tenant(request)
    entry = get_object_or_404(
        ScheduleEntry, pk=entry_id, tenant=tenant, professor=request.user
    )

    if request.method == 'POST':
        form = CancellationForm(request.POST)
        if form.is_valid():
            ScheduleException.objects.create(
                tenant=tenant,
                schedule_entry=entry,
                exception_type='cancellation',
                date=form.cleaned_data['date'],
                reason=form.cleaned_data['reason'],
                notify_students=form.cleaned_data['notify_students'],
                is_approved=True,
                approved_by=request.user,
                created_by=request.user,
            )
            messages.success(request, _('Class cancelled successfully.'))
            return redirect('frontend:scheduling:professor_schedule')
    else:
        form = CancellationForm()

    return render(request, 'scheduling/mark_cancellation.html', {
        'title': _('Cancel Class'),
        'entry': entry,
        'form': form,
    })


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def request_substitution(request, entry_id):
    """Professor requests a substitute for a class."""
    tenant = get_current_tenant(request)
    entry = get_object_or_404(
        ScheduleEntry, pk=entry_id, tenant=tenant, professor=request.user
    )

    if request.method == 'POST':
        form = SubstitutionRequestForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.tenant = tenant
            sub.schedule_entry = entry
            sub.requesting_professor = request.user
            sub.save()
            messages.success(request, _('Substitution request submitted.'))
            return redirect('frontend:scheduling:my_substitution_requests')
    else:
        form = SubstitutionRequestForm(initial={'schedule_entry': entry})

    return render(request, 'scheduling/request_substitution.html', {
        'title': _('Request Substitution'),
        'entry': entry,
        'form': form,
    })


@login_required
@professor_only
@tenant_required
def my_substitution_requests(request):
    """List professor's substitution requests."""
    tenant = get_current_tenant(request)
    requests_list = SubstitutionRequest.objects.filter(
        tenant=tenant,
        requesting_professor=request.user,
    ).select_related('schedule_entry__course', 'assigned_substitute')

    paginator = Paginator(requests_list, 20)
    page = request.GET.get('page')
    requests_list = paginator.get_page(page)

    return render(request, 'scheduling/my_substitution_requests.html', {
        'title': _('My Substitution Requests'),
        'substitution_requests': requests_list,
    })


# ============================================================================
# PARENT VIEW
# ============================================================================

@login_required
@parent_only
@tenant_required
def parent_child_schedule(request):
    """Parent sees child's schedule."""
    tenant = get_current_tenant(request)

    from accounts.models import Parent
    try:
        parent = Parent.objects.get(user=request.user)
        children = parent.students.select_related('student').all()
    except Parent.DoesNotExist:
        children = []

    # Get selected child or first child
    child_id = request.GET.get('child_id')
    selected_child = None
    entries = []

    if children:
        if child_id:
            selected_child = next(
                (c for c in children if str(c.student.id) == child_id), children[0]
            )
        else:
            selected_child = children[0]

        if selected_child and selected_child.program:
            entries = ScheduleEntry.objects.filter(
                tenant=tenant,
                filiere=selected_child.program,
                status='active',
            ).select_related(
                'course', 'professor', 'room', 'time_slot'
            ).order_by('time_slot__day_of_week', 'time_slot__start_time')

    return render(request, 'scheduling/parent_schedule.html', {
        'title': _("Child's Schedule"),
        'children': children,
        'selected_child': selected_child,
        'entries': entries,
    })


# ============================================================================
# ROOM MANAGEMENT (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def room_list(request):
    """List all rooms."""
    tenant = get_current_tenant(request)
    rooms = Room.objects.filter(tenant=tenant).order_by('building', 'floor', 'name')

    room_type = request.GET.get('room_type', '')
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    paginator = Paginator(rooms, 20)
    page = request.GET.get('page')
    rooms = paginator.get_page(page)

    return render(request, 'scheduling/rooms/room_list.html', {
        'title': _('Rooms'),
        'rooms': rooms,
        'room_type_choices': Room._meta.get_field('room_type').choices,
        'current_room_type': room_type,
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def room_create(request):
    """Create a new room."""
    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.tenant = tenant
            room.save()
            messages.success(request, _('Room created successfully.'))
            return redirect('frontend:scheduling:room_list')
    else:
        form = RoomForm()

    return render(request, 'scheduling/rooms/room_form.html', {
        'form': form,
        'title': _('Create Room'),
    })


@login_required
@direction_only
@tenant_required
def room_detail(request, pk):
    """View room details and its schedule."""
    tenant = get_current_tenant(request)
    room = get_object_or_404(Room, pk=pk, tenant=tenant)

    entries = ScheduleEntry.objects.filter(
        room=room, status='active'
    ).select_related('course', 'professor', 'time_slot').order_by(
        'time_slot__day_of_week', 'time_slot__start_time'
    )

    return render(request, 'scheduling/rooms/room_detail.html', {
        'title': room.name,
        'room': room,
        'entries': entries,
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def room_edit(request, pk):
    """Edit a room."""
    tenant = get_current_tenant(request)
    room = get_object_or_404(Room, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, _('Room updated successfully.'))
            return redirect('frontend:scheduling:room_detail', pk=room.pk)
    else:
        form = RoomForm(instance=room)

    return render(request, 'scheduling/rooms/room_form.html', {
        'form': form,
        'room': room,
        'title': _('Edit Room'),
    })


@login_required
@direction_only
@tenant_required
def room_delete(request, pk):
    """Delete a room."""
    tenant = get_current_tenant(request)
    room = get_object_or_404(Room, pk=pk, tenant=tenant)

    if request.method == 'POST':
        name = room.name
        room.delete()
        messages.success(request, _(f'Room "{name}" has been deleted.'))
        return redirect('frontend:scheduling:room_list')

    return render(request, 'scheduling/rooms/room_confirm_delete.html', {
        'room': room,
        'title': _('Delete Room'),
    })


# ============================================================================
# TIME SLOT CONFIGURATION (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def timeslot_config(request):
    """List all time slots grouped by day."""
    tenant = get_current_tenant(request)
    slots = TimeSlot.objects.filter(tenant=tenant).order_by(
        'day_of_week', 'order', 'start_time'
    )

    # Group by day
    from collections import defaultdict
    days = defaultdict(list)
    for slot in slots:
        days[slot.get_day_of_week_display()].append(slot)

    return render(request, 'scheduling/timeslots/config.html', {
        'title': _('Time Slots Configuration'),
        'days': dict(days),
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def timeslot_create(request):
    """Create a new time slot."""
    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.tenant = tenant
            slot.save()
            messages.success(request, _('Time slot created successfully.'))
            return redirect('frontend:scheduling:timeslot_config')
    else:
        form = TimeSlotForm()

    return render(request, 'scheduling/timeslots/form.html', {
        'form': form,
        'title': _('Create Time Slot'),
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def timeslot_edit(request, pk):
    """Edit a time slot."""
    tenant = get_current_tenant(request)
    slot = get_object_or_404(TimeSlot, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = TimeSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, _('Time slot updated successfully.'))
            return redirect('frontend:scheduling:timeslot_config')
    else:
        form = TimeSlotForm(instance=slot)

    return render(request, 'scheduling/timeslots/form.html', {
        'form': form,
        'slot': slot,
        'title': _('Edit Time Slot'),
    })


@login_required
@direction_only
@tenant_required
def timeslot_delete(request, pk):
    """Delete a time slot."""
    tenant = get_current_tenant(request)
    slot = get_object_or_404(TimeSlot, pk=pk, tenant=tenant)

    if request.method == 'POST':
        slot.delete()
        messages.success(request, _('Time slot deleted.'))
        return redirect('frontend:scheduling:timeslot_config')

    return render(request, 'scheduling/timeslots/confirm_delete.html', {
        'slot': slot,
        'title': _('Delete Time Slot'),
    })


# ============================================================================
# SCHEDULE EDITOR (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def schedule_editor(request):
    """Drag-and-drop schedule editor with FullCalendar."""
    tenant = get_current_tenant(request)

    from filieres.models import Filiere
    from course.models import Course, CourseAllocation
    from django.contrib.auth import get_user_model
    User = get_user_model()

    filieres = Filiere.objects.filter(tenant=tenant, is_active=True)
    rooms = Room.objects.filter(tenant=tenant, is_active=True)
    professors = User.objects.filter(tenant=tenant, role='professor')

    # Unscheduled courses (courses with allocations but no schedule entries)
    allocated_course_ids = CourseAllocation.objects.values_list(
        'courses__id', flat=True
    ).distinct()
    scheduled_course_ids = ScheduleEntry.objects.filter(
        tenant=tenant, status='active'
    ).values_list('course_id', flat=True).distinct()
    unscheduled_courses = Course.objects.filter(
        id__in=allocated_course_ids
    ).exclude(id__in=scheduled_course_ids)

    return render(request, 'scheduling/editor/schedule_editor.html', {
        'title': _('Schedule Editor'),
        'filieres': filieres,
        'rooms': rooms,
        'professors': professors,
        'unscheduled_courses': unscheduled_courses,
    })


# ============================================================================
# SCHEDULE ENTRY CRUD
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def schedule_entry_create(request):
    """Create a new schedule entry."""
    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = ScheduleEntryForm(request.POST, tenant=tenant)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.tenant = tenant
            entry.created_by = request.user
            entry.save()
            messages.success(request, _('Schedule entry created.'))
            return redirect('frontend:scheduling:schedule_editor')
    else:
        form = ScheduleEntryForm(tenant=tenant)

    return render(request, 'scheduling/entries/entry_form.html', {
        'form': form,
        'title': _('Create Schedule Entry'),
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def schedule_entry_edit(request, pk):
    """Edit a schedule entry."""
    tenant = get_current_tenant(request)
    entry = get_object_or_404(ScheduleEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ScheduleEntryForm(request.POST, instance=entry, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Schedule entry updated.'))
            return redirect('frontend:scheduling:schedule_editor')
    else:
        form = ScheduleEntryForm(instance=entry, tenant=tenant)

    return render(request, 'scheduling/entries/entry_form.html', {
        'form': form,
        'entry': entry,
        'title': _('Edit Schedule Entry'),
    })


@login_required
@direction_only
@tenant_required
def schedule_entry_delete(request, pk):
    """Delete a schedule entry."""
    tenant = get_current_tenant(request)
    entry = get_object_or_404(ScheduleEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        entry.delete()
        messages.success(request, _('Schedule entry deleted.'))
        return redirect('frontend:scheduling:schedule_editor')

    return render(request, 'scheduling/entries/entry_confirm_delete.html', {
        'entry': entry,
        'title': _('Delete Schedule Entry'),
    })


# ============================================================================
# AUTO-GENERATION WIZARD (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def timetable_wizard_step1(request):
    """Step 1: Select scope (session, semester, filieres, date range)."""
    tenant = get_current_tenant(request)

    from core.models import Session, Semester
    from filieres.models import Filiere

    sessions = Session.objects.all()
    semesters = Semester.objects.all()
    filieres = Filiere.objects.filter(tenant=tenant, is_active=True)

    if request.method == 'POST':
        request.session['wizard_config'] = {
            'session_id': request.POST.get('session'),
            'semester_id': request.POST.get('semester'),
            'filiere_ids': request.POST.getlist('filieres'),
            'effective_from': request.POST.get('effective_from'),
            'effective_until': request.POST.get('effective_until'),
        }
        return redirect('frontend:scheduling:timetable_wizard_step2')

    return render(request, 'scheduling/wizard/step1_scope.html', {
        'title': _('Generate Timetable - Step 1: Scope'),
        'sessions': sessions,
        'semesters': semesters,
        'filieres': filieres,
    })


@login_required
@direction_only
@tenant_required
def timetable_wizard_step2(request):
    """Step 2: Configure constraints."""
    config = request.session.get('wizard_config', {})
    if not config:
        return redirect('frontend:scheduling:timetable_wizard_step1')

    if request.method == 'POST':
        config['constraints'] = {
            'max_classes_per_day': int(request.POST.get('max_classes_per_day', 4)),
            'max_consecutive_hours': int(request.POST.get('max_consecutive_hours', 4)),
            'respect_lunch_break': request.POST.get('respect_lunch_break') == 'on',
            'prefer_morning': request.POST.get('prefer_morning') == 'on',
        }
        request.session['wizard_config'] = config
        return redirect('frontend:scheduling:timetable_wizard_step3')

    return render(request, 'scheduling/wizard/step2_constraints.html', {
        'title': _('Generate Timetable - Step 2: Constraints'),
        'config': config,
    })


@login_required
@direction_only
@tenant_required
def timetable_wizard_step3(request):
    """Step 3: Preview and validate before generation."""
    config = request.session.get('wizard_config', {})
    if not config:
        return redirect('frontend:scheduling:timetable_wizard_step1')

    tenant = get_current_tenant(request)

    from core.models import Session, Semester
    from filieres.models import Filiere, FiliereSubject
    from course.models import CourseAllocation

    session = Session.objects.filter(id=config.get('session_id')).first()
    semester = Semester.objects.filter(id=config.get('semester_id')).first()
    filieres = Filiere.objects.filter(id__in=config.get('filiere_ids', []))

    # Count subjects to schedule
    subjects = FiliereSubject.objects.filter(
        filiere__in=filieres,
        semester=semester.semester if semester else 'First',
    )
    total_subjects = subjects.count()

    # Count available rooms and slots
    rooms_count = Room.objects.filter(tenant=tenant, is_active=True).count()
    slots_count = TimeSlot.objects.filter(
        tenant=tenant, is_active=True, slot_type='class'
    ).count()

    # Check for courses without professor allocation
    subject_course_ids = subjects.values_list('subject_id', flat=True)
    allocated_course_ids = CourseAllocation.objects.values_list(
        'courses__id', flat=True
    ).distinct()
    unallocated = set(subject_course_ids) - set(allocated_course_ids)

    warnings = []
    if rooms_count == 0:
        warnings.append(_('No rooms configured. Please add rooms first.'))
    if slots_count == 0:
        warnings.append(_('No time slots configured. Please add time slots first.'))
    if unallocated:
        warnings.append(_(f'{len(unallocated)} course(s) have no professor allocation.'))

    return render(request, 'scheduling/wizard/step3_preview.html', {
        'title': _('Generate Timetable - Step 3: Preview'),
        'config': config,
        'session': session,
        'semester': semester,
        'filieres': filieres,
        'total_subjects': total_subjects,
        'rooms_count': rooms_count,
        'slots_count': slots_count,
        'warnings': warnings,
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='5/h', method='POST')
def timetable_wizard_generate(request):
    """Trigger timetable generation."""
    if request.method != 'POST':
        return redirect('frontend:scheduling:timetable_wizard_step1')

    config = request.session.get('wizard_config', {})
    if not config:
        return redirect('frontend:scheduling:timetable_wizard_step1')

    tenant = get_current_tenant(request)

    from core.models import Session, Semester

    session = Session.objects.filter(id=config.get('session_id')).first()
    semester = Semester.objects.filter(id=config.get('semester_id')).first()

    if not session or not semester:
        messages.error(request, _('Invalid session or semester.'))
        return redirect('frontend:scheduling:timetable_wizard_step1')

    # Create generation record
    generation = TimetableGeneration.objects.create(
        tenant=tenant,
        session=session,
        semester=semester,
        config=config,
        created_by=request.user,
    )

    # Try async (Celery), fall back to synchronous
    try:
        from .tasks import generate_timetable_task
        generate_timetable_task.delay(generation.id)
        generation.status = 'running'
        generation.started_at = timezone.now()
        generation.save(update_fields=['status', 'started_at'])
        messages.info(request, _('Timetable generation started. This may take a moment...'))
    except Exception:
        from .engine.generator import TimetableGenerator
        generator = TimetableGenerator(generation)
        generator.generate()
        messages.success(request, _('Timetable generated successfully.'))

    # Clear wizard session
    if 'wizard_config' in request.session:
        del request.session['wizard_config']

    return redirect('frontend:scheduling:timetable_wizard_results', gen_id=generation.id)


@login_required
@direction_only
@tenant_required
def timetable_wizard_results(request, gen_id):
    """View generation results."""
    tenant = get_current_tenant(request)
    generation = get_object_or_404(TimetableGeneration, pk=gen_id, tenant=tenant)

    entries = generation.entries.select_related(
        'course', 'professor', 'room', 'time_slot', 'filiere'
    ).order_by('time_slot__day_of_week', 'time_slot__start_time')

    return render(request, 'scheduling/wizard/results.html', {
        'title': _('Generation Results'),
        'generation': generation,
        'entries': entries,
    })


# ============================================================================
# CONFLICT MANAGEMENT (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def conflict_list(request):
    """List scheduling conflicts."""
    tenant = get_current_tenant(request)

    from .engine.validator import detect_conflicts
    conflicts = detect_conflicts(tenant)

    return render(request, 'scheduling/conflicts/conflict_list.html', {
        'title': _('Schedule Conflicts'),
        'conflicts': conflicts,
    })


@login_required
@direction_only
@tenant_required
def conflict_resolve(request, pk):
    """Resolve a specific conflict."""
    tenant = get_current_tenant(request)
    entry = get_object_or_404(ScheduleEntry, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = ScheduleEntryForm(request.POST, instance=entry, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Conflict resolved.'))
            return redirect('frontend:scheduling:conflict_list')
    else:
        form = ScheduleEntryForm(instance=entry, tenant=tenant)

    return render(request, 'scheduling/conflicts/resolve.html', {
        'title': _('Resolve Conflict'),
        'entry': entry,
        'form': form,
    })


# ============================================================================
# REPORTS (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def room_utilization_report(request):
    """Room utilization statistics."""
    tenant = get_current_tenant(request)
    rooms = Room.objects.filter(tenant=tenant, is_active=True)

    room_stats = []
    for room in rooms:
        entry_count = ScheduleEntry.objects.filter(
            room=room, status='active'
        ).count()
        total_slots = TimeSlot.objects.filter(
            tenant=tenant, is_active=True, slot_type='class'
        ).count()
        utilization = (entry_count / max(total_slots, 1)) * 100

        room_stats.append({
            'room': room,
            'entries': entry_count,
            'total_slots': total_slots,
            'utilization': round(utilization, 1),
        })

    room_stats.sort(key=lambda x: x['utilization'], reverse=True)

    return render(request, 'scheduling/reports/utilization.html', {
        'title': _('Room Utilization Report'),
        'room_stats': room_stats,
    })


@login_required
@direction_only
@tenant_required
def export_timetable_pdf(request):
    """Export timetable as PDF."""
    tenant = get_current_tenant(request)

    filiere_id = request.GET.get('filiere_id')
    professor_id = request.GET.get('professor_id')
    room_id = request.GET.get('room_id')

    entries = ScheduleEntry.objects.filter(
        tenant=tenant, status='active'
    ).select_related('course', 'professor', 'room', 'time_slot', 'filiere')

    title = _('Complete Timetable')
    if filiere_id:
        entries = entries.filter(filiere_id=filiere_id)
        from filieres.models import Filiere
        fil = Filiere.objects.filter(id=filiere_id).first()
        if fil:
            title = f"{_('Timetable')} - {fil.name}"
    if professor_id:
        entries = entries.filter(professor_id=professor_id)
    if room_id:
        entries = entries.filter(room_id=room_id)

    entries = entries.order_by('time_slot__day_of_week', 'time_slot__start_time')

    # Build timetable grid
    from collections import defaultdict
    grid = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        day = entry.time_slot.get_day_of_week_display()
        time_range = f"{entry.time_slot.start_time:%H:%M}-{entry.time_slot.end_time:%H:%M}"
        grid[day][time_range].append(entry)

    # Render as HTML then convert to PDF
    from django.template.loader import render_to_string
    html_content = render_to_string('scheduling/reports/timetable_pdf.html', {
        'title': title,
        'grid': dict(grid),
        'entries': entries,
        'generated_at': timezone.now(),
    })

    try:
        from xhtml2pdf import pisa
        from io import BytesIO

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode('utf-8')), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="timetable.pdf"'
            return response
    except ImportError:
        pass

    # Fallback: return HTML
    return HttpResponse(html_content)


# ============================================================================
# SUBSTITUTION MANAGEMENT (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def substitution_list(request):
    """List all substitution requests."""
    tenant = get_current_tenant(request)
    subs = SubstitutionRequest.objects.filter(tenant=tenant).select_related(
        'schedule_entry__course', 'requesting_professor',
        'assigned_substitute',
    )

    status_filter = request.GET.get('status', '')
    if status_filter:
        subs = subs.filter(status=status_filter)

    paginator = Paginator(subs, 20)
    page = request.GET.get('page')
    subs = paginator.get_page(page)

    return render(request, 'scheduling/substitutions/list.html', {
        'title': _('Substitution Requests'),
        'substitution_requests': subs,
        'current_status': status_filter,
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def substitution_review(request, pk):
    """Review and approve/reject a substitution request."""
    tenant = get_current_tenant(request)
    sub = get_object_or_404(SubstitutionRequest, pk=pk, tenant=tenant)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            substitute_id = request.POST.get('substitute_id')
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

            # Create exception
            ScheduleException.objects.create(
                tenant=tenant,
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
            messages.success(request, _('Substitution approved.'))

        elif action == 'reject':
            sub.status = 'rejected'
            sub.reviewed_by = request.user
            sub.reviewed_at = timezone.now()
            sub.save()
            messages.info(request, _('Substitution rejected.'))

        return redirect('frontend:scheduling:substitution_list')

    # Get available professors for this time slot
    from django.contrib.auth import get_user_model
    User = get_user_model()
    busy_ids = ScheduleEntry.objects.filter(
        tenant=tenant,
        status='active',
        time_slot=sub.schedule_entry.time_slot,
    ).values_list('professor_id', flat=True)

    available_professors = User.objects.filter(
        tenant=tenant, role='professor'
    ).exclude(id__in=busy_ids)

    return render(request, 'scheduling/substitutions/review.html', {
        'title': _('Review Substitution'),
        'sub': sub,
        'available_professors': available_professors,
    })


# ============================================================================
# EXCEPTION MANAGEMENT (Direction/Admin)
# ============================================================================

@login_required
@direction_only
@tenant_required
def exception_list(request):
    """List all schedule exceptions."""
    tenant = get_current_tenant(request)
    exceptions = ScheduleException.objects.filter(tenant=tenant).select_related(
        'schedule_entry__course', 'new_room', 'substitute_professor',
    )

    paginator = Paginator(exceptions, 20)
    page = request.GET.get('page')
    exceptions = paginator.get_page(page)

    return render(request, 'scheduling/exceptions/list.html', {
        'title': _('Schedule Exceptions'),
        'exceptions': exceptions,
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def exception_create(request):
    """Create a schedule exception."""
    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = ScheduleExceptionForm(request.POST)
        if form.is_valid():
            exc = form.save(commit=False)
            exc.tenant = tenant
            exc.created_by = request.user
            exc.save()
            messages.success(request, _('Exception created.'))
            return redirect('frontend:scheduling:exception_list')
    else:
        form = ScheduleExceptionForm()

    return render(request, 'scheduling/exceptions/form.html', {
        'form': form,
        'title': _('Create Exception'),
    })


# ============================================================================
# NOTIFICATION VIEWS
# ============================================================================

@login_required
@tenant_required
def notification_list(request):
    """List user's schedule notifications."""
    notifications = ScheduleNotification.objects.filter(
        recipient=request.user
    )

    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications = paginator.get_page(page)

    return render(request, 'scheduling/notifications/list.html', {
        'title': _('Schedule Notifications'),
        'notifications': notifications,
    })


@login_required
@tenant_required
def notification_mark_read(request, pk):
    """Mark a notification as read (AJAX)."""
    notification = get_object_or_404(
        ScheduleNotification, pk=pk, recipient=request.user
    )
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=['is_read', 'read_at'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('frontend:scheduling:notification_list')


@login_required
@tenant_required
def notification_mark_all_read(request):
    """Mark all notifications as read (AJAX)."""
    count = ScheduleNotification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'marked_read': count})
    return redirect('frontend:scheduling:notification_list')

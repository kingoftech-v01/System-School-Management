"""
Parent Portal Views - All views for the parent dashboard and child monitoring.
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import parent_only
from accounts.forms import (
    AppointmentRequestForm,
    DisciplineAcknowledgmentForm,
    ParentMessageForm,
    PermissionSlipSignForm,
)
from accounts.models import (
    Parent,
    ParentTeacherAppointment,
    ParentTeacherMessage,
    PermissionSlip,
    Student,
    User,
)
from core.models import Semester, Session
from course.models import Course
from result.models import Result, TakenCourse


# ============================================================================
# Helpers
# ============================================================================

def get_parent_profiles(user):
    """Get all parent profiles for the current user."""
    return Parent.objects.select_related('student', 'student__student', 'student__program').filter(user=user)


def get_active_child(request):
    """Get the currently selected child from session, or default to first."""
    profiles = get_parent_profiles(request.user).exclude(student__isnull=True)
    if not profiles.exists():
        return None, None

    active_child_id = request.session.get('active_child_id')
    parent = None
    if active_child_id:
        parent = profiles.filter(student_id=active_child_id).first()
    if not parent:
        parent = profiles.first()

    return parent, parent.student if parent else None


def get_children_context(request):
    """Get common context for child selector in templates."""
    profiles = get_parent_profiles(request.user)
    children = [(p.student, p) for p in profiles if p.student]
    active_child_id = request.session.get('active_child_id')
    return {
        'children': children,
        'active_child_id': active_child_id,
    }


# ============================================================================
# Child Selection
# ============================================================================

@login_required
@parent_only
def parent_select_child(request, student_id):
    """Set the active child in session."""
    parent = get_parent_profiles(request.user).filter(student_id=student_id).first()
    if not parent:
        messages.error(request, _("You don't have access to this student's information."))
        return redirect('frontend:accounts:parent_dashboard')

    request.session['active_child_id'] = student_id
    messages.success(request, _('Switched to %(name)s.') % {'name': parent.student})
    return redirect('frontend:accounts:parent_dashboard')


# ============================================================================
# Dashboard
# ============================================================================

@login_required
@parent_only
def parent_dashboard(request):
    """Parent overview dashboard for the selected child."""
    parent, student = get_active_child(request)
    if not student:
        from enrollment.models import RegistrationForm
        pending = RegistrationForm.objects.filter(
            parent_user=request.user,
            status__in=['pending', 'under_review']
        ).order_by('-submitted_at')
        return render(request, 'parent/dashboard.html', {
            **get_children_context(request),
            'page_title': _('Parent Dashboard'),
            'no_children': True,
            'pending_enrollments': pending,
        })

    # Recent grades
    recent_grades = TakenCourse.objects.filter(
        student=student
    ).select_related('course').order_by('-id')[:5]

    # Pending invoices
    from payments.models import Invoice
    pending_invoices = Invoice.objects.filter(
        student=student, payment_complete=False
    ).order_by('-created_at')[:5]

    # Unread messages
    unread_count = ParentTeacherMessage.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    # Pending permission slips
    pending_slips = PermissionSlip.objects.filter(
        student=student, status='pending'
    ).count()

    # Unacknowledged discipline
    from discipline.models import DisciplinaryAction
    unacked_discipline = DisciplinaryAction.objects.filter(
        student=student.student, parent_acknowledged=False
    ).count()

    # GPA
    latest_result = Result.objects.filter(student=student).order_by('-id').first()

    # --- Analytics data for parent ---
    engagement_dates = json.dumps([])
    engagement_scores = json.dumps([])
    at_risk_status = None

    try:
        from analytics.models import StudentEngagement
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        engagement_qs = (
            StudentEngagement.objects
            .filter(student=student, date__gte=thirty_days_ago)
            .values('date')
            .annotate(avg_score=Avg('engagement_score'))
            .order_by('date')
        )
        dates_list = [e['date'].strftime('%b %d') for e in engagement_qs]
        scores_list = [round(float(e['avg_score'] or 0), 1) for e in engagement_qs]
        engagement_dates = json.dumps(dates_list)
        engagement_scores = json.dumps(scores_list)
    except Exception:
        pass

    try:
        from analytics.models import AtRiskStudent
        at_risk_status = AtRiskStudent.objects.filter(
            student=student, is_active=True
        ).order_by('-risk_score').first()
    except Exception:
        pass

    context = {
        **get_children_context(request),
        'page_title': _('Parent Dashboard'),
        'student': student,
        'parent': parent,
        'recent_grades': recent_grades,
        'pending_invoices': pending_invoices,
        'unread_count': unread_count,
        'pending_slips': pending_slips,
        'unacked_discipline': unacked_discipline,
        'latest_result': latest_result,
        # Analytics
        'engagement_dates': engagement_dates,
        'engagement_scores': engagement_scores,
        'at_risk_status': at_risk_status,
    }
    return render(request, 'parent/dashboard.html', context)


# ============================================================================
# Academic Monitoring
# ============================================================================

@login_required
@parent_only
def parent_child_grades(request):
    """View child's grades by semester."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    courses = TakenCourse.objects.filter(
        student=student
    ).select_related('course', 'course__program').order_by('course__semester', 'course__title')

    results = Result.objects.filter(student=student).order_by('-session', '-semester')

    context = {
        **get_children_context(request),
        'page_title': _('Grades & Results'),
        'student': student,
        'courses': courses,
        'results': results,
    }
    return render(request, 'parent/grades.html', context)


@login_required
@parent_only
def parent_child_attendance(request):
    """View child's attendance records."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from attendance.models import AttendanceReport
    reports = AttendanceReport.objects.filter(
        student=student
    ).select_related('attendance').order_by('-attendance__date')

    # Calculate stats
    total = reports.count()
    present = reports.filter(status='PRESENT').count()
    absent = reports.filter(status='ABSENT').count()
    late = reports.filter(status='LATE').count()
    rate = round((present / total * 100), 1) if total > 0 else 0

    paginator = Paginator(reports, 25)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Attendance'),
        'student': student,
        'reports': page,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'attendance_rate': rate,
    }
    return render(request, 'parent/attendance.html', context)


@login_required
@parent_only
def parent_child_timetable(request):
    """View child's enrolled courses / schedule."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first() if current_session else None

    enrolled_courses = TakenCourse.objects.filter(
        student=student
    ).select_related('course').order_by('course__semester', 'course__title')

    if current_semester:
        enrolled_courses = enrolled_courses.filter(course__semester=current_semester)

    context = {
        **get_children_context(request),
        'page_title': _('Timetable'),
        'student': student,
        'enrolled_courses': enrolled_courses,
        'current_session': current_session,
        'current_semester': current_semester,
    }
    return render(request, 'parent/timetable.html', context)


# ============================================================================
# Financial
# ============================================================================

@login_required
@parent_only
def parent_child_invoices(request):
    """List child's invoices."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from payments.models import Invoice
    invoices = Invoice.objects.filter(
        student=student
    ).select_related('fee_structure', 'semester').order_by('-created_at')

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'paid':
        invoices = invoices.filter(payment_complete=True)
    elif status_filter == 'unpaid':
        invoices = invoices.filter(payment_complete=False)

    paginator = Paginator(invoices, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Invoices'),
        'student': student,
        'invoices': page,
        'status_filter': status_filter,
    }
    return render(request, 'parent/invoices.html', context)


@login_required
@parent_only
def parent_child_payment_history(request):
    """View child's payment history."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from payments.models import Payment
    payments = Payment.objects.filter(
        invoice__student=student, status='completed'
    ).select_related('invoice').order_by('-payment_date')

    paginator = Paginator(payments, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Payment History'),
        'student': student,
        'payments': page,
    }
    return render(request, 'parent/payment_history.html', context)


@login_required
@parent_only
def parent_make_payment(request, invoice_id):
    """Pay an invoice for child via Stripe (redirects to existing payment gateway)."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from payments.models import Invoice
    invoice = get_object_or_404(Invoice, pk=invoice_id, student=student)

    if invoice.payment_complete:
        messages.info(request, _('This invoice has already been paid.'))
        return redirect('frontend:accounts:parent_child_invoices')

    # Store invoice in session and redirect to existing payment gateway
    request.session['invoice_session'] = invoice.invoice_code
    return redirect('frontend:payments:payment_gateways')


# ============================================================================
# Communication
# ============================================================================

@login_required
@parent_only
def parent_messages_inbox(request):
    """List parent's messages with teachers."""
    msgs = ParentTeacherMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient', 'student', 'student__student').order_by('-created_at')

    paginator = Paginator(msgs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    unread_count = ParentTeacherMessage.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    context = {
        **get_children_context(request),
        'page_title': _('Messages'),
        'messages_list': page,
        'unread_count': unread_count,
    }
    return render(request, 'parent/messages_inbox.html', context)


@login_required
@parent_only
def parent_messages_compose(request):
    """Send a message to a teacher."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    if request.method == 'POST':
        form = ParentMessageForm(request.POST, student=student)
        if form.is_valid():
            ParentTeacherMessage.objects.create(
                sender=request.user,
                recipient=form.cleaned_data['recipient'],
                student=student,
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['body'],
                parent_initiated=True,
            )
            messages.success(request, _('Message sent successfully.'))
            return redirect('frontend:accounts:parent_messages_inbox')
    else:
        form = ParentMessageForm(student=student)

    context = {
        **get_children_context(request),
        'page_title': _('Compose Message'),
        'form': form,
        'student': student,
    }
    return render(request, 'parent/messages_compose.html', context)


@login_required
@parent_only
def parent_messages_thread(request, message_id):
    """View a message and its conversation thread."""
    msg = get_object_or_404(
        ParentTeacherMessage.objects.select_related('sender', 'recipient', 'student'),
        pk=message_id,
    )

    # Verify access
    if msg.sender != request.user and msg.recipient != request.user:
        messages.error(request, _('You do not have access to this message.'))
        return redirect('frontend:accounts:parent_messages_inbox')

    # Mark as read if recipient is viewing
    if msg.recipient == request.user and not msg.is_read:
        msg.mark_read()

    # Get related thread (same sender/recipient pair + same student + same subject)
    thread = ParentTeacherMessage.objects.filter(
        student=msg.student,
        subject=msg.subject,
    ).filter(
        Q(sender=msg.sender, recipient=msg.recipient) |
        Q(sender=msg.recipient, recipient=msg.sender)
    ).select_related('sender', 'recipient').order_by('created_at')

    # Mark all in thread as read for current user
    thread.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )

    # Reply form
    if request.method == 'POST':
        reply_body = request.POST.get('reply_body', '').strip()
        if reply_body:
            other = msg.sender if msg.recipient == request.user else msg.recipient
            ParentTeacherMessage.objects.create(
                sender=request.user,
                recipient=other,
                student=msg.student,
                subject=msg.subject,
                body=reply_body,
                parent_initiated=(request.user.role == 'parent'),
            )
            messages.success(request, _('Reply sent.'))
            return redirect('frontend:accounts:parent_messages_thread', message_id=msg.pk)

    context = {
        **get_children_context(request),
        'page_title': msg.subject,
        'message': msg,
        'thread': thread,
    }
    return render(request, 'parent/messages_thread.html', context)


# ============================================================================
# Appointments
# ============================================================================

@login_required
@parent_only
def parent_appointments(request):
    """List parent's appointments."""
    parent, student = get_active_child(request)
    profiles = get_parent_profiles(request.user)
    parent_ids = profiles.values_list('pk', flat=True)

    appointments = ParentTeacherAppointment.objects.filter(
        parent__in=parent_ids
    ).select_related('parent', 'teacher', 'student', 'student__student').order_by('-date', 'time_slot')

    paginator = Paginator(appointments, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Appointments'),
        'appointments': page,
    }
    return render(request, 'parent/appointments.html', context)


@login_required
@parent_only
def parent_appointment_request(request):
    """Request a new appointment with a teacher."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST, student=student)
        if form.is_valid():
            # Check for conflicts
            conflict = ParentTeacherAppointment.objects.filter(
                teacher=form.cleaned_data['teacher'],
                date=form.cleaned_data['preferred_date'],
                time_slot=form.cleaned_data['preferred_time'],
                status__in=['requested', 'confirmed'],
            ).exists()

            if conflict:
                messages.error(request, _('This time slot is already booked. Please choose another.'))
            else:
                ParentTeacherAppointment.objects.create(
                    parent=parent,
                    teacher=form.cleaned_data['teacher'],
                    student=student,
                    date=form.cleaned_data['preferred_date'],
                    time_slot=form.cleaned_data['preferred_time'],
                    reason=form.cleaned_data['reason'],
                    status='requested',
                )
                messages.success(request, _('Appointment request submitted. You will be notified when confirmed.'))
                return redirect('frontend:accounts:parent_appointments')
    else:
        form = AppointmentRequestForm(student=student)

    context = {
        **get_children_context(request),
        'page_title': _('Request Appointment'),
        'form': form,
        'student': student,
    }
    return render(request, 'parent/appointment_request.html', context)


# ============================================================================
# Discipline
# ============================================================================

@login_required
@parent_only
def parent_disciplinary_records(request):
    """View child's disciplinary actions."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from discipline.models import DisciplinaryAction
    records = DisciplinaryAction.objects.filter(
        student=student.student
    ).order_by('-incident_date')

    paginator = Paginator(records, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Disciplinary Records'),
        'student': student,
        'records': page,
    }
    return render(request, 'parent/discipline.html', context)


@login_required
@parent_only
def parent_acknowledge_discipline(request, action_id):
    """Acknowledge a disciplinary action with an optional response."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    from discipline.models import DisciplinaryAction
    action = get_object_or_404(DisciplinaryAction, pk=action_id, student=student.student)

    if action.parent_acknowledged:
        messages.info(request, _('This action has already been acknowledged.'))
        return redirect('frontend:accounts:parent_disciplinary_records')

    if request.method == 'POST':
        form = DisciplineAcknowledgmentForm(request.POST)
        if form.is_valid():
            action.parent_acknowledged = True
            action.parent_acknowledged_at = timezone.now()
            action.parent_response = form.cleaned_data.get('response', '')
            action.save(update_fields=['parent_acknowledged', 'parent_acknowledged_at', 'parent_response'])
            messages.success(request, _('Disciplinary action acknowledged.'))
            return redirect('frontend:accounts:parent_disciplinary_records')
    else:
        form = DisciplineAcknowledgmentForm()

    context = {
        **get_children_context(request),
        'page_title': _('Acknowledge Disciplinary Action'),
        'action': action,
        'form': form,
        'student': student,
    }
    return render(request, 'parent/discipline_acknowledge.html', context)


# ============================================================================
# Permission Slips
# ============================================================================

@login_required
@parent_only
def parent_permission_slips(request):
    """List permission slips for child."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    slips = PermissionSlip.objects.filter(
        student=student
    ).select_related('created_by', 'signed_by').order_by('-created_at')

    # Auto-expire overdue slips
    slips.filter(status='pending', deadline__lt=timezone.now().date()).update(status='expired')

    paginator = Paginator(slips, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Permission Slips'),
        'student': student,
        'slips': page,
    }
    return render(request, 'parent/permission_slips.html', context)


@login_required
@parent_only
def parent_sign_permission_slip(request, slip_id):
    """Sign or decline a permission slip."""
    parent, student = get_active_child(request)
    if not student:
        messages.error(request, _('No student selected.'))
        return redirect('frontend:accounts:parent_dashboard')

    slip = get_object_or_404(PermissionSlip, pk=slip_id, student=student)

    if slip.status != 'pending':
        messages.info(request, _('This permission slip has already been %(status)s.') % {'status': slip.get_status_display()})
        return redirect('frontend:accounts:parent_permission_slips')

    if request.method == 'POST':
        form = PermissionSlipSignForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data.get('notes', '')
            if action == 'sign':
                slip.sign(parent, notes)
                messages.success(request, _('Permission slip signed successfully.'))
            else:
                slip.decline(parent, notes)
                messages.success(request, _('Permission slip declined.'))
            return redirect('frontend:accounts:parent_permission_slips')
    else:
        form = PermissionSlipSignForm()

    context = {
        **get_children_context(request),
        'page_title': _('Sign Permission Slip'),
        'slip': slip,
        'form': form,
        'student': student,
    }
    return render(request, 'parent/permission_slip_sign.html', context)


# ============================================================================
# Events
# ============================================================================

@login_required
@parent_only
def parent_events(request):
    """Events filtered for parent audience."""
    from events.models import Event
    events = Event.objects.filter(
        target_audience__in=['all', 'parents'],
        end_date__gte=timezone.now(),
    ).order_by('start_date')

    paginator = Paginator(events, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        **get_children_context(request),
        'page_title': _('Events'),
        'events': page,
    }
    return render(request, 'parent/events.html', context)


@login_required
@parent_only
def parent_event_detail(request, event_id):
    """Event detail view for parents."""
    from events.models import Event
    event = get_object_or_404(Event, pk=event_id)

    context = {
        **get_children_context(request),
        'page_title': event.title,
        'event': event,
    }
    return render(request, 'parent/event_detail.html', context)

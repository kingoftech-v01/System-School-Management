"""
Attendance Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Taking attendance for classes
- Viewing attendance reports
- Managing students, groups, and subjects
- Attendance statistics and analytics

All views render HTML templates.
Frontend URL namespace: frontend:attendance:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from accounts.decorators import lecturer_required, direction_only, tenant_required

from .models import Student, Group, Subject, Attendance, AttendanceReport, Satus
from .forms import AttendanceForm, AttendanceReportForm, StudentForm, GroupForm, SubjectForm


# ============================================================================
# ATTENDANCE TAKING VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def attendance_dashboard(request):
    """Main attendance dashboard."""
    today = timezone.now().date()

    # Get today's attendance sessions
    today_attendances = Attendance.objects.filter(
        date=today,
        lecturer=request.user
    ).select_related('subject', 'group')

    # Get recent attendance sessions
    recent_attendances = Attendance.objects.filter(
        lecturer=request.user
    ).select_related('subject', 'group').order_by('-date', '-created_at')[:10]

    context = {
        'today_attendances': today_attendances,
        'recent_attendances': recent_attendances,
        'title': _('Attendance Dashboard'),
    }

    return render(request, 'attendance/dashboard.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def take_attendance(request):
    """Take attendance for a class session."""
    if request.method == 'POST':
        form = AttendanceForm(request.POST, lecturer=request.user)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.lecturer = request.user
            attendance.save()

            messages.success(request, _('Attendance session created. Now mark students.'))
            return redirect('frontend:attendance:mark_attendance', pk=attendance.pk)
    else:
        form = AttendanceForm(lecturer=request.user)

    context = {
        'form': form,
        'title': _('Take Attendance'),
    }

    return render(request, 'attendance/take_attendance.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def mark_attendance(request, pk):
    """Mark individual student attendance for a session."""
    attendance = get_object_or_404(
        Attendance,
        pk=pk,
        lecturer=request.user
    )

    # Get students in the group
    students = Student.objects.filter(group=attendance.group).order_by('last_name', 'first_name')

    if request.method == 'POST':
        # Process attendance marks
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                AttendanceReport.objects.update_or_create(
                    attendance=attendance,
                    student=student,
                    defaults={'status': status}
                )

        messages.success(request, _('Attendance marked successfully.'))
        return redirect('frontend:attendance:attendance_detail', pk=attendance.pk)

    # Get existing reports
    existing_reports = {
        report.student_id: report.status
        for report in AttendanceReport.objects.filter(attendance=attendance)
    }

    context = {
        'attendance': attendance,
        'students': students,
        'existing_reports': existing_reports,
        'status_choices': Satus.choices if hasattr(Satus, 'choices') else [],
        'title': _('Mark Attendance'),
    }

    return render(request, 'attendance/mark_attendance.html', context)


@login_required
@tenant_required
def attendance_detail(request, pk):
    """View attendance session details."""
    attendance = get_object_or_404(
        Attendance.objects.select_related('subject', 'group', 'lecturer'),
        pk=pk
    )

    # Get attendance reports for this session
    reports = AttendanceReport.objects.filter(
        attendance=attendance
    ).select_related('student').order_by('student__last_name')

    # Statistics
    total_students = reports.count()
    present_count = reports.filter(status=Satus.PRESENT).count() if hasattr(Satus, 'PRESENT') else 0
    absent_count = reports.filter(status=Satus.ABSENT).count() if hasattr(Satus, 'ABSENT') else 0
    late_count = reports.filter(status=Satus.LATE).count() if hasattr(Satus, 'LATE') else 0

    context = {
        'attendance': attendance,
        'reports': reports,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'title': _('Attendance Details'),
    }

    return render(request, 'attendance/attendance_detail.html', context)


# ============================================================================
# STUDENT ATTENDANCE REPORTS
# ============================================================================

@login_required
@tenant_required
def student_attendance_report(request, student_id):
    """View attendance report for a specific student."""
    student = get_object_or_404(Student, pk=student_id)

    # Get all attendance reports for this student
    reports = AttendanceReport.objects.filter(
        student=student
    ).select_related('attendance__subject').order_by('-attendance__date')

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        reports = reports.filter(attendance__subject_id=subject_id)

    # Pagination
    paginator = Paginator(reports, 50)
    page_num = request.GET.get('page', 1)
    reports_page = paginator.get_page(page_num)

    # Calculate attendance percentage
    attendance_percentage = student.get_attendance_percentage()

    context = {
        'student': student,
        'reports': reports_page,
        'attendance_percentage': attendance_percentage,
        'subjects': student.get_subjects,
        'title': _('Student Attendance Report'),
    }

    return render(request, 'attendance/student_report.html', context)


# ============================================================================
# MANAGEMENT VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
def student_list(request):
    """List all students."""
    students = Student.objects.select_related('group').order_by('last_name', 'first_name')

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Filter by group
    group_id = request.GET.get('group')
    if group_id:
        students = students.filter(group_id=group_id)

    # Pagination
    paginator = Paginator(students, 50)
    page_num = request.GET.get('page', 1)
    students_page = paginator.get_page(page_num)

    context = {
        'students': students_page,
        'groups': Group.objects.all(),
        'title': _('Students'),
    }

    return render(request, 'attendance/student_list.html', context)


@login_required
@direction_only
@tenant_required
def group_list(request):
    """List all groups."""
    groups = Group.objects.annotate(
        student_count=Count('students')
    ).order_by('name')

    context = {
        'groups': groups,
        'title': _('Groups'),
    }

    return render(request, 'attendance/group_list.html', context)


@login_required
@tenant_required
def subject_list(request):
    """List all subjects."""
    subjects = Subject.objects.annotate(
        group_count=Count('groups')
    ).order_by('name')

    context = {
        'subjects': subjects,
        'title': _('Subjects'),
    }

    return render(request, 'attendance/subject_list.html', context)

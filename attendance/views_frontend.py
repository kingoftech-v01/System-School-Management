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
from accounts.decorators import lecturer_required, prefet_allowed, role_required, tenant_required

from .models import Student, Group, Subject, Attendance, AttendanceReport, Satus
from .forms import AttendanceForm, AttendanceReportForm, StudentForm, GroupForm, SubjectForm


# ============================================================================
# ATTENDANCE TAKING VIEWS
# ============================================================================

@login_required
@role_required('professor', 'prefet', 'direction', 'admin')
@tenant_required
@ratelimit(key='user', rate='100/h')
def attendance_dashboard(request):
    """Main attendance dashboard."""
    today = timezone.now().date()

    # Get today's attendance sessions
    today_attendances = Attendance.objects.filter(
        date=today,
        subject__teacher=request.user
    ).select_related('subject')

    # Get recent attendance sessions
    recent_attendances = Attendance.objects.filter(
        subject__teacher=request.user
    ).select_related('subject').order_by('-date', '-created_at')[:10]

    # Summary stats for today's attendance reports
    today_reports = AttendanceReport.objects.filter(
        attendance__date=today,
        attendance__subject__teacher=request.user
    )
    present_count = today_reports.filter(status=Satus.PRESENT).count() if hasattr(Satus, 'PRESENT') else 0
    absent_count = today_reports.filter(status=Satus.ABSENT).count() if hasattr(Satus, 'ABSENT') else 0
    late_count = today_reports.filter(status=Satus.LATE).count() if hasattr(Satus, 'LATE') else 0
    total_count = today_reports.count()

    context = {
        'today_attendances': today_attendances,
        'recent_attendances': recent_attendances,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'total_count': total_count,
        'title': _('Attendance Dashboard'),
    }

    return render(request, 'attendance/dashboard.html', context)


@login_required
@role_required('professor', 'prefet', 'direction', 'admin')
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def take_attendance(request):
    """Take attendance for a class session."""
    if request.method == 'POST':
        form = AttendanceForm(request.POST, lecturer=request.user)
        if form.is_valid():
            attendance = form.save()

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
@role_required('professor', 'prefet', 'direction', 'admin')
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def mark_attendance(request, pk):
    """Mark individual student attendance for a session."""
    attendance = get_object_or_404(
        Attendance,
        pk=pk,
        subject__teacher=request.user
    )

    # Get students from all groups associated with the subject
    groups = attendance.subject.group.all()
    students = Student.objects.filter(group__in=groups).order_by('last_name', 'first_name')

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
@lecturer_required
@tenant_required
def attendance_detail(request, pk):
    """View attendance session details."""
    attendance = get_object_or_404(
        Attendance.objects.select_related('subject', 'subject__teacher'),
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

    # Permission check: students can only view their own attendance
    user_role = getattr(request.user, 'role', '')
    if user_role == 'student' or (hasattr(request.user, 'is_student') and request.user.is_student):
        from accounts.models import Student as AccountStudent
        try:
            own_student = AccountStudent.objects.get(student=request.user)
            # Compare by email since attendance Student is a different model
            if student.email != request.user.email:
                messages.error(request, "You can only view your own attendance report.")
                return redirect("frontend:attendance:dashboard")
        except AccountStudent.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect("frontend:attendance:dashboard")
    elif user_role == 'parent':
        messages.error(request, "Access denied.")
        return redirect("frontend:core:dashboard")

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
@prefet_allowed
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
@prefet_allowed
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
        group_count=Count('group')
    ).order_by('name')

    context = {
        'subjects': subjects,
        'title': _('Subjects'),
    }

    return render(request, 'attendance/subject_list.html', context)


# ============================================================================
# ATTENDANCE SESSION EDIT/DELETE
# ============================================================================

@login_required
@role_required('professor', 'prefet', 'direction', 'admin')
@tenant_required
@ratelimit(key='user', rate='100/h')
def attendance_edit(request, pk):
    """Edit an attendance session."""
    attendance = get_object_or_404(Attendance, pk=pk, subject__teacher=request.user)

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance, lecturer=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Attendance session updated successfully.'))
            return redirect('frontend:attendance:attendance_detail', pk=attendance.pk)
    else:
        form = AttendanceForm(instance=attendance, lecturer=request.user)

    context = {
        'form': form,
        'attendance': attendance,
        'title': _('Edit Attendance Session'),
    }

    return render(request, 'attendance/attendance_form.html', context)


@login_required
@role_required('professor', 'prefet', 'direction', 'admin')
@tenant_required
@ratelimit(key='user', rate='100/h')
def attendance_delete(request, pk):
    """Delete an attendance session with GET confirmation and POST action."""
    attendance = get_object_or_404(Attendance, pk=pk, subject__teacher=request.user)

    if request.method == 'POST':
        attendance.delete()
        messages.success(request, _('Attendance session deleted successfully.'))
        return redirect('frontend:attendance:dashboard')

    context = {
        'object': attendance,
        'object_name': str(attendance),
        'cancel_url': 'frontend:attendance:attendance_detail',
        'cancel_pk': attendance.pk,
        'title': _('Delete Attendance Session'),
    }

    return render(request, 'attendance/confirm_delete.html', context)


# ============================================================================
# STUDENT CRUD
# ============================================================================

@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def student_create(request):
    """Create a new attendance student."""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, _('Student created successfully.'))
            return redirect('frontend:attendance:student_list')
    else:
        form = StudentForm()

    context = {
        'form': form,
        'title': _('Add Student'),
    }

    return render(request, 'attendance/student_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def student_edit(request, pk):
    """Edit an attendance student."""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, _('Student updated successfully.'))
            return redirect('frontend:attendance:student_list')
    else:
        form = StudentForm(instance=student)

    context = {
        'form': form,
        'student': student,
        'title': _('Edit Student'),
    }

    return render(request, 'attendance/student_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def student_delete(request, pk):
    """Delete an attendance student with GET confirmation and POST action."""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        name = f"{student.first_name} {student.last_name}"
        student.delete()
        messages.success(request, _(f'Student {name} deleted successfully.'))
        return redirect('frontend:attendance:student_list')

    context = {
        'object': student,
        'object_name': str(student),
        'cancel_url': 'frontend:attendance:student_list',
        'title': _('Delete Student'),
    }

    return render(request, 'attendance/confirm_delete.html', context)


# ============================================================================
# GROUP CRUD
# ============================================================================

@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def group_create(request):
    """Create a new group."""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Group created successfully.'))
            return redirect('frontend:attendance:group_list')
    else:
        form = GroupForm()

    context = {
        'form': form,
        'title': _('Add Group'),
    }

    return render(request, 'attendance/group_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def group_edit(request, pk):
    """Edit a group."""
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, _('Group updated successfully.'))
            return redirect('frontend:attendance:group_list')
    else:
        form = GroupForm(instance=group)

    context = {
        'form': form,
        'group': group,
        'title': _('Edit Group'),
    }

    return render(request, 'attendance/group_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def group_delete(request, pk):
    """Delete a group with GET confirmation and POST action."""
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, _(f'Group {name} deleted successfully.'))
        return redirect('frontend:attendance:group_list')

    context = {
        'object': group,
        'object_name': group.name,
        'cancel_url': 'frontend:attendance:group_list',
        'title': _('Delete Group'),
    }

    return render(request, 'attendance/confirm_delete.html', context)


# ============================================================================
# SUBJECT CRUD
# ============================================================================

@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def subject_create(request):
    """Create a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Subject created successfully.'))
            return redirect('frontend:attendance:subject_list')
    else:
        form = SubjectForm()

    context = {
        'form': form,
        'title': _('Add Subject'),
    }

    return render(request, 'attendance/subject_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def subject_edit(request, pk):
    """Edit a subject."""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, _('Subject updated successfully.'))
            return redirect('frontend:attendance:subject_list')
    else:
        form = SubjectForm(instance=subject)

    context = {
        'form': form,
        'subject': subject,
        'title': _('Edit Subject'),
    }

    return render(request, 'attendance/subject_form.html', context)


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def subject_delete(request, pk):
    """Delete a subject with GET confirmation and POST action."""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        name = subject.name
        subject.delete()
        messages.success(request, _(f'Subject {name} deleted successfully.'))
        return redirect('frontend:attendance:subject_list')

    context = {
        'object': subject,
        'object_name': subject.name,
        'cancel_url': 'frontend:attendance:subject_list',
        'title': _('Delete Subject'),
    }

    return render(request, 'attendance/confirm_delete.html', context)

"""
Cross-app data gathering functions for report generation.
Each function returns a context dict ready for template rendering.
"""
from accounts.models import Parent, Student


def collect_student_complete_record(student_pk):
    """Gather ALL data for a student complete record PDF."""
    student = Student.objects.select_related(
        'student', 'program'
    ).get(pk=student_pk)
    user = student.student

    parents = Parent.objects.filter(student=student).select_related('user')

    # Enrollment history
    from enrollment.models import RegistrationForm
    registrations = RegistrationForm.objects.filter(
        email=user.email
    ).order_by('-submitted_at')

    # Grades
    from result.models import TakenCourse, Result
    taken_courses = TakenCourse.objects.filter(
        student=student
    ).select_related('course').order_by('course__title')

    results = Result.objects.filter(student=student).order_by('semester')

    # Attendance summary
    from attendance.models import AttendanceReport, Status
    try:
        from attendance.models import Student as AttStudent
        att_student = AttStudent.objects.get(email=user.email)
        attendance_reports = AttendanceReport.objects.filter(
            student=att_student
        )
        total_att = attendance_reports.count()
        present = attendance_reports.filter(status=Status.PRESENT).count()
        absent = attendance_reports.filter(status=Status.ABSENT).count()
        late = attendance_reports.filter(status=Status.LATE).count()
    except Exception:
        total_att = present = absent = late = 0

    # Discipline history
    from discipline.models import DisciplinaryAction
    discipline_actions = DisciplinaryAction.objects.filter(
        student=user
    ).order_by('-incident_date')

    # Certificates
    from certificates.models import Certificate
    certificates = Certificate.objects.filter(
        student=student
    ).order_by('-created_at')

    # Safeguarding incidents
    from safeguarding.models import Incident
    incidents = Incident.objects.filter(
        students_involved=student
    ).order_by('-incident_date')

    # Visitor logs
    from safeguarding.models import VisitorLog
    visitor_logs = VisitorLog.objects.filter(
        students_involved=student
    ).order_by('-time_in')

    return {
        'student': student,
        'user': user,
        'parents': parents,
        'registrations': registrations,
        'taken_courses': taken_courses,
        'results': results,
        'attendance_summary': {
            'total': total_att,
            'present': present,
            'absent': absent,
            'late': late,
            'percentage': (
                round((present + late) / total_att * 100, 1)
                if total_att > 0 else 0
            ),
        },
        'discipline_actions': discipline_actions,
        'certificates': certificates,
        'incidents': incidents,
        'visitor_logs': visitor_logs,
    }


def collect_incident_report(incident_pk):
    """Gather data for a single incident report PDF."""
    from safeguarding.models import Incident
    incident = Incident.objects.select_related(
        'reported_by', 'updated_by', 'tenant', 'disciplinary_action',
    ).prefetch_related(
        'students_involved', 'staff_involved', 'attachments',
    ).get(pk=incident_pk)

    return {
        'incident': incident,
    }


def collect_discipline_history(student_user_pk, date_from=None, date_to=None):
    """Gather complete discipline history for a student."""
    from django.contrib.auth import get_user_model
    from discipline.models import DisciplinaryAction

    User = get_user_model()
    user = User.objects.get(pk=student_user_pk)
    actions = DisciplinaryAction.objects.filter(
        student=user
    ).select_related('reported_by', 'updated_by').order_by('-incident_date')

    if date_from:
        actions = actions.filter(incident_date__gte=date_from)
    if date_to:
        actions = actions.filter(incident_date__lte=date_to)

    severity_counts = {}
    for action in actions:
        severity_counts[action.severity] = (
            severity_counts.get(action.severity, 0) + 1
        )

    return {
        'student_user': user,
        'actions': actions,
        'total_incidents': actions.count(),
        'severity_counts': severity_counts,
        'unresolved_count': actions.filter(is_resolved=False).count(),
        'date_from': date_from,
        'date_to': date_to,
    }


def collect_attendance_report(
    student_pk=None, group_pk=None, date_from=None, date_to=None,
):
    """Gather attendance data for a report."""
    from attendance.models import (
        AttendanceReport,
        DailyAttendanceStat,
        Group,
        Student as AttStudent,
    )

    filters = {}
    if date_from:
        filters['attendance__date__gte'] = date_from
    if date_to:
        filters['attendance__date__lte'] = date_to

    if student_pk:
        att_student = AttStudent.objects.get(pk=student_pk)
        reports = AttendanceReport.objects.filter(
            student=att_student, **filters
        ).select_related(
            'attendance', 'attendance__subject'
        ).order_by('-attendance__date')

        return {
            'mode': 'student',
            'student': att_student,
            'reports': reports,
            'date_from': date_from,
            'date_to': date_to,
        }

    elif group_pk:
        group = Group.objects.get(pk=group_pk)
        daily_stats = DailyAttendanceStat.objects.filter(
            group=group
        ).select_related('subject')

        if date_from:
            daily_stats = daily_stats.filter(date__gte=date_from)
        if date_to:
            daily_stats = daily_stats.filter(date__lte=date_to)

        return {
            'mode': 'class',
            'group': group,
            'daily_stats': daily_stats.order_by('-date'),
            'date_from': date_from,
            'date_to': date_to,
        }

    return {'mode': 'empty'}

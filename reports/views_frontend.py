"""
Frontend views for report exports.
Each view collects data, renders a PDF/CSV/Excel, and logs the export.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit

from accounts.decorators import direction_only, prefet_allowed, role_required
from accounts.models import Student

from .data_collectors import (
    collect_attendance_report,
    collect_discipline_history,
    collect_incident_report,
    collect_student_complete_record,
)
from .forms import (
    AttendanceReportFilterForm,
    DisciplineHistoryFilterForm,
    ExportReasonForm,
    GradesExportFilterForm,
)
from .models import ReportExportLog
from .utils import (
    log_export,
    render_csv_response,
    render_excel_response,
    render_report_pdf,
)


# ---- Student Complete Record ----

@login_required
@role_required('direction', 'admin', 'registrar', 'prefet')
@ratelimit(key='user', rate='20/h')
def student_complete_record(request, pk):
    """Export a student's complete record as PDF. Requires reason."""
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = ExportReasonForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            context = collect_student_complete_record(pk)
            user = context['user']

            log_export(
                request,
                report_type='student_complete_record',
                export_format='pdf',
                title=f'Complete Record: {user.get_full_name}',
                student_id=pk,
                reason=reason,
            )

            return render_report_pdf(
                'reports/pdf/student_complete_record.html',
                context,
                request=request,
                filename=f'student_record_{user.username}.pdf',
                confidential=True,
            )
    else:
        form = ExportReasonForm()

    return render(request, 'reports/export_reason_form.html', {
        'form': form,
        'student': student,
        'title': _('Export Student Complete Record'),
        'report_type': _('Student Complete Record'),
    })


# ---- Incident Report PDF ----

@login_required
@prefet_allowed
@ratelimit(key='user', rate='30/h')
def incident_report_pdf(request, pk):
    """Export a single incident report as PDF."""
    context = collect_incident_report(pk)
    incident = context['incident']

    log_export(
        request,
        report_type='incident_report',
        export_format='pdf',
        title=f'Incident: {incident.title}',
        incident_id=pk,
    )

    return render_report_pdf(
        'reports/pdf/incident_report.html',
        context,
        request=request,
        filename=f'incident_{pk}.pdf',
        confidential=True,
    )


# ---- Attendance Report ----

@login_required
@role_required(
    'direction', 'admin', 'professor', 'prefet', 'registrar', 'secretary'
)
@ratelimit(key='user', rate='30/h')
def attendance_report(request):
    """Export attendance report as PDF, CSV, or Excel."""
    if request.method == 'POST':
        form = AttendanceReportFilterForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data.get('student')
            group = form.cleaned_data.get('group')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            export_format = form.cleaned_data['export_format']

            context = collect_attendance_report(
                student_pk=student.pk if student else None,
                group_pk=group.pk if group else None,
                date_from=date_from,
                date_to=date_to,
            )

            filter_params = {
                'student_pk': student.pk if student else None,
                'group_pk': group.pk if group else None,
                'date_from': str(date_from) if date_from else None,
                'date_to': str(date_to) if date_to else None,
            }

            if export_format == 'pdf':
                report_type = 'attendance_report'
                title = 'Attendance Report'
                if student:
                    title += f': {student}'
                elif group:
                    title += f': {group}'

                log_export(
                    request,
                    report_type=report_type,
                    export_format='pdf',
                    title=title,
                    student_id=student.pk if student else None,
                    filter_params=filter_params,
                )

                return render_report_pdf(
                    'reports/pdf/attendance_report.html',
                    context,
                    request=request,
                    filename='attendance_report.pdf',
                )

            elif export_format == 'csv':
                header, rows = _attendance_to_rows(context)
                log_export(
                    request,
                    report_type='attendance_csv',
                    export_format='csv',
                    title='Attendance CSV Export',
                    student_id=student.pk if student else None,
                    filter_params=filter_params,
                )
                return render_csv_response(
                    'attendance_report.csv', header, rows,
                )

            else:  # xlsx
                header, rows = _attendance_to_rows(context)
                log_export(
                    request,
                    report_type='attendance_xlsx',
                    export_format='xlsx',
                    title='Attendance Excel Export',
                    student_id=student.pk if student else None,
                    filter_params=filter_params,
                )
                return render_excel_response(
                    'attendance_report.xlsx', 'Attendance', header, rows,
                )
    else:
        form = AttendanceReportFilterForm()

    return render(request, 'reports/attendance_filter.html', {
        'form': form,
        'title': _('Attendance Report'),
    })


def _attendance_to_rows(context):
    """Convert attendance context to header + rows for CSV/Excel."""
    mode = context.get('mode')
    if mode == 'student':
        header = ['Date', 'Subject', 'Status']
        rows = []
        for r in context.get('reports', []):
            rows.append([
                str(r.attendance.date),
                str(r.attendance.subject) if r.attendance.subject else '',
                r.get_status_display(),
            ])
        return header, rows

    elif mode == 'class':
        header = ['Date', 'Subject', 'Total', 'Present', 'Absent', 'Late']
        rows = []
        for stat in context.get('daily_stats', []):
            rows.append([
                str(stat.date),
                str(stat.subject) if stat.subject else '',
                stat.total_students,
                stat.present_count,
                stat.absent_count,
                stat.late_count,
            ])
        return header, rows

    return ['No data'], []


# ---- Discipline History PDF ----

@login_required
@prefet_allowed
@ratelimit(key='user', rate='30/h')
def discipline_history_pdf(request, pk):
    """Export discipline history for a student's user account."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = get_object_or_404(User, pk=pk)

    form = DisciplineHistoryFilterForm(request.GET or None)
    date_from = None
    date_to = None
    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

    context = collect_discipline_history(
        pk, date_from=date_from, date_to=date_to,
    )

    log_export(
        request,
        report_type='discipline_history',
        export_format='pdf',
        title=f'Discipline History: {user.get_full_name}',
        student_id=pk,
        filter_params={
            'date_from': str(date_from) if date_from else None,
            'date_to': str(date_to) if date_to else None,
        },
    )

    return render_report_pdf(
        'reports/pdf/discipline_history.html',
        context,
        request=request,
        filename=f'discipline_{user.username}.pdf',
        confidential=True,
    )


# ---- Grades Export (CSV / Excel) ----

@login_required
@role_required('direction', 'admin', 'professor', 'registrar')
@ratelimit(key='user', rate='30/h')
def grades_export(request, pk):
    """Export grades for a student as CSV or Excel."""
    student = get_object_or_404(Student, pk=pk)
    user = student.student

    form = GradesExportFilterForm(request.GET or None)
    export_format = 'csv'
    if form.is_valid():
        export_format = form.cleaned_data.get('export_format', 'csv')

    from result.models import TakenCourse
    taken_courses = TakenCourse.objects.filter(
        student=student
    ).select_related('course').order_by('course__title')

    header = ['Course', 'Credit', 'Grade', 'Point', 'Comment']
    rows = []
    for tc in taken_courses:
        rows.append([
            tc.course.title if tc.course else '',
            tc.course.credit if tc.course else '',
            tc.grade if hasattr(tc, 'grade') else '',
            tc.point if hasattr(tc, 'point') else '',
            tc.comment if hasattr(tc, 'comment') else '',
        ])

    if export_format == 'xlsx':
        report_type = 'grades_xlsx'
        log_export(
            request,
            report_type=report_type,
            export_format='xlsx',
            title=f'Grades Export: {user.get_full_name}',
            student_id=pk,
        )
        return render_excel_response(
            f'grades_{user.username}.xlsx',
            'Grades',
            header,
            rows,
        )
    else:
        report_type = 'grades_csv'
        log_export(
            request,
            report_type=report_type,
            export_format='csv',
            title=f'Grades Export: {user.get_full_name}',
            student_id=pk,
        )
        return render_csv_response(
            f'grades_{user.username}.csv', header, rows,
        )


# ---- Export Audit Log ----

@login_required
@direction_only
@ratelimit(key='user', rate='100/h')
def export_audit_log(request):
    """View the audit log of all report exports."""
    logs = ReportExportLog.objects.select_related(
        'exported_by'
    ).order_by('-exported_at')

    tenant = getattr(request, 'tenant', None)
    if tenant:
        logs = logs.filter(tenant=tenant)

    report_type = request.GET.get('type', '').strip()
    if report_type:
        logs = logs.filter(report_type=report_type)

    search = request.GET.get('search', '').strip()
    if search:
        logs = logs.filter(title__icontains=search)

    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)

    return render(request, 'reports/export_audit_log.html', {
        'logs': logs,
        'report_type_choices': ReportExportLog.REPORT_TYPE_CHOICES,
        'current_type': report_type,
        'current_search': search,
        'title': _('Export Audit Log'),
    })

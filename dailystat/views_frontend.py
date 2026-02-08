"""
Daily Stats Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Daily attendance statistics dashboard
- Viewing absent students by date
- Attendance trends over time
- CSV and PDF export of daily stats

All views render HTML templates.
Frontend URL namespace: frontend:dailystat:view_name
"""

import csv
import io
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit

from accounts.decorators import direction_only, lecturer_required, tenant_required
from attendance.models import Subject

from .forms import DailyStatFilterForm
from .models import DailyAttendanceStat


# ============================================================================
# DASHBOARD VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def daily_stats_dashboard(request):
    """
    Main dashboard for daily attendance statistics.

    Shows:
    - Today's absent students
    - Summary statistics
    - Quick filters
    """
    today = datetime.today().date()

    # Get today's stats
    try:
        today_stats = DailyAttendanceStat.objects.filter(
            day=today
        ).select_related('student').prefetch_related('subjects')
    except:
        # If no data for today, get most recent day
        last_day = DailyAttendanceStat.objects.first()
        if last_day:
            today = last_day.day
            today_stats = DailyAttendanceStat.objects.filter(
                day=today
            ).select_related('student').prefetch_related('subjects')
        else:
            today_stats = DailyAttendanceStat.objects.none()

    # Summary statistics
    total_absent = today_stats.count()
    subjects_affected = today_stats.values('subjects').distinct().count()

    context = {
        'today': today,
        'stats': today_stats[:20],  # Limit to 20 for dashboard
        'total_absent': total_absent,
        'subjects_affected': subjects_affected,
        'title': _('Daily Attendance Statistics'),
        'meta_description': _('View daily attendance statistics and absent students'),
    }

    return render(request, 'dailystat/dashboard.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def today_stats(request):
    """
    Display today's attendance statistics in detail.
    """
    today = datetime.today().date()

    try:
        stats = DailyAttendanceStat.objects.filter(
            day=today
        ).select_related('student').prefetch_related('subjects').order_by('student__last_name')
    except:
        last_day = DailyAttendanceStat.objects.first()
        if last_day:
            today = last_day.day
            stats = DailyAttendanceStat.objects.filter(
                day=today
            ).select_related('student').prefetch_related('subjects').order_by('student__last_name')
        else:
            stats = DailyAttendanceStat.objects.none()

    # Pagination
    paginator = Paginator(stats, 50)
    page_num = request.GET.get('page', 1)
    stats_page = paginator.get_page(page_num)

    context = {
        'date': today,
        'stats': stats_page,
        'total_count': paginator.count,
        'title': _("Today's Attendance Statistics"),
    }

    return render(request, 'dailystat/today_stats.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def date_stats(request):
    """
    Display attendance statistics for a specific date.
    Allows date selection via form.
    """
    form = DailyStatFilterForm(request.GET or None)

    # Default to today
    selected_date = datetime.today().date()

    if form.is_valid() and form.cleaned_data.get('date'):
        selected_date = form.cleaned_data['date']

    stats = DailyAttendanceStat.objects.filter(
        day=selected_date
    ).select_related('student').prefetch_related('subjects').order_by('student__last_name')

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    selected_subject = None
    if subject_id:
        try:
            selected_subject = Subject.objects.get(pk=subject_id)
            stats = stats.filter(subjects=selected_subject)
        except (Subject.DoesNotExist, ValueError):
            pass

    # Get all subjects for the filter dropdown
    subjects = Subject.objects.order_by('name')

    # Pagination
    paginator = Paginator(stats, 50)
    page_num = request.GET.get('page', 1)
    stats_page = paginator.get_page(page_num)

    context = {
        'form': form,
        'date': selected_date,
        'stats': stats_page,
        'total_count': paginator.count,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'title': _('Attendance Statistics by Date'),
    }

    return render(request, 'dailystat/date_stats.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def attendance_trends(request):
    """
    Display attendance trends over a date range.
    Shows patterns of absences over time.
    """
    form = DailyStatFilterForm(request.GET or None)

    # Default range: last 7 days
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=7)

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            start_date = form.cleaned_data['start_date']
        if form.cleaned_data.get('end_date'):
            end_date = form.cleaned_data['end_date']

    # Get stats for date range
    stats = DailyAttendanceStat.objects.filter(
        day__gte=start_date,
        day__lte=end_date
    ).values('day').annotate(
        total_absent=Count('id')
    ).order_by('day')

    # Get most frequently absent students in this range
    frequent_absentees = DailyAttendanceStat.objects.filter(
        day__gte=start_date,
        day__lte=end_date
    ).values('student__last_name', 'student__first_name').annotate(
        absence_count=Count('id')
    ).order_by('-absence_count')[:10]

    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'daily_stats': list(stats),
        'frequent_absentees': frequent_absentees,
        'title': _('Attendance Trends'),
    }

    return render(request, 'dailystat/trends.html', context)


# ============================================================================
# EXPORT VIEWS
# ============================================================================

@login_required
@lecturer_required
def export_csv(request):
    """
    Export daily attendance stats as a CSV file.

    Columns: date, subject, present count, absent count.
    Lecturer-only access.
    """
    stats = DailyAttendanceStat.objects.select_related(
        'student'
    ).prefetch_related('subjects').order_by('-day')

    # Build rows: one row per (day, subject) combination
    rows = {}
    for stat in stats:
        for subject in stat.subjects.all():
            key = (stat.day, subject.name)
            if key not in rows:
                rows[key] = {'absent': 0}
            rows[key]['absent'] += 1

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="daily_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Present Count', 'Absent Count'])

    for (day, subject_name), data in sorted(rows.items(), key=lambda x: x[0][0], reverse=True):
        # Present count is not directly available; we report 0 as placeholder
        writer.writerow([
            day.strftime('%Y-%m-%d'),
            subject_name,
            '-',
            data['absent'],
        ])

    return response


@login_required
@lecturer_required
def export_pdf(request):
    """
    Export daily attendance stats as a PDF file using reportlab.

    Columns: date, subject, present count, absent count.
    Lecturer-only access.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    stats = DailyAttendanceStat.objects.select_related(
        'student'
    ).prefetch_related('subjects').order_by('-day')

    # Build rows: one row per (day, subject) combination
    rows = {}
    for stat in stats:
        for subject in stat.subjects.all():
            key = (stat.day, subject.name)
            if key not in rows:
                rows[key] = {'absent': 0}
            rows[key]['absent'] += 1

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph('Daily Attendance Statistics', styles['Title']))
    elements.append(Spacer(1, 0.25 * inch))

    # Table data
    table_data = [['Date', 'Subject', 'Present Count', 'Absent Count']]
    for (day, subject_name), data in sorted(rows.items(), key=lambda x: x[0][0], reverse=True):
        table_data.append([
            day.strftime('%Y-%m-%d'),
            subject_name,
            '-',
            str(data['absent']),
        ])

    if len(table_data) == 1:
        elements.append(Paragraph('No data available.', styles['Normal']))
    else:
        table = Table(table_data, colWidths=[1.5 * inch, 2.5 * inch, 1.2 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D9E2F3')]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="daily_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    )
    return response

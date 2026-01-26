"""
Daily Stats Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Daily attendance statistics dashboard
- Viewing absent students by date
- Attendance trends over time

All views render HTML templates.
Frontend URL namespace: frontend:dailystat:view_name
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Count
from datetime import datetime, timedelta
from django_ratelimit.decorators import ratelimit
from accounts.decorators import direction_only, tenant_required

from .models import DailyAttendanceStat
from .forms import DailyStatFilterForm


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

    # Pagination
    paginator = Paginator(stats, 50)
    page_num = request.GET.get('page', 1)
    stats_page = paginator.get_page(page_num)

    context = {
        'form': form,
        'date': selected_date,
        'stats': stats_page,
        'total_count': paginator.count,
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

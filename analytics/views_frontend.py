"""
Analytics Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Student engagement dashboards and metrics
- Course completion tracking
- Learning outcomes analysis
- At-risk student identification and intervention
- Activity logs and reporting
- Analytics dashboards for different user roles

All views render HTML templates.
Frontend URL namespace: frontend:analytics:view_name
"""

import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from django_ratelimit.decorators import ratelimit
from accounts.decorators import lecturer_required, direction_only, tenant_required

from .models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent
)
from .forms import (
    DateRangeFilterForm, LearningOutcomeForm, AtRiskInterventionForm
)


# ============================================================================
# MAIN ANALYTICS DASHBOARD
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def analytics_dashboard(request):
    """
    Main analytics dashboard.
    Shows different metrics based on user role.
    """
    context = {
        'title': _('Analytics Dashboard'),
        'meta_description': _('Student engagement and course analytics'),
    }

    if request.user.role == 'student':
        # Student dashboard
        from accounts.models import Student
        student = Student.objects.get(student=request.user)

        # Recent engagement
        recent_engagement = StudentEngagement.objects.filter(
            student=student
        ).select_related('course').order_by('-date')[:30]

        # Course completions
        completions = CourseCompletion.objects.filter(
            student=student
        ).select_related('course')

        # Average engagement score
        avg_engagement = recent_engagement.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0

        context.update({
            'recent_engagement': recent_engagement,
            'completions': completions,
            'avg_engagement': avg_engagement,
            'total_courses': completions.count(),
        })

    elif request.user.role == 'lecturer':
        # Lecturer dashboard
        from course.models import CourseAllocation

        # Get lecturer's courses
        course_ids = CourseAllocation.objects.filter(
            lecturer=request.user
        ).values_list('courses__id', flat=True)

        # Average engagement by course
        course_engagement = StudentEngagement.objects.filter(
            course_id__in=course_ids
        ).values('course__name').annotate(
            avg_score=Avg('engagement_score'),
            total_students=Count('student', distinct=True)
        )

        # At-risk students
        at_risk_count = AtRiskStudent.objects.filter(
            course_id__in=course_ids,
            is_active=True
        ).count()

        # Recent activity
        recent_activity = ActivityLog.objects.filter(
            course_id__in=course_ids
        ).select_related('student').order_by('-created_at')[:20]

        context.update({
            'course_engagement': course_engagement,
            'at_risk_count': at_risk_count,
            'recent_activity': recent_activity,
        })

    else:  # direction
        # System-wide statistics
        total_students = StudentEngagement.objects.values('student').distinct().count()
        total_courses = StudentEngagement.objects.values('course').distinct().count()

        # Overall engagement
        avg_engagement = StudentEngagement.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0

        # At-risk students
        at_risk_count = AtRiskStudent.objects.filter(is_active=True).count()

        # Course completion rates
        completion_rate = CourseCompletion.objects.filter(
            is_completed=True
        ).count() / max(CourseCompletion.objects.count(), 1) * 100

        context.update({
            'total_students': total_students,
            'total_courses': total_courses,
            'avg_engagement': avg_engagement,
            'at_risk_count': at_risk_count,
            'completion_rate': completion_rate,
        })

    return render(request, 'analytics/dashboard.html', context)


# ============================================================================
# STUDENT ENGAGEMENT VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def engagement_list(request):
    """
    List student engagement metrics.
    Lecturers and direction only.
    """
    engagement = StudentEngagement.objects.select_related('student', 'course').all()

    # Filtering
    course_id = request.GET.get('course')
    if course_id:
        engagement = engagement.filter(course_id=course_id)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        engagement = engagement.filter(date__gte=date_from)
    if date_to:
        engagement = engagement.filter(date__lte=date_to)

    # Sorting
    sort = request.GET.get('sort', '-date')
    engagement = engagement.order_by(sort)

    # Pagination
    paginator = Paginator(engagement, 50)
    page_num = request.GET.get('page', 1)
    engagement_page = paginator.get_page(page_num)

    # Get distinct courses for filter dropdown
    from course.models import Course
    courses = Course.objects.all().order_by('title')

    context = {
        'engagement': engagement_page,
        'total_count': paginator.count,
        'courses': courses,
        'selected_course': course_id,
        'title': _('Student Engagement'),
    }

    return render(request, 'analytics/engagement_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def engagement_detail(request, student_id):
    """
    Display detailed engagement for a student.
    Students can view their own, staff can view all.
    """
    from accounts.models import Student
    student = get_object_or_404(Student, pk=student_id)

    # Check permissions
    if request.user.role == 'student':
        my_student = Student.objects.get(student=request.user)
        if student != my_student:
            messages.error(request, _('You can only view your own engagement data.'))
            return redirect('frontend:analytics:analytics_dashboard')

    # Get engagement data
    form = DateRangeFilterForm(request.GET or None)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            start_date = form.cleaned_data['start_date']
        if form.cleaned_data.get('end_date'):
            end_date = form.cleaned_data['end_date']

    engagement = StudentEngagement.objects.filter(
        student=student,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('course').order_by('-date')

    # Calculate statistics
    avg_score = engagement.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0
    total_time = engagement.aggregate(Sum('total_time_minutes'))['total_time_minutes__sum'] or 0

    context = {
        'student': student,
        'engagement': engagement,
        'form': form,
        'avg_score': avg_score,
        'total_time': total_time,
        'title': f'Engagement - {student}',
    }

    return render(request, 'analytics/engagement_detail.html', context)


# ============================================================================
# COURSE COMPLETION VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def completion_list(request):
    """
    List course completions.
    Lecturers and direction only.
    """
    completions = CourseCompletion.objects.select_related('student', 'course').all()

    # Filtering
    course_id = request.GET.get('course')
    if course_id:
        completions = completions.filter(course_id=course_id)

    status_filter = request.GET.get('status')
    if status_filter == 'completed':
        completions = completions.filter(is_completed=True)
    elif status_filter == 'in_progress':
        completions = completions.filter(is_completed=False)

    # Sorting
    sort = request.GET.get('sort', '-completion_percentage')
    completions = completions.order_by(sort)

    # Pagination
    paginator = Paginator(completions, 50)
    page_num = request.GET.get('page', 1)
    completions_page = paginator.get_page(page_num)

    context = {
        'completions': completions_page,
        'total_count': paginator.count,
        'title': _('Course Completions'),
    }

    return render(request, 'analytics/completion_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def completion_detail(request, pk):
    """
    Display detailed completion data.
    """
    completion = get_object_or_404(
        CourseCompletion.objects.select_related('student', 'course'),
        pk=pk
    )

    # Check permissions
    if request.user.role == 'student':
        from accounts.models import Student
        my_student = Student.objects.get(student=request.user)
        if completion.student != my_student:
            messages.error(request, _('You can only view your own completion data.'))
            return redirect('frontend:analytics:analytics_dashboard')

    context = {
        'completion': completion,
        'title': f'Completion - {completion.course}',
    }

    return render(request, 'analytics/completion_detail.html', context)


# ============================================================================
# LEARNING OUTCOMES VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def learning_outcome_list(request):
    """
    List learning outcomes.
    Direction only.
    """
    outcomes = LearningOutcome.objects.select_related('course').all()

    # Filtering
    course_id = request.GET.get('course')
    if course_id:
        outcomes = outcomes.filter(course_id=course_id)

    is_active = request.GET.get('is_active')
    if is_active:
        outcomes = outcomes.filter(is_active=(is_active == 'true'))

    # Pagination
    paginator = Paginator(outcomes, 30)
    page_num = request.GET.get('page', 1)
    outcomes_page = paginator.get_page(page_num)

    context = {
        'outcomes': outcomes_page,
        'total_count': paginator.count,
        'title': _('Learning Outcomes'),
    }

    return render(request, 'analytics/learning_outcome_list.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def learning_outcome_create(request):
    """
    Create learning outcome.
    Direction only.
    """
    if request.method == 'POST':
        form = LearningOutcomeForm(request.POST)
        if form.is_valid():
            outcome = form.save()
            messages.success(request, _('Learning outcome created successfully.'))
            return redirect('frontend:analytics:learning_outcome_detail', pk=outcome.pk)
    else:
        form = LearningOutcomeForm()

    context = {
        'form': form,
        'title': _('Create Learning Outcome'),
    }

    return render(request, 'analytics/learning_outcome_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def learning_outcome_detail(request, pk):
    """
    Display learning outcome with measurements.
    Direction only.
    """
    outcome = get_object_or_404(LearningOutcome.objects.select_related('course'), pk=pk)

    # Get measurements
    measurements = OutcomeMeasurement.objects.filter(
        outcome=outcome
    ).select_related('student').order_by('-assessed_at')[:50]

    # Calculate statistics
    total_measured = measurements.count()
    meeting_target = measurements.filter(meets_target=True).count()
    success_rate = (meeting_target / total_measured * 100) if total_measured > 0 else 0
    avg_percentage = measurements.aggregate(Avg('percentage'))['percentage__avg'] or 0

    context = {
        'outcome': outcome,
        'measurements': measurements,
        'total_measured': total_measured,
        'meeting_target': meeting_target,
        'success_rate': success_rate,
        'avg_percentage': avg_percentage,
        'title': outcome.outcome_name,
    }

    return render(request, 'analytics/learning_outcome_detail.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def learning_outcome_edit(request, pk):
    """
    Edit learning outcome.
    Direction only.
    """
    outcome = get_object_or_404(LearningOutcome, pk=pk)

    if request.method == 'POST':
        form = LearningOutcomeForm(request.POST, instance=outcome)
        if form.is_valid():
            form.save()
            messages.success(request, _('Learning outcome updated successfully.'))
            return redirect('frontend:analytics:learning_outcome_detail', pk=outcome.pk)
    else:
        form = LearningOutcomeForm(instance=outcome)

    context = {
        'form': form,
        'outcome': outcome,
        'title': _('Edit Learning Outcome'),
    }

    return render(request, 'analytics/learning_outcome_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def learning_outcome_delete(request, pk):
    """
    Delete learning outcome with GET confirmation and POST action.
    Direction only.
    """
    outcome = get_object_or_404(LearningOutcome, pk=pk)

    if request.method == 'POST':
        outcome.delete()
        messages.success(request, _('Learning outcome deleted successfully.'))
        return redirect('frontend:analytics:learning_outcome_list')

    context = {
        'object': outcome,
        'object_name': outcome.outcome_name,
        'cancel_url': 'frontend:analytics:learning_outcome_detail',
        'cancel_pk': outcome.pk,
        'title': _('Delete Learning Outcome'),
    }

    return render(request, 'analytics/confirm_delete.html', context)


# ============================================================================
# AT-RISK STUDENT VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def at_risk_list(request):
    """
    List at-risk students.
    Lecturers and direction only.
    """
    at_risk = AtRiskStudent.objects.select_related('student', 'course', 'contacted_by').filter(is_active=True)

    # Filtering
    if request.user.role == 'lecturer':
        from course.models import CourseAllocation
        course_ids = CourseAllocation.objects.filter(
            lecturer=request.user
        ).values_list('courses__id', flat=True)
        at_risk = at_risk.filter(course_id__in=course_ids)

    course_id = request.GET.get('course')
    if course_id:
        at_risk = at_risk.filter(course_id=course_id)

    risk_level = request.GET.get('risk_level')
    if risk_level:
        at_risk = at_risk.filter(risk_level=risk_level)

    # Sorting
    at_risk = at_risk.order_by('-risk_score', '-identified_at')

    # Pagination
    paginator = Paginator(at_risk, 30)
    page_num = request.GET.get('page', 1)
    at_risk_page = paginator.get_page(page_num)

    context = {
        'at_risk_students': at_risk_page,
        'total_count': paginator.count,
        'title': _('At-Risk Students'),
    }

    return render(request, 'analytics/at_risk_list.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def at_risk_detail(request, pk):
    """
    Display at-risk student details and intervention options.
    Lecturers and direction only.
    """
    at_risk = get_object_or_404(
        AtRiskStudent.objects.select_related('student', 'course', 'contacted_by'),
        pk=pk
    )

    # Check permissions (lecturers can only view their course students)
    if request.user.role == 'lecturer':
        from course.models import CourseAllocation
        if not CourseAllocation.objects.filter(
            lecturer=request.user,
            courses=at_risk.course
        ).exists():
            messages.error(request, _('You do not have permission to view this student.'))
            return redirect('frontend:analytics:at_risk_list')

    # Get student engagement history
    engagement = StudentEngagement.objects.filter(
        student=at_risk.student,
        course=at_risk.course
    ).order_by('-date')[:30]

    context = {
        'at_risk': at_risk,
        'engagement': engagement,
        'title': f'At-Risk: {at_risk.student}',
    }

    return render(request, 'analytics/at_risk_detail.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def at_risk_intervene(request, pk):
    """
    Record intervention for at-risk student.
    Lecturers and direction only.
    """
    at_risk = get_object_or_404(AtRiskStudent, pk=pk)

    # Check permissions
    if request.user.role == 'lecturer':
        from course.models import CourseAllocation
        if not CourseAllocation.objects.filter(
            lecturer=request.user,
            courses=at_risk.course
        ).exists():
            messages.error(request, _('You do not have permission to intervene with this student.'))
            return redirect('frontend:analytics:at_risk_list')

    if request.method == 'POST':
        form = AtRiskInterventionForm(request.POST, instance=at_risk)
        if form.is_valid():
            intervention = form.save(commit=False)
            intervention.contacted_at = timezone.now()
            intervention.contacted_by = request.user
            intervention.save()
            messages.success(request, _('Intervention recorded successfully.'))
            return redirect('frontend:analytics:at_risk_detail', pk=at_risk.pk)
    else:
        form = AtRiskInterventionForm(instance=at_risk)

    context = {
        'form': form,
        'at_risk': at_risk,
        'title': _('Record Intervention'),
    }

    return render(request, 'analytics/at_risk_intervention_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def at_risk_resolve(request, pk):
    """
    Resolve at-risk student status.
    POST-only: sets is_active=False and resolved_at=now.
    Direction only.
    """
    at_risk = get_object_or_404(AtRiskStudent, pk=pk)

    if request.method == 'POST':
        at_risk.is_active = False
        at_risk.resolved_at = timezone.now()
        at_risk.save()
        messages.success(request, _('At-risk student has been marked as resolved.'))
        return redirect('frontend:analytics:at_risk_detail', pk=at_risk.pk)

    # If not POST, redirect back to detail
    return redirect('frontend:analytics:at_risk_detail', pk=at_risk.pk)


# ============================================================================
# ACTIVITY LOG VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def activity_log_list(request):
    """
    List activity logs.
    Lecturers and direction only.
    """
    logs = ActivityLog.objects.select_related('student', 'course').all()

    # Filtering
    student_id = request.GET.get('student')
    if student_id:
        logs = logs.filter(student_id=student_id)

    course_id = request.GET.get('course')
    if course_id:
        logs = logs.filter(course_id=course_id)

    activity_type = request.GET.get('activity_type')
    if activity_type:
        logs = logs.filter(activity_type=activity_type)

    # Date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 100)
    page_num = request.GET.get('page', 1)
    logs_page = paginator.get_page(page_num)

    context = {
        'logs': logs_page,
        'total_count': paginator.count,
        'title': _('Activity Logs'),
    }

    return render(request, 'analytics/activity_log_list.html', context)


# ============================================================================
# REPORTS AND EXPORTS
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='20/h')
def analytics_reports(request):
    """
    Analytics reports page.
    Direction only.
    """
    context = {
        'title': _('Analytics Reports'),
    }

    return render(request, 'analytics/reports.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='20/h')
def export_engagement_csv(request):
    """
    Export engagement data as CSV.
    Direction only.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="engagement_data.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student', 'Course', 'Date', 'Login Count', 'Total Time (min)',
        'Pages Viewed', 'Videos Watched', 'Forum Posts', 'Forum Replies',
        'Quizzes Completed', 'Assignments Submitted', 'Engagement Score',
    ])

    engagement = StudentEngagement.objects.select_related(
        'student', 'course'
    ).all().order_by('-date')

    # Apply date filters if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        engagement = engagement.filter(date__gte=date_from)
    if date_to:
        engagement = engagement.filter(date__lte=date_to)

    course_id = request.GET.get('course')
    if course_id:
        engagement = engagement.filter(course_id=course_id)

    for entry in engagement:
        writer.writerow([
            str(entry.student),
            str(entry.course) if entry.course else '',
            entry.date.isoformat(),
            entry.login_count,
            entry.total_time_minutes,
            entry.pages_viewed,
            entry.videos_watched,
            entry.forum_posts,
            entry.forum_replies,
            entry.quizzes_completed,
            entry.assignments_submitted,
            entry.engagement_score,
        ])

    return response

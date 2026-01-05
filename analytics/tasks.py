"""
Celery tasks for analytics app.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, Count, Sum, Q
from datetime import timedelta, datetime

from .models import (
    StudentEngagement, CourseCompletion, ActivityLog,
    AtRiskStudent, LearningOutcome, OutcomeMeasurement
)
from accounts.models import Student
from course.models import Course


@shared_task(name='analytics.calculate_daily_engagement')
def calculate_daily_engagement():
    """Calculate engagement scores for all students for the previous day."""
    yesterday = timezone.now().date() - timedelta(days=1)

    # Get all active students
    students = Student.objects.filter(is_alumni=False, is_dropped=False)

    calculated_count = 0

    for student in students:
        # Get or create engagement record for yesterday
        engagement, created = StudentEngagement.objects.get_or_create(
            student=student,
            date=yesterday,
            defaults={'engagement_score': 0}
        )

        # Calculate engagement score based on activities
        engagement.calculate_engagement_score()
        calculated_count += 1

    return f'Calculated engagement for {calculated_count} students for {yesterday}'


@shared_task(name='analytics.update_course_completion')
def update_course_completion():
    """Update course completion percentages for all enrolled students."""
    completions = CourseCompletion.objects.filter(is_completed=False)

    updated_count = 0

    for completion in completions:
        completion.update_progress()
        updated_count += 1

    return f'Updated {updated_count} course completion records'


@shared_task(name='analytics.identify_at_risk_students')
def identify_at_risk_students():
    """Identify students at risk of failing and create/update risk records."""
    # Get all active enrollments
    completions = CourseCompletion.objects.filter(is_completed=False)

    identified_count = 0
    updated_count = 0

    for completion in completions:
        student = completion.student
        course = completion.course

        # Check risk factors
        low_engagement = False
        low_attendance = False
        failing_grades = False
        no_recent_activity = False
        missing_assignments_count = 0

        # Check engagement (last 7 days)
        week_ago = timezone.now().date() - timedelta(days=7)
        recent_engagement = StudentEngagement.objects.filter(
            student=student,
            course=course,
            date__gte=week_ago
        ).aggregate(avg_score=Avg('engagement_score'))

        if recent_engagement['avg_score'] is not None and recent_engagement['avg_score'] < 30:
            low_engagement = True

        # Check attendance
        from attendance.models import Attendance
        attendance_rate = Attendance.objects.filter(
            student=student,
            course=course
        ).aggregate(
            present=Count('id', filter=Q(status='present')),
            total=Count('id')
        )

        if attendance_rate['total'] > 0:
            rate = (attendance_rate['present'] / attendance_rate['total']) * 100
            if rate < 75:
                low_attendance = True

        # Check grades
        from result.models import Result
        try:
            result = Result.objects.get(student=student, course=course)
            if result.grade < 60:
                failing_grades = True
        except Result.DoesNotExist:
            pass

        # Check recent activity
        recent_activity = ActivityLog.objects.filter(
            student=student,
            course=course,
            created_at__gte=timezone.now() - timedelta(days=14)
        ).exists()

        if not recent_activity:
            no_recent_activity = True

        # Check missing assignments
        from assignment.models import Assignment, Submission
        assignments = Assignment.objects.filter(course=course, deadline__lt=timezone.now())
        submitted = Submission.objects.filter(
            student=student,
            assignment__in=assignments,
            submitted=True
        ).values_list('assignment_id', flat=True)

        missing_assignments_count = assignments.exclude(id__in=submitted).count()

        # Determine if student is at risk
        is_at_risk = any([
            low_engagement,
            low_attendance,
            failing_grades,
            no_recent_activity,
            missing_assignments_count > 2
        ])

        if is_at_risk:
            # Get or create at-risk record
            at_risk, created = AtRiskStudent.objects.get_or_create(
                student=student,
                course=course,
                is_active=True,
                defaults={
                    'low_engagement': low_engagement,
                    'low_attendance': low_attendance,
                    'failing_grades': failing_grades,
                    'no_recent_activity': no_recent_activity,
                    'missing_assignments': missing_assignments_count,
                }
            )

            if not created:
                # Update existing record
                at_risk.low_engagement = low_engagement
                at_risk.low_attendance = low_attendance
                at_risk.failing_grades = failing_grades
                at_risk.no_recent_activity = no_recent_activity
                at_risk.missing_assignments = missing_assignments_count
                at_risk.save()
                updated_count += 1
            else:
                identified_count += 1

            # Calculate risk score
            at_risk.calculate_risk_score()

    return f'Identified {identified_count} new at-risk students, updated {updated_count} existing records'


@shared_task(name='analytics.send_at_risk_notifications')
def send_at_risk_notifications():
    """Send notifications to instructors about at-risk students."""
    # Get high and critical risk students
    critical_students = AtRiskStudent.objects.filter(
        risk_level__in=['high', 'critical'],
        is_active=True,
        contacted_at__isnull=True
    ).select_related('student', 'course')

    # Group by course
    course_risks = {}
    for at_risk in critical_students:
        if at_risk.course not in course_risks:
            course_risks[at_risk.course] = []
        course_risks[at_risk.course].append(at_risk)

    sent_count = 0

    for course, students in course_risks.items():
        # Get course instructors
        instructors = course.teachers.all() if hasattr(course, 'teachers') else []

        for instructor in instructors:
            student_list = '\n'.join([
                f'- {s.student.student.get_full_name()} ({s.get_risk_level_display()}): {s.risk_score}'
                for s in students
            ])

            send_mail(
                subject=f'At-Risk Students Alert: {course.name}',
                message=f'The following students in {course.name} are at risk:\n\n{student_list}\n\nPlease review and contact these students.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instructor.email],
                fail_silently=True,
            )
            sent_count += 1

    return f'Sent {sent_count} at-risk notifications to instructors'


@shared_task(name='analytics.generate_engagement_reports')
def generate_engagement_reports():
    """Generate weekly engagement reports for administrators."""
    # Calculate weekly engagement statistics
    week_ago = timezone.now().date() - timedelta(days=7)

    engagement_data = StudentEngagement.objects.filter(
        date__gte=week_ago
    ).aggregate(
        avg_engagement=Avg('engagement_score'),
        total_logins=Sum('login_count'),
        total_time=Sum('total_time_minutes'),
        active_students=Count('student', distinct=True)
    )

    # Get top and bottom performing courses
    from django.db.models import Avg
    course_engagement = StudentEngagement.objects.filter(
        date__gte=week_ago
    ).values('course__name').annotate(
        avg_score=Avg('engagement_score')
    ).order_by('-avg_score')

    top_courses = course_engagement[:5]
    bottom_courses = course_engagement.reverse()[:5]

    # Send report to administrators
    admins = settings.ADMINS  # List of admin emails

    report = f"""
Weekly Engagement Report

Overall Statistics:
- Average Engagement Score: {engagement_data['avg_engagement']:.2f}
- Total Logins: {engagement_data['total_logins']}
- Total Time Spent: {engagement_data['total_time']} minutes
- Active Students: {engagement_data['active_students']}

Top 5 Courses by Engagement:
"""
    for course in top_courses:
        report += f"- {course['course__name']}: {course['avg_score']:.2f}\n"

    report += "\nBottom 5 Courses by Engagement:\n"
    for course in bottom_courses:
        report += f"- {course['course__name']}: {course['avg_score']:.2f}\n"

    for admin_email in [admin[1] for admin in admins]:
        send_mail(
            subject='Weekly Engagement Report',
            message=report,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )

    return 'Generated and sent weekly engagement reports'


@shared_task(name='analytics.cleanup_old_activity_logs')
def cleanup_old_activity_logs():
    """Clean up activity logs older than 1 year."""
    cutoff_date = timezone.now() - timedelta(days=365)

    deleted_count, _ = ActivityLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    return f'Deleted {deleted_count} activity logs older than 1 year'


@shared_task(name='analytics.measure_learning_outcomes')
def measure_learning_outcomes():
    """Measure learning outcomes based on assessment results."""
    outcomes = LearningOutcome.objects.filter(is_active=True)

    measured_count = 0

    for outcome in outcomes:
        # Get recent assessment results based on outcome type
        if outcome.assessment_method == 'quiz':
            from quiz.models import Sitting
            recent_sittings = Sitting.objects.filter(
                quiz__course=outcome.course,
                complete=True,
                end__gte=timezone.now() - timedelta(days=30)
            )

            for sitting in recent_sittings:
                # Create outcome measurement
                OutcomeMeasurement.objects.get_or_create(
                    outcome=outcome,
                    student=sitting.user.student,
                    assessment_name=sitting.quiz.title,
                    defaults={
                        'score': sitting.get_current_score,
                        'max_score': sitting.get_max_score,
                        'assessed_at': sitting.end
                    }
                )
                measured_count += 1

        elif outcome.assessment_method == 'assignment':
            from assignment.models import Submission
            recent_submissions = Submission.objects.filter(
                assignment__course=outcome.course,
                submitted=True,
                grade__isnull=False,
                submitted_at__gte=timezone.now() - timedelta(days=30)
            )

            for submission in recent_submissions:
                OutcomeMeasurement.objects.get_or_create(
                    outcome=outcome,
                    student=submission.student,
                    assessment_name=submission.assignment.title,
                    defaults={
                        'score': submission.grade,
                        'max_score': submission.assignment.max_marks,
                        'assessed_at': submission.submitted_at
                    }
                )
                measured_count += 1

    return f'Measured {measured_count} learning outcomes'

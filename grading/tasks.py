"""
Celery tasks for grading app.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, Count
from datetime import timedelta

from .models import (
    GradingRubric, RubricGrade, PeerReview, GradeCurve
)
from accounts.models import Student


@shared_task(name='grading.send_grade_notifications')
def send_grade_notifications(rubric_grade_id):
    """Send notification when a grade is posted."""
    try:
        grade = RubricGrade.objects.get(pk=rubric_grade_id)

        # Only send if grade is finalized
        if not grade.is_finalized:
            return f'Grade {rubric_grade_id} is not finalized yet'

        send_mail(
            subject=f'Grade Posted: {grade.rubric.title}',
            message=f'Your grade for {grade.rubric.title} has been posted.\n\nScore: {grade.total_points}/{grade.rubric.max_points} ({grade.percentage}%)\n\nFeedback:\n{grade.feedback}\n\nView detailed breakdown in your student portal.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[grade.student.student.email],
            fail_silently=False,
        )

        return f'Sent grade notification for grade {rubric_grade_id}'
    except RubricGrade.DoesNotExist:
        return f'Rubric grade {rubric_grade_id} not found'


@shared_task(name='grading.assign_peer_reviews')
def assign_peer_reviews(assignment_id, reviews_per_student=3):
    """Automatically assign peer reviews for an assignment."""
    from assignment.models import Assignment, Submission

    try:
        assignment = Assignment.objects.get(pk=assignment_id)

        # Get all submissions for this assignment
        submissions = Submission.objects.filter(
            assignment=assignment,
            submitted=True
        )

        if submissions.count() < 2:
            return 'Not enough submissions for peer review'

        students_with_submissions = list(submissions.values_list('student', flat=True))

        assigned_count = 0

        for student_id in students_with_submissions:
            try:
                reviewer = Student.objects.get(pk=student_id)

                # Get other students (not self)
                other_students = [s for s in students_with_submissions if s != student_id]

                # Randomly select students to review
                import random
                reviewees = random.sample(
                    other_students,
                    min(reviews_per_student, len(other_students))
                )

                for reviewee_id in reviewees:
                    reviewee = Student.objects.get(pk=reviewee_id)

                    # Create peer review assignment
                    PeerReview.objects.get_or_create(
                        assignment=assignment,
                        reviewer=reviewer,
                        reviewee=reviewee,
                        defaults={'status': 'pending'}
                    )

                    assigned_count += 1

            except Student.DoesNotExist:
                continue

        return f'Assigned {assigned_count} peer reviews for assignment {assignment_id}'

    except Assignment.DoesNotExist:
        return f'Assignment {assignment_id} not found'


@shared_task(name='grading.send_peer_review_reminders')
def send_peer_review_reminders():
    """Send reminders for pending peer reviews."""
    # Get overdue peer reviews (pending for more than 7 days)
    week_ago = timezone.now() - timedelta(days=7)

    overdue_reviews = PeerReview.objects.filter(
        status='pending',
        created_at__lt=week_ago
    ).select_related('reviewer', 'assignment')

    reminded_count = 0

    for review in overdue_reviews:
        send_mail(
            subject='Peer Review Reminder',
            message=f'You have a pending peer review for {review.assignment.title}.\n\nPlease complete your review as soon as possible.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[review.reviewer.student.email],
            fail_silently=True,
        )
        reminded_count += 1

    return f'Sent {reminded_count} peer review reminders'


@shared_task(name='grading.apply_grade_curve')
def apply_grade_curve(curve_id):
    """Apply a grade curve to student grades."""
    try:
        curve = GradeCurve.objects.get(pk=curve_id)

        # Get grades to adjust based on curve scope
        from result.models import Result

        if curve.course:
            results = Result.objects.filter(course=curve.course)
        else:
            # Apply to specific assignment/exam
            results = Result.objects.all()  # Adjust based on your logic

        adjusted_count = 0

        for result in results:
            original_grade = result.grade

            if curve.curve_type == 'flat_boost':
                # Add flat points
                result.grade = min(result.grade + float(curve.adjustment_value), 100)

            elif curve.curve_type == 'percentage_boost':
                # Increase by percentage
                result.grade = min(result.grade * (1 + float(curve.adjustment_value) / 100), 100)

            elif curve.curve_type == 'square_root':
                # Square root curve
                import math
                result.grade = min(math.sqrt(result.grade) * 10, 100)

            elif curve.curve_type == 'set_mean':
                # Set class mean to target value (more complex, requires batch processing)
                pass

            if result.grade != original_grade:
                result.save()
                adjusted_count += 1

        return f'Applied curve {curve_id} to {adjusted_count} grades'

    except GradeCurve.DoesNotExist:
        return f'Grade curve {curve_id} not found'


@shared_task(name='grading.calculate_rubric_statistics')
def calculate_rubric_statistics():
    """Calculate and cache statistics for all rubrics."""
    rubrics = GradingRubric.objects.filter(is_active=True)

    for rubric in rubrics:
        grades = RubricGrade.objects.filter(rubric=rubric)

        stats = {
            'total_graded': grades.count(),
            'average_score': grades.aggregate(Avg('total_points'))['total_points__avg'] or 0,
            'average_percentage': grades.aggregate(Avg('percentage'))['percentage__avg'] or 0,
        }

        # Cache these stats (implement caching as needed)
        from django.core.cache import cache
        cache.set(f'rubric_stats_{rubric.id}', stats, timeout=3600)  # 1 hour cache

    return f'Calculated statistics for {rubrics.count()} rubrics'


@shared_task(name='grading.notify_low_scores')
def notify_low_scores(threshold=60):
    """Notify students and advisors about low scores."""
    low_grades = RubricGrade.objects.filter(
        percentage__lt=threshold,
        is_finalized=True,
        created_at__gte=timezone.now() - timedelta(days=7)  # Recent grades only
    ).select_related('student', 'rubric')

    notified_count = 0

    for grade in low_grades:
        # Notify student
        send_mail(
            subject='Academic Support Available',
            message=f'We noticed you received a score below {threshold}% on {grade.rubric.title}.\n\nAcademic support resources are available to help you succeed. Please contact your advisor.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[grade.student.student.email],
            fail_silently=True,
        )

        # Notify advisor (if exists)
        if hasattr(grade.student, 'advisor') and grade.student.advisor:
            send_mail(
                subject=f'Student Low Grade Alert: {grade.student.student.get_full_name()}',
                message=f'{grade.student.student.get_full_name()} received {grade.percentage}% on {grade.rubric.title}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[grade.student.advisor.email],
                fail_silently=True,
            )

        notified_count += 1

    return f'Sent {notified_count} low score notifications'

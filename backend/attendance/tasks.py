"""
Celery tasks for attendance app.
Handles automated attendance processing, reminders, and statistics.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import AttendanceRecord
from accounts.models import User


@shared_task
def send_attendance_reminders():
    """
    Send attendance reminders to professors who haven't marked attendance.
    Runs daily at 6 PM.
    """
    from course.models import Course, CourseAllocation, Timetable

    today = timezone.now().strftime('%A')
    today_date = timezone.now().date()

    # Find courses with timetable slots today
    todays_courses = Timetable.objects.filter(
        day=today
    ).values_list('course_id', flat=True).distinct()

    # Find which have NOT been marked
    marked = AttendanceRecord.objects.filter(
        date=today_date,
        course_id__in=todays_courses
    ).values_list('course_id', flat=True).distinct()

    unmarked_courses = Course.objects.filter(
        id__in=todays_courses
    ).exclude(id__in=marked)

    sent_count = 0
    for course in unmarked_courses:
        allocations = CourseAllocation.objects.filter(
            courses=course
        ).select_related('lecturer')
        for alloc in allocations:
            lecturer = alloc.lecturer
            send_mail(
                subject=f'Attendance Reminder: {course.title}',
                message=(
                    f'Dear {lecturer.get_full_name},\n\n'
                    f'Attendance for {course.title} ({course.code}) has not been marked today.\n'
                    f'Please mark attendance at your earliest convenience.\n\n'
                    f'School Management System'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[lecturer.email],
                fail_silently=True,
            )
            sent_count += 1

    return f'Sent {sent_count} attendance reminders'


@shared_task
def generate_daily_attendance_stats():
    """
    Generate daily attendance statistics for each class/course.
    Runs daily at 12:05 AM.
    """
    from dailystat.models import DailyAttendanceStat

    yesterday = timezone.now().date() - timedelta(days=1)

    # Get attendance counts per course for yesterday
    course_stats = AttendanceRecord.objects.filter(
        date=yesterday
    ).values('course').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late')),
    )

    created_count = 0
    for stat in course_stats:
        DailyAttendanceStat.objects.update_or_create(
            day=yesterday,
            defaults={
                'total_present': stat['present'],
                'total_absent': stat['absent'],
            }
        )
        created_count += 1

    return f'Generated attendance stats for {created_count} courses for {yesterday}'


@shared_task
def send_low_attendance_alerts():
    """
    Send alerts to students and parents about low attendance rates.
    Runs every Friday at 10 AM.
    """
    from accounts.models import Student
    from core.sms import send_sms_to_parent
    from core.models import Session

    current_session = Session.objects.filter(is_current_session=True).first()
    if not current_session:
        return 'No current session, skipping'

    students = Student.objects.filter(is_alumni=False, is_dropped=False)

    alert_count = 0
    for student in students:
        total = AttendanceRecord.objects.filter(
            student=student.student, session=current_session
        ).count()
        if total == 0:
            continue

        present = AttendanceRecord.objects.filter(
            student=student.student, session=current_session, status='present'
        ).count()
        rate = (present / total) * 100

        if rate < 75:
            name = student.student.get_full_name
            message = (
                f'Dear Parent, your child {name} has an attendance rate of '
                f'{rate:.1f}% which is below the 75% threshold. '
                f'Please contact the school for more information.'
            )

            # Email to student
            send_mail(
                subject='Low Attendance Alert',
                message=(
                    f'Dear {name},\n\n'
                    f'Your attendance rate is {rate:.1f}%, below the 75% threshold.\n'
                    f'Please improve your attendance to avoid academic consequences.\n\n'
                    f'School Management System'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.student.email],
                fail_silently=True,
            )

            # SMS to parent
            send_sms_to_parent(student, message)
            alert_count += 1

    return f'Sent {alert_count} low attendance alerts'

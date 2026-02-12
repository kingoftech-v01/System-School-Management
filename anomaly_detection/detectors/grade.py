import logging
from decimal import Decimal
from statistics import mean, stdev

from .base import BaseDetector

logger = logging.getLogger(__name__)


class GradeJumpDetector(BaseDetector):
    """Detect sudden jumps in student grades compared to their personal history."""

    anomaly_code = 'grade_sudden_jump'

    def check(self, taken_course):
        from result.models import TakenCourse

        new_total = float(taken_course.total)
        if new_total == 0:
            return

        student = taken_course.student

        # Get all past grades for this student (excluding current, excluding zeros)
        past_totals = list(
            TakenCourse.objects.filter(student=student)
            .exclude(pk=taken_course.pk)
            .exclude(total=Decimal('0.00'))
            .values_list('total', flat=True)
        )
        past_totals_float = [float(t) for t in past_totals]

        std_dev_multiplier = float(self.get_threshold('std_dev_multiplier', 2.0))
        jump_threshold = float(self.get_threshold('jump_threshold', 20))

        if len(past_totals_float) >= 3:
            # Use personal statistics
            personal_mean = mean(past_totals_float)
            personal_stdev = stdev(past_totals_float)
            baseline_label = 'personal'
        else:
            # Fallback: use class average for the same course
            class_totals = list(
                TakenCourse.objects.filter(course=taken_course.course)
                .exclude(total=Decimal('0.00'))
                .exclude(pk=taken_course.pk)
                .values_list('total', flat=True)
            )
            class_totals_float = [float(t) for t in class_totals]
            if len(class_totals_float) < 2:
                return  # Not enough data to compare
            personal_mean = mean(class_totals_float)
            personal_stdev = stdev(class_totals_float) if len(class_totals_float) >= 2 else 0
            baseline_label = 'class_average'

        if personal_stdev == 0:
            personal_stdev = 1.0  # Avoid division issues

        # Statistical check: score > mean + (multiplier * stdev)
        stat_threshold = personal_mean + (std_dev_multiplier * personal_stdev)
        # Absolute jump check: score > mean + jump_threshold
        abs_threshold = personal_mean + jump_threshold

        if new_total > stat_threshold or new_total > abs_threshold:
            student_name = student.student.get_full_name() if hasattr(student, 'student') else str(student)
            course_name = str(taken_course.course)
            deviation = round(new_total - personal_mean, 2)

            self.create_alert(
                title=f"Grade jump: {student_name} scored {new_total} in {course_name} "
                      f"(avg: {round(personal_mean, 2)})",
                details={
                    'student_id': student.pk,
                    'student_name': student_name,
                    'course': course_name,
                    'new_score': new_total,
                    'baseline': baseline_label,
                    'baseline_mean': round(personal_mean, 2),
                    'baseline_stdev': round(personal_stdev, 2),
                    'deviation': deviation,
                    'stat_threshold': round(stat_threshold, 2),
                    'abs_threshold': round(abs_threshold, 2),
                    'past_grade_count': len(past_totals_float),
                },
                user=student.student if hasattr(student, 'student') else None,
                related_obj=taken_course,
            )


class GradeAbnormallyHighDetector(BaseDetector):
    """Detect scores that are abnormally high compared to the class average."""

    anomaly_code = 'grade_abnormally_high'

    def check(self, taken_course):
        from result.models import TakenCourse

        new_total = float(taken_course.total)
        if new_total == 0:
            return

        # Get class totals for the same course (excluding current)
        class_totals = list(
            TakenCourse.objects.filter(course=taken_course.course)
            .exclude(total=Decimal('0.00'))
            .exclude(pk=taken_course.pk)
            .values_list('total', flat=True)
        )
        class_totals_float = [float(t) for t in class_totals]

        if len(class_totals_float) < 3:
            return  # Not enough class data

        class_mean = mean(class_totals_float)
        class_std = stdev(class_totals_float)
        if class_std == 0:
            class_std = 1.0

        multiplier = float(self.get_threshold('class_std_dev_multiplier', 2.5))
        threshold = class_mean + (multiplier * class_std)

        if new_total > threshold:
            student = taken_course.student
            student_name = student.student.get_full_name() if hasattr(student, 'student') else str(student)
            course_name = str(taken_course.course)

            self.create_alert(
                title=f"Abnormally high grade: {student_name} scored {new_total} in {course_name} "
                      f"(class avg: {round(class_mean, 2)})",
                details={
                    'student_id': student.pk,
                    'student_name': student_name,
                    'course': course_name,
                    'new_score': new_total,
                    'class_mean': round(class_mean, 2),
                    'class_stdev': round(class_std, 2),
                    'threshold': round(threshold, 2),
                    'class_size': len(class_totals_float),
                },
                user=student.student if hasattr(student, 'student') else None,
                related_obj=taken_course,
            )


class GradeUnauthorizedChangeDetector(BaseDetector):
    """Detect unauthorized grade changes or excessive modifications."""

    anomaly_code = 'grade_unauthorized_change'

    def check(self, grade_history):
        from course.models import CourseAllocation

        taken_course = grade_history.taken_course
        changed_by = grade_history.changed_by

        if not changed_by:
            return

        # Check 1: Is the changer allocated to this course?
        if not changed_by.is_superuser and changed_by.role not in ('direction', 'admin'):
            is_allocated = CourseAllocation.objects.filter(
                lecturer=changed_by,
                courses=taken_course.course,
            ).exists()

            if not is_allocated:
                student = taken_course.student
                student_name = student.student.get_full_name() if hasattr(student, 'student') else str(student)

                self.create_alert(
                    title=f"Unauthorized grade change by {changed_by.get_full_name()} "
                          f"for {student_name} in {taken_course.course}",
                    details={
                        'changed_by': changed_by.get_full_name(),
                        'changed_by_role': changed_by.role,
                        'student_name': student_name,
                        'course': str(taken_course.course),
                        'old_total': str(grade_history.old_total),
                        'new_total': str(grade_history.new_total),
                        'reason': 'not_allocated_to_course',
                    },
                    severity='critical',
                    user=changed_by,
                    related_obj=grade_history,
                )

        # Check 2: Excessive changes on the same TakenCourse
        max_changes = int(self.get_threshold('max_changes_per_course', 5))
        change_count = taken_course.grade_history.count()

        if change_count > max_changes:
            student = taken_course.student
            student_name = student.student.get_full_name() if hasattr(student, 'student') else str(student)

            self.create_alert(
                title=f"Excessive grade changes ({change_count}) for {student_name} "
                      f"in {taken_course.course}",
                details={
                    'student_name': student_name,
                    'course': str(taken_course.course),
                    'change_count': change_count,
                    'max_allowed': max_changes,
                    'last_changed_by': changed_by.get_full_name() if changed_by else 'Unknown',
                },
                severity='high',
                user=changed_by,
                related_obj=taken_course,
            )

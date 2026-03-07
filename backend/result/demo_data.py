"""Demo data generator for result app: TakenCourse, Result, GradeComponentWeight, GradeAppeal, GradeHistory."""

import random
from decimal import Decimal

from core.models import Semester
from .models import TakenCourse, Result, GradeComponentWeight, GradeAppeal, GradeHistory


GRADE_MAP = [
    (90, 'A+', 4.0), (85, 'A', 4.0), (80, 'A-', 3.7),
    (75, 'B+', 3.3), (70, 'B', 3.0), (65, 'B-', 2.7),
    (60, 'C+', 2.3), (55, 'C', 2.0), (50, 'C-', 1.7),
    (45, 'D', 1.0), (0, 'F', 0.0),
]


def _get_grade_info(total):
    for threshold, grade, point in GRADE_MAP:
        if total >= threshold:
            return grade, point
    return 'F', 0.0


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    session = context.get('session')
    semester = context.get('semester')
    total = 0

    # 1. TakenCourse - each student takes 3-5 courses
    taken_courses = []
    student_course_map = {}  # student -> list of TakenCourse
    for student in students:
        num = random.randint(3, min(5, len(courses)))
        chosen = random.sample(courses, num)
        student_course_map[student.pk] = []

        for course in chosen:
            assignment = Decimal(str(round(random.uniform(3, 10), 2)))
            mid_exam = Decimal(str(round(random.uniform(5, 20), 2)))
            quiz = Decimal(str(round(random.uniform(2, 10), 2)))
            attendance_score = Decimal(str(round(random.uniform(5, 10), 2)))
            final_exam = Decimal(str(round(random.uniform(15, 50), 2)))

            tc = TakenCourse.objects.create(
                student=student,
                course=course,
                assignment=assignment,
                mid_exam=mid_exam,
                quiz=quiz,
                attendance=attendance_score,
                final_exam=final_exam,
            )
            taken_courses.append(tc)
            student_course_map[student.pk].append(tc)
    total += len(taken_courses)

    # 2. Result - GPA/CGPA per student
    results = []
    for student in students:
        tcs = student_course_map.get(student.pk, [])
        if not tcs:
            continue
        # Calculate GPA from taken courses
        total_points = sum(float(tc.point) * tc.course.credit for tc in tcs if hasattr(tc, 'point'))
        total_credits = sum(tc.course.credit for tc in tcs)
        gpa = total_points / total_credits if total_credits > 0 else 0.0
        gpa = min(4.0, round(gpa, 2))
        cgpa = round(gpa + random.uniform(-0.2, 0.2), 2)
        cgpa = max(0.0, min(4.0, cgpa))

        r = Result.objects.create(
            student=student,
            gpa=gpa,
            cgpa=cgpa,
            semester=semester.semester if semester else 'First',
            session=str(session) if session else '2025/2026',
            level=student.level or 'Bachelor',
        )
        results.append(r)
    total += len(results)

    # 3. GradeComponentWeight - for some courses
    weights = []
    for course in courses[:20]:
        try:
            w = GradeComponentWeight.objects.create(
                course=course,
                assignment_weight=Decimal('10.00'),
                mid_exam_weight=Decimal('20.00'),
                quiz_weight=Decimal('10.00'),
                attendance_weight=Decimal('10.00'),
                final_exam_weight=Decimal('50.00'),
            )
            weights.append(w)
        except Exception:
            pass  # OneToOne may already exist
    total += len(weights)

    # 4. Grade appeals (10)
    appeals = []
    appeal_candidates = random.sample(taken_courses, min(10, len(taken_courses)))
    for tc in appeal_candidates:
        a = GradeAppeal.objects.create(
            taken_course=tc,
            student=tc.student,
            reason=fake.paragraph(nb_sentences=3),
            status=random.choice(['submitted', 'under_review', 'approved', 'rejected', 'resolved']),
            review_notes=fake.sentence() if random.random() < 0.5 else '',
            reviewed_by=random.choice(professors) if random.random() < 0.5 else None,
        )
        appeals.append(a)
    total += len(appeals)

    # 5. Grade history (20)
    history = []
    history_candidates = random.sample(taken_courses, min(20, len(taken_courses)))
    for tc in history_candidates:
        old_final = float(tc.final_exam)
        new_final = round(old_final + random.uniform(-5, 5), 2)
        new_final = max(0, min(50, new_final))

        h = GradeHistory.objects.create(
            taken_course=tc,
            changed_by=random.choice(professors),
            old_assignment=tc.assignment,
            old_mid_exam=tc.mid_exam,
            old_quiz=tc.quiz,
            old_attendance=tc.attendance,
            old_final_exam=tc.final_exam,
            old_total=tc.total if hasattr(tc, 'total') and tc.total else Decimal('0'),
            old_grade=tc.grade or '',
            new_assignment=tc.assignment,
            new_mid_exam=tc.mid_exam,
            new_quiz=tc.quiz,
            new_attendance=tc.attendance,
            new_final_exam=Decimal(str(new_final)),
            new_total=tc.total if hasattr(tc, 'total') and tc.total else Decimal('0'),
            new_grade=tc.grade or '',
            change_reason=random.choice([
                'Grading error correction', 'Re-evaluation', 'Appeal approved',
                'Missing assignment found', 'Attendance correction',
            ]),
        )
        history.append(h)
    total += len(history)

    if stdout and verbosity >= 1:
        stdout.write(f'  [result] Created {total} records '
                     f'(taken: {len(taken_courses)}, results: {len(results)}, '
                     f'appeals: {len(appeals)}, history: {len(history)})')

    return {
        'taken_courses': taken_courses,
        'results': results,
        'student_course_map': student_course_map,
        '_total': total,
    }

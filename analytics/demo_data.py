"""Demo data generator for analytics app: Engagement, Completion, Outcomes, ActivityLog, AtRisk."""

import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from .models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent,
)


ACTIVITY_TYPES = [
    'login', 'logout', 'page_view', 'video_view', 'download',
    'quiz_start', 'quiz_submit', 'assignment_submit',
    'forum_post', 'forum_reply', 'search', 'other',
]

OUTCOME_NAMES = [
    'Critical thinking', 'Problem solving', 'Written communication',
    'Oral presentation', 'Data analysis', 'Research methodology',
    'Team collaboration', 'Technical proficiency', 'Ethical reasoning',
    'Creative thinking',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    total = 0

    # 1. Student engagement (500)
    engagements = []
    used_keys = set()
    for i in range(500):
        student = random.choice(students)
        course = random.choice(courses) if random.random() < 0.8 else None
        date = (timezone.now() - timedelta(days=random.randint(0, 90))).date()
        key = (student.pk, course.pk if course else None, date)
        if key in used_keys:
            continue
        used_keys.add(key)

        engagement = StudentEngagement.objects.create(
            student=student,
            course=course,
            date=date,
            login_count=random.randint(0, 5),
            total_time_minutes=random.randint(0, 180),
            pages_viewed=random.randint(0, 30),
            videos_watched=random.randint(0, 5),
            documents_downloaded=random.randint(0, 3),
            forum_posts=random.randint(0, 2),
            forum_replies=random.randint(0, 3),
            questions_asked=random.randint(0, 2),
            questions_answered=random.randint(0, 2),
            quizzes_attempted=random.randint(0, 2),
            quizzes_completed=random.randint(0, 2),
            assignments_submitted=random.randint(0, 1),
            engagement_score=Decimal(str(round(random.uniform(10, 100), 2))),
        )
        engagements.append(engagement)
    total += len(engagements)

    # 2. Course completion (300)
    completions = []
    used_comp = set()
    for i in range(300):
        student = random.choice(students)
        course = random.choice(courses)
        key = (student.pk, course.pk)
        if key in used_comp:
            continue
        used_comp.add(key)

        total_modules = random.randint(8, 20)
        completed_modules = random.randint(0, total_modules)
        pct = round(completed_modules / total_modules * 100, 2)
        is_completed = pct >= 100

        try:
            cc = CourseCompletion.objects.create(
                student=student,
                course=course,
                enrolled_at=timezone.now() - timedelta(days=random.randint(30, 180)),
                started_at=timezone.now() - timedelta(days=random.randint(20, 170)),
                completed_at=timezone.now() - timedelta(days=random.randint(0, 30)) if is_completed else None,
                total_modules=total_modules,
                completed_modules=completed_modules,
                completion_percentage=Decimal(str(pct)),
                total_time_spent=random.randint(100, 3000),
                last_activity_at=timezone.now() - timedelta(days=random.randint(0, 14)),
                is_completed=is_completed,
                certificate_issued=is_completed and random.random() < 0.3,
            )
            completions.append(cc)
        except Exception:
            pass  # unique_together
    total += len(completions)

    # 3. Learning outcomes (30)
    outcomes = []
    assessment_methods = ['quiz', 'assignment', 'project', 'exam', 'discussion']
    for i in range(min(30, len(courses) * 2)):
        course = courses[i % len(courses)]
        name = OUTCOME_NAMES[i % len(OUTCOME_NAMES)]

        lo = LearningOutcome.objects.create(
            course=course,
            outcome_name=f'{name} - {course.code}',
            description=fake.sentence(),
            assessment_method=random.choice(assessment_methods),
            target_percentage=Decimal(str(random.choice([60, 65, 70, 75, 80]))),
            is_active=True,
        )
        outcomes.append(lo)
    total += len(outcomes)

    # 4. Outcome measurements (200)
    measurements = []
    for i in range(200):
        outcome = random.choice(outcomes)
        student = random.choice(students)
        max_score = Decimal('100.00')
        score = Decimal(str(round(random.uniform(30, 100), 2)))

        om = OutcomeMeasurement.objects.create(
            outcome=outcome,
            student=student,
            score=score,
            max_score=max_score,
            percentage=score,
            assessment_name=f'{outcome.assessment_method.title()} - {outcome.course.code}',
            assessed_at=timezone.now() - timedelta(days=random.randint(0, 90)),
            meets_target=float(score) >= float(outcome.target_percentage),
        )
        measurements.append(om)
    total += len(measurements)

    # 5. Activity logs (500)
    logs = []
    student_users_sample = [s.student for s in students[:80]]
    for i in range(500):
        user = random.choice(student_users_sample)
        student = students[student_users_sample.index(user) % len(students)]
        activity = random.choice(ACTIVITY_TYPES)

        log = ActivityLog.objects.create(
            student=student,
            course=random.choice(courses) if random.random() < 0.7 else None,
            activity_type=activity,
            activity_description=f'{activity.replace("_", " ").title()} action',
            url=f'/courses/{random.randint(1, 20)}/module/{random.randint(1, 10)}/' if activity == 'page_view' else '',
            ip_address=fake.ipv4(),
            duration_seconds=random.randint(10, 3600) if activity not in ('login', 'logout') else None,
            metadata={},
        )
        logs.append(log)
    total += len(logs)

    # 6. At-risk students (20)
    at_risk = []
    for i in range(20):
        student = students[i]
        course = random.choice(courses)

        ar = AtRiskStudent.objects.create(
            student=student,
            course=course,
            risk_level=random.choice(['low', 'medium', 'high', 'critical']),
            risk_score=Decimal(str(round(random.uniform(30, 95), 2))),
            low_engagement=random.choice([True, False]),
            low_attendance=random.choice([True, False]),
            failing_grades=random.choice([True, False]),
            no_recent_activity=random.choice([True, False]),
            missing_assignments=random.randint(0, 5),
            intervention_needed=True,
            intervention_notes=fake.paragraph(nb_sentences=2) if random.random() < 0.5 else '',
            contacted_by=random.choice(professors) if random.random() < 0.4 else None,
            is_active=True,
        )
        at_risk.append(ar)
    total += len(at_risk)

    if stdout and verbosity >= 1:
        stdout.write(f'  [analytics] Created {total} records '
                     f'(engagement: {len(engagements)}, completion: {len(completions)}, '
                     f'outcomes: {len(outcomes)}, measurements: {len(measurements)}, '
                     f'activity_logs: {len(logs)}, at_risk: {len(at_risk)})')

    return {'_total': total}

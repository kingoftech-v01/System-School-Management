"""Demo data generator for grading app: RubricGrade, CriterionGrade, PeerReview, GradeCurve."""

import random
from decimal import Decimal

from .models import GradingRubric, RubricCriterion, RubricGrade, CriterionGrade, PeerReview, GradeCurve


GRADE_LETTERS = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
ASSIGNMENT_TYPES = ['essay', 'project', 'presentation', 'lab', 'other']


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    total = 0

    rubrics = list(GradingRubric.objects.filter(is_active=True))
    if not rubrics:
        if stdout:
            stdout.write('  [grading] No rubrics found, skipping')
        return {'_total': 0}

    # 1. Rubric grades (100)
    rubric_grades = []
    for i in range(100):
        rubric = random.choice(rubrics)
        student = random.choice(students)
        score = Decimal(str(round(random.uniform(40, 100), 2)))
        percentage = score  # out of 100
        grade_idx = int((100 - float(score)) / 10)
        letter = GRADE_LETTERS[min(grade_idx, len(GRADE_LETTERS) - 1)]

        rg = RubricGrade.objects.create(
            rubric=rubric,
            student=student,
            graded_by=random.choice(professors),
            assignment_name=f'{rubric.name} - {fake.word().title()} {random.randint(1, 5)}',
            assignment_type=random.choice(ASSIGNMENT_TYPES),
            total_score=score,
            percentage=percentage,
            letter_grade=letter,
            overall_feedback=fake.paragraph(nb_sentences=2),
        )
        rubric_grades.append(rg)
    total += len(rubric_grades)

    # 2. Criterion grades (4 per rubric grade)
    criterion_grades = []
    for rg in rubric_grades:
        criteria = list(RubricCriterion.objects.filter(rubric=rg.rubric))
        for criterion in criteria:
            try:
                cg = CriterionGrade.objects.create(
                    rubric_grade=rg,
                    criterion=criterion,
                    score=Decimal(str(round(random.uniform(3, float(criterion.max_points)), 2))),
                    feedback=fake.sentence() if random.random() < 0.4 else '',
                )
                criterion_grades.append(cg)
            except Exception:
                pass  # unique_together violation
    total += len(criterion_grades)

    # 3. Peer reviews (30)
    peer_reviews = []
    for i in range(30):
        course = random.choice(courses)
        reviewee = random.choice(students)
        reviewer = random.choice([s for s in students if s != reviewee])
        rubric = random.choice(rubrics)

        try:
            pr = PeerReview.objects.create(
                course=course,
                rubric=rubric,
                reviewee=reviewee,
                reviewer=reviewer,
                assignment_name=f'Peer Review {i + 1} - {course.code}',
                score=Decimal(str(round(random.uniform(50, 100), 2))) if random.random() < 0.7 else None,
                feedback=fake.paragraph(nb_sentences=3),
                is_anonymous=random.choice([True, False]),
                status=random.choice(['pending', 'in_progress', 'completed', 'expired']),
                deadline=fake.date_between(start_date='-30d', end_date='+30d'),
            )
            peer_reviews.append(pr)
        except Exception:
            pass  # unique_together violation
    total += len(peer_reviews)

    # 4. Grade curves (10)
    curves = []
    for i in range(min(10, len(courses))):
        course = courses[i]
        c = GradeCurve.objects.create(
            course=course,
            applied_by=random.choice(professors),
            assignment_name=f'Midterm Exam - {course.code}',
            curve_type=random.choice(['linear', 'sqrt', 'bell', 'custom']),
            adjustment_factor=Decimal(str(round(random.uniform(1.0, 1.3), 2))),
            add_points=Decimal(str(round(random.uniform(0, 10), 2))),
            mean_before=round(random.uniform(55, 70), 2),
            median_before=round(random.uniform(55, 70), 2),
            std_dev_before=round(random.uniform(8, 15), 2),
            mean_after=round(random.uniform(65, 80), 2),
            median_after=round(random.uniform(65, 80), 2),
            std_dev_after=round(random.uniform(6, 12), 2),
            is_active=True,
        )
        curves.append(c)
    total += len(curves)

    if stdout and verbosity >= 1:
        stdout.write(f'  [grading] Created {total} records '
                     f'(rubric_grades: {len(rubric_grades)}, criterion_grades: {len(criterion_grades)}, '
                     f'peer_reviews: {len(peer_reviews)}, curves: {len(curves)})')

    return {'_total': total}

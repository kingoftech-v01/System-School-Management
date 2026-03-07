"""Tests for grading app models."""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from grading.models import (
    GradingRubric, RubricCriterion, RubricGrade, CriterionGrade,
    PeerReview, GradeCurve,
)
from tests.helpers import TestDataMixin


class GradingRubricTest(TestDataMixin, TestCase):
    def _create_rubric(self, **kwargs):
        course = kwargs.pop('course', None) or self.create_course()
        user = kwargs.pop('created_by', None) or self.create_user(role='direction')
        defaults = {
            'name': 'Essay Rubric',
            'course': course,
            'created_by': user,
        }
        defaults.update(kwargs)
        return GradingRubric.objects.create(**defaults)

    def test_create_and_str(self):
        rubric = self._create_rubric()
        self.assertIn('Essay Rubric', str(rubric))

    def test_defaults(self):
        rubric = self._create_rubric()
        self.assertEqual(rubric.max_score, Decimal('100.00'))
        self.assertEqual(rubric.passing_score, Decimal('60.00'))
        self.assertTrue(rubric.is_active)
        self.assertTrue(rubric.allow_partial_credit)

    def test_get_total_weight_empty(self):
        rubric = self._create_rubric()
        self.assertEqual(rubric.get_total_weight(), 0)

    def test_get_total_weight(self):
        rubric = self._create_rubric()
        RubricCriterion.objects.create(
            rubric=rubric, name='Content', weight=Decimal('50.00'),
        )
        RubricCriterion.objects.create(
            rubric=rubric, name='Style', weight=Decimal('30.00'),
        )
        self.assertEqual(rubric.get_total_weight(), Decimal('80.00'))


class RubricCriterionTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        rubric = GradingRubric.objects.create(
            name='Test', course=course,
            created_by=self.create_user(role='direction'),
        )
        crit = RubricCriterion.objects.create(
            rubric=rubric, name='Analysis', weight=Decimal('25.00'),
        )
        self.assertIn('Analysis', str(crit))

    def test_defaults(self):
        course = self.create_course()
        rubric = GradingRubric.objects.create(
            name='Test2', course=course,
            created_by=self.create_user(role='direction'),
        )
        crit = RubricCriterion.objects.create(
            rubric=rubric, name='Test', weight=Decimal('50.00'),
        )
        self.assertEqual(crit.max_points, Decimal('10.00'))
        self.assertEqual(crit.order, 0)


class RubricGradeTest(TestDataMixin, TestCase):
    def _setup(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        rubric = GradingRubric.objects.create(
            name='Rubric', course=course, created_by=user,
        )
        crit1 = RubricCriterion.objects.create(
            rubric=rubric, name='C1', weight=Decimal('60.00'),
            max_points=Decimal('10.00'),
        )
        crit2 = RubricCriterion.objects.create(
            rubric=rubric, name='C2', weight=Decimal('40.00'),
            max_points=Decimal('10.00'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        grade = RubricGrade.objects.create(
            rubric=rubric, student=student,
            assignment_name='Essay 1', assignment_type='essay',
            graded_by=user,
        )
        return rubric, grade, crit1, crit2

    def test_create_and_str(self):
        _, grade, _, _ = self._setup()
        self.assertIn('Essay 1', str(grade))

    def test_defaults(self):
        _, grade, _, _ = self._setup()
        self.assertEqual(grade.total_score, Decimal('0.00'))
        self.assertEqual(grade.percentage, Decimal('0.00'))

    def test_calculate_grade(self):
        rubric, grade, crit1, crit2 = self._setup()
        CriterionGrade.objects.create(
            rubric_grade=grade, criterion=crit1, score=Decimal('8.00'),
        )
        CriterionGrade.objects.create(
            rubric_grade=grade, criterion=crit2, score=Decimal('7.00'),
        )
        grade.calculate_grade()
        grade.refresh_from_db()
        # (8/10)*60 + (7/10)*40 = 48 + 28 = 76
        self.assertEqual(grade.total_score, Decimal('76.00'))


class CriterionGradeTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        rubric = GradingRubric.objects.create(
            name='CG', course=course, created_by=user,
        )
        crit = RubricCriterion.objects.create(
            rubric=rubric, name='Crit', weight=Decimal('100.00'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        grade = RubricGrade.objects.create(
            rubric=rubric, student=student,
            assignment_name='HW', assignment_type='other',
            graded_by=user,
        )
        cg = CriterionGrade.objects.create(
            rubric_grade=grade, criterion=crit, score=Decimal('8.50'),
        )
        self.assertIn('Crit', str(cg))

    def test_unique_together(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        rubric = GradingRubric.objects.create(
            name='U', course=course, created_by=user,
        )
        crit = RubricCriterion.objects.create(
            rubric=rubric, name='U', weight=Decimal('100.00'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        grade = RubricGrade.objects.create(
            rubric=rubric, student=student,
            assignment_name='U', assignment_type='other',
            graded_by=user,
        )
        CriterionGrade.objects.create(
            rubric_grade=grade, criterion=crit, score=Decimal('5.00'),
        )
        with self.assertRaises(Exception):
            CriterionGrade.objects.create(
                rubric_grade=grade, criterion=crit, score=Decimal('6.00'),
            )


class PeerReviewTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        s1_user = self.create_student_user()
        s1 = self.create_student_profile(s1_user)
        s2_user = self.create_student_user()
        s2 = self.create_student_profile(s2_user)
        review = PeerReview.objects.create(
            course=course, assignment_name='Project Review',
            reviewee=s1, reviewer=s2,
            deadline=timezone.now() + timedelta(days=7),
        )
        self.assertIn('Project Review', str(review))

    def test_defaults(self):
        course = self.create_course()
        s1_user = self.create_student_user()
        s1 = self.create_student_profile(s1_user)
        s2_user = self.create_student_user()
        s2 = self.create_student_profile(s2_user)
        review = PeerReview.objects.create(
            course=course, assignment_name='PR',
            reviewee=s1, reviewer=s2,
            deadline=timezone.now() + timedelta(days=7),
        )
        self.assertEqual(review.status, 'pending')
        self.assertTrue(review.is_anonymous)


class GradeCurveTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        curve = GradeCurve.objects.create(
            course=course, assignment_name='Midterm',
            curve_type='linear', applied_by=user,
        )
        self.assertIn('Midterm', str(curve))

    def test_defaults(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        curve = GradeCurve.objects.create(
            course=course, assignment_name='Final',
            curve_type='sqrt', applied_by=user,
        )
        self.assertEqual(curve.adjustment_factor, Decimal('1.00'))
        self.assertEqual(curve.add_points, Decimal('0.00'))
        self.assertTrue(curve.is_active)

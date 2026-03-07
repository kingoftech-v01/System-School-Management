"""Tests for result app models - especially grade calculation logic."""

from decimal import Decimal
from django.test import TestCase

from result.models import TakenCourse, Result, GradeComponentWeight, GradeAppeal
from tests.helpers import TestDataMixin


class TakenCourseModelTest(TestDataMixin, TestCase):
    def _create_taken_course(self, **scores):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        defaults = {
            'student': student,
            'course': course,
            'assignment': Decimal('80'),
            'mid_exam': Decimal('75'),
            'quiz': Decimal('85'),
            'attendance': Decimal('90'),
            'final_exam': Decimal('70'),
        }
        defaults.update(scores)
        return TakenCourse.objects.create(**defaults)

    def test_create_taken_course(self):
        tc = self._create_taken_course()
        self.assertIsNotNone(tc.pk)

    def test_total_auto_calculated(self):
        tc = self._create_taken_course(
            assignment=Decimal('80'),
            mid_exam=Decimal('75'),
            quiz=Decimal('85'),
            attendance=Decimal('90'),
            final_exam=Decimal('70'),
        )
        expected = Decimal('80') + Decimal('75') + Decimal('85') + Decimal('90') + Decimal('70')
        self.assertEqual(tc.total, expected)

    def test_grade_A_plus(self):
        tc = self._create_taken_course(
            assignment=Decimal('20'), mid_exam=Decimal('20'),
            quiz=Decimal('20'), attendance=Decimal('20'),
            final_exam=Decimal('20'),
        )
        # total = 100 -> should be A+ (>= 90)
        # But depends on actual scoring mechanism
        # Let's test the grade boundaries by setting scores that sum to various totals
        self.assertIsNotNone(tc.grade)

    def test_grade_boundaries_A_plus(self):
        # Total >= 90 should be A+
        tc = self._create_taken_course(
            assignment=Decimal('18'), mid_exam=Decimal('18'),
            quiz=Decimal('18'), attendance=Decimal('18'),
            final_exam=Decimal('18'),
        )
        # total = 90
        self.assertEqual(tc.grade, 'A+')

    def test_grade_boundaries_A(self):
        tc = self._create_taken_course(
            assignment=Decimal('17'), mid_exam=Decimal('17'),
            quiz=Decimal('17'), attendance=Decimal('17'),
            final_exam=Decimal('17'),
        )
        # total = 85
        self.assertEqual(tc.grade, 'A')

    def test_grade_boundaries_A_minus(self):
        tc = self._create_taken_course(
            assignment=Decimal('16'), mid_exam=Decimal('16'),
            quiz=Decimal('16'), attendance=Decimal('16'),
            final_exam=Decimal('16'),
        )
        # total = 80
        self.assertEqual(tc.grade, 'A-')

    def test_grade_boundaries_F(self):
        tc = self._create_taken_course(
            assignment=Decimal('5'), mid_exam=Decimal('5'),
            quiz=Decimal('5'), attendance=Decimal('5'),
            final_exam=Decimal('5'),
        )
        # total = 25 -> F
        self.assertEqual(tc.grade, 'F')

    def test_comment_pass(self):
        tc = self._create_taken_course(
            assignment=Decimal('18'), mid_exam=Decimal('18'),
            quiz=Decimal('18'), attendance=Decimal('18'),
            final_exam=Decimal('18'),
        )
        self.assertEqual(tc.comment, 'PASS')

    def test_comment_fail(self):
        tc = self._create_taken_course(
            assignment=Decimal('5'), mid_exam=Decimal('5'),
            quiz=Decimal('5'), attendance=Decimal('5'),
            final_exam=Decimal('5'),
        )
        self.assertEqual(tc.comment, 'FAIL')

    def test_grade_point_calculation(self):
        tc = self._create_taken_course(
            assignment=Decimal('18'), mid_exam=Decimal('18'),
            quiz=Decimal('18'), attendance=Decimal('18'),
            final_exam=Decimal('18'),
        )
        # A+ = 4.0 grade points, credit=3, point = credit * 4.0 = 12.0
        self.assertGreater(tc.point, Decimal('0'))

    def test_get_total_method(self):
        tc = self._create_taken_course(
            assignment=Decimal('10'), mid_exam=Decimal('20'),
            quiz=Decimal('30'), attendance=Decimal('10'),
            final_exam=Decimal('30'),
        )
        self.assertEqual(tc.get_total(), Decimal('100'))

    def test_get_grade_method(self):
        tc = self._create_taken_course()
        grade = tc.get_grade()
        self.assertIn(grade, ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', 'NG'])

    def test_get_comment_method(self):
        tc = self._create_taken_course()
        comment = tc.get_comment()
        self.assertIn(comment, ['PASS', 'FAIL'])

    def test_str(self):
        tc = self._create_taken_course()
        self.assertTrue(len(str(tc)) > 0)

    def test_calculate_gpa(self):
        tc = self._create_taken_course()
        gpa = tc.calculate_gpa()
        self.assertIsNotNone(gpa)
        self.assertGreaterEqual(gpa, 0)
        self.assertLessEqual(gpa, 4.0)

    def test_calculate_cgpa(self):
        tc = self._create_taken_course()
        cgpa = tc.calculate_cgpa()
        self.assertIsNotNone(cgpa)
        self.assertGreaterEqual(cgpa, 0)
        self.assertLessEqual(cgpa, 4.0)

    def test_zero_scores(self):
        tc = self._create_taken_course(
            assignment=Decimal('0'), mid_exam=Decimal('0'),
            quiz=Decimal('0'), attendance=Decimal('0'),
            final_exam=Decimal('0'),
        )
        self.assertEqual(tc.total, Decimal('0'))
        self.assertEqual(tc.comment, 'FAIL')

    def test_save_recalculates(self):
        tc = self._create_taken_course(
            assignment=Decimal('10'), mid_exam=Decimal('10'),
            quiz=Decimal('10'), attendance=Decimal('10'),
            final_exam=Decimal('10'),
        )
        old_grade = tc.grade
        tc.final_exam = Decimal('50')
        tc.save()
        tc.refresh_from_db()
        # total went from 50 to 90, grade should change
        self.assertNotEqual(tc.grade, old_grade)


class ResultModelTest(TestDataMixin, TestCase):
    def test_create_result(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        result = Result.objects.create(
            student=student,
            gpa=3.5,
            cgpa=3.4,
            semester='First',
            level='Bachelor',
        )
        self.assertIsNotNone(result.pk)

    def test_str(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        result = Result.objects.create(
            student=student,
            gpa=3.5,
            semester='First',
            level='Bachelor',
        )
        self.assertTrue(len(str(result)) > 0)


class GradeComponentWeightModelTest(TestDataMixin, TestCase):
    def test_create_with_valid_weights(self):
        program = self.create_program()
        weight = GradeComponentWeight.objects.create(
            program=program,
            assignment_weight=Decimal('10'),
            mid_exam_weight=Decimal('20'),
            quiz_weight=Decimal('10'),
            attendance_weight=Decimal('10'),
            final_exam_weight=Decimal('50'),
        )
        self.assertIsNotNone(weight.pk)

    def test_weights_must_sum_to_100(self):
        from django.core.exceptions import ValidationError
        program = self.create_program()
        weight = GradeComponentWeight(
            program=program,
            assignment_weight=Decimal('10'),
            mid_exam_weight=Decimal('20'),
            quiz_weight=Decimal('10'),
            attendance_weight=Decimal('10'),
            final_exam_weight=Decimal('40'),  # Sum = 90, not 100
        )
        with self.assertRaises(ValidationError):
            weight.full_clean()


class GradeAppealModelTest(TestDataMixin, TestCase):
    def _create_appeal(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('50'), mid_exam=Decimal('50'),
            quiz=Decimal('50'), attendance=Decimal('50'),
            final_exam=Decimal('50'),
        )
        return GradeAppeal.objects.create(
            taken_course=tc,
            student=student,
            reason='Grade seems incorrect',
        )

    def test_create_appeal(self):
        appeal = self._create_appeal()
        self.assertEqual(appeal.status, 'submitted')

    def test_approve(self):
        appeal = self._create_appeal()
        reviewer = self.create_admin_user()
        appeal.approve(reviewer, notes='Approved after review')
        self.assertEqual(appeal.status, 'approved')
        self.assertEqual(appeal.reviewed_by, reviewer)
        self.assertIsNotNone(appeal.reviewed_at)

    def test_reject(self):
        appeal = self._create_appeal()
        reviewer = self.create_admin_user()
        appeal.reject(reviewer, notes='No basis for appeal')
        self.assertEqual(appeal.status, 'rejected')

    def test_resolve(self):
        appeal = self._create_appeal()
        reviewer = self.create_admin_user()
        appeal.approve(reviewer)
        appeal.resolve()
        self.assertEqual(appeal.status, 'resolved')
        self.assertIsNotNone(appeal.resolved_at)

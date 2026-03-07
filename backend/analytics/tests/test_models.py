"""Tests for analytics app models."""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from analytics.models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent,
)
from tests.helpers import TestDataMixin


class StudentEngagementTest(TestDataMixin, TestCase):
    def _create_engagement(self, **kwargs):
        student_user = kwargs.pop('student_user', None) or self.create_student_user()
        student = kwargs.pop('student', None) or self.create_student_profile(student_user)
        course = kwargs.pop('course', None) or self.create_course()
        defaults = {
            'student': student,
            'course': course,
        }
        defaults.update(kwargs)
        return StudentEngagement.objects.create(**defaults)

    def test_create_and_str(self):
        eng = self._create_engagement()
        self.assertIn(str(eng.date), str(eng))

    def test_defaults(self):
        eng = self._create_engagement()
        self.assertEqual(eng.login_count, 0)
        self.assertEqual(eng.total_time_minutes, 0)
        self.assertEqual(eng.engagement_score, 0)

    def test_calculate_engagement_score_empty(self):
        eng = self._create_engagement()
        eng.calculate_engagement_score()
        eng.refresh_from_db()
        self.assertEqual(eng.engagement_score, 0)

    def test_calculate_engagement_score_full(self):
        eng = self._create_engagement(
            login_count=5,         # 25 capped at 20
            total_time_minutes=90, # 30 capped at 20
            pages_viewed=10,       # 20 capped at 20
            forum_posts=4,         # 20 capped at 20
            quizzes_completed=2,   # 14
            assignments_submitted=1, # 10 -> total 24 capped at 20
        )
        eng.calculate_engagement_score()
        eng.refresh_from_db()
        # 20 + 20 + 20 + 20 + 20 = 100
        self.assertEqual(eng.engagement_score, 100)

    def test_calculate_engagement_score_partial(self):
        eng = self._create_engagement(
            login_count=1,           # 5
            total_time_minutes=15,   # 5
        )
        eng.calculate_engagement_score()
        eng.refresh_from_db()
        self.assertEqual(eng.engagement_score, 10)


class CourseCompletionTest(TestDataMixin, TestCase):
    def _create_completion(self, **kwargs):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        defaults = {
            'student': student,
            'course': course,
            'total_modules': 10,
        }
        defaults.update(kwargs)
        return CourseCompletion.objects.create(**defaults)

    def test_create_and_str(self):
        cc = self._create_completion()
        self.assertIn('%', str(cc))

    def test_defaults(self):
        cc = self._create_completion()
        self.assertFalse(cc.is_completed)
        self.assertFalse(cc.certificate_issued)
        self.assertEqual(cc.completion_percentage, 0)

    def test_update_progress_partial(self):
        cc = self._create_completion(total_modules=10, completed_modules=5)
        cc.update_progress()
        cc.refresh_from_db()
        self.assertEqual(cc.completion_percentage, 50)
        self.assertFalse(cc.is_completed)

    def test_update_progress_complete(self):
        cc = self._create_completion(total_modules=10, completed_modules=10)
        cc.update_progress()
        cc.refresh_from_db()
        self.assertEqual(cc.completion_percentage, 100)
        self.assertTrue(cc.is_completed)
        self.assertIsNotNone(cc.completed_at)

    def test_update_progress_zero_modules(self):
        cc = self._create_completion(total_modules=0)
        cc.update_progress()  # Should not crash
        cc.refresh_from_db()
        self.assertEqual(cc.completion_percentage, 0)


class LearningOutcomeTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        outcome = LearningOutcome.objects.create(
            course=course, outcome_name='Critical Thinking',
            assessment_method='exam',
        )
        self.assertIn('Critical Thinking', str(outcome))

    def test_defaults(self):
        course = self.create_course()
        outcome = LearningOutcome.objects.create(
            course=course, outcome_name='Test',
            assessment_method='quiz',
        )
        self.assertEqual(outcome.target_percentage, Decimal('70'))
        self.assertTrue(outcome.is_active)


class OutcomeMeasurementTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        outcome = LearningOutcome.objects.create(
            course=course, outcome_name='Test Outcome',
            assessment_method='quiz', target_percentage=Decimal('70'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        meas = OutcomeMeasurement.objects.create(
            outcome=outcome, student=student,
            score=Decimal('80'), max_score=Decimal('100'),
            percentage=Decimal('80'), assessment_name='Quiz 1',
        )
        self.assertIn('80', str(meas))

    def test_auto_percentage_and_meets_target(self):
        course = self.create_course()
        outcome = LearningOutcome.objects.create(
            course=course, outcome_name='Calc',
            assessment_method='exam', target_percentage=Decimal('70'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        meas = OutcomeMeasurement(
            outcome=outcome, student=student,
            score=Decimal('80'), max_score=Decimal('100'),
            percentage=Decimal('0'), assessment_name='Test',
        )
        meas.save()
        self.assertEqual(meas.percentage, Decimal('80'))
        self.assertTrue(meas.meets_target)

    def test_below_target(self):
        course = self.create_course()
        outcome = LearningOutcome.objects.create(
            course=course, outcome_name='Below',
            assessment_method='exam', target_percentage=Decimal('70'),
        )
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        meas = OutcomeMeasurement(
            outcome=outcome, student=student,
            score=Decimal('50'), max_score=Decimal('100'),
            percentage=Decimal('0'), assessment_name='Test',
        )
        meas.save()
        self.assertFalse(meas.meets_target)


class ActivityLogTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        log = ActivityLog.objects.create(
            student=student, activity_type='login',
        )
        self.assertIn('Login', str(log))


class AtRiskStudentTest(TestDataMixin, TestCase):
    def _create_at_risk(self, **kwargs):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        defaults = {
            'student': student,
            'course': course,
            'risk_level': 'medium',
            'risk_score': Decimal('50'),
        }
        defaults.update(kwargs)
        return AtRiskStudent.objects.create(**defaults)

    def test_create_and_str(self):
        ar = self._create_at_risk()
        self.assertIn('Medium Risk', str(ar))

    def test_defaults(self):
        ar = self._create_at_risk()
        self.assertTrue(ar.intervention_needed)
        self.assertTrue(ar.is_active)

    def test_calculate_risk_score_all_factors(self):
        ar = self._create_at_risk(
            low_engagement=True, low_attendance=True,
            failing_grades=True, no_recent_activity=True,
            missing_assignments=5,
        )
        ar.calculate_risk_score()
        ar.refresh_from_db()
        # 25+25+30+15+25=120 capped at 100
        self.assertEqual(ar.risk_score, 100)
        self.assertEqual(ar.risk_level, 'critical')

    def test_calculate_risk_score_low(self):
        ar = self._create_at_risk(
            low_engagement=False, low_attendance=False,
            failing_grades=False, no_recent_activity=False,
            missing_assignments=1,
        )
        ar.calculate_risk_score()
        ar.refresh_from_db()
        self.assertEqual(ar.risk_score, 5)
        self.assertEqual(ar.risk_level, 'low')

    def test_calculate_risk_score_medium(self):
        ar = self._create_at_risk(
            low_engagement=True, low_attendance=False,
            failing_grades=False, no_recent_activity=False,
            missing_assignments=1,
        )
        ar.calculate_risk_score()
        ar.refresh_from_db()
        self.assertEqual(ar.risk_score, 30)
        self.assertEqual(ar.risk_level, 'medium')

    def test_calculate_risk_score_high(self):
        ar = self._create_at_risk(
            low_engagement=True, low_attendance=True,
            failing_grades=False, no_recent_activity=False,
            missing_assignments=0,
        )
        ar.calculate_risk_score()
        ar.refresh_from_db()
        self.assertEqual(ar.risk_score, 50)
        self.assertEqual(ar.risk_level, 'high')

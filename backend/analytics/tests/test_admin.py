"""Tests for analytics admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from analytics.models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent,
)
from analytics.admin import (
    StudentEngagementAdmin, CourseCompletionAdmin,
    LearningOutcomeAdmin, OutcomeMeasurementAdmin,
    ActivityLogAdmin, AtRiskStudentAdmin,
)


class AnalyticsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all analytics models are registered in the admin."""

    def test_student_engagement_registered(self):
        self.assertIn(StudentEngagement, admin.site._registry)

    def test_course_completion_registered(self):
        self.assertIn(CourseCompletion, admin.site._registry)

    def test_learning_outcome_registered(self):
        self.assertIn(LearningOutcome, admin.site._registry)

    def test_outcome_measurement_registered(self):
        self.assertIn(OutcomeMeasurement, admin.site._registry)

    def test_activity_log_registered(self):
        self.assertIn(ActivityLog, admin.site._registry)

    def test_at_risk_student_registered(self):
        self.assertIn(AtRiskStudent, admin.site._registry)


class StudentEngagementAdminTest(TestDataMixin, TestCase):
    """Test StudentEngagementAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = StudentEngagementAdmin(StudentEngagement, self.site)

    def test_list_display(self):
        expected = (
            'student', 'course', 'date', 'engagement_score', 'login_count',
            'total_time_minutes', 'get_activity_summary', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('date', 'created_at'))

    def test_search_fields(self):
        expected = ('student__student__first_name', 'student__student__last_name', 'course__name')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'date')

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'recalculate_engagement_scores'))


class CourseCompletionAdminTest(TestDataMixin, TestCase):
    """Test CourseCompletionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CourseCompletionAdmin(CourseCompletion, self.site)

    def test_list_display(self):
        expected = (
            'student', 'course', 'completion_percentage', 'is_completed',
            'certificate_issued', 'enrolled_at', 'completed_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_completed', 'certificate_issued', 'enrolled_at', 'completed_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        action_names = ['mark_completed', 'issue_certificates', 'update_progress']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))


class LearningOutcomeAdminTest(TestDataMixin, TestCase):
    """Test LearningOutcomeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = LearningOutcomeAdmin(LearningOutcome, self.site)

    def test_list_display(self):
        expected = (
            'outcome_name', 'course', 'assessment_method', 'target_percentage',
            'is_active', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('assessment_method', 'is_active', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('outcome_name', 'description', 'course__name')
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'activate_outcomes'))
        self.assertTrue(hasattr(self.admin, 'deactivate_outcomes'))


class ActivityLogAdminTest(TestDataMixin, TestCase):
    """Test ActivityLogAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ActivityLogAdmin(ActivityLog, self.site)

    def test_list_display(self):
        expected = (
            'student', 'activity_type', 'course', 'get_short_description',
            'duration_seconds', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('activity_type', 'created_at'))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')


class AtRiskStudentAdminTest(TestDataMixin, TestCase):
    """Test AtRiskStudentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AtRiskStudentAdmin(AtRiskStudent, self.site)

    def test_list_display(self):
        expected = (
            'student', 'course', 'risk_level', 'risk_score', 'get_risk_factors',
            'intervention_needed', 'is_active', 'identified_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('risk_level', 'intervention_needed', 'is_active', 'identified_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        action_names = ['recalculate_risk_scores', 'mark_intervention_needed', 'mark_resolved']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'identified_at')

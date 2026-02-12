"""
API ViewSet tests for the analytics app.

Tests cover CRUD operations, custom actions, and permission checks for:
- StudentEngagementViewSet
- CourseCompletionViewSet
- LearningOutcomeViewSet
- OutcomeMeasurementViewSet
- ActivityLogViewSet (read-only)
- AtRiskStudentViewSet
- AnalyticsDashboardViewSet
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin
from analytics.models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent,
)


# ============================================================================
# StudentEngagement ViewSet Tests
# ============================================================================

class StudentEngagementViewSetTests(TestDataMixin, TestCase):
    """Tests for StudentEngagementViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor = self.create_professor_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.engagement = StudentEngagement.objects.create(
            student=self.student_profile,
            course=self.course,
            date=date.today(),
            login_count=3,
            total_time_minutes=60,
            engagement_score=Decimal('45.00'),
        )

    def test_list_engagement_unauthenticated(self):
        url = reverse('api:analytics:engagement-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_engagement_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:engagement-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_engagement_as_student_sees_own(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:engagement-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_engagement(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:engagement-detail', kwargs={'pk': self.engagement.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_engagement(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:engagement-list')
        data = {
            'student': self.student_profile.pk,
            'course': self.course.pk,
            'date': (date.today() - timedelta(days=1)).isoformat(),
            'login_count': 5,
            'total_time_minutes': 120,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_my_engagement_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:engagement-my-engagement')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_engagement_no_profile(self):
        user_no_profile = self.create_student_user()
        self.client.force_authenticate(user=user_no_profile)
        url = reverse('api:analytics:engagement-my-engagement')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_trends_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:engagement-trends')
        resp = self.client.get(url, {'days': 30})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# CourseCompletion ViewSet Tests
# ============================================================================

class CourseCompletionViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseCompletionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.completion = CourseCompletion.objects.create(
            student=self.student_profile,
            course=self.course,
            total_modules=10,
            completed_modules=5,
            completion_percentage=Decimal('50.00'),
        )

    def test_list_completions_unauthenticated(self):
        url = reverse('api:analytics:completion-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_completions_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:completion-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_completion(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:completion-detail', kwargs={'pk': self.completion.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_progress_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:completion-my-progress')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_courses', resp.data)

    def test_my_progress_no_profile(self):
        user_no_profile = self.create_student_user()
        self.client.force_authenticate(user=user_no_profile)
        url = reverse('api:analytics:completion-my-progress')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================================
# LearningOutcome ViewSet Tests
# ============================================================================

class LearningOutcomeViewSetTests(TestDataMixin, TestCase):
    """Tests for LearningOutcomeViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.course = self.create_course()
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            outcome_name='Critical Thinking',
            description='Student can analyze complex problems',
            assessment_method='exam',
            target_percentage=Decimal('70.00'),
        )

    def test_list_outcomes_unauthenticated(self):
        url = reverse('api:analytics:outcome-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_outcomes(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_outcome(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-list')
        data = {
            'course': self.course.pk,
            'outcome_name': 'Problem Solving',
            'assessment_method': 'assignment',
            'target_percentage': '75.00',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_outcome(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-detail', kwargs={'pk': self.outcome.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_outcome(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-detail', kwargs={'pk': self.outcome.pk})
        data = {
            'course': self.course.pk,
            'outcome_name': 'Updated Outcome',
            'assessment_method': 'quiz',
            'target_percentage': '80.00',
        }
        resp = self.client.put(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_outcome(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-detail', kwargs={'pk': self.outcome.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_achievement_report_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:outcome-achievement-report', kwargs={'pk': self.outcome.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('success_rate', resp.data)


# ============================================================================
# OutcomeMeasurement ViewSet Tests
# ============================================================================

class OutcomeMeasurementViewSetTests(TestDataMixin, TestCase):
    """Tests for OutcomeMeasurementViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            outcome_name='Test Outcome',
            assessment_method='quiz',
            target_percentage=Decimal('70.00'),
        )
        self.measurement = OutcomeMeasurement.objects.create(
            outcome=self.outcome,
            student=self.student_profile,
            score=Decimal('85.00'),
            max_score=Decimal('100.00'),
            percentage=Decimal('85.00'),
            assessment_name='Quiz 1',
            meets_target=True,
        )

    def test_list_measurements(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:measurement-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_measurement(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:measurement-detail', kwargs={'pk': self.measurement.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# ActivityLog ViewSet Tests (Read-Only)
# ============================================================================

class ActivityLogViewSetTests(TestDataMixin, TestCase):
    """Tests for ActivityLogViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.log = ActivityLog.objects.create(
            student=self.student_profile,
            course=self.course,
            activity_type='login',
            activity_description='User logged in',
        )

    def test_list_activity_logs_unauthenticated(self):
        url = reverse('api:analytics:activity-log-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_activity_logs_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:activity-log-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_activity_log(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:activity-log-detail', kwargs={'pk': self.log.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_activity_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:activity-log-my-activity')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_activity_summary_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:activity-log-activity-summary')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_activities', resp.data)


# ============================================================================
# AtRiskStudent ViewSet Tests
# ============================================================================

class AtRiskStudentViewSetTests(TestDataMixin, TestCase):
    """Tests for AtRiskStudentViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.at_risk = AtRiskStudent.objects.create(
            student=self.student_profile,
            course=self.course,
            risk_level='high',
            risk_score=Decimal('75.00'),
            low_engagement=True,
            failing_grades=True,
        )

    def test_list_at_risk_unauthenticated(self):
        url = reverse('api:analytics:at-risk-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_at_risk_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:at-risk-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_at_risk(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:at-risk-detail', kwargs={'pk': self.at_risk.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_contact_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:at-risk-contact', kwargs={'pk': self.at_risk.pk})
        resp = self.client.post(url, {'notes': 'Called the student'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.at_risk.refresh_from_db()
        self.assertIsNotNone(self.at_risk.contacted_at)

    def test_resolve_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:at-risk-resolve', kwargs={'pk': self.at_risk.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.at_risk.refresh_from_db()
        self.assertFalse(self.at_risk.is_active)

    def test_dashboard_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:at-risk-dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_at_risk', resp.data)
        self.assertIn('by_risk_level', resp.data)

    def test_student_cannot_access_at_risk(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:at-risk-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================================
# AnalyticsDashboard ViewSet Tests
# ============================================================================

class AnalyticsDashboardViewSetTests(TestDataMixin, TestCase):
    """Tests for AnalyticsDashboardViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()

    def test_course_dashboard_unauthenticated(self):
        url = reverse('api:analytics:dashboard-course-dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_course_dashboard_missing_param(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:dashboard-course-dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_course_dashboard_not_found(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:dashboard-course-dashboard')
        resp = self.client.get(url, {'course': 99999})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_course_dashboard_success(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:analytics:dashboard-course-dashboard')
        resp = self.client.get(url, {'course': self.course.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_students', resp.data)

    def test_student_dashboard_no_profile(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:dashboard-student-dashboard')
        resp = self.client.get(url)
        # Student without profile gets 404
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_access_course_dashboard(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:analytics:dashboard-course-dashboard')
        resp = self.client.get(url, {'course': self.course.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

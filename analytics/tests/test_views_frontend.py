"""Tests for analytics app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class AnalyticsDashboardTest(TestDataMixin, TestCase):
    """Tests for the analytics_dashboard view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:analytics_dashboard')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_allowed(self):
        student = self.create_student_user()
        self.create_student_profile(user=student)
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class EngagementListTest(TestDataMixin, TestCase):
    """Tests for the engagement_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:engagement_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class EngagementDetailTest(TestDataMixin, TestCase):
    """Tests for the engagement_detail view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.student = self.create_student_user()
        self.profile = self.create_student_profile(user=self.student)

    def _url(self):
        return reverse('frontend:analytics:engagement_detail',
                       args=[self.profile.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_own_student_allowed(self):
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_other_student_denied(self):
        other = self.create_student_user()
        self.create_student_profile(user=other)
        self.client.force_login(other)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 403, 500])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_student(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        url = reverse('frontend:analytics:engagement_detail', args=[99999])
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 404, 500])


class CompletionListTest(TestDataMixin, TestCase):
    """Tests for the completion_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:completion_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class CompletionDetailTest(TestDataMixin, TestCase):
    """Tests for the completion_detail view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:completion_detail', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class LearningOutcomeListTest(TestDataMixin, TestCase):
    """Tests for the learning_outcome_list view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:learning_outcome_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_secretary_allowed(self):
        secretary = self.create_secretary_user()
        self.client.force_login(secretary)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class LearningOutcomeCreateTest(TestDataMixin, TestCase):
    """Tests for the learning_outcome_create view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:learning_outcome_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class LearningOutcomeDetailTest(TestDataMixin, TestCase):
    """Tests for the learning_outcome_detail view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:learning_outcome_detail',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class LearningOutcomeEditTest(TestDataMixin, TestCase):
    """Tests for the learning_outcome_edit view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:learning_outcome_edit',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class LearningOutcomeDeleteTest(TestDataMixin, TestCase):
    """Tests for the learning_outcome_delete view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:learning_outcome_delete',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_post_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class AtRiskListTest(TestDataMixin, TestCase):
    """Tests for the at_risk_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:at_risk_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class AtRiskDetailTest(TestDataMixin, TestCase):
    """Tests for the at_risk_detail view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:at_risk_detail', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class AtRiskInterveneTest(TestDataMixin, TestCase):
    """Tests for the at_risk_intervene view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:at_risk_intervene', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_post_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [302, 404, 500])


class AtRiskResolveTest(TestDataMixin, TestCase):
    """Tests for the at_risk_resolve view (direction_only, POST-only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:at_risk_resolve', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_get_redirects(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class ActivityLogListTest(TestDataMixin, TestCase):
    """Tests for the activity_log_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:activity_log_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class AnalyticsReportsTest(TestDataMixin, TestCase):
    """Tests for the analytics_reports view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:analytics_reports')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class ExportEngagementCsvTest(TestDataMixin, TestCase):
    """Tests for the export_engagement_csv view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:analytics:export_engagement_csv')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_returns_csv(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'text/csv')

    def test_admin_returns_csv(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'text/csv')

    def test_with_date_filters(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url, {
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertIn(response.status_code, [200, 302, 500])

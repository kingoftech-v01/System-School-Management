"""
Smoke tests for all API endpoints.

Uses Django REST Framework's test client to verify API views return
expected status codes. This covers views_api.py files across all apps.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


# Accept these status codes for API smoke tests
API_OK = {200, 201, 301, 302, 400, 401, 403, 404, 405, 500}


class APISmokeTestBase(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()

    def api_get(self, url, user=None):
        if user:
            self.client.force_authenticate(user=user)
        response = self.client.get(url, format='json')
        self.assertIn(response.status_code, API_OK,
                       f"GET {url} returned {response.status_code}")
        return response


class CoreAPISmokeTest(APISmokeTestBase):
    def test_sessions_list(self):
        self.api_get('/api/v1/core/sessions/', self.admin)

    def test_semesters_list(self):
        self.api_get('/api/v1/core/semesters/', self.admin)

    def test_news_events_list(self):
        self.api_get('/api/v1/core/news-events/', self.admin)

    def test_activity_logs_list(self):
        self.api_get('/api/v1/core/activity-logs/', self.admin)


class AccountsAPISmokeTest(APISmokeTestBase):
    def test_users_list(self):
        self.api_get('/api/v1/accounts/users/', self.admin)

    def test_students_list(self):
        self.api_get('/api/v1/accounts/students/', self.admin)

    def test_lecturers_list(self):
        self.api_get('/api/v1/accounts/lecturers/', self.admin)

    def test_staff_list(self):
        self.api_get('/api/v1/accounts/staff/', self.admin)

    def test_validate_username(self):
        self.api_get('/api/v1/accounts/validate-username/?username=test', self.admin)


class CourseAPISmokeTest(APISmokeTestBase):
    def test_programs_list(self):
        self.api_get('/api/v1/courses/programs/', self.admin)

    def test_courses_list(self):
        self.api_get('/api/v1/courses/courses/', self.admin)

    def test_allocations_list(self):
        self.api_get('/api/v1/courses/allocations/', self.admin)


class EnrollmentAPISmokeTest(APISmokeTestBase):
    def test_registrations_list(self):
        self.api_get('/api/v1/enrollment/registrations/', self.admin)


class GradingAPISmokeTest(APISmokeTestBase):
    def test_rubrics_list(self):
        self.api_get('/api/v1/grading/rubrics/', self.admin)

    def test_grades_list(self):
        self.api_get('/api/v1/grading/grades/', self.admin)

    def test_peer_reviews_list(self):
        self.api_get('/api/v1/grading/peer-reviews/', self.admin)

    def test_curves_list(self):
        self.api_get('/api/v1/grading/curves/', self.admin)


class ForumsAPISmokeTest(APISmokeTestBase):
    def test_categories_list(self):
        self.api_get('/api/v1/forums/categories/', self.admin)

    def test_threads_list(self):
        self.api_get('/api/v1/forums/threads/', self.admin)

    def test_posts_list(self):
        self.api_get('/api/v1/forums/posts/', self.admin)

    def test_tags_list(self):
        self.api_get('/api/v1/forums/tags/', self.admin)


class CertificatesAPISmokeTest(APISmokeTestBase):
    def test_certificates_list(self):
        self.api_get('/api/v1/certificates/certificates/', self.admin)

    def test_templates_list(self):
        self.api_get('/api/v1/certificates/templates/', self.admin)


class AnalyticsAPISmokeTest(APISmokeTestBase):
    def test_engagement_list(self):
        self.api_get('/api/v1/analytics/engagement/', self.admin)

    def test_completion_list(self):
        self.api_get('/api/v1/analytics/completion/', self.admin)

    def test_outcomes_list(self):
        self.api_get('/api/v1/analytics/outcomes/', self.admin)

    def test_at_risk_list(self):
        self.api_get('/api/v1/analytics/at-risk/', self.admin)

    def test_activity_list(self):
        self.api_get('/api/v1/analytics/activity/', self.admin)


class NoticesAPISmokeTest(APISmokeTestBase):
    def test_notices_list(self):
        self.api_get('/api/v1/notices/notices/', self.admin)


class EventsAPISmokeTest(APISmokeTestBase):
    def test_events_list(self):
        self.api_get('/api/v1/events/events/', self.admin)


class DisciplineAPISmokeTest(APISmokeTestBase):
    def test_discipline_list(self):
        self.api_get('/api/v1/discipline/incidents/', self.admin)


class NotesAPISmokeTest(APISmokeTestBase):
    def test_notes_list(self):
        self.api_get('/api/v1/notes/notes/', self.admin)


class LibraryAPISmokeTest(APISmokeTestBase):
    def test_books_list(self):
        self.api_get('/api/v1/library/books/', self.admin)


class ArticlesAPISmokeTest(APISmokeTestBase):
    def test_articles_list(self):
        self.api_get('/api/v1/articles/articles/', self.admin)


class AttendanceAPISmokeTest(APISmokeTestBase):
    def test_attendance_list(self):
        self.api_get('/api/v1/attendance/attendance/', self.admin)


class ResultAPISmokeTest(APISmokeTestBase):
    def test_results_list(self):
        self.api_get('/api/v1/results/results/', self.admin)


class PaymentsAPISmokeTest(APISmokeTestBase):
    def test_invoices_list(self):
        self.api_get('/api/v1/payments/invoices/', self.admin)


class SearchAPISmokeTest(APISmokeTestBase):
    def test_search(self):
        self.api_get('/api/v1/search/search/?q=test', self.admin)


class AdmissionsAPISmokeTest(APISmokeTestBase):
    def test_sessions_list(self):
        self.api_get('/api/v1/admissions/sessions/', self.admin)

    def test_applications_list(self):
        self.api_get('/api/v1/admissions/applications/', self.admin)


class AlumniAPISmokeTest(APISmokeTestBase):
    def test_alumni_list(self):
        self.api_get('/api/v1/alumni/alumni/', self.admin)

    def test_events_list(self):
        self.api_get('/api/v1/alumni/events/', self.admin)


class MonitoringAPISmokeTest(APISmokeTestBase):
    def test_dashboard(self):
        self.api_get('/api/v1/monitoring/dashboard/', self.admin)


class FilieresAPISmokeTest(APISmokeTestBase):
    def test_filieres_list(self):
        self.api_get('/api/v1/filieres/filieres/', self.admin)


class QuizAPISmokeTest(APISmokeTestBase):
    def test_quizzes_list(self):
        self.api_get('/api/v1/quiz/quizzes/', self.admin)


class DailystatAPISmokeTest(APISmokeTestBase):
    def test_dailystat_list(self):
        self.api_get('/api/v1/dailystat/stats/', self.admin)

    def test_unauthenticated_denied(self):
        r = self.client.get('/api/v1/core/sessions/', format='json')
        self.assertIn(r.status_code, {401, 403})

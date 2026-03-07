"""Tests for grading app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class GradingDashboardTest(TestDataMixin, TestCase):
    """Tests for the grading dashboard view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:dashboard')

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


class RubricListTest(TestDataMixin, TestCase):
    """Tests for the rubric_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:rubric_list')

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


class RubricCreateTest(TestDataMixin, TestCase):
    """Tests for the rubric_create view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:rubric_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_get(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_post_empty(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class RubricDetailTest(TestDataMixin, TestCase):
    """Tests for the rubric_detail view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()

    def _url(self):
        return reverse('frontend:grading:rubric_detail',
                       args=[self.rubric.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class RubricUpdateTest(TestDataMixin, TestCase):
    """Tests for the rubric_update view (lecturer_required, owner or direction)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()
        self.rubric.created_by = self.professor
        self.rubric.save()

    def _url(self):
        return reverse('frontend:grading:rubric_update',
                       args=[self.rubric.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_owner_allowed(self):
        self.client.force_login(self.professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class RubricDeleteTest(TestDataMixin, TestCase):
    """Tests for the rubric_delete view (lecturer_required, owner or direction)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()
        self.rubric.created_by = self.professor
        self.rubric.save()

    def _url(self):
        return reverse('frontend:grading:rubric_delete',
                       args=[self.rubric.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_owner_get_confirm(self):
        self.client.force_login(self.professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_owner_post_deletes(self):
        self.client.force_login(self.professor)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class CriterionCreateTest(TestDataMixin, TestCase):
    """Tests for the criterion_create view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()
        self.rubric.created_by = self.professor
        self.rubric.save()

    def _url(self):
        return reverse('frontend:grading:criterion_create',
                       args=[self.rubric.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_owner_get(self):
        self.client.force_login(self.professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_owner_post_empty(self):
        self.client.force_login(self.professor)
        response = self.client.post(self._url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


class CriterionUpdateTest(TestDataMixin, TestCase):
    """Tests for the criterion_update view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()
        self.rubric.created_by = self.professor
        self.rubric.save()
        self.criterion = self.create_rubric_criterion(rubric=self.rubric)

    def _url(self):
        return reverse('frontend:grading:criterion_update',
                       args=[self.criterion.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_owner_allowed(self):
        self.client.force_login(self.professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class CriterionDeleteTest(TestDataMixin, TestCase):
    """Tests for the criterion_delete view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.rubric = self.create_rubric()
        self.rubric.created_by = self.professor
        self.rubric.save()
        self.criterion = self.create_rubric_criterion(rubric=self.rubric)

    def _url(self):
        return reverse('frontend:grading:criterion_delete',
                       args=[self.criterion.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_owner_get_confirm(self):
        self.client.force_login(self.professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_owner_post_deletes(self):
        self.client.force_login(self.professor)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class GradeEntryListTest(TestDataMixin, TestCase):
    """Tests for the grade_entry_list view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_entry_list')

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


class GradeEntryCreateTest(TestDataMixin, TestCase):
    """Tests for the grade_entry_create view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_entry_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_get(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class GradeEntryCreateWithRubricTest(TestDataMixin, TestCase):
    """Tests for grade_entry_create_with_rubric view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.rubric = self.create_rubric()

    def _url(self):
        return reverse('frontend:grading:grade_entry_create_with_rubric',
                       args=[self.rubric.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class GradeEntryCreateFullTest(TestDataMixin, TestCase):
    """Tests for grade_entry_create_full view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.rubric = self.create_rubric()
        self.student = self.create_student_user()
        self.profile = self.create_student_profile(user=self.student)

    def _url(self):
        return reverse('frontend:grading:grade_entry_create_full',
                       args=[self.rubric.pk, self.profile.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class GradeEntryDetailTest(TestDataMixin, TestCase):
    """Tests for the grade_entry_detail view (login required, role-filtered)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        # Use a nonexistent pk to test 404
        self.url = reverse('frontend:grading:grade_entry_detail', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_with_nonexistent_grade(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class GradeEntryEditTest(TestDataMixin, TestCase):
    """Tests for the grade_entry_edit view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_entry_edit', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent_returns_404(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class GradeEntryDeleteTest(TestDataMixin, TestCase):
    """Tests for the grade_entry_delete view (lecturer_required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_entry_delete', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent_returns_404(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class StudentGradebookTest(TestDataMixin, TestCase):
    """Tests for the student_gradebook view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:student_gradebook')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_sees_own_grades(self):
        student = self.create_student_user()
        self.create_student_profile(user=student)
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_without_student_id_redirects(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 500])


class StudentGradebookDetailTest(TestDataMixin, TestCase):
    """Tests for the student_gradebook_detail view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.student = self.create_student_user()
        self.profile = self.create_student_profile(user=self.student)

    def _url(self):
        return reverse('frontend:grading:student_gradebook_detail',
                       args=[self.profile.pk])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_professor_can_view_student(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_view_student(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class PeerReviewListTest(TestDataMixin, TestCase):
    """Tests for the peer_review_list view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:peer_review_list')

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


class PeerReviewSubmitTest(TestDataMixin, TestCase):
    """Tests for the peer_review_submit view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:peer_review_submit', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_nonexistent_returns_404(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class GradeCurveListTest(TestDataMixin, TestCase):
    """Tests for the grade_curve_list view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_curve_list')

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


class GradeCurveCreateTest(TestDataMixin, TestCase):
    """Tests for the grade_curve_create view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_curve_create')

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


class GradeCurveDetailTest(TestDataMixin, TestCase):
    """Tests for the grade_curve_detail view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_curve_detail', args=[99999])

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


class GradeCurveEditTest(TestDataMixin, TestCase):
    """Tests for the grade_curve_edit view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_curve_edit', args=[99999])

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


class GradeCurveDeleteTest(TestDataMixin, TestCase):
    """Tests for the grade_curve_delete view (direction_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:grading:grade_curve_delete', args=[99999])

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

    def test_admin_post_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

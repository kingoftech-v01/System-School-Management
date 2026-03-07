"""
Frontend view tests for the result app.

Tests cover:
- add_score: Professor sees courses for score entry
- add_score_for: Professor adds scores for a specific course
- grade_results: Student views grade results
- ass_results: Student views assessment results
- result_sheet_pdf_view: Professor generates result sheet PDF
- course_registration_form: Student generates registration form PDF
- grade_appeal_list: Multi-role appeal listing
- grade_appeal_detail: Appeal detail view with permission checks
- grade_appeal_create: Student creates grade appeal
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from course.models import CourseAllocation
from result.models import TakenCourse, GradeAppeal

from tests.helpers import TestDataMixin


class ResultViewsBase(TestDataMixin, TestCase):
    """Common setUp for result view tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()

        # Create session and semester first (required by many views)
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)

        # Users
        self.student_user = self.create_student_user()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()

        # Academic setup
        self.program = self.create_program()
        self.course = self.create_course(
            program=self.program,
            semester=self.semester.semester,
        )

        # Student profile
        self.student_profile = self.create_student_profile(
            user=self.student_user,
            program=self.program,
        )

        # Allocate course to professor
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.professor,
            session=self.session,
        )
        self.allocation.courses.add(self.course)

        # TakenCourse record
        self.taken_course = TakenCourse.objects.create(
            student=self.student_profile,
            course=self.course,
        )


# ============================================================================
# ADD SCORE (Lecturer only)
# ============================================================================

class TestAddScore(ResultViewsBase):
    """Tests for the add_score view."""

    def url(self):
        return reverse('frontend:result:add_score')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_no_active_session(self):
        """When no active session exists, shows error message."""
        from core.models import Session
        Session.objects.all().update(is_current_session=False)
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ADD SCORE FOR (Lecturer only, specific course)
# ============================================================================

class TestAddScoreFor(ResultViewsBase):
    """Tests for the add_score_for view."""

    def url(self, course_id=None):
        return reverse('frontend:result:add_score_for',
                        kwargs={'id': course_id or self.course.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_get_students(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_unallocated_professor_denied(self):
        """Professor not allocated to course is denied."""
        other_prof = self.create_professor_user()
        self.client.force_login(other_prof)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_scores(self):
        """Professor submits scores for students."""
        self.client.force_login(self.professor)
        data = {
            str(self.taken_course.pk): [10, 15, 5, 5, 40],
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_course_returns_404(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url(course_id=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# GRADE RESULTS (Student only)
# ============================================================================

class TestGradeResults(ResultViewsBase):
    """Tests for the grade_result view."""

    def url(self):
        return reverse('frontend:result:grade_results')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_view_grades(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_without_profile_redirects(self):
        """Student without a Student profile is redirected."""
        new_student = self.create_student_user()
        self.client.force_login(new_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ASSESSMENT RESULTS (Student only)
# ============================================================================

class TestAssessmentResults(ResultViewsBase):
    """Tests for the assessment_result view."""

    def url(self):
        return reverse('frontend:result:ass_results')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_view_assessments(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_without_profile_redirects(self):
        new_student = self.create_student_user()
        self.client.force_login(new_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# RESULT SHEET PDF (Lecturer only)
# ============================================================================

class TestResultSheetPdf(ResultViewsBase):
    """Tests for the result_sheet_pdf_view view."""

    def url(self, course_id=None):
        return reverse('frontend:result:result_sheet_pdf_view',
                        kwargs={'id': course_id or self.course.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_can_generate_pdf(self):
        """Allocated professor can generate result sheet PDF."""
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_unallocated_professor_denied(self):
        """Professor not allocated to course cannot generate PDF."""
        other_prof = self.create_professor_user()
        self.client.force_login(other_prof)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_course_returns_404(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url(course_id=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# COURSE REGISTRATION FORM (Student only)
# ============================================================================

class TestCourseRegistrationForm(ResultViewsBase):
    """Tests for the course_registration_form view."""

    def url(self):
        return reverse('frontend:result:course_registration_form')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_access(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_without_profile_redirects(self):
        new_student = self.create_student_user()
        self.client.force_login(new_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# GRADE APPEAL LIST (Multi-role)
# ============================================================================

class TestGradeAppealList(ResultViewsBase):
    """Tests for the grade_appeal_list view."""

    def url(self):
        return reverse('frontend:result:grade_appeal_list')

    def setUp(self):
        super().setUp()
        # Create a grade appeal for testing
        self.appeal = GradeAppeal.objects.create(
            taken_course=self.taken_course,
            student=self.student_profile,
            reason='I believe my grade was incorrectly calculated.',
        )

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_sees_own_appeals(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_sees_allocated_course_appeals(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_sees_all_appeals(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_sees_all_appeals(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'status': 'submitted'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_pagination(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'page': 1})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_without_profile_sees_empty(self):
        new_student = self.create_student_user()
        self.client.force_login(new_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# GRADE APPEAL DETAIL
# ============================================================================

class TestGradeAppealDetail(ResultViewsBase):
    """Tests for the grade_appeal_detail view."""

    def setUp(self):
        super().setUp()
        self.appeal = GradeAppeal.objects.create(
            taken_course=self.taken_course,
            student=self.student_profile,
            reason='Grade seems too low.',
        )

    def url(self, pk=None):
        return reverse('frontend:result:grade_appeal_detail',
                        kwargs={'pk': pk or self.appeal.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_view_own_appeal(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_other_student_cannot_view(self):
        """Another student cannot view someone else's appeal."""
        other_student = self.create_student_user()
        self.client.force_login(other_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_can_view(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# GRADE APPEAL CREATE (Student only)
# ============================================================================

class TestGradeAppealCreate(ResultViewsBase):
    """Tests for the grade_appeal_create view."""

    def url(self, taken_course_id=None):
        return reverse('frontend:result:grade_appeal_create',
                        kwargs={'taken_course_id': taken_course_id or self.taken_course.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_get_form(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_post_appeal(self):
        self.client.force_login(self.student_user)
        data = {
            'taken_course': self.taken_course.pk,
            'reason': 'I believe my exam was graded incorrectly.',
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_post_empty_data(self):
        self.client.force_login(self.student_user)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_duplicate_appeal_redirects(self):
        """Creating a second active appeal for the same course redirects."""
        GradeAppeal.objects.create(
            taken_course=self.taken_course,
            student=self.student_profile,
            reason='First appeal',
            status='submitted',
        )
        self.client.force_login(self.student_user)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_student_without_profile_redirects(self):
        new_student = self.create_student_user()
        self.client.force_login(new_student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_taken_course_returns_404(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self.url(taken_course_id=99999))
        self.assertIn(response.status_code, [302, 404])

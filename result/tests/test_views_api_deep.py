"""
Deep API view tests for the result app.

Tests cover:
- TakenCourseViewSet (CRUD, my_grades, by_semester)
- ResultViewSet (CRUD, my_results, calculate_gpa)
- GradeComponentWeightViewSet (CRUD)
- GradeAppealViewSet (CRUD, my_appeals, approve, reject)
- GradeHistoryViewSet (read-only)
- TranscriptViewSet (CRUD, my_transcripts, certify)
- Authentication checks
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from result.models import (
    GradeAppeal, GradeComponentWeight, GradeHistory,
    Result, TakenCourse, Transcript,
)
from tests.helpers import TestDataMixin


class TakenCourseViewSetTests(TestDataMixin, TestCase):
    """Tests for TakenCourseViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.course = self.create_course(program=self.program)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile, course=self.course,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:result:taken-course-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:result:taken-course-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_taken_course(self):
        self._auth(self.admin)
        url = reverse('api:result:taken-course-detail', kwargs={'pk': self.taken.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_taken_course(self):
        self._auth(self.admin)
        course2 = self.create_course(program=self.program)
        url = reverse('api:result:taken-course-list')
        data = {
            'student': self.student_profile.pk,
            'course': course2.pk,
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_update_scores(self):
        self._auth(self.admin)
        url = reverse('api:result:taken-course-detail', kwargs={'pk': self.taken.pk})
        data = {
            'assignment': '20.00',
            'mid_exam': '25.00',
            'quiz': '10.00',
            'attendance': '5.00',
            'final_exam': '30.00',
        }
        resp = self.client.patch(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.taken.refresh_from_db()
        self.assertEqual(self.taken.total, Decimal('90.00'))

    def test_my_grades_with_student(self):
        self._auth(self.student_user)
        url = reverse('api:result:taken-course-my-grades')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_grades_no_student_profile(self):
        other = self.create_user(role='professor', is_lecturer=True)
        self._auth(other)
        url = reverse('api:result:taken-course-my-grades')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_by_semester_missing_param(self):
        self._auth(self.admin)
        url = reverse('api:result:taken-course-by-semester')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_by_semester_valid(self):
        session = self.create_session()
        semester = self.create_semester(session=session)
        self._auth(self.admin)
        url = reverse('api:result:taken-course-by-semester')
        resp = self.client.get(url, {'semester_id': semester.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_search_by_course_title(self):
        self._auth(self.admin)
        url = reverse('api:result:taken-course-list')
        resp = self.client.get(url, {'search': self.course.title})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ResultViewSetTests(TestDataMixin, TestCase):
    """Tests for ResultViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.result = Result.objects.create(
            student=self.student_profile,
            gpa=3.5,
            cgpa=3.2,
            semester='First',
            session='2024/2025',
            level='Bachelor',
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:result:result-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:result:result-detail', kwargs={'pk': self.result.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_results(self):
        self._auth(self.student_user)
        url = reverse('api:result:result-my-results')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_calculate_gpa_no_semester(self):
        self._auth(self.student_user)
        # Make sure no current semester exists
        from core.models import Semester
        Semester.objects.filter(is_current_semester=True).update(is_current_semester=False)
        url = reverse('api:result:result-calculate-gpa')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_calculate_gpa_with_semester(self):
        session = self.create_session()
        self.create_semester(session=session)
        self._auth(self.student_user)
        url = reverse('api:result:result-calculate-gpa')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('current_gpa', resp.data)
        self.assertIn('cumulative_gpa', resp.data)


class GradeComponentWeightViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeComponentWeightViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.program = self.create_program()
        self.weight = GradeComponentWeight.objects.create(
            program=self.program,
            assignment_weight=Decimal('10.00'),
            mid_exam_weight=Decimal('20.00'),
            quiz_weight=Decimal('10.00'),
            attendance_weight=Decimal('10.00'),
            final_exam_weight=Decimal('50.00'),
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:result:grade-weight-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:result:grade-weight-detail', kwargs={'pk': self.weight.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class GradeAppealViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeAppealViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.course = self.create_course(program=self.program)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile, course=self.course,
        )
        self.appeal = GradeAppeal.objects.create(
            taken_course=self.taken,
            student=self.student_profile,
            reason='Grade seems incorrect',
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:result:appeal-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_appeals(self):
        self._auth(self.student_user)
        url = reverse('api:result:appeal-my-appeals')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_approve_by_lecturer(self):
        self._auth(self.professor)
        url = reverse('api:result:appeal-approve', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url, {'notes': 'Approved after review'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, 'approved')

    def test_approve_by_student_denied(self):
        self._auth(self.student_user)
        url = reverse('api:result:appeal-approve', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_by_admin(self):
        self._auth(self.admin)
        url = reverse('api:result:appeal-reject', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url, {'notes': 'No evidence'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, 'rejected')

    def test_reject_by_student_denied(self):
        self._auth(self.student_user)
        url = reverse('api:result:appeal-reject', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class GradeHistoryViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeHistoryViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.course = self.create_course(program=self.program)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile, course=self.course,
        )
        self.history = GradeHistory.objects.create(
            taken_course=self.taken,
            old_assignment=Decimal('10.00'), old_mid_exam=Decimal('20.00'),
            old_quiz=Decimal('10.00'), old_attendance=Decimal('5.00'),
            old_final_exam=Decimal('30.00'), old_total=Decimal('75.00'),
            old_grade='B+',
            new_assignment=Decimal('15.00'), new_mid_exam=Decimal('25.00'),
            new_quiz=Decimal('10.00'), new_attendance=Decimal('5.00'),
            new_final_exam=Decimal('35.00'), new_total=Decimal('90.00'),
            new_grade='A+',
            changed_by=self.admin,
            change_reason='Recount',
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:result:grade-history-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:result:grade-history-detail', kwargs={'pk': self.history.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_not_allowed(self):
        """GradeHistoryViewSet is read-only."""
        self._auth(self.admin)
        url = reverse('api:result:grade-history-list')
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TranscriptViewSetTests(TestDataMixin, TestCase):
    """Tests for TranscriptViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.transcript = Transcript.objects.create(
            student=self.student_profile,
            transcript_type='unofficial',
            generated_by=self.admin,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:result:transcript-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_transcripts(self):
        self._auth(self.student_user)
        url = reverse('api:result:transcript-my-transcripts')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_certify_by_admin(self):
        self._auth(self.admin)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {'certification_number': 'CERT-001'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.transcript.refresh_from_db()
        self.assertTrue(self.transcript.is_certified)

    def test_certify_missing_number(self):
        self._auth(self.admin)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_certify_by_non_staff_denied(self):
        self._auth(self.student_user)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {'certification_number': 'CERT-002'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

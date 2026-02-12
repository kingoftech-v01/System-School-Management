"""
API ViewSet tests for the result app.

Tests cover CRUD operations, custom actions, and permission checks for:
- TakenCourseViewSet
- ResultViewSet
- GradeComponentWeightViewSet
- GradeAppealViewSet
- GradeHistoryViewSet (read-only)
- TranscriptViewSet
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin
from result.models import (
    TakenCourse, Result, GradeComponentWeight,
    GradeAppeal, GradeHistory, Transcript,
)


# ============================================================================
# TakenCourse ViewSet Tests
# ============================================================================

class TakenCourseViewSetTests(TestDataMixin, TestCase):
    """Tests for TakenCourseViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile,
            course=self.course,
        )

    def test_list_taken_courses_unauthenticated(self):
        url = reverse('api:result:taken-course-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_taken_courses(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:taken-course-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_taken_course(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:taken-course-detail', kwargs={'pk': self.taken.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_taken_course_scores(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:taken-course-detail', kwargs={'pk': self.taken.pk})
        data = {
            'assignment': 20,
            'mid_exam': 15,
            'quiz': 10,
            'attendance': 5,
            'final_exam': 30,
        }
        resp = self.client.patch(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_grades_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:taken-course-my-grades')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_by_semester_missing_param(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:taken-course-by-semester')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_by_semester_with_param(self):
        semester = self.create_semester()
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:taken-course-by-semester')
        resp = self.client.get(url, {'semester_id': semester.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Result ViewSet Tests
# ============================================================================

class ResultViewSetTests(TestDataMixin, TestCase):
    """Tests for ResultViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.result = Result.objects.create(
            student=self.student_profile,
            gpa=3.5,
            cgpa=3.4,
            semester='First',
            session='2024/2025',
            level='Bachelor',
        )

    def test_list_results_unauthenticated(self):
        url = reverse('api:result:result-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_results(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:result-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_result(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:result-detail', kwargs={'pk': self.result.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_results_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:result-my-results')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# GradeComponentWeight ViewSet Tests
# ============================================================================

class GradeComponentWeightViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeComponentWeightViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.course = self.create_course()
        self.program = self.create_program()
        self.weight = GradeComponentWeight.objects.create(
            course=self.course,
            program=self.program,
            assignment_weight=20,
            mid_exam_weight=20,
            quiz_weight=10,
            attendance_weight=10,
            final_exam_weight=40,
        )

    def test_list_weights_unauthenticated(self):
        url = reverse('api:result:grade-weight-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_weights(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:grade-weight-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_weight(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:grade-weight-detail', kwargs={'pk': self.weight.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# GradeAppeal ViewSet Tests
# ============================================================================

class GradeAppealViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeAppealViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile,
            course=self.course,
        )
        self.appeal = GradeAppeal.objects.create(
            taken_course=self.taken,
            student=self.student_profile,
            reason='I believe my exam was graded incorrectly.',
        )

    def test_list_appeals_unauthenticated(self):
        url = reverse('api:result:appeal-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_appeals(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:appeal-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_appeal(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:appeal-detail', kwargs={'pk': self.appeal.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_appeals_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:appeal-my-appeals')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_approve_appeal(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:result:appeal-approve', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url, {'notes': 'Reviewed and approved'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_reject_appeal(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:result:appeal-reject', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url, {'notes': 'Grade is correct'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_approve_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:appeal-approve', kwargs={'pk': self.appeal.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================================
# GradeHistory ViewSet Tests (Read-Only)
# ============================================================================

class GradeHistoryViewSetTests(TestDataMixin, TestCase):
    """Tests for GradeHistoryViewSet (read-only audit trail)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.taken = TakenCourse.objects.create(
            student=self.student_profile, course=self.course,
        )
        self.history = GradeHistory.objects.create(
            taken_course=self.taken,
            changed_by=self.admin,
            old_total=60,
            new_total=75,
            old_grade='C',
            new_grade='B',
            change_reason='Re-evaluation',
        )

    def test_list_history_unauthenticated(self):
        url = reverse('api:result:grade-history-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_history(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:grade-history-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_history(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:grade-history-detail', kwargs={'pk': self.history.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Transcript ViewSet Tests
# ============================================================================

class TranscriptViewSetTests(TestDataMixin, TestCase):
    """Tests for TranscriptViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.student_profile = self.create_student_profile(user=self.student_user)
        self.transcript = Transcript.objects.create(
            student=self.student_profile,
            transcript_type='official',
            generated_by=self.admin,
        )

    def test_list_transcripts_unauthenticated(self):
        url = reverse('api:result:transcript-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_transcripts(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:transcript-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_transcript(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:transcript-detail', kwargs={'pk': self.transcript.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_my_transcripts_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:transcript-my-transcripts')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_certify_action_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {'certification_number': 'CN-001'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.transcript.refresh_from_db()
        self.assertTrue(self.transcript.is_certified)

    def test_certify_missing_number(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_certify_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:result:transcript-certify', kwargs={'pk': self.transcript.pk})
        resp = self.client.post(url, {'certification_number': 'CN-002'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

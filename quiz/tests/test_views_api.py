"""
API ViewSet tests for the quiz app.

Tests cover CRUD operations, custom actions, and permission checks for:
- QuizViewSet
- MCQuestionViewSet
- EssayQuestionViewSet
- SittingViewSet
- ProgressViewSet (read-only)
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin
from quiz.models import Quiz, MCQuestion, EssayQuestion, Sitting, Progress


# ============================================================================
# Quiz ViewSet Tests
# ============================================================================

class QuizViewSetTests(TestDataMixin, TestCase):
    """Tests for QuizViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.quiz = self.create_quiz(course=self.course)

    def test_list_quizzes_unauthenticated(self):
        url = reverse('api:quiz:quiz-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_quizzes_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_quizzes_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:quiz-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_quiz_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:quiz-list')
        data = {
            'course': self.course.pk,
            'title': 'New Quiz',
            'description': 'A test quiz',
            'pass_mark': 50,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_quiz_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-list')
        data = {
            'course': self.course.pk,
            'title': 'Student Quiz',
            'pass_mark': 50,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_quiz(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-detail', kwargs={'pk': self.quiz.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_quiz_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:quiz-detail', kwargs={'pk': self.quiz.pk})
        resp = self.client.patch(url, {'title': 'Updated Quiz'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Updated Quiz')

    def test_delete_quiz_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:quiz-detail', kwargs={'pk': self.quiz.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_quiz_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-detail', kwargs={'pk': self.quiz.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_questions_action(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-questions', kwargs={'pk': self.quiz.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('mc_questions', resp.data)
        self.assertIn('essay_questions', resp.data)

    def test_students_see_only_non_draft_quizzes(self):
        draft_quiz = self.create_quiz(course=self.course)
        draft_quiz.draft = True
        draft_quiz.save()
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:quiz-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        quiz_ids = [q['id'] for q in resp.data]
        self.assertNotIn(draft_quiz.pk, quiz_ids)


# ============================================================================
# MCQuestion ViewSet Tests
# ============================================================================

class MCQuestionViewSetTests(TestDataMixin, TestCase):
    """Tests for MCQuestionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.quiz = self.create_quiz(course=self.course)
        self.question = MCQuestion.objects.create(
            quiz=self.quiz,
            content='What is 2+2?',
            explanation='Basic math',
            order=1,
        )

    def test_list_mc_questions(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:mc-question-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_mc_question_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:mc-question-list')
        data = {
            'quiz': self.quiz.pk,
            'content': 'What is 3+3?',
            'order': 2,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_mc_question_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:mc-question-list')
        data = {'quiz': self.quiz.pk, 'content': 'Q?', 'order': 3}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_mc_question(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:mc-question-detail', kwargs={'pk': self.question.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# EssayQuestion ViewSet Tests
# ============================================================================

class EssayQuestionViewSetTests(TestDataMixin, TestCase):
    """Tests for EssayQuestionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.quiz = self.create_quiz(course=self.course)
        self.essay = EssayQuestion.objects.create(
            quiz=self.quiz,
            content='Discuss the topic.',
            order=1,
        )

    def test_list_essay_questions(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:essay-question-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_essay_question_as_professor(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:essay-question-list')
        data = {
            'quiz': self.quiz.pk,
            'content': 'Write about X.',
            'order': 2,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_essay_question_as_student_forbidden(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:essay-question-list')
        data = {'quiz': self.quiz.pk, 'content': 'Topic?', 'order': 3}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_essay_question(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:essay-question-detail', kwargs={'pk': self.essay.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Sitting ViewSet Tests
# ============================================================================

class SittingViewSetTests(TestDataMixin, TestCase):
    """Tests for SittingViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.course = self.create_course()
        self.quiz = self.create_quiz(course=self.course)
        self.sitting = Sitting.objects.create(
            user=self.student_user,
            quiz=self.quiz,
        )

    def test_list_sittings_unauthenticated(self):
        url = reverse('api:quiz:sitting-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_sittings_as_student_sees_own(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:sitting-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_sittings_as_professor_sees_all(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:quiz:sitting-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_sitting(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:sitting-detail', kwargs={'pk': self.sitting.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# Progress ViewSet Tests (Read-Only)
# ============================================================================

class ProgressViewSetTests(TestDataMixin, TestCase):
    """Tests for ProgressViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.progress = Progress.objects.create(
            user=self.student_user,
            score='75',
        )

    def test_list_progress_unauthenticated(self):
        url = reverse('api:quiz:progress-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_progress_as_student_sees_own(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:progress-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_progress(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:quiz:progress-detail', kwargs={'pk': self.progress.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

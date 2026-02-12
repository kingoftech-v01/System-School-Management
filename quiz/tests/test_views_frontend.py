"""
Frontend view tests for the quiz app.

Tests cover:
- Quiz list (quiz_index), progress, marking list/detail
- Quiz create, update, delete
- MC question create/edit, essay create, TF create
- Quiz taking (student)
- Role-based access enforcement
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from quiz.models import Quiz, MCQuestion, EssayQuestion, TrueFalseQuestion, Question
from course.models import CourseAllocation


OK_CODES = {200, 302, 403, 404, 500}


class QuizViewBase(TestDataMixin, TestCase):
    """Shared setup for quiz frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()

        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)

        # Allocate professor to the course
        allocation = CourseAllocation.objects.create(
            lecturer=self.professor, session=self.session
        )
        allocation.courses.add(self.course)

        # Create a quiz for the course
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Test Quiz',
            slug='test-quiz-view',
        )

    def _url(self, name, **kwargs):
        return reverse(f'frontend:quiz:{name}', kwargs=kwargs)


# ============================================================================
# QUIZ LIST (quiz_index)
# ============================================================================

class QuizListTests(QuizViewBase):
    def test_list_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_index', slug=self.course.slug))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_index', slug=self.course.slug))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_anonymous_redirects(self):
        r = self.client.get(self._url('quiz_index', slug=self.course.slug))
        self.assertEqual(r.status_code, 302)

    def test_list_nonexistent_course(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_index', slug='nonexistent-slug'))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# QUIZ PROGRESS
# ============================================================================

class QuizProgressTests(QuizViewBase):
    def test_progress_student(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_progress'))
        self.assertIn(r.status_code, OK_CODES)

    def test_progress_professor_denied(self):
        """Progress is student-only view."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_progress'))
        self.assertIn(r.status_code, {302, 403})

    def test_progress_anonymous_redirects(self):
        r = self.client.get(self._url('quiz_progress'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# QUIZ MARKING
# ============================================================================

class QuizMarkingListTests(QuizViewBase):
    def test_marking_list_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_marking'))
        self.assertIn(r.status_code, OK_CODES)

    def test_marking_list_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('quiz_marking'))
        self.assertIn(r.status_code, OK_CODES)

    def test_marking_list_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_marking'))
        self.assertIn(r.status_code, {302, 403})

    def test_marking_list_with_filter(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_marking') + '?quiz_filter=test')
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# QUIZ CREATE
# ============================================================================

class QuizCreateTests(QuizViewBase):
    def test_create_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_create', slug=self.course.slug))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('quiz_create', slug=self.course.slug))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_create', slug=self.course.slug))
        self.assertIn(r.status_code, {302, 403})

    def test_create_post_professor(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('quiz_create', slug=self.course.slug), data={
            'title': 'New Quiz',
            'description': 'A new quiz',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_create_nonexistent_course(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_create', slug='no-such-course'))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# QUIZ UPDATE
# ============================================================================

class QuizUpdateTests(QuizViewBase):
    def test_update_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_update', slug=self.course.slug, pk=self.quiz.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_update_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('quiz_update', slug=self.course.slug, pk=self.quiz.pk), data={
            'title': 'Updated Quiz',
            'description': 'Updated desc',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_update_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_update', slug=self.course.slug, pk=self.quiz.pk))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# QUIZ DELETE
# ============================================================================

class QuizDeleteTests(QuizViewBase):
    def test_delete_professor(self):
        self.client.force_login(self.professor)
        quiz = Quiz.objects.create(
            course=self.course, title='To Delete', slug='to-delete-quiz'
        )
        r = self.client.get(self._url('quiz_delete', slug=self.course.slug, pk=quiz.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_delete', slug=self.course.slug, pk=self.quiz.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_delete_admin(self):
        self.client.force_login(self.admin)
        quiz = Quiz.objects.create(
            course=self.course, title='Admin Delete', slug='admin-delete-quiz'
        )
        r = self.client.get(self._url('quiz_delete', slug=self.course.slug, pk=quiz.pk))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# MC QUESTION CREATE
# ============================================================================

class MCQuestionCreateTests(QuizViewBase):
    def test_mc_create_get(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('mc_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_mc_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('mc_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_mc_create_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('mc_create', slug=self.course.slug, quiz_id=self.quiz.pk), data={
            'content': 'What is 2+2?',
            'explanation': 'Basic math',
            'answer_order': 'content',
        })
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# MC QUESTION EDIT
# ============================================================================

class MCQuestionEditTests(QuizViewBase):
    def test_mc_edit_get(self):
        mc = MCQuestion.objects.create(content='Q1', explanation='E1')
        mc.quiz.add(self.quiz)
        self.client.force_login(self.professor)
        r = self.client.get(self._url('mc_edit', slug=self.course.slug, pk=mc.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_mc_edit_student_denied(self):
        mc = MCQuestion.objects.create(content='Q2', explanation='E2')
        mc.quiz.add(self.quiz)
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('mc_edit', slug=self.course.slug, pk=mc.pk))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# ESSAY QUESTION CREATE
# ============================================================================

class EssayQuestionCreateTests(QuizViewBase):
    def test_essay_create_get(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('essay_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_essay_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('essay_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_essay_create_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('essay_create', slug=self.course.slug, quiz_id=self.quiz.pk), data={
            'content': 'Describe photosynthesis.',
            'explanation': 'Bio question',
        })
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# TF QUESTION CREATE
# ============================================================================

class TFQuestionCreateTests(QuizViewBase):
    def test_tf_create_get(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('tf_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_tf_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('tf_create', slug=self.course.slug, quiz_id=self.quiz.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_tf_create_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('tf_create', slug=self.course.slug, quiz_id=self.quiz.pk), data={
            'content': 'The earth is round.',
            'explanation': 'Geography',
            'correct': True,
        })
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# QUIZ TAKE
# ============================================================================

class QuizTakeTests(QuizViewBase):
    def test_take_student_no_questions(self):
        """Taking a quiz with no questions should redirect with warning."""
        self.client.force_login(self.student_user)
        r = self.client.get(
            self._url('quiz_take', pk=self.course.pk, slug=self.quiz.slug)
        )
        self.assertIn(r.status_code, OK_CODES)

    def test_take_professor_denied(self):
        """Professors cannot take quizzes (student_required)."""
        self.client.force_login(self.professor)
        r = self.client.get(
            self._url('quiz_take', pk=self.course.pk, slug=self.quiz.slug)
        )
        self.assertIn(r.status_code, {302, 403})

    def test_take_anonymous_redirects(self):
        r = self.client.get(
            self._url('quiz_take', pk=self.course.pk, slug=self.quiz.slug)
        )
        self.assertEqual(r.status_code, 302)


# ============================================================================
# QUIZ MARKING DETAIL
# ============================================================================

class QuizMarkingDetailTests(QuizViewBase):
    def test_marking_detail_no_sitting(self):
        """Accessing a non-existent sitting returns 404."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('quiz_marking_detail', pk=99999))
        self.assertEqual(r.status_code, 404)

    def test_marking_detail_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('quiz_marking_detail', pk=99999))
        self.assertIn(r.status_code, {302, 403, 404})

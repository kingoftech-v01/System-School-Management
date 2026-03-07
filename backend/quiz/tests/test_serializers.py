"""Tests for quiz app serializers."""

from django.test import TestCase

from tests.helpers import TestDataMixin
from quiz.serializers import (
    QuizSerializer,
    QuizListSerializer,
    QuizCreateSerializer,
    QuestionSerializer,
    MCQuestionSerializer,
    EssayQuestionSerializer,
    SittingSerializer,
    SittingListSerializer,
    ProgressSerializer,
)
from quiz.models import Quiz, Question, MCQuestion, EssayQuestion, Sitting, Progress


class QuizSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        quiz = self.create_quiz()
        serializer = QuizSerializer(quiz)
        self.assertIn('title', serializer.data)
        self.assertIn('course_name', serializer.data)
        self.assertIn('slug', serializer.data)
        self.assertIn('question_count', serializer.data)

    def test_read_only_slug(self):
        quiz = self.create_quiz()
        serializer = QuizSerializer(quiz)
        self.assertTrue(serializer.data['slug'])

    def test_pass_mark_included(self):
        quiz = self.create_quiz()
        serializer = QuizSerializer(quiz)
        self.assertIn('pass_mark', serializer.data)


class QuizListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        quiz = self.create_quiz()
        serializer = QuizListSerializer(quiz)
        self.assertIn('title', serializer.data)
        self.assertIn('course_name', serializer.data)
        self.assertIn('category_display', serializer.data)
        # Should not include description (lightweight)
        self.assertNotIn('description', serializer.data)

    def test_includes_draft_flag(self):
        quiz = self.create_quiz()
        serializer = QuizListSerializer(quiz)
        self.assertIn('draft', serializer.data)


class QuizCreateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.course = self.create_course()

    def test_valid_data(self):
        data = {
            'course': self.course.pk,
            'title': 'New Quiz',
            'pass_mark': 50,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_pass_mark_below_zero_invalid(self):
        data = {
            'course': self.course.pk,
            'title': 'Bad Quiz',
            'pass_mark': -10,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('pass_mark', serializer.errors)

    def test_pass_mark_above_100_invalid(self):
        data = {
            'course': self.course.pk,
            'title': 'Bad Quiz',
            'pass_mark': 150,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('pass_mark', serializer.errors)

    def test_pass_mark_zero_valid(self):
        data = {
            'course': self.course.pk,
            'title': 'Easy Quiz',
            'pass_mark': 0,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_pass_mark_100_valid(self):
        data = {
            'course': self.course.pk,
            'title': 'Hard Quiz',
            'pass_mark': 100,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        serializer = QuizCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('course', serializer.errors)
        self.assertIn('title', serializer.errors)

    def test_with_optional_fields(self):
        data = {
            'course': self.course.pk,
            'title': 'Full Quiz',
            'description': 'A detailed quiz',
            'category': 'exam',
            'pass_mark': 60,
            'time_limit': 30,
            'random_order': True,
            'single_attempt': True,
        }
        serializer = QuizCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class QuestionSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        quiz = self.create_quiz()
        question = Question.objects.create(content='What is 2+2?')
        question.quiz.add(quiz)
        serializer = QuestionSerializer(question)
        self.assertIn('content', serializer.data)

    def test_figure_url_none_when_no_figure(self):
        question = Question.objects.create(content='No figure')
        serializer = QuestionSerializer(question)
        self.assertIsNone(serializer.data['figure_url'])


class MCQuestionSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        quiz = self.create_quiz()
        mcq = MCQuestion.objects.create(content='What color is the sky?', choice_order='random')
        mcq.quiz.add(quiz)
        serializer = MCQuestionSerializer(mcq)
        self.assertIn('content', serializer.data)
        self.assertIn('choice_order', serializer.data)


class EssayQuestionSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        quiz = self.create_quiz()
        essay = EssayQuestion.objects.create(content='Explain polymorphism.')
        essay.quiz.add(quiz)
        serializer = EssayQuestionSerializer(essay)
        self.assertIn('content', serializer.data)
        self.assertIn('explanation', serializer.data)


class SittingSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_student_user()
        self.quiz = self.create_quiz()
        self.course = self.quiz.course
        self.sitting = Sitting.objects.create(
            user=self.user, quiz=self.quiz, course=self.course,
            question_order='1,2,', question_list='1,2,',
            incorrect_questions='', current_score=1,
            complete=False, user_answers='{}',
        )

    def test_serializes(self):
        serializer = SittingSerializer(self.sitting)
        self.assertIn('user_name', serializer.data)
        self.assertIn('quiz_title', serializer.data)
        self.assertIn('percentage', serializer.data)
        self.assertIn('complete', serializer.data)

    def test_percentage_calculation(self):
        serializer = SittingSerializer(self.sitting)
        # 1 out of 2 = 50%
        self.assertEqual(serializer.data['percentage'], 50)


class SittingListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_student_user()
        quiz = self.create_quiz()
        sitting = Sitting.objects.create(
            user=user, quiz=quiz, course=quiz.course,
            question_order='1,', question_list='1,',
            incorrect_questions='', current_score=0,
            complete=True, user_answers='{}',
        )
        serializer = SittingListSerializer(sitting)
        self.assertIn('user_name', serializer.data)
        self.assertIn('quiz_title', serializer.data)
        self.assertIn('complete', serializer.data)


class ProgressSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        user = self.create_student_user()
        progress = Progress.objects.create(user=user, score='')
        serializer = ProgressSerializer(progress)
        self.assertIn('user_name', serializer.data)
        self.assertIn('score', serializer.data)

"""Tests for quiz app forms."""

from django.test import TestCase

from quiz.models import Quiz, MCQuestion, Choice, EssayQuestion
from quiz.forms import QuestionForm, EssayForm, QuizAddForm
from tests.helpers import TestDataMixin


class QuestionFormTest(TestDataMixin, TestCase):
    def test_mc_question_form(self):
        course = self.create_course()
        quiz = Quiz.objects.create(
            course=course, title='Form Quiz', category='assignment', pass_mark=50,
        )
        q = MCQuestion.objects.create(content='What is 2+2?')
        q.quiz.add(quiz)
        c1 = Choice.objects.create(question=q, choice_text='4', correct=True)
        c2 = Choice.objects.create(question=q, choice_text='5', correct=False)

        form = QuestionForm(question=q)
        self.assertIn('answers', form.fields)

    def test_mc_question_form_submit(self):
        course = self.create_course()
        quiz = Quiz.objects.create(
            course=course, title='Form Quiz 2', category='assignment', pass_mark=50,
        )
        q = MCQuestion.objects.create(content='What is 3+3?')
        q.quiz.add(quiz)
        c1 = Choice.objects.create(question=q, choice_text='6', correct=True)
        c2 = Choice.objects.create(question=q, choice_text='7', correct=False)

        form = QuestionForm(question=q, data={'answers': str(c1.pk)})
        self.assertTrue(form.is_valid(), form.errors)


class EssayFormTest(TestDataMixin, TestCase):
    def test_essay_form(self):
        q = EssayQuestion.objects.create(content='Explain decorators')
        form = EssayForm(question=q)
        self.assertIn('answers', form.fields)

    def test_essay_form_submit(self):
        q = EssayQuestion.objects.create(content='Explain decorators')
        form = EssayForm(question=q, data={'answers': 'Decorators are wrappers...'})
        self.assertTrue(form.is_valid(), form.errors)


class QuizAddFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        course = self.create_course()
        form = QuizAddForm(data={
            'course': course.pk,
            'title': 'New Quiz',
            'category': 'assignment',
            'pass_mark': 50,
            'random_order': False,
            'answers_at_end': False,
            'exam_paper': False,
            'single_attempt': False,
            'draft': False,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_pass_mark(self):
        course = self.create_course()
        form = QuizAddForm(data={
            'course': course.pk,
            'title': 'Bad Quiz',
            'category': 'assignment',
            'pass_mark': 150,  # Over 100
        })
        self.assertFalse(form.is_valid())

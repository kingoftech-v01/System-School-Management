"""Tests for quiz app models."""

from django.test import TestCase
from django.contrib.auth import get_user_model

from quiz.models import Quiz, Progress, Sitting, MCQuestion, Choice, EssayQuestion, TrueFalseQuestion
from tests.helpers import TestDataMixin

User = get_user_model()

_quiz_counter = 0


def _qn():
    global _quiz_counter
    _quiz_counter += 1
    return _quiz_counter


class QuizModelTest(TestDataMixin, TestCase):
    def _create_quiz(self, **overrides):
        course = overrides.pop('course', None) or self.create_course()
        defaults = {
            'course': course,
            'title': f'Test Quiz {_qn()}',
            'category': 'assignment',
            'pass_mark': 50,
        }
        defaults.update(overrides)
        return Quiz.objects.create(**defaults)

    def test_create_quiz(self):
        quiz = self._create_quiz()
        self.assertIsNotNone(quiz.pk)
        self.assertIsNotNone(quiz.slug)

    def test_str(self):
        quiz = self._create_quiz(title='My Quiz')
        self.assertIn('My Quiz', str(quiz))

    def test_slug_auto_generated(self):
        quiz = self._create_quiz(title='Auto Slug Test')
        self.assertTrue(len(quiz.slug) > 0)

    def test_pass_mark_validation(self):
        quiz = self._create_quiz(pass_mark=50)
        self.assertEqual(quiz.pass_mark, 50)

    def test_single_attempt_sets_exam_paper(self):
        quiz = self._create_quiz(single_attempt=True)
        self.assertTrue(quiz.exam_paper)

    def test_draft_default_false(self):
        quiz = self._create_quiz()
        self.assertFalse(quiz.draft)

    def test_get_max_score(self):
        quiz = self._create_quiz()
        self.assertEqual(quiz.get_max_score, 0)

    def test_search_manager(self):
        quiz = self._create_quiz(title='Searchable Quiz XYZ')
        qs = Quiz.objects.search('Searchable Quiz XYZ')
        self.assertIn(quiz, qs)

    def test_search_none(self):
        result = Quiz.objects.search(None)
        self.assertIsNotNone(result)


class MCQuestionModelTest(TestDataMixin, TestCase):
    def _create_mc_question(self, quiz=None):
        if quiz is None:
            course = self.create_course()
            quiz = Quiz.objects.create(
                course=course, title=f'Q Quiz {_qn()}',
                category='assignment', pass_mark=50,
            )
        q = MCQuestion.objects.create(
            content=f'What is 1+1? #{_qn()}',
            explanation='Basic math',
        )
        q.quiz.add(quiz)
        Choice.objects.create(question=q, choice_text='2', correct=True)
        Choice.objects.create(question=q, choice_text='3', correct=False)
        Choice.objects.create(question=q, choice_text='4', correct=False)
        return q

    def test_create_question(self):
        q = self._create_mc_question()
        self.assertIsNotNone(q.pk)

    def test_check_if_correct(self):
        q = self._create_mc_question()
        correct_choice = Choice.objects.get(question=q, correct=True)
        self.assertTrue(q.check_if_correct(str(correct_choice.pk)))

    def test_check_if_incorrect(self):
        q = self._create_mc_question()
        wrong_choice = Choice.objects.filter(question=q, correct=False).first()
        self.assertFalse(q.check_if_correct(str(wrong_choice.pk)))

    def test_get_choices(self):
        q = self._create_mc_question()
        choices = q.get_choices()
        self.assertEqual(choices.count(), 3)

    def test_get_choices_list(self):
        q = self._create_mc_question()
        choices_list = q.get_choices_list()
        self.assertEqual(len(choices_list), 3)

    def test_answer_choice_to_string(self):
        q = self._create_mc_question()
        correct_choice = Choice.objects.get(question=q, correct=True)
        text = q.answer_choice_to_string(str(correct_choice.pk))
        self.assertEqual(text, '2')


class EssayQuestionModelTest(TestCase):
    def test_create_essay(self):
        q = EssayQuestion.objects.create(
            content='Explain Python decorators',
            explanation='Decorators are...',
        )
        self.assertIsNotNone(q.pk)

    def test_check_if_correct_always_false(self):
        q = EssayQuestion.objects.create(content='Essay question')
        self.assertFalse(q.check_if_correct('any answer'))

    def test_get_answers_returns_false(self):
        q = EssayQuestion.objects.create(content='Essay question')
        self.assertFalse(q.get_answers())


class TrueFalseQuestionModelTest(TestCase):
    def test_create_true_false(self):
        q = TrueFalseQuestion.objects.create(
            content='Python is a programming language',
            correct_answer=True,
        )
        self.assertIsNotNone(q.pk)

    def test_check_correct_true(self):
        q = TrueFalseQuestion.objects.create(
            content='Python is a language',
            correct_answer=True,
        )
        self.assertTrue(q.check_if_correct('True'))

    def test_check_correct_false(self):
        q = TrueFalseQuestion.objects.create(
            content='Python is compiled',
            correct_answer=False,
        )
        self.assertTrue(q.check_if_correct('False'))

    def test_check_incorrect(self):
        q = TrueFalseQuestion.objects.create(
            content='Python is a language',
            correct_answer=True,
        )
        self.assertFalse(q.check_if_correct('False'))

    def test_get_answers_list(self):
        q = TrueFalseQuestion.objects.create(
            content='Test TF',
            correct_answer=True,
        )
        answers = q.get_answers_list()
        self.assertEqual(len(answers), 2)


class SittingModelTest(TestDataMixin, TestCase):
    def _create_sitting(self):
        user = self.create_student_user()
        course = self.create_course()
        quiz = Quiz.objects.create(
            course=course, title=f'Sitting Quiz {_qn()}',
            category='assignment', pass_mark=50,
        )
        q1 = MCQuestion.objects.create(content=f'Q1 {_qn()}')
        q1.quiz.add(quiz)
        Choice.objects.create(question=q1, choice_text='A', correct=True)
        Choice.objects.create(question=q1, choice_text='B', correct=False)

        q2 = MCQuestion.objects.create(content=f'Q2 {_qn()}')
        q2.quiz.add(quiz)
        Choice.objects.create(question=q2, choice_text='C', correct=True)
        Choice.objects.create(question=q2, choice_text='D', correct=False)

        sitting = Sitting.objects.new_sitting(user, quiz, course)
        return sitting

    def test_create_sitting(self):
        sitting = self._create_sitting()
        self.assertIsNotNone(sitting.pk)
        self.assertFalse(sitting.complete)

    def test_get_first_question(self):
        sitting = self._create_sitting()
        q = sitting.get_first_question()
        self.assertIsNotNone(q)

    def test_remove_first_question(self):
        sitting = self._create_sitting()
        sitting.remove_first_question()
        q = sitting.get_first_question()
        self.assertIsNotNone(q)

    def test_add_to_score(self):
        sitting = self._create_sitting()
        sitting.add_to_score(1)
        self.assertEqual(sitting.get_current_score, 1)

    def test_mark_quiz_complete(self):
        sitting = self._create_sitting()
        sitting.mark_quiz_complete()
        self.assertTrue(sitting.complete)
        self.assertIsNotNone(sitting.end)

    def test_check_if_passed_true(self):
        sitting = self._create_sitting()
        sitting.add_to_score(2)
        sitting.mark_quiz_complete()
        self.assertTrue(sitting.check_if_passed)

    def test_check_if_passed_false(self):
        sitting = self._create_sitting()
        sitting.mark_quiz_complete()
        self.assertFalse(sitting.check_if_passed)

    def test_progress(self):
        sitting = self._create_sitting()
        answered, total = sitting.progress()
        self.assertEqual(total, 2)

    def test_get_percent_correct(self):
        sitting = self._create_sitting()
        sitting.add_to_score(1)
        pct = sitting.get_percent_correct
        self.assertEqual(pct, 50)

    def test_add_user_answer(self):
        sitting = self._create_sitting()
        q = sitting.get_first_question()
        sitting.add_user_answer(q, '1')
        answers = sitting.questions_with_user_answers
        self.assertIsNotNone(answers)


class ProgressModelTest(TestDataMixin, TestCase):
    def test_new_progress(self):
        user = self.create_student_user()
        progress = Progress.objects.new_progress(user)
        self.assertIsNotNone(progress.pk)

    def test_show_exams(self):
        user = self.create_student_user()
        progress = Progress.objects.new_progress(user)
        exams = progress.show_exams()
        self.assertIsNotNone(exams)

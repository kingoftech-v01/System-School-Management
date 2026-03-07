"""Extended quiz model tests for uncovered branches."""

import json

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase
from django.utils.timezone import now

from course.models import Course, Program
from core.models import Session, Semester
from quiz.models import (
    Quiz, QuizManager, Progress, ProgressManager,
    Sitting, SittingManager, Question, MCQuestion, Choice,
)
from tests.helpers import TestDataMixin


class QuizModelTestMixin(TestDataMixin):
    """Shared helpers for quiz tests."""

    def _make_quiz(self, **kwargs):
        course = self.create_course()
        defaults = {
            'course': course,
            'title': 'Test Quiz',
            'pass_mark': 50,
        }
        defaults.update(kwargs)
        return Quiz.objects.create(**defaults)

    def _make_question(self, quiz):
        q = MCQuestion.objects.create(
            content='What is 1+1?',
            choice_order='content',
        )
        q.quiz.add(quiz)
        return q

    def _make_choice(self, question, text='Answer', correct=False):
        return Choice.objects.create(
            question=question,
            choice_text=text,
            correct=correct,
        )


class QuizManagerTest(QuizModelTestMixin, TestCase):
    def test_search_with_query(self):
        quiz = self._make_quiz(title='Biology Final')
        qs = Quiz.objects.search('Biology')
        self.assertIn(quiz, qs)

    def test_search_empty_query(self):
        self._make_quiz()
        qs = Quiz.objects.search(None)
        self.assertTrue(qs.exists())

    def test_search_no_results(self):
        self._make_quiz(title='Math')
        qs = Quiz.objects.search('ZZZNotFound')
        self.assertEqual(qs.count(), 0)

    def test_search_by_description(self):
        quiz = self._make_quiz(description='Advanced physics topics')
        qs = Quiz.objects.search('physics')
        self.assertIn(quiz, qs)

    def test_search_by_category(self):
        quiz = self._make_quiz(category='exam')
        qs = Quiz.objects.search('exam')
        self.assertIn(quiz, qs)


class QuizSaveTest(QuizModelTestMixin, TestCase):
    def test_single_attempt_sets_exam_paper(self):
        quiz = self._make_quiz(single_attempt=True, exam_paper=False)
        self.assertTrue(quiz.exam_paper)

    def test_invalid_pass_mark_raises(self):
        with self.assertRaises(ValidationError):
            self._make_quiz(pass_mark=101)

    def test_negative_pass_mark_raises(self):
        with self.assertRaises(ValidationError):
            self._make_quiz(pass_mark=-1)

    def test_slug_auto_generated(self):
        quiz = self._make_quiz(slug='')
        self.assertTrue(quiz.slug)

    def test_str(self):
        quiz = self._make_quiz(title='My Quiz')
        self.assertEqual(str(quiz), 'My Quiz')

    def test_get_max_score(self):
        quiz = self._make_quiz()
        self._make_question(quiz)
        self._make_question(quiz)
        self.assertEqual(quiz.get_max_score, 2)

    def test_get_questions(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        questions = quiz.get_questions()
        self.assertEqual(questions.count(), 1)


class ProgressTest(QuizModelTestMixin, TestCase):
    def test_new_progress(self):
        user = self.create_user()
        progress = Progress.objects.new_progress(user)
        self.assertEqual(progress.score, '')
        self.assertEqual(progress.user, user)

    def test_update_score_new_entry(self):
        user = self.create_user()
        progress = Progress.objects.new_progress(user)
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        progress.update_score(q, 1, 1)
        # Score gets stored as "quiz_str,score,possible,"
        self.assertIn('1,1,', progress.score)

    def test_update_score_existing_entry(self):
        user = self.create_user()
        progress = Progress.objects.new_progress(user)
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        progress.update_score(q, 1, 1)
        progress.update_score(q, 1, 1)
        # Score should be updated to 2
        self.assertIn('2,2,', progress.score)

    def test_update_score_invalid_type(self):
        user = self.create_user()
        progress = Progress.objects.new_progress(user)
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        result = progress.update_score(q, 'bad', 1)
        # Should return error tuple
        self.assertIsNotNone(result)

    def test_show_exams_superuser(self):
        user = self.create_admin_user()
        user.is_superuser = True
        user.save()
        progress = Progress.objects.new_progress(user)
        exams = progress.show_exams()
        self.assertEqual(exams.count(), 0)

    def test_show_exams_regular_user(self):
        user = self.create_user()
        progress = Progress.objects.new_progress(user)
        exams = progress.show_exams()
        self.assertEqual(exams.count(), 0)


class SittingManagerTest(QuizModelTestMixin, TestCase):
    def _make_sitting(self, user=None, quiz=None, course=None):
        user = user or self.create_user()
        if not quiz:
            course = course or self.create_course()
            quiz = self._make_quiz(course=course)
        else:
            course = course or quiz.course
        q = self._make_question(quiz)
        self._make_choice(q, 'A', correct=True)
        return Sitting.objects.new_sitting(user, quiz, course)

    def test_new_sitting_creates(self):
        sitting = self._make_sitting()
        self.assertFalse(sitting.complete)
        self.assertTrue(sitting.question_order)
        self.assertTrue(sitting.question_list)

    def test_new_sitting_empty_questions_raises(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course)
        # No questions added
        with self.assertRaises(ImproperlyConfigured):
            Sitting.objects.new_sitting(user, quiz, course)

    def test_new_sitting_random_order(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course, random_order=True)
        self._make_question(quiz)
        sitting = Sitting.objects.new_sitting(user, quiz, course)
        self.assertTrue(sitting.question_order)

    def test_user_sitting_creates_new(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course)
        self._make_question(quiz)
        sitting = Sitting.objects.user_sitting(user, quiz, course)
        self.assertIsNotNone(sitting)

    def test_user_sitting_returns_existing(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course)
        self._make_question(quiz)
        s1 = Sitting.objects.user_sitting(user, quiz, course)
        s2 = Sitting.objects.user_sitting(user, quiz, course)
        self.assertEqual(s1.pk, s2.pk)

    def test_user_sitting_single_attempt_completed(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course, single_attempt=True)
        self._make_question(quiz)
        sitting = Sitting.objects.new_sitting(user, quiz, course)
        sitting.mark_quiz_complete()
        result = Sitting.objects.user_sitting(user, quiz, course)
        self.assertFalse(result)


class SittingModelTest(QuizModelTestMixin, TestCase):
    def _make_sitting_with_questions(self):
        user = self.create_user()
        course = self.create_course()
        quiz = self._make_quiz(course=course)
        q1 = self._make_question(quiz)
        q2 = MCQuestion.objects.create(content='What is 2+2?')
        q2.quiz.add(quiz)
        self._make_choice(q1, 'Two', correct=True)
        self._make_choice(q1, 'Three', correct=False)
        self._make_choice(q2, 'Four', correct=True)
        sitting = Sitting.objects.new_sitting(user, quiz, course)
        return sitting, q1, q2

    def test_get_first_question(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        first = sitting.get_first_question()
        self.assertIsNotNone(first)

    def test_get_first_question_empty_list(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.question_list = ''
        sitting.save()
        self.assertFalse(sitting.get_first_question())

    def test_remove_first_question(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        original = sitting.question_list
        sitting.remove_first_question()
        self.assertNotEqual(sitting.question_list, original)

    def test_remove_first_question_empty(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.question_list = ''
        sitting.save()
        sitting.remove_first_question()  # Should not raise

    def test_add_to_score(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.add_to_score(5)
        self.assertEqual(sitting.current_score, 5)

    def test_get_current_score(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.add_to_score(3)
        self.assertEqual(sitting.get_current_score, 3)

    def test_get_percent_correct(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        sitting.add_to_score(1)
        pct = sitting.get_percent_correct
        self.assertGreater(pct, 0)
        self.assertLessEqual(pct, 100)

    def test_get_percent_correct_zero_questions(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.question_order = ''
        sitting.save()
        self.assertEqual(sitting.get_percent_correct, 0)

    def test_mark_quiz_complete(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.mark_quiz_complete()
        self.assertTrue(sitting.complete)
        self.assertIsNotNone(sitting.end)
        self.assertIsNotNone(sitting.time_spent)

    def test_get_time_remaining_no_limit(self):
        sitting, _, _ = self._make_sitting_with_questions()
        self.assertIsNone(sitting.get_time_remaining())

    def test_get_time_remaining_with_limit(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.quiz.time_limit = 60
        sitting.quiz.save()
        remaining = sitting.get_time_remaining()
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)

    def test_get_time_remaining_completed(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.quiz.time_limit = 60
        sitting.quiz.save()
        sitting.mark_quiz_complete()
        self.assertEqual(sitting.get_time_remaining(), 0)

    def test_is_time_expired_no_limit(self):
        sitting, _, _ = self._make_sitting_with_questions()
        self.assertFalse(sitting.is_time_expired())

    def test_is_time_expired_not_expired(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.quiz.time_limit = 60
        sitting.quiz.save()
        self.assertFalse(sitting.is_time_expired())

    def test_add_incorrect_question(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_incorrect_question(q1)
        self.assertIn(q1.id, sitting.get_incorrect_questions)

    def test_remove_incorrect_question(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_incorrect_question(q1)
        sitting.remove_incorrect_question(q1)
        self.assertNotIn(q1.id, sitting.get_incorrect_questions)

    def test_remove_incorrect_question_not_in_list(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        # Should not raise
        sitting.remove_incorrect_question(q1)

    def test_check_if_passed(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        sitting.add_to_score(2)  # 100%
        self.assertTrue(sitting.check_if_passed)

    def test_check_if_failed(self):
        sitting, _, _ = self._make_sitting_with_questions()
        # 0 score
        self.assertFalse(sitting.check_if_passed)

    def test_result_message_passed(self):
        sitting, _, _ = self._make_sitting_with_questions()
        sitting.add_to_score(2)
        self.assertIn('passed', str(sitting.result_message).lower())

    def test_result_message_failed(self):
        sitting, _, _ = self._make_sitting_with_questions()
        self.assertIn('failed', str(sitting.result_message).lower())

    def test_add_user_answer(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_user_answer(q1, '42')
        answers = json.loads(sitting.user_answers)
        self.assertEqual(answers[str(q1.id)], '42')

    def test_get_questions(self):
        sitting, q1, q2 = self._make_sitting_with_questions()
        questions = sitting.get_questions()
        self.assertEqual(len(questions), 2)

    def test_get_questions_with_answers(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_user_answer(q1, '42')
        questions = sitting.get_questions(with_answers=True)
        self.assertTrue(any(hasattr(q, 'user_answer') for q in questions))

    def test_questions_with_user_answers(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_user_answer(q1, '42')
        result = sitting.questions_with_user_answers
        self.assertIsInstance(result, dict)

    def test_get_max_score(self):
        sitting, _, _ = self._make_sitting_with_questions()
        self.assertEqual(sitting.get_max_score, 2)

    def test_progress(self):
        sitting, q1, _ = self._make_sitting_with_questions()
        sitting.add_user_answer(q1, '42')
        answered, total = sitting.progress()
        self.assertEqual(answered, 1)
        self.assertEqual(total, 2)


class MCQuestionTest(QuizModelTestMixin, TestCase):
    def test_check_if_correct_true(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        choice = self._make_choice(q, 'Right', correct=True)
        self.assertTrue(q.check_if_correct(str(choice.id)))

    def test_check_if_correct_false(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        choice = self._make_choice(q, 'Wrong', correct=False)
        self.assertFalse(q.check_if_correct(str(choice.id)))

    def test_check_if_correct_invalid(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        self.assertFalse(q.check_if_correct('999999'))

    def test_check_if_correct_bad_value(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        self.assertFalse(q.check_if_correct('not_a_number'))

    def test_order_choices_content(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        q.choice_order = 'content'
        self._make_choice(q, 'Zebra')
        self._make_choice(q, 'Apple')
        choices = q.get_choices()
        self.assertEqual(choices.first().choice_text, 'Apple')

    def test_order_choices_random(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        q.choice_order = 'random'
        self._make_choice(q, 'A')
        self._make_choice(q, 'B')
        choices = q.get_choices()
        self.assertEqual(choices.count(), 2)

    def test_order_choices_none(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        q.choice_order = 'none'
        self._make_choice(q, 'A')
        choices = q.get_choices()
        self.assertEqual(choices.count(), 1)

    def test_get_choices_list(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        c = self._make_choice(q, 'Test')
        result = q.get_choices_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], 'Test')

    def test_answer_choice_to_string(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        c = self._make_choice(q, 'My Answer')
        self.assertEqual(q.answer_choice_to_string(str(c.id)), 'My Answer')

    def test_answer_choice_to_string_invalid(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        self.assertEqual(q.answer_choice_to_string('999999'), '')

    def test_answer_choice_to_string_bad_value(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        self.assertEqual(q.answer_choice_to_string('abc'), '')

    def test_question_str(self):
        quiz = self._make_quiz()
        q = self._make_question(quiz)
        self.assertEqual(str(q), 'What is 1+1?')

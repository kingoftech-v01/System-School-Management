"""Tests for quiz template tags: quiz_tags.py."""

from unittest.mock import MagicMock

from django.test import TestCase

from quiz.templatetags.quiz_tags import correct_answer_for_all, answer_choice_to_string
from tests.helpers import TestDataMixin


class CorrectAnswerForAllTagTest(TestDataMixin, TestCase):
    """Tests for the correct_answer_for_all inclusion tag function."""

    def _make_question(self, question_id, choices=None):
        """Create a mock question object."""
        question = MagicMock()
        question.id = question_id
        question.get_choices.return_value = choices or ['A', 'B', 'C']
        return question

    def test_correct_answer_user_was_incorrect(self):
        """When question.id is in incorrect_questions, user_was_incorrect is True."""
        question = self._make_question(42)
        context = {'incorrect_questions': [42, 55]}
        result = correct_answer_for_all(context, question)
        self.assertTrue(result['user_was_incorrect'])
        self.assertEqual(result['previous']['answers'], ['A', 'B', 'C'])

    def test_correct_answer_user_was_correct(self):
        """When question.id is not in incorrect_questions, user_was_incorrect is False."""
        question = self._make_question(42)
        context = {'incorrect_questions': [55, 99]}
        result = correct_answer_for_all(context, question)
        self.assertFalse(result['user_was_incorrect'])

    def test_correct_answer_empty_incorrect_list(self):
        """When incorrect_questions is empty, user_was_incorrect is False."""
        question = self._make_question(1)
        context = {'incorrect_questions': []}
        result = correct_answer_for_all(context, question)
        self.assertFalse(result['user_was_incorrect'])

    def test_correct_answer_no_incorrect_key_in_context(self):
        """When context has no incorrect_questions key, defaults to empty list."""
        question = self._make_question(1)
        context = {}
        result = correct_answer_for_all(context, question)
        self.assertFalse(result['user_was_incorrect'])

    def test_correct_answer_returns_answers_from_question(self):
        """The tag returns answers from question.get_choices()."""
        choices = ['Option 1', 'Option 2']
        question = self._make_question(5, choices=choices)
        context = {'incorrect_questions': []}
        result = correct_answer_for_all(context, question)
        self.assertEqual(result['previous']['answers'], choices)

    def test_correct_answer_calls_get_choices(self):
        """The tag calls get_choices() on the question object."""
        question = self._make_question(10)
        context = {'incorrect_questions': []}
        correct_answer_for_all(context, question)
        question.get_choices.assert_called_once()


class AnswerChoiceToStringFilterTest(TestDataMixin, TestCase):
    """Tests for the answer_choice_to_string filter."""

    def test_delegates_to_question_method(self):
        """answer_choice_to_string calls question.answer_choice_to_string(answer)."""
        question = MagicMock()
        question.answer_choice_to_string.return_value = 'Choice A'
        result = answer_choice_to_string(question, 1)
        self.assertEqual(result, 'Choice A')
        question.answer_choice_to_string.assert_called_once_with(1)

    def test_returns_string_answer(self):
        """answer_choice_to_string returns whatever the question method returns."""
        question = MagicMock()
        question.answer_choice_to_string.return_value = 'True'
        result = answer_choice_to_string(question, 'true')
        self.assertEqual(result, 'True')

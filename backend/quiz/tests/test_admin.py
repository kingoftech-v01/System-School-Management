"""Tests for quiz admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from quiz.models import Quiz, MCQuestion, Progress, EssayQuestion, Sitting
from quiz.admin import MCQuestionAdmin, ProgressAdmin, EssayQuestionAdmin


class QuizAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all quiz models are registered in the admin."""

    def test_quiz_registered(self):
        self.assertIn(Quiz, admin.site._registry)

    def test_mcquestion_registered(self):
        self.assertIn(MCQuestion, admin.site._registry)

    def test_progress_registered(self):
        self.assertIn(Progress, admin.site._registry)

    def test_essay_question_registered(self):
        self.assertIn(EssayQuestion, admin.site._registry)

    def test_sitting_registered(self):
        self.assertIn(Sitting, admin.site._registry)


class MCQuestionAdminTest(TestDataMixin, TestCase):
    """Test MCQuestionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = MCQuestionAdmin(MCQuestion, self.site)

    def test_list_display(self):
        expected = ("content",)
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        expected = ("content", "explanation")
        self.assertEqual(self.admin.search_fields, expected)

    def test_filter_horizontal(self):
        self.assertEqual(self.admin.filter_horizontal, ("quiz",))

    def test_inlines(self):
        from quiz.admin import ChoiceInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(ChoiceInline, inline_classes)


class ProgressAdminTest(TestDataMixin, TestCase):
    """Test ProgressAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ProgressAdmin(Progress, self.site)

    def test_search_fields(self):
        expected = ("user", "score")
        self.assertEqual(self.admin.search_fields, expected)


class EssayQuestionAdminTest(TestDataMixin, TestCase):
    """Test EssayQuestionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = EssayQuestionAdmin(EssayQuestion, self.site)

    def test_list_display(self):
        expected = ("content",)
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        expected = ("content", "explanation")
        self.assertEqual(self.admin.search_fields, expected)

    def test_filter_horizontal(self):
        self.assertEqual(self.admin.filter_horizontal, ("quiz",))

    def test_fields(self):
        expected = ("content", "quiz", "explanation")
        self.assertEqual(self.admin.fields, expected)

"""Tests for grading admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from grading.models import (
    GradingRubric, RubricCriterion, RubricGrade,
    CriterionGrade, PeerReview, GradeCurve,
)
from grading.admin import (
    GradingRubricAdmin, RubricCriterionAdmin, RubricGradeAdmin,
    CriterionGradeAdmin, PeerReviewAdmin, GradeCurveAdmin,
)


class GradingAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all grading models are registered in the admin."""

    def test_grading_rubric_registered(self):
        self.assertIn(GradingRubric, admin.site._registry)

    def test_rubric_criterion_registered(self):
        self.assertIn(RubricCriterion, admin.site._registry)

    def test_rubric_grade_registered(self):
        self.assertIn(RubricGrade, admin.site._registry)

    def test_criterion_grade_registered(self):
        self.assertIn(CriterionGrade, admin.site._registry)

    def test_peer_review_registered(self):
        self.assertIn(PeerReview, admin.site._registry)

    def test_grade_curve_registered(self):
        self.assertIn(GradeCurve, admin.site._registry)


class GradingRubricAdminTest(TestDataMixin, TestCase):
    """Test GradingRubricAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = GradingRubricAdmin(GradingRubric, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = (
            'name', 'course', 'max_score', 'passing_score',
            'is_active', 'allow_partial_credit', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_active', 'allow_partial_credit', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('name', 'description', 'course__name', 'created_by__username')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')

    def test_inlines(self):
        from grading.admin import RubricCriterionInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(RubricCriterionInline, inline_classes)

    def test_actions_exist(self):
        action_names = ['activate_rubrics', 'deactivate_rubrics', 'duplicate_rubric']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_activate_rubrics_action(self):
        rubric = self.create_rubric()
        GradingRubric.objects.filter(pk=rubric.pk).update(is_active=False)
        qs = GradingRubric.objects.filter(pk=rubric.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.activate_rubrics(request, qs)
        rubric.refresh_from_db()
        self.assertTrue(rubric.is_active)

    def test_get_criteria_count(self):
        rubric = self.create_rubric()
        self.create_rubric_criterion(rubric=rubric)
        count = self.admin.get_criteria_count(rubric)
        self.assertEqual(count, 1)


class RubricCriterionAdminTest(TestDataMixin, TestCase):
    """Test RubricCriterionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = RubricCriterionAdmin(RubricCriterion, self.site)

    def test_list_display(self):
        expected = ('name', 'rubric', 'max_points', 'weight', 'order')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('rubric__course',))

    def test_search_fields(self):
        expected = ('name', 'description', 'rubric__name')
        self.assertEqual(self.admin.search_fields, expected)


class RubricGradeAdminTest(TestDataMixin, TestCase):
    """Test RubricGradeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = RubricGradeAdmin(RubricGrade, self.site)

    def test_list_display(self):
        expected = (
            'student', 'rubric', 'graded_by', 'total_score', 'percentage',
            'get_grade_display', 'graded_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('rubric__course', 'graded_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'graded_at')

    def test_inlines(self):
        from grading.admin import CriterionGradeInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(CriterionGradeInline, inline_classes)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'recalculate_grades'))


class CriterionGradeAdminTest(TestDataMixin, TestCase):
    """Test CriterionGradeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CriterionGradeAdmin(CriterionGrade, self.site)

    def test_list_display(self):
        expected = ('rubric_grade', 'criterion', 'score', 'get_max_points', 'get_percentage')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('criterion__rubric__course',))


class PeerReviewAdminTest(TestDataMixin, TestCase):
    """Test PeerReviewAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = PeerReviewAdmin(PeerReview, self.site)

    def test_list_display(self):
        expected = (
            'reviewer', 'reviewee', 'assignment_name', 'status', 'is_anonymous',
            'score', 'deadline', 'submitted_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'is_anonymous', 'deadline', 'submitted_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'deadline')

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'mark_pending'))
        self.assertTrue(hasattr(self.admin, 'mark_completed'))


class GradeCurveAdminTest(TestDataMixin, TestCase):
    """Test GradeCurveAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = GradeCurveAdmin(GradeCurve, self.site)

    def test_list_display(self):
        expected = (
            'course', 'assignment_name', 'curve_type', 'get_student_count',
            'mean_before', 'mean_after', 'applied_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('curve_type', 'applied_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('course__name', 'assignment_name', 'applied_by__username')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'applied_at')

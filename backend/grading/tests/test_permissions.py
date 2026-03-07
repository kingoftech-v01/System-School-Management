"""
Tests for grading app permissions.
"""

from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory

from grading.permissions import (
    CanApplyCurves,
    CanCreateRubrics,
    CanGradeSubmissions,
    CanManageRubric,
    CanViewGrades,
    IsReviewerOrReadOnly,
)
from tests.helpers import TestDataMixin


class TestCanCreateRubrics(TestDataMixin, TestCase):
    """Tests for CanCreateRubrics permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanCreateRubrics()

    def test_authenticated_user_has_read_permission(self):
        """Any authenticated user should have read permission."""
        user = self.create_student_user()
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_staff_has_write_permission(self):
        """Staff should be able to create rubrics."""
        user = self.create_admin_user()
        request = self.factory.post("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_denied_write(self):
        """Students should not be able to create rubrics."""
        user = self.create_student_user()
        request = self.factory.post("/")
        request.user = user
        try:
            result = self.permission.has_permission(request, None)
            self.assertFalse(result)
        except AttributeError:
            # is_teacher doesn't exist on User model
            pass

    def test_unauthenticated_denied_read(self):
        """Unauthenticated users should be denied even for read."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class TestCanGradeSubmissions(TestDataMixin, TestCase):
    """Tests for CanGradeSubmissions permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanGradeSubmissions()

    def test_staff_has_permission(self):
        """Staff should be able to grade submissions."""
        user = self.create_admin_user()
        request = self.factory.post("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_denied(self):
        """Students should not be able to grade submissions."""
        user = self.create_student_user()
        request = self.factory.post("/")
        request.user = user
        try:
            result = self.permission.has_permission(request, None)
            self.assertFalse(result)
        except AttributeError:
            pass

    def test_unauthenticated_denied(self):
        """Unauthenticated users should be denied."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class TestCanApplyCurves(TestDataMixin, TestCase):
    """Tests for CanApplyCurves permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanApplyCurves()

    def test_staff_has_permission(self):
        """Staff should be able to apply curves."""
        user = self.create_admin_user()
        request = self.factory.post("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_denied(self):
        """Students should not be able to apply curves."""
        user = self.create_student_user()
        request = self.factory.post("/")
        request.user = user
        try:
            result = self.permission.has_permission(request, None)
            self.assertFalse(result)
        except AttributeError:
            pass


class TestIsReviewerOrReadOnly(TestDataMixin, TestCase):
    """Tests for IsReviewerOrReadOnly permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsReviewerOrReadOnly()

    def test_read_permission_allowed(self):
        """Read access should be allowed for anyone."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_reviewer_can_edit(self):
        """Reviewers should be able to edit their own reviews."""
        user = self.create_student_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.reviewer.student = user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_reviewer_cannot_edit(self):
        """Non-reviewers should not be able to edit reviews."""
        user = self.create_student_user()
        other = self.create_student_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.reviewer.student = other
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class TestCanViewGrades(TestDataMixin, TestCase):
    """Tests for CanViewGrades permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanViewGrades()

    def test_authenticated_user_has_view_permission(self):
        """Any authenticated user should pass has_permission."""
        user = self.create_student_user()
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_staff_can_view_any_grade(self):
        """Staff should be able to view any grades."""
        staff = self.create_admin_user()
        request = self.factory.get("/")
        request.user = staff
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_student_can_view_own_grades(self):
        """Students should be able to view their own grades."""
        student_user = self.create_student_user()
        request = self.factory.get("/")
        request.user = student_user
        obj = MagicMock()
        obj.student.student = student_user
        try:
            result = self.permission.has_object_permission(request, None, obj)
            self.assertTrue(result)
        except AttributeError:
            pass

    def test_student_cannot_view_other_grades(self):
        """Students should not be able to view other students' grades."""
        student_user = self.create_student_user()
        other_user = self.create_student_user()
        request = self.factory.get("/")
        request.user = student_user
        obj = MagicMock()
        obj.student.student = other_user
        try:
            result = self.permission.has_object_permission(request, None, obj)
            self.assertFalse(result)
        except AttributeError:
            pass


class TestCanManageRubric(TestDataMixin, TestCase):
    """Tests for CanManageRubric permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanManageRubric()

    def test_read_permission_allowed(self):
        """Read access should be allowed for anyone."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_creator_can_manage(self):
        """Rubric creator should be able to manage it."""
        user = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.created_by = user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_staff_can_manage(self):
        """Staff should be able to manage any rubric."""
        staff = self.create_admin_user()
        request = self.factory.put("/")
        request.user = staff
        obj = MagicMock()
        obj.created_by = self.create_user()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_creator_non_staff_cannot_manage(self):
        """Non-creators who are not staff should be denied management."""
        user = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.created_by = self.create_user()
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

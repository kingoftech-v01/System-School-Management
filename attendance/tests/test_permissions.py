"""
Tests for attendance app permissions.
"""

from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory

from attendance.permissions import IsTeacher
from tests.helpers import TestDataMixin


class TestIsTeacher(TestDataMixin, TestCase):
    """Tests for IsTeacher permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsTeacher()

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should be denied."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))

    def test_lecturer_has_permission(self):
        """Lecturers should have permission."""
        user = self.create_professor_user()
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_staff_has_permission(self):
        """Staff users should have permission."""
        user = self.create_admin_user()
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_denied(self):
        """Students should be denied."""
        user = self.create_student_user()
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_superuser_has_object_permission(self):
        """Superusers should have full object access."""
        user = self.create_admin_user()
        request = self.factory.get("/")
        request.user = user
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_lecturer_can_access_own_object(self):
        """Lecturers can only access objects where obj == user."""
        user = self.create_professor_user()
        request = self.factory.get("/")
        request.user = user
        # Object is the user themselves
        self.assertTrue(self.permission.has_object_permission(request, None, user))

    def test_lecturer_cannot_access_other_object(self):
        """Lecturers cannot access objects belonging to others."""
        user = self.create_professor_user()
        other = self.create_professor_user()
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_object_permission(request, None, other))

    def test_unauthenticated_user_denied_object_permission(self):
        """Unauthenticated users should be denied object permission."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        obj = MagicMock()
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

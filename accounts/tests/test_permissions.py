"""Tests for accounts app DRF permissions."""

from unittest.mock import MagicMock

from django.test import TestCase

from accounts.permissions import (
    IsDirectionUser,
    IsLecturerOrAdmin,
    IsStudentOrAdmin,
    IsOwnerOrAdmin,
    IsLecturerUser,
    IsProfessorUser,
)
from tests.helpers import TestDataMixin


def _make_request(user):
    """Create a mock request with the given user."""
    request = MagicMock()
    request.user = user
    return request


class IsDirectionUserTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsDirectionUser()
        self.view = MagicMock()

    def test_staff_allowed(self):
        user = self.create_user(role='direction', is_staff=True)
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_superuser_allowed(self):
        user = self.create_admin_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_student_denied(self):
        user = self.create_student_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))

    def test_anonymous_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        user.is_staff = False
        user.is_superuser = False
        user.is_direction = False
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))


class IsLecturerOrAdminTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsLecturerOrAdmin()
        self.view = MagicMock()

    def test_lecturer_allowed(self):
        user = self.create_professor_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_staff_allowed(self):
        user = self.create_user(role='direction', is_staff=True)
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_student_denied(self):
        user = self.create_student_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))


class IsStudentOrAdminTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsStudentOrAdmin()
        self.view = MagicMock()

    def test_student_allowed(self):
        user = self.create_student_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_staff_allowed(self):
        user = self.create_user(role='direction', is_staff=True)
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_lecturer_denied(self):
        user = self.create_professor_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))


class IsOwnerOrAdminTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsOwnerOrAdmin()
        self.view = MagicMock()

    def test_admin_always_allowed(self):
        user = self.create_admin_user()
        obj = MagicMock()
        self.assertTrue(
            self.perm.has_object_permission(_make_request(user), self.view, obj)
        )

    def test_owner_allowed_via_user(self):
        user = self.create_student_user()
        obj = MagicMock(spec=['user'])
        obj.user = user
        self.assertTrue(
            self.perm.has_object_permission(_make_request(user), self.view, obj)
        )

    def test_non_owner_denied(self):
        user1 = self.create_student_user()
        user2 = self.create_student_user()
        obj = MagicMock(spec=['user'])
        obj.user = user2
        self.assertFalse(
            self.perm.has_object_permission(_make_request(user1), self.view, obj)
        )

    def test_owner_via_student_student(self):
        user = self.create_student_user()
        student_profile = MagicMock()
        student_profile.student = user
        obj = MagicMock(spec=['student'])
        obj.student = student_profile
        self.assertTrue(
            self.perm.has_object_permission(_make_request(user), self.view, obj)
        )

    def test_no_owner_attr_denied(self):
        user = self.create_student_user()
        obj = MagicMock(spec=[])
        self.assertFalse(
            self.perm.has_object_permission(_make_request(user), self.view, obj)
        )


class IsLecturerUserTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsLecturerUser()
        self.view = MagicMock()

    def test_lecturer_allowed(self):
        user = self.create_professor_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_student_denied(self):
        user = self.create_student_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))


class IsProfessorUserTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsProfessorUser()
        self.view = MagicMock()

    def test_lecturer_allowed(self):
        user = self.create_professor_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_staff_allowed(self):
        user = self.create_user(role='admin', is_staff=True, is_superuser=True)
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_student_denied(self):
        user = self.create_student_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))

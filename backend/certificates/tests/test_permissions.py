"""Tests for certificates app DRF permissions."""

from unittest.mock import MagicMock

from django.test import TestCase

from certificates.permissions import (
    CanIssueCertificates,
    CanVerifyCertificates,
    CanRevokeCertificates,
    IsStudentOrStaffReadOnly,
    CanManageTemplates,
)
from tests.helpers import TestDataMixin


def _make_request(user, method='GET'):
    request = MagicMock()
    request.user = user
    request.method = method
    return request


class CanIssueCertificatesTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = CanIssueCertificates()
        self.view = MagicMock()

    def test_staff_allowed(self):
        user = self.create_user(role='admin', is_staff=True, is_superuser=True)
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_student_denied(self):
        user = self.create_student_user()
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))

    def test_anonymous_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        user.is_staff = False
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))


class CanVerifyCertificatesTest(TestCase):
    def test_anyone_allowed(self):
        perm = CanVerifyCertificates()
        self.assertTrue(perm.has_permission(MagicMock(), MagicMock()))


class CanRevokeCertificatesTest(TestDataMixin, TestCase):
    def test_staff_allowed(self):
        perm = CanRevokeCertificates()
        user = self.create_user(role='admin', is_staff=True, is_superuser=True)
        self.assertTrue(perm.has_permission(_make_request(user), MagicMock()))

    def test_non_staff_denied(self):
        perm = CanRevokeCertificates()
        user = self.create_student_user()
        self.assertFalse(perm.has_permission(_make_request(user), MagicMock()))


class IsStudentOrStaffReadOnlyTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = IsStudentOrStaffReadOnly()
        self.view = MagicMock()

    def test_authenticated_has_permission(self):
        user = self.create_student_user()
        self.assertTrue(self.perm.has_permission(_make_request(user), self.view))

    def test_anonymous_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        self.assertFalse(self.perm.has_permission(_make_request(user), self.view))

    def test_staff_object_permission(self):
        user = self.create_user(role='admin', is_staff=True, is_superuser=True)
        obj = MagicMock()
        self.assertTrue(
            self.perm.has_object_permission(_make_request(user), self.view, obj)
        )

    def test_student_owner_get(self):
        user = self.create_student_user()
        student_profile = MagicMock()
        student_profile.student = user
        obj = MagicMock()
        obj.student = student_profile
        self.assertTrue(
            self.perm.has_object_permission(
                _make_request(user, 'GET'), self.view, obj
            )
        )

    def test_student_non_owner_denied(self):
        user1 = self.create_student_user()
        user2 = self.create_student_user()
        student_profile = MagicMock()
        student_profile.student = user2
        obj = MagicMock()
        obj.student = student_profile
        self.assertFalse(
            self.perm.has_object_permission(
                _make_request(user1, 'GET'), self.view, obj
            )
        )

    def test_student_write_denied(self):
        user = self.create_student_user()
        student_profile = MagicMock()
        student_profile.student = user
        obj = MagicMock()
        obj.student = student_profile
        self.assertFalse(
            self.perm.has_object_permission(
                _make_request(user, 'PUT'), self.view, obj
            )
        )


class CanManageTemplatesTest(TestDataMixin, TestCase):
    def setUp(self):
        self.perm = CanManageTemplates()
        self.view = MagicMock()

    def test_get_allowed_for_anonymous(self):
        user = MagicMock()
        user.is_authenticated = False
        # GET is a safe method
        self.assertTrue(
            self.perm.has_permission(_make_request(user, 'GET'), self.view)
        )

    def test_post_requires_staff(self):
        user = self.create_student_user()
        self.assertFalse(
            self.perm.has_permission(_make_request(user, 'POST'), self.view)
        )

    def test_post_allowed_for_staff(self):
        user = self.create_user(role='admin', is_staff=True, is_superuser=True)
        self.assertTrue(
            self.perm.has_permission(_make_request(user, 'POST'), self.view)
        )

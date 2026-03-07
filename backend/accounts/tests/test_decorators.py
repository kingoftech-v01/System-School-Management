"""Tests for accounts/decorators.py -- expanded for full coverage."""

from unittest.mock import MagicMock, patch
import logging

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
from accounts.decorators import (
    get_user_role,
    role_required,
    tenant_required,
    rate_limit_by_role,
    direction_only,
    financial_only,
    prefet_allowed,
    prefet_only,
    accountant_allowed,
    accountant_only,
    librarian_only,
    registrar_only,
    professor_only,
    student_only,
    parent_only,
    admin_required,
    lecturer_required,
    student_required,
    require_2fa,
)
from tests.helpers import TestDataMixin

User = get_user_model()


def _add_middleware(request):
    """Add session and message middleware to a RequestFactory request."""
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    MessageMiddleware(lambda req: None).process_request(request)
    return request


class AdminRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        self.user = User.objects.create_user(
            username="user", email="user@example.com", password="password"
        )
        self.factory = RequestFactory()

    def admin_view(self, request):
        return HttpResponse("Admin View Content")

    def test_admin_required_decorator_redirects(self):
        decorated_view = admin_required(self.admin_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.user
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_admin_required_decorator_redirects_to_correct_path(self):
        decorated_view = admin_required(function=self.admin_view, redirect_to="/login/")

        request = self.factory.get("restricted-view")
        _add_middleware(request)
        request.user = self.user
        response = decorated_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_admin_required_decorator_does_not_redirect_superuser(self):
        decorated_view = admin_required(self.admin_view)

        request = self.factory.get("/restricted-view")
        request.user = self.superuser
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Admin View Content")

    def test_admin_redirect_decorator_return_correct_response(self):
        decorated_view = admin_required(self.admin_view)

        request = self.factory.get("/restricted-view")
        request.user = self.superuser
        response = decorated_view(request)
        self.assertIsInstance(response, HttpResponse)


class LecturerRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@example.com",
            password="password",
            is_lecturer=True,
            role='professor',
        )
        self.user = User.objects.create_user(
            username="user", email="user@example.com", password="password"
        )
        self.factory = RequestFactory()

    def lecturer_view(self, request):
        return HttpResponse("Lecturer View Content")

    def test_lecturer_required_decorator_redirects(self):
        decorated_view = lecturer_required(self.lecturer_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.user

        response = decorated_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_lecturer_required_decorator_redirects_to_correct_path(self):
        decorated_view = lecturer_required(
            function=self.lecturer_view, redirect_to="/login/"
        )

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.user

        response = decorated_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_lecturer_required_decorator_does_not_redirect_lecturer(self):
        decorated_view = lecturer_required(self.lecturer_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.lecturer

        response = decorated_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Lecturer View Content")

    def test_lecturer_redirect_decorator_return_correct_response(self):
        decorated_view = lecturer_required(self.lecturer_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.lecturer

        response = decorated_view(request)

        self.assertIsInstance(response, HttpResponse)


class StudentRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="password",
            is_student=True,
            role='student',
        )
        self.user = User.objects.create_user(
            username="user", email="user@example.com", password="password",
            role='professor',
        )
        self.factory = RequestFactory()

    def student_view(self, request):
        return HttpResponse("Student View Content")

    def test_student_required_decorator_redirects(self):
        decorated_view = student_required(self.student_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.user

        response = decorated_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_student_required_decorator_redirects_to_correct_path(self):
        decorated_view = student_required(
            function=self.student_view, redirect_to="/login/"
        )

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.user

        response = decorated_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_student_required_decorator_does_not_redirect_student(self):
        decorated_view = student_required(self.student_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.student

        response = decorated_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Student View Content")

    def test_student_redirect_decorator_return_correct_response(self):
        decorated_view = student_required(self.student_view)

        request = self.factory.get("/restricted-view")
        _add_middleware(request)
        request.user = self.student

        response = decorated_view(request)

        self.assertIsInstance(response, HttpResponse)


# -------------------------------------------------------
# New tests for untested decorators
# -------------------------------------------------------

def _dummy_view(request):
    return HttpResponse('OK')


class GetUserRoleTest(TestDataMixin, TestCase):
    def test_role_field(self):
        user = self.create_student_user()
        self.assertEqual(get_user_role(user), 'student')

    def test_superuser_fallback(self):
        user = MagicMock(role=None, is_superuser=True, is_student=False,
                         is_lecturer=False, is_parent=False, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'admin')

    def test_lecturer_fallback(self):
        user = MagicMock(role=None, is_superuser=False, is_student=False,
                         is_lecturer=True, is_parent=False, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'professor')

    def test_parent_fallback(self):
        user = MagicMock(role=None, is_superuser=False, is_student=False,
                         is_lecturer=False, is_parent=True, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'parent')

    def test_dep_head_fallback(self):
        user = MagicMock(role=None, is_superuser=False, is_student=False,
                         is_lecturer=False, is_parent=False, is_dep_head=True)
        self.assertEqual(get_user_role(user), 'direction')

    def test_no_role(self):
        user = MagicMock(role=None, is_superuser=False, is_student=False,
                         is_lecturer=False, is_parent=False, is_dep_head=False)
        self.assertIsNone(get_user_role(user))


class RoleRequiredTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_allowed_role_passes(self):
        decorated = role_required('student')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_wrong_role_redirects(self):
        decorated = role_required('direction')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_superuser_bypasses(self):
        decorated = role_required('direction')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_admin_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_custom_redirect_to(self):
        decorated = role_required('direction', redirect_to='/custom/')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.url, '/custom/')

    def test_multiple_roles(self):
        decorated = role_required('professor', 'direction')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)


class TenantRequiredTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_superuser_bypasses(self):
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_admin_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_no_tenant_redirects(self):
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_student_user()
        request.user = user
        # No tenant attribute
        if hasattr(request, 'tenant'):
            del request.tenant
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_matching_tenant_passes(self):
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        school = self.create_school()
        user = self.create_student_user()
        user.tenant = school
        user.save(update_fields=['tenant'])
        request.user = user
        request.tenant = school
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_mismatched_tenant_forbidden(self):
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        school1 = self.create_school()
        school2 = self.create_school()
        user = self.create_student_user()
        user.tenant = school1
        user.save(update_fields=['tenant'])
        request.user = user
        request.tenant = school2  # Different tenant
        response = decorated(request)
        self.assertEqual(response.status_code, 403)


class ShortcutDecoratorsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_direction_only_allows_direction(self):
        decorated = direction_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_direction_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_direction_only_denies_student(self):
        decorated = direction_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_professor_only_allows_professor(self):
        decorated = professor_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_only_allows_student(self):
        decorated = student_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_parent_only_allows_parent(self):
        decorated = parent_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_user(role='parent', is_parent=True)
        response = decorated(request)
        self.assertEqual(response.status_code, 200)


class Require2FATest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_user_without_2fa_redirected(self):
        decorated = require_2fa(_dummy_view)
        request = self.factory.get('/sensitive/')
        _add_middleware(request)
        user = self.create_professor_user()
        request.user = user
        response = decorated(request)
        # No 2FA configured, should redirect
        self.assertEqual(response.status_code, 302)

    def test_user_with_totp_device_passes(self):
        decorated = require_2fa(_dummy_view)
        request = self.factory.get('/sensitive/')
        _add_middleware(request)
        user = self.create_professor_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request.user = mock_user
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_user_with_mfa_passes(self):
        decorated = require_2fa(_dummy_view)
        request = self.factory.get('/sensitive/')
        _add_middleware(request)
        user = self.create_professor_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_mfa = MagicMock()
        mock_mfa.exists.return_value = True
        mock_user.mfa = mock_mfa
        request.user = mock_user
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_user_without_totp_or_mfa_redirected(self):
        """User with no TOTP and no MFA should be redirected."""
        decorated = require_2fa(_dummy_view)
        request = self.factory.get('/sensitive/')
        _add_middleware(request)
        user = self.create_student_user()
        request.user = user
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


# ============================================================================
# Extended shortcut decorator tests
# ============================================================================

class FinancialOnlyTest(TestDataMixin, TestCase):
    """Tests for financial_only decorator (direction/admin + 2FA)."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_direction_with_2fa_passes(self):
        decorated = financial_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_direction_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.is_superuser = False
        mock_user.role = 'direction'
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request.user = mock_user
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_with_2fa_passes(self):
        decorated = financial_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_admin_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.is_superuser = True
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request.user = mock_user
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = financial_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_direction_without_2fa_redirected(self):
        decorated = financial_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_direction_user()
        request.user = user
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class PrefetAllowedTest(TestDataMixin, TestCase):
    """Tests for prefet_allowed decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_prefet_passes(self):
        decorated = prefet_allowed(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_prefet_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_secretary_passes(self):
        decorated = prefet_allowed(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_secretary_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = prefet_allowed(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class PrefetOnlyTest(TestDataMixin, TestCase):
    """Tests for prefet_only decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_prefet_passes(self):
        decorated = prefet_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_prefet_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_direction_passes(self):
        decorated = prefet_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_direction_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_professor_denied(self):
        decorated = prefet_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class AccountantAllowedTest(TestDataMixin, TestCase):
    """Tests for accountant_allowed decorator (direction/admin/accountant + 2FA)."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_accountant_with_2fa_passes(self):
        decorated = accountant_allowed(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_accountant_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.is_superuser = False
        mock_user.role = 'accountant'
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request.user = mock_user
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = accountant_allowed(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class AccountantOnlyTest(TestDataMixin, TestCase):
    """Tests for accountant_only decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_accountant_passes(self):
        decorated = accountant_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_accountant_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = accountant_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class LibrarianOnlyTest(TestDataMixin, TestCase):
    """Tests for librarian_only decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_librarian_passes(self):
        decorated = librarian_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_librarian_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_secretary_passes(self):
        decorated = librarian_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_secretary_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = librarian_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


class RegistrarOnlyTest(TestDataMixin, TestCase):
    """Tests for registrar_only decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_registrar_passes(self):
        decorated = registrar_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_registrar_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_student_denied(self):
        decorated = registrar_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)


# ============================================================================
# TenantRequired -- extended tests
# ============================================================================

class TenantRequiredExtendedTest(TestDataMixin, TestCase):
    """Extended tests for tenant_required decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_user_with_no_tenant_attribute_passes(self):
        """User without a .tenant field passes if request has a tenant."""
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        user = self.create_student_user()
        # user.tenant is None by default
        request.user = user
        school = self.create_school()
        request.tenant = school
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_superuser_cross_tenant_logs_warning(self):
        """Superuser accessing a different tenant should log a warning."""
        decorated = tenant_required(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        school1 = self.create_school()
        school2 = self.create_school()
        user = self.create_admin_user()
        user.tenant = school1
        user.save(update_fields=['tenant'])
        request.user = user
        request.tenant = school2
        with self.assertLogs('accounts.decorators', level='WARNING') as cm:
            response = decorated(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('CROSS-TENANT' in m for m in cm.output))


# ============================================================================
# RateLimitByRole tests
# ============================================================================

class RateLimitByRoleTest(TestDataMixin, TestCase):
    """Tests for rate_limit_by_role decorator."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(RATE_LIMITS={'student': '200/h'})
    def test_rate_limit_applies(self):
        decorated = rate_limit_by_role(group='test', rate='100/h')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_default_rate(self):
        decorated = rate_limit_by_role(group='default')(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)


# ============================================================================
# GetUserRole -- extended is_student fallback
# ============================================================================

class GetUserRoleExtendedTest(TestDataMixin, TestCase):
    """Extended tests for get_user_role covering is_student fallback."""

    def test_is_student_fallback(self):
        """When role is None/empty but is_student=True, returns 'student'."""
        user = MagicMock(role='', is_superuser=False, is_student=True,
                         is_lecturer=False, is_parent=False, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'student')

    def test_is_lecturer_fallback(self):
        user = MagicMock(role='', is_superuser=False, is_student=False,
                         is_lecturer=True, is_parent=False, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'professor')

    def test_role_field_preferred_over_boolean(self):
        """Role field takes priority over boolean flags."""
        user = MagicMock(role='direction', is_superuser=False, is_student=True,
                         is_lecturer=False, is_parent=False, is_dep_head=False)
        self.assertEqual(get_user_role(user), 'direction')


# ============================================================================
# Role-specific shortcut decorator denials
# ============================================================================

class ShortcutDecoratorsExtendedTest(TestDataMixin, TestCase):
    """Additional tests for shortcut decorators."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_direction_only_allows_secretary(self):
        decorated = direction_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_secretary_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_direction_only_allows_admin(self):
        decorated = direction_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_admin_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 200)

    def test_professor_only_denies_student(self):
        decorated = professor_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_student_only_denies_professor(self):
        decorated = student_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_parent_only_denies_professor(self):
        decorated = parent_only(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)

    def test_lecturer_required_no_function(self):
        """lecturer_required without function argument returns a decorator."""
        decorator = lecturer_required(redirect_to='/custom/')
        decorated = decorator(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/')

    def test_student_required_no_function(self):
        """student_required without function argument returns a decorator."""
        decorator = student_required(redirect_to='/custom/')
        decorated = decorator(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_professor_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/')

    def test_admin_required_no_function(self):
        """admin_required without function argument returns a decorator."""
        decorator = admin_required(redirect_to='/custom/')
        decorated = decorator(_dummy_view)
        request = self.factory.get('/test/')
        _add_middleware(request)
        request.user = self.create_student_user()
        response = decorated(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/custom/')

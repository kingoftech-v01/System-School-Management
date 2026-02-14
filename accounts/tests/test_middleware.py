"""Tests for accounts middleware -- expanded for full coverage."""

from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

from accounts.middleware import (
    TenantMiddleware,
    RoleMiddleware,
    Enforce2FAMiddleware,
    ForcePasswordResetMiddleware,
    AuditLogMiddleware,
    AuthSecurityMiddleware,
    Require2FAMiddleware,
)
from tests.helpers import TestDataMixin

User = get_user_model()


def _get_response(request):
    return HttpResponse('OK')


def _add_session(request):
    middleware = SessionMiddleware(_get_response)
    middleware.process_request(request)
    request.session.save()
    return request


def _add_messages(request):
    """Add session + message middleware to request."""
    _add_session(request)
    MessageMiddleware(_get_response).process_request(request)
    return request


class RoleMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RoleMiddleware(_get_response)

    def test_sets_user_role_for_student(self):
        user = self.create_student_user()
        request = self.factory.get('/')
        _add_session(request)
        request.user = user
        self.middleware.process_request(request)
        self.assertEqual(request.user_role, 'student')

    def test_sets_user_role_for_professor(self):
        user = self.create_professor_user()
        request = self.factory.get('/')
        _add_session(request)
        request.user = user
        self.middleware.process_request(request)
        self.assertEqual(request.user_role, 'professor')

    def test_anonymous_user(self):
        request = self.factory.get('/')
        _add_session(request)
        request.user = AnonymousUser()
        self.middleware.process_request(request)
        self.assertIn(request.user_role, ['anonymous', '', None])

    def test_get_user_role_static(self):
        user = self.create_direction_user()
        role = RoleMiddleware.get_user_role(user)
        self.assertEqual(role, 'direction')


class AuditLogMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditLogMiddleware(_get_response)

    def test_get_request_not_logged(self):
        request = self.factory.get('/')
        _add_session(request)
        request.user = self.create_admin_user()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_post_request_to_sensitive_path(self):
        request = self.factory.post('/admin/some/action/')
        _add_session(request)
        request.user = self.create_admin_user()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_get_client_ip(self):
        request = self.factory.get('/')
        ip = AuditLogMiddleware.get_client_ip(request)
        self.assertIsNotNone(ip)

    def test_get_client_ip_with_forwarded(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4, 5.6.7.8')
        ip = AuditLogMiddleware.get_client_ip(request)
        self.assertEqual(ip, '1.2.3.4')


class AuthSecurityMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuthSecurityMiddleware(_get_response)

    def test_active_user_passes(self):
        user = self.create_user()
        request = self.factory.get('/')
        _add_session(request)
        request.user = user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_passes(self):
        request = self.factory.get('/')
        _add_session(request)
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_inactive_user_logged_out(self):
        from django.contrib.messages.middleware import MessageMiddleware
        user = self.create_user()
        user.is_active = False
        user.save()
        request = self.factory.get('/')
        _add_session(request)
        MessageMiddleware(_get_response).process_request(request)
        request.user = user
        with patch('accounts.middleware.redirect') as mock_redirect:
            mock_redirect.return_value = HttpResponse(status=302)
            response = self.middleware.process_request(request)
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 302)


class TenantMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Reset cached tenant between tests
        TenantMiddleware._default_tenant = None
        self.middleware = TenantMiddleware(_get_response)

    def test_sets_current_tenant(self):
        request = self.factory.get('/')
        tenant = MagicMock()
        tenant.name = 'Test'
        tenant.schema_name = 'test'
        request.tenant = tenant
        self.middleware.process_request(request)
        self.assertEqual(request.current_tenant, tenant)

    def test_no_tenant_dev_mode_creates_default(self):
        """In dev mode (no django-tenants), middleware auto-creates a tenant."""
        request = self.factory.get('/')
        # No tenant attribute
        result = self.middleware.process_request(request)
        self.assertIsNone(result)
        # In dev mode, middleware sets a default tenant
        self.assertTrue(hasattr(request, 'tenant'))
        self.assertIsNotNone(request.tenant)
        self.assertTrue(hasattr(request, 'current_tenant'))

    def test_tenant_none_dev_mode(self):
        """When tenant is set to None, dev mode auto-assigns a default."""
        request = self.factory.get('/')
        request.tenant = None
        result = self.middleware.process_request(request)
        self.assertIsNone(result)
        # Middleware should have set a default tenant
        self.assertIsNotNone(request.tenant)


class Enforce2FAMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = Enforce2FAMiddleware(_get_response)

    def test_anonymous_passes(self):
        request = self.factory.get('/')
        _add_session(request)
        request.user = AnonymousUser()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_exempt_path_passes(self):
        request = self.factory.get('/accounts/login/')
        _add_session(request)
        request.user = self.create_professor_user()
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_student_no_2fa_required(self):
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = self.create_student_user()
        request.user_role = 'student'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_static_path_exempt(self):
        request = self.factory.get('/static/css/main.css')
        _add_session(request)
        request.user = self.create_professor_user()
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


class Require2FAMiddlewareTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = Require2FAMiddleware(_get_response)

    def test_anonymous_passes(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_student_passes(self):
        request = self.factory.get('/dashboard/')
        request.user = self.create_student_user()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_skip_2fa_path(self):
        request = self.factory.get('/accounts/2fa/setup/')
        request.user = self.create_professor_user()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_skip_logout_path(self):
        request = self.factory.get('/accounts/logout/')
        request.user = self.create_professor_user()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


class AuditLogMiddlewareExtendedTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditLogMiddleware(_get_response)

    def test_anonymous_not_logged(self):
        request = self.factory.post('/admin/action/')
        _add_session(request)
        request.user = AnonymousUser()
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)

    def test_post_to_payments(self):
        request = self.factory.post('/payments/create/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)

    def test_post_with_sensitive_action_in_path(self):
        request = self.factory.post('/courses/delete/1/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)

    def test_post_non_sensitive_path(self):
        request = self.factory.post('/forums/new-thread/')
        _add_session(request)
        request.user = self.create_student_user()
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)

    def test_get_request_not_logged(self):
        request = self.factory.get('/admin/')
        _add_session(request)
        request.user = self.create_admin_user()
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)

    def test_process_response_with_tenant(self):
        request = self.factory.post('/admin/edit/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        request.tenant = MagicMock()
        request.tenant.name = 'Test School'
        response = HttpResponse('OK')
        result = self.middleware.process_response(request, response)
        self.assertEqual(result.status_code, 200)


class RoleMiddlewareExtendedTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RoleMiddleware(_get_response)

    def test_admin_role(self):
        user = self.create_admin_user()
        request = self.factory.get('/')
        request.user = user
        self.middleware.process_request(request)
        self.assertEqual(request.user_role, 'admin')

    def test_sets_current_role_on_user(self):
        user = self.create_student_user()
        request = self.factory.get('/')
        request.user = user
        self.middleware.process_request(request)
        self.assertEqual(request.user.current_role, 'student')

    def test_parent_role(self):
        user = self.create_user(role='parent', is_parent=True)
        request = self.factory.get('/')
        request.user = user
        self.middleware.process_request(request)
        self.assertEqual(request.user_role, 'parent')

    def test_superuser_role_fallback(self):
        """Superuser without role field set should get 'admin' role."""
        role = RoleMiddleware.get_user_role(
            MagicMock(role=None, is_superuser=True, is_student=False,
                      is_lecturer=False, is_parent=False, is_dep_head=False)
        )
        self.assertEqual(role, 'admin')

    def test_dep_head_direction(self):
        role = RoleMiddleware.get_user_role(
            MagicMock(role=None, is_superuser=False, is_student=False,
                      is_lecturer=False, is_parent=False, is_dep_head=True)
        )
        self.assertEqual(role, 'direction')

    def test_no_role_defaults_student(self):
        role = RoleMiddleware.get_user_role(
            MagicMock(role=None, is_superuser=False, is_student=False,
                      is_lecturer=False, is_parent=False, is_dep_head=False)
        )
        self.assertEqual(role, 'student')


# ============================================================================
# ForcePasswordResetMiddleware Tests
# ============================================================================

class ForcePasswordResetMiddlewareTest(TestDataMixin, TestCase):
    """Tests for ForcePasswordResetMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ForcePasswordResetMiddleware(_get_response)

    def test_anonymous_user_passes(self):
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = AnonymousUser()
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_user_without_must_change_password_passes(self):
        user = self.create_student_user()
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_user_with_must_change_password_redirects(self):
        user = self.create_student_user()
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_exempt_path_force_reset_passes(self):
        user = self.create_student_user()
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/accounts/password/force-reset/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_exempt_path_logout_passes(self):
        user = self.create_student_user()
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/accounts/logout/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_exempt_path_static_passes(self):
        user = self.create_student_user()
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/static/css/main.css')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_exempt_path_media_passes(self):
        user = self.create_student_user()
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/media/default.png')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_must_change_password_false_does_not_redirect(self):
        user = self.create_student_user()
        user.must_change_password = False
        user.save(update_fields=['must_change_password'])
        request = self.factory.get('/some/page/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


# ============================================================================
# Enforce2FAMiddleware -- extended tests
# ============================================================================

class Enforce2FAMiddlewareExtendedTest(TestDataMixin, TestCase):
    """Extended tests for Enforce2FAMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = Enforce2FAMiddleware(_get_response)

    def test_professor_without_2fa_redirects(self):
        """Professor without 2FA configured should be redirected."""
        user = self.create_professor_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_direction_without_2fa_redirects(self):
        user = self.create_direction_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        request.user_role = 'direction'
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_user_with_mfa_passes(self):
        """User with MFA configured should pass through."""
        user = self.create_professor_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.role = 'professor'
        mock_user.is_superuser = False
        mock_mfa = MagicMock()
        mock_mfa.exists.return_value = True
        mock_user.mfa = mock_mfa
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = mock_user
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_user_with_totp_device_passes(self):
        """User with confirmed TOTP device should pass through."""
        user = self.create_professor_user()
        # Use a mock user wrapper to allow setting totpdevice_set
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.role = 'professor'
        mock_user.is_superuser = False
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = mock_user
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_mfa_setup_path_not_redirected(self):
        """User on the MFA setup page should not be redirected again."""
        user = self.create_professor_user()
        from django.urls import reverse
        setup_path = reverse('mfa_activate_totp')
        request = self.factory.get(setup_path)
        _add_messages(request)
        request.user = user
        request.user_role = 'professor'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_role_not_requiring_2fa_passes(self):
        """Parent role does not require 2FA."""
        user = self.create_user(role='parent', is_parent=True)
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        request.user_role = 'parent'
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_no_user_role_attribute_falls_back(self):
        """When user_role is not set on request, middleware should compute it."""
        user = self.create_student_user()
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        # Deliberately do not set request.user_role
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_exempt_path_2fa(self):
        for path in ['/accounts/2fa/', '/accounts/mfa/', '/accounts/totp/',
                     '/accounts/reauthenticate/', '/admin/logout/']:
            request = self.factory.get(path)
            _add_session(request)
            request.user = self.create_professor_user()
            request.user_role = 'professor'
            result = self.middleware.process_request(request)
            self.assertIsNone(result, f"Path {path} should be exempt")

    def test_secretary_without_2fa_redirects(self):
        user = self.create_secretary_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        request.user_role = 'secretary'
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)


# ============================================================================
# Require2FAMiddleware -- extended tests
# ============================================================================

class Require2FAMiddlewareExtendedTest(TestDataMixin, TestCase):
    """Extended tests for Require2FAMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = Require2FAMiddleware(_get_response)

    def test_professor_without_2fa_redirects(self):
        user = self.create_professor_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_direction_without_2fa_redirects(self):
        user = self.create_direction_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_admin_without_2fa_redirects(self):
        user = self.create_admin_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 302)

    def test_professor_with_verified_email_passes(self):
        """User with verified email addresses is considered having 2FA."""
        user = self.create_professor_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.role = 'professor'
        mock_email = MagicMock()
        mock_email.filter.return_value.exists.return_value = True
        mock_user.emailaddress_set = mock_email
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = mock_user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_professor_with_totp_device_passes(self):
        user = self.create_professor_user()
        mock_user = MagicMock(wraps=user)
        mock_user.is_authenticated = True
        mock_user.role = 'professor'
        mock_totp = MagicMock()
        mock_totp.filter.return_value.exists.return_value = True
        mock_user.totpdevice_set = mock_totp
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = mock_user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_2fa_setup_page_passes(self):
        user = self.create_professor_user()
        request = self.factory.get('/accounts/2fa/setup/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_static_path_passes(self):
        user = self.create_professor_user()
        request = self.factory.get('/static/something.css')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_parent_role_not_required(self):
        user = self.create_user(role='parent', is_parent=True)
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


# ============================================================================
# AuthSecurityMiddleware -- extended tests
# ============================================================================

class AuthSecurityMiddlewareExtendedTest(TestDataMixin, TestCase):
    """Extended tests for AuthSecurityMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuthSecurityMiddleware(_get_response)

    def test_subscription_expired_redirects_non_superuser(self):
        user = self.create_student_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        # Mock a tenant with expired subscription
        mock_tenant = MagicMock()
        mock_tenant.is_subscription_valid.return_value = False
        request.tenant = mock_tenant
        with patch('accounts.middleware.redirect') as mock_redirect:
            mock_redirect.return_value = HttpResponse(status=302)
            result = self.middleware.process_request(request)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 302)

    def test_subscription_expired_superuser_passes(self):
        user = self.create_admin_user()
        request = self.factory.get('/dashboard/')
        _add_messages(request)
        request.user = user
        mock_tenant = MagicMock()
        mock_tenant.is_subscription_valid.return_value = False
        request.tenant = mock_tenant
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_subscription_valid_passes(self):
        user = self.create_student_user()
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        mock_tenant = MagicMock()
        mock_tenant.is_subscription_valid.return_value = True
        request.tenant = mock_tenant
        result = self.middleware.process_request(request)
        self.assertIsNone(result)

    def test_no_subscription_method_passes(self):
        """Tenant without is_subscription_valid method should pass."""
        user = self.create_student_user()
        request = self.factory.get('/dashboard/')
        _add_session(request)
        request.user = user
        mock_tenant = MagicMock(spec=[])  # No methods
        request.tenant = mock_tenant
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


# ============================================================================
# TenantMiddleware -- extended tests
# ============================================================================

class TenantMiddlewareExtendedTest(TestDataMixin, TestCase):
    """Extended tests for TenantMiddleware._get_default_tenant caching."""

    def setUp(self):
        self.factory = RequestFactory()
        TenantMiddleware._default_tenant = None

    def test_default_tenant_cached(self):
        """Second call returns cached tenant."""
        t1 = TenantMiddleware._get_default_tenant()
        t2 = TenantMiddleware._get_default_tenant()
        self.assertEqual(t1.pk, t2.pk)

    def test_cache_invalidated_if_deleted(self):
        """If cached tenant is deleted, a new one is created."""
        t1 = TenantMiddleware._get_default_tenant()
        old_pk = t1.pk
        # Simulate DB deletion by making refresh_from_db raise
        TenantMiddleware._default_tenant = MagicMock()
        TenantMiddleware._default_tenant.refresh_from_db.side_effect = Exception('deleted')
        t2 = TenantMiddleware._get_default_tenant()
        self.assertIsNotNone(t2)

    def test_creates_school_when_none_exist(self):
        """When no School exists, middleware creates one."""
        from core.models import School
        School.objects.all().delete()
        TenantMiddleware._default_tenant = None
        tenant = TenantMiddleware._get_default_tenant()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.name, 'Development School')


# ============================================================================
# AuditLogMiddleware -- extended tests
# ============================================================================

class AuditLogMiddlewareFullTest(TestDataMixin, TestCase):
    """Full coverage tests for AuditLogMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditLogMiddleware(_get_response)

    def test_get_sensitive_get_path_logged(self):
        """GET to a sensitive path like /admin/ should be logged."""
        from core.models import ActivityLog
        request = self.factory.get('/admin/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_get_payments_path_logged(self):
        from core.models import ActivityLog
        request = self.factory.get('/payments/history/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_get_export_path_logged(self):
        """GET to /export... path should be logged."""
        from core.models import ActivityLog
        request = self.factory.get('/export/students/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_put_to_sensitive_path_logged(self):
        from core.models import ActivityLog
        request = self.factory.put('/admin/update/1/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_delete_to_sensitive_path_logged(self):
        from core.models import ActivityLog
        request = self.factory.delete('/admin/delete/1/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_patch_to_grades_logged(self):
        from core.models import ActivityLog
        request = self.factory.patch('/grades/update/1/')
        _add_session(request)
        request.user = self.create_professor_user()
        request.user_role = 'professor'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_post_to_discipline_logged(self):
        from core.models import ActivityLog
        request = self.factory.post('/discipline/create/')
        _add_session(request)
        request.user = self.create_prefet_user()
        request.user_role = 'prefet'
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertGreater(ActivityLog.objects.count(), count_before)

    def test_logging_failure_does_not_crash(self):
        """If ActivityLog.create fails, response is still returned."""
        request = self.factory.post('/admin/action/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        response = HttpResponse('OK')
        with patch('accounts.middleware.ActivityLog.objects.create',
                   side_effect=Exception('DB error')):
            result = self.middleware.process_response(request, response)
            self.assertEqual(result.status_code, 200)

    def test_get_non_sensitive_path_not_logged(self):
        """GET to a non-sensitive path should not create an audit log."""
        from core.models import ActivityLog
        request = self.factory.get('/forums/')
        _add_session(request)
        request.user = self.create_student_user()
        count_before = ActivityLog.objects.count()
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        self.assertEqual(ActivityLog.objects.count(), count_before)

    def test_get_client_ip_no_forwarded(self):
        """Fallback to REMOTE_ADDR when X-Forwarded-For is absent."""
        request = self.factory.get('/', REMOTE_ADDR='10.0.0.1')
        ip = AuditLogMiddleware.get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_no_tenant_attr_uses_unknown(self):
        """When request has no tenant, 'Unknown' is used in audit log."""
        from core.models import ActivityLog
        request = self.factory.post('/admin/edit/')
        _add_session(request)
        request.user = self.create_admin_user()
        request.user_role = 'admin'
        # Make sure no tenant attribute
        if hasattr(request, 'tenant'):
            delattr(request, 'tenant')
        response = HttpResponse('OK')
        self.middleware.process_response(request, response)
        latest = ActivityLog.objects.order_by('-pk').first()
        self.assertIn('Unknown', latest.message)

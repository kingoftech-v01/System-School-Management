"""Tests for accounts middleware."""

from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

from accounts.middleware import (
    TenantMiddleware,
    RoleMiddleware,
    Enforce2FAMiddleware,
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

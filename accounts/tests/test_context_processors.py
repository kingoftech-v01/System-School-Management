"""Tests for accounts context processors."""

from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from accounts.context_processors import (
    tenant_context,
    user_role_context,
    app_settings_context,
    navigation_context,
    permissions_context,
)
from tests.helpers import TestDataMixin

User = get_user_model()


class UserRoleContextTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _get_request(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_student_role(self):
        user = self.create_student_user()
        ctx = user_role_context(self._get_request(user))
        self.assertEqual(ctx['user_role'], 'student')
        self.assertTrue(ctx['is_student'])
        self.assertFalse(ctx['is_professor'])

    def test_professor_role(self):
        user = self.create_professor_user()
        ctx = user_role_context(self._get_request(user))
        self.assertEqual(ctx['user_role'], 'professor')
        self.assertTrue(ctx['is_professor'])
        self.assertFalse(ctx['is_student'])

    def test_direction_role(self):
        user = self.create_direction_user()
        ctx = user_role_context(self._get_request(user))
        self.assertEqual(ctx['user_role'], 'direction')
        self.assertTrue(ctx['is_direction'])

    def test_anonymous_user(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = user_role_context(request)
        self.assertFalse(ctx.get('is_student', False))
        self.assertFalse(ctx.get('is_professor', False))


class AppSettingsContextTest(TestCase):
    def test_returns_site_name(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        ctx = app_settings_context(request)
        self.assertIn('SITE_NAME', ctx)

    def test_returns_debug(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        ctx = app_settings_context(request)
        self.assertIn('DEBUG', ctx)


class PermissionsContextTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_admin_gets_all_permissions(self):
        user = self.create_admin_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'admin'  # Set by RoleMiddleware normally
        ctx = permissions_context(request)
        self.assertTrue(ctx.get('can_manage_payments', False))
        self.assertTrue(ctx.get('can_export_data', False))

    def test_student_limited_permissions(self):
        user = self.create_student_user()
        request = self.factory.get('/')
        request.user = user
        ctx = permissions_context(request)
        self.assertFalse(ctx.get('can_manage_payments', False))

    def test_anonymous_no_permissions(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = permissions_context(request)
        self.assertFalse(ctx.get('can_manage_payments', False))

    def test_direction_full_access(self):
        user = self.create_direction_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'direction'
        ctx = permissions_context(request)
        self.assertTrue(ctx['can_view_all_students'])
        self.assertTrue(ctx['can_manage_enrollment'])
        self.assertTrue(ctx['can_view_monitoring'])
        self.assertTrue(ctx['can_manage_discipline'])
        self.assertTrue(ctx['can_export_data'])

    def test_professor_limited_permissions(self):
        user = self.create_professor_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'professor'
        ctx = permissions_context(request)
        self.assertFalse(ctx['can_view_monitoring'])
        self.assertTrue(ctx['can_manage_discipline'])


class TenantContextTest(TestCase):
    def test_with_tenant(self):
        request = MagicMock()
        tenant = MagicMock()
        tenant.name = 'Test School'
        tenant.logo = None
        tenant.primary_color = '#333'
        request.tenant = tenant
        ctx = tenant_context(request)
        self.assertEqual(ctx['tenant_name'], 'Test School')
        self.assertIsNone(ctx['tenant_logo'])
        self.assertEqual(ctx['school_name'], 'Test School')
        self.assertEqual(ctx['school'], tenant)

    def test_with_tenant_logo(self):
        request = MagicMock()
        tenant = MagicMock()
        tenant.name = 'School'
        tenant.logo.url = '/media/logo.png'
        tenant.logo.__bool__ = lambda self: True
        tenant.primary_color = '#fff'
        request.tenant = tenant
        ctx = tenant_context(request)
        self.assertEqual(ctx['tenant_logo'], '/media/logo.png')

    def test_without_tenant(self):
        request = MagicMock(spec=[])
        ctx = tenant_context(request)
        self.assertEqual(ctx, {})

    def test_tenant_is_none(self):
        request = MagicMock()
        request.tenant = None
        ctx = tenant_context(request)
        self.assertEqual(ctx, {})


class NavigationContextTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_unauthenticated_empty(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = navigation_context(request)
        self.assertEqual(ctx['navigation'], [])

    def test_student_nav(self):
        user = self.create_student_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'student'
        ctx = navigation_context(request)
        urls = [item['url'] for item in ctx['navigation']]
        self.assertIn('/dashboard/', urls)
        self.assertIn('/courses/', urls)
        self.assertIn('/payments/my/', urls)

    def test_professor_nav(self):
        user = self.create_professor_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'professor'
        ctx = navigation_context(request)
        urls = [item['url'] for item in ctx['navigation']]
        self.assertIn('/dashboard/', urls)

    def test_direction_nav(self):
        user = self.create_direction_user()
        user.is_superuser = False
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'direction'
        ctx = navigation_context(request)
        urls = [item['url'] for item in ctx['navigation']]
        self.assertIn('/monitoring/', urls)
        self.assertIn('/enrollment/', urls)

    def test_parent_nav(self):
        user = self.create_user(role='parent', is_parent=True)
        user.is_superuser = False
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'parent'
        ctx = navigation_context(request)
        urls = [item['url'] for item in ctx['navigation']]
        self.assertIn('/dashboard/', urls)

    def test_superuser_gets_admin_link(self):
        user = self.create_admin_user()
        request = self.factory.get('/')
        request.user = user
        request.user_role = 'admin'
        ctx = navigation_context(request)
        urls = [item['url'] for item in ctx['navigation']]
        self.assertIn('/admin/', urls)

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from accounts.decorators import (
    get_user_role,
    role_required,
    tenant_required,
    rate_limit_by_role,
    direction_only,
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

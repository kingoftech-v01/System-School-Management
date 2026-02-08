"""
Shared test helpers and factory mixin for all test files.

Usage:
    from tests.helpers import TestDataMixin

    class MyTest(TestDataMixin, TestCase):
        def test_something(self):
            school = self.create_school()
            user = self.create_user(role='student')
"""

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory

from core.models import School, Session, Semester

USE_TENANTS = 'django_tenants' in settings.INSTALLED_APPS
User = get_user_model()

# Counter for unique values
_counter = 0


def _next_counter():
    global _counter
    _counter += 1
    return _counter


class TestDataMixin:
    """Mixin providing factory methods for test data creation."""

    @classmethod
    def _school_kwargs(cls, **overrides):
        """Build School creation kwargs that work in both dev and production."""
        n = _next_counter()
        kwargs = {
            'name': f'Test School {n}',
            'slug': f'test-school-{n}',
            'email': f'test{n}@school.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'postal_code': '12345',
            'license_key': f'TEST-KEY-{n:04d}',
            'subscription_start': date.today(),
            'subscription_end': date.today() + timedelta(days=365),
        }
        if USE_TENANTS:
            kwargs['schema_name'] = f'test_school_{n}'
        kwargs.update(overrides)
        return kwargs

    def create_school(self, **overrides):
        """Create and return a School instance."""
        return School.objects.create(**self._school_kwargs(**overrides))

    def create_user(self, role='student', **overrides):
        """Create and return a User instance with the given role."""
        n = _next_counter()
        defaults = {
            'username': f'testuser{n}',
            'email': f'testuser{n}@example.com',
            'password': 'TestPass123!@#',
            'first_name': 'Test',
            'last_name': f'User{n}',
            'role': role,
        }
        # Map role to legacy boolean flags
        if role == 'student':
            defaults['is_student'] = True
        elif role == 'professor':
            defaults['is_lecturer'] = True
        elif role == 'parent':
            defaults['is_parent'] = True
        elif role == 'admin':
            defaults['is_superuser'] = True
            defaults['is_staff'] = True

        defaults.update(overrides)
        password = defaults.pop('password')
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user

    def create_student_user(self, **overrides):
        """Create a user with student role."""
        return self.create_user(role='student', is_student=True, **overrides)

    def create_professor_user(self, **overrides):
        """Create a user with professor/lecturer role."""
        return self.create_user(role='professor', is_lecturer=True, **overrides)

    def create_direction_user(self, **overrides):
        """Create a user with direction role."""
        return self.create_user(role='direction', **overrides)

    def create_admin_user(self, **overrides):
        """Create a superuser."""
        return self.create_user(
            role='admin', is_superuser=True, is_staff=True, **overrides
        )

    def create_program(self, **overrides):
        """Create and return a Program instance."""
        from course.models import Program
        n = _next_counter()
        defaults = {
            'title': f'Test Program {n}',
            'summary': f'Summary for test program {n}',
        }
        defaults.update(overrides)
        return Program.objects.create(**defaults)

    def create_course(self, program=None, **overrides):
        """Create and return a Course instance."""
        from course.models import Course
        if program is None:
            program = self.create_program()
        n = _next_counter()
        defaults = {
            'title': f'Test Course {n}',
            'code': f'TC{n:04d}',
            'credit': 3,
            'summary': f'Summary for test course {n}',
            'program': program,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        }
        defaults.update(overrides)
        return Course.objects.create(**defaults)

    def create_session(self, **overrides):
        """Create and return a Session instance."""
        n = _next_counter()
        defaults = {
            'session': f'2024/2025-{n}',
            'is_current_session': True,
        }
        defaults.update(overrides)
        return Session.objects.create(**defaults)

    def create_semester(self, session=None, **overrides):
        """Create and return a Semester instance."""
        if session is None:
            session = self.create_session()
        defaults = {
            'semester': 'First',
            'is_current_semester': True,
            'session': session,
        }
        defaults.update(overrides)
        return Semester.objects.create(**defaults)

    def create_student_profile(self, user=None, program=None, **overrides):
        """Create and return an accounts.Student profile."""
        from accounts.models import Student
        if user is None:
            user = self.create_student_user()
        if program is None:
            program = self.create_program()
        defaults = {
            'student': user,
            'level': 'Bachelor',
            'program': program,
        }
        defaults.update(overrides)
        return Student.objects.create(**defaults)

    def create_filiere(self, tenant=None, **overrides):
        """Create and return a Filiere instance."""
        from filieres.models import Filiere
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'name': f'Test Filiere {n}',
            'code': f'TF{n:04d}',
            'level': 'Bachelor',
            'duration_years': 3,
        }
        defaults.update(overrides)
        return Filiere.objects.create(**defaults)

    def create_registration(self, tenant=None, **overrides):
        """Create and return an enrollment RegistrationForm instance."""
        from enrollment.models import RegistrationForm
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'student_name': f'Student {n}',
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'email': f'student{n}@test.com',
            'phone': '+1234567890',
            'address': '123 Test St',
            'parent_name': f'Parent {n}',
            'parent_email': f'parent{n}@test.com',
            'parent_phone': '+0987654321',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        defaults.update(overrides)
        return RegistrationForm.objects.create(**defaults)

    def create_invoice(self, user=None, **overrides):
        """Create and return a payments Invoice instance."""
        from payments.models import Invoice
        if user is None:
            user = self.create_user(role='direction')
        n = _next_counter()
        defaults = {
            'user': user,
            'total': 1000.0,
            'amount': 1000.0,
            'invoice_code': f'INV-{n:06d}',
        }
        defaults.update(overrides)
        return Invoice.objects.create(**defaults)

    def _ensure_session(self, **overrides):
        """Ensure a current Session exists and return it."""
        try:
            existing = Session.objects.filter(is_current_session=True).first()
            if existing:
                return existing
        except Exception:
            pass
        return self.create_session(**overrides)

    def _ensure_semester(self, session=None, **overrides):
        """Ensure a current Semester exists and return it."""
        try:
            existing = Semester.objects.filter(is_current_semester=True).first()
            if existing:
                return existing
        except Exception:
            pass
        if session is None:
            session = self._ensure_session()
        return self.create_semester(session=session, **overrides)

    @staticmethod
    def add_middleware(request):
        """Add session and message middleware to a RequestFactory request."""
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda req: None).process_request(request)
        return request

    @staticmethod
    def get_request_factory():
        """Return a RequestFactory instance."""
        return RequestFactory()

"""
Project-level pytest conftest.py with shared fixtures.
"""

import pytest
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core.models import School, Session, Semester

USE_TENANTS = 'django_tenants' in settings.INSTALLED_APPS
User = get_user_model()


def _school_kwargs(**overrides):
    kwargs = {
        'name': 'Fixture School',
        'slug': 'fixture-school',
        'email': 'fixture@school.com',
        'phone': '1234567890',
        'address': '123 Fixture St',
        'city': 'Fixture City',
        'postal_code': '12345',
        'license_key': 'FIXTURE-KEY-001',
        'subscription_start': date.today(),
        'subscription_end': date.today() + timedelta(days=365),
    }
    if USE_TENANTS:
        kwargs['schema_name'] = 'fixture_school'
    kwargs.update(overrides)
    return kwargs


@pytest.fixture
def school(db):
    return School.objects.create(**_school_kwargs())


@pytest.fixture
def session(db):
    return Session.objects.create(
        session='2024/2025',
        is_current_session=True,
    )


@pytest.fixture
def semester(db, session):
    return Semester.objects.create(
        semester='First',
        is_current_semester=True,
        session=session,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin_fixture',
        email='admin@fixture.com',
        password='TestPass123!@#',
    )


@pytest.fixture
def student_user(db):
    user = User(
        username='student_fixture',
        email='student@fixture.com',
        first_name='Student',
        last_name='Fixture',
        role='student',
        is_student=True,
    )
    user.set_password('TestPass123!@#')
    user.save()
    return user


@pytest.fixture
def professor_user(db):
    user = User(
        username='professor_fixture',
        email='professor@fixture.com',
        first_name='Professor',
        last_name='Fixture',
        role='professor',
        is_lecturer=True,
    )
    user.set_password('TestPass123!@#')
    user.save()
    return user


@pytest.fixture
def program(db):
    from course.models import Program
    return Program.objects.create(
        title='Fixture Program',
        summary='A fixture program for tests',
    )


@pytest.fixture
def course(db, program):
    from course.models import Course
    return Course.objects.create(
        title='Fixture Course',
        code='FC001',
        credit=3,
        summary='A fixture course',
        program=program,
        level='bachelor',
        year=1,
        semester='fall',
    )


@pytest.fixture
def request_factory():
    return RequestFactory()

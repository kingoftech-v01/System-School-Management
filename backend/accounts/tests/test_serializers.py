"""Tests for accounts app serializers."""

from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.serializers import (
    UserSerializer,
    UserCreateSerializer,
    StudentSerializer,
    LecturerSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
)
from accounts.models import Student
from tests.helpers import TestDataMixin

User = get_user_model()


class UserSerializerTest(TestDataMixin, TestCase):
    def test_serializes_user(self):
        user = self.create_user(first_name='John', last_name='Doe', role='direction')
        serializer = UserSerializer(user)
        data = serializer.data
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')

    def test_full_name_field(self):
        user = self.create_user(first_name='John', last_name='Doe', role='direction')
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data['full_name'], 'John Doe')

    def test_includes_role(self):
        user = self.create_user(role='direction')
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data['role'], 'direction')


class UserCreateSerializerTest(TestDataMixin, TestCase):
    def test_valid_creation(self):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'TestPass123!@#',
            'password_confirm': 'TestPass123!@#',
            'first_name': 'New',
            'last_name': 'User',
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'TestPass123!@#',
            'password_confirm': 'Different123!@#',
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class StudentSerializerTest(TestDataMixin, TestCase):
    def test_serializes_student(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        serializer = StudentSerializer(student)
        data = serializer.data
        self.assertEqual(data['level'], 'Bachelor')


class LecturerSerializerTest(TestDataMixin, TestCase):
    def test_serializes_lecturer(self):
        user = self.create_professor_user()
        serializer = LecturerSerializer(user)
        data = serializer.data
        self.assertTrue(data['is_lecturer'])


class ProfileSerializerTest(TestDataMixin, TestCase):
    def _mock_request(self, user):
        return type('Request', (), {'user': user})()

    def test_valid_update(self):
        user = self.create_user(role='direction')
        serializer = ProfileSerializer(
            instance=user,
            data={'first_name': 'Updated', 'last_name': 'Name', 'email': 'upd@test.com'},
            partial=True,
            context={'request': self._mock_request(user)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_email_uniqueness(self):
        existing = self.create_user(email='taken_ser@test.com', role='direction')
        user = self.create_user(role='direction')
        serializer = ProfileSerializer(
            instance=user,
            data={'email': 'taken_ser@test.com'},
            partial=True,
            context={'request': self._mock_request(user)},
        )
        self.assertFalse(serializer.is_valid())


class ChangePasswordSerializerTest(TestDataMixin, TestCase):
    def test_password_mismatch(self):
        user = self.create_user(role='direction')
        serializer = ChangePasswordSerializer(
            data={
                'old_password': 'TestPass123!@#',
                'new_password': 'NewPass123!@#',
                'new_password_confirm': 'Different123!@#',
            },
            context={'request': type('obj', (object,), {'user': user})()},
        )
        self.assertFalse(serializer.is_valid())

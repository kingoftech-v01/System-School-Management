"""Tests for accounts app forms."""

from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.forms import (
    StaffAddForm,
    StudentAddForm,
    ProfileUpdateForm,
    ParentAddForm,
)
from tests.helpers import TestDataMixin

User = get_user_model()


class StaffAddFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = StaffAddForm(data={
            'username': 'newlecturer',
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'address': '123 St',
            'phone': '1234567890',
            'email': 'lecturer@test.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_sets_is_lecturer(self):
        form = StaffAddForm(data={
            'username': 'newlec2',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'gender': 'F',
            'address': '456 St',
            'phone': '0987654321',
            'email': 'jane@test.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_lecturer)

    def test_password_mismatch(self):
        form = StaffAddForm(data={
            'username': 'mismatch',
            'address': '123 St',
            'phone': '111',
            'password1': 'TestPass123!@#',
            'password2': 'DifferentPass456!@#',
        })
        self.assertFalse(form.is_valid())

    def test_missing_required_fields(self):
        form = StaffAddForm(data={})
        self.assertFalse(form.is_valid())
        # first_name, last_name, gender, email are required
        self.assertTrue(len(form.errors) > 0)


class StudentAddFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        program = self.create_program()
        form = StudentAddForm(data={
            'username': 'newstudent',
            'first_name': 'Student',
            'last_name': 'Test',
            'gender': 'M',
            'address': '123 Student St',
            'phone': '1234567890',
            'email': 'student@test.com',
            'level': 'Bachelor',
            'program': program.pk,
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_sets_is_student(self):
        program = self.create_program()
        form = StudentAddForm(data={
            'username': 'newstd2',
            'first_name': 'Test',
            'last_name': 'Std',
            'gender': 'M',
            'address': '456 St',
            'phone': '111',
            'email': 'std2@test.com',
            'level': 'Bachelor',
            'program': program.pk,
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_student)

    def test_save_creates_student_profile(self):
        from accounts.models import Student
        program = self.create_program()
        form = StudentAddForm(data={
            'username': 'newstd3',
            'first_name': 'New',
            'last_name': 'Student',
            'gender': 'F',
            'address': '789 St',
            'phone': '222',
            'email': 'newstd3@test.com',
            'level': 'Bachelor',
            'program': program.pk,
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(Student.objects.filter(student=user).exists())


class ProfileUpdateFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        user = self.create_user(role='direction')
        form = ProfileUpdateForm(data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': user.email,
            'gender': 'M',
            'phone': '1234567890',
            'address': '123 Test St',
        }, instance=user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_update_email(self):
        user = self.create_user(role='direction')
        form = ProfileUpdateForm(data={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': 'updated@test.com',
            'gender': 'M',
            'phone': '111',
            'address': '123 St',
        }, instance=user)
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.email, 'updated@test.com')


class ParentAddFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        form = ParentAddForm(data={
            'username': 'newparent',
            'first_name': 'Parent',
            'last_name': 'User',
            'email': 'parent@test.com',
            'address': '123 Parent St',
            'phone': '0987654321',
            'student': student.pk,
            'relation_ship': 'Father',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_sets_is_parent(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        form = ParentAddForm(data={
            'username': 'newparent2',
            'first_name': 'Parent2',
            'last_name': 'User2',
            'email': 'parent2@test.com',
            'address': '456 St',
            'phone': '333',
            'student': student.pk,
            'relation_ship': 'Mother',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_parent)

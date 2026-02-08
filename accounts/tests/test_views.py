"""Tests for accounts app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tests.helpers import TestDataMixin

User = get_user_model()


class RegisterViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_get(self):
        response = self.client.get(reverse('frontend:accounts:register'))
        self.assertIn(response.status_code, [200, 302])

    def test_register_post_valid(self):
        program = self.create_program()
        response = self.client.post(reverse('frontend:accounts:register'), {
            'username': 'newreg',
            'first_name': 'New',
            'last_name': 'Reg',
            'gender': 'M',
            'address': '123 St',
            'phone': '111',
            'email': 'newreg@test.com',
            'level': 'Bachelor',
            'program': program.pk,
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#',
        })
        self.assertIn(response.status_code, [200, 302])


class ValidateUsernameViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()

    def test_username_available(self):
        response = self.client.get(
            reverse('frontend:accounts:validate_username'),
            {'username': 'notexist'}
        )
        self.assertEqual(response.status_code, 200)

    def test_username_taken(self):
        self.create_user(role='direction', username='takenuser')
        response = self.client.get(
            reverse('frontend:accounts:validate_username'),
            {'username': 'takenuser'}
        )
        self.assertEqual(response.status_code, 200)


class ProfileViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = self.create_admin_user()
        self.client.force_login(self.user)

    def test_profile_get(self):
        response = self.client.get(reverse('frontend:accounts:profile'))
        self.assertIn(response.status_code, [200, 302])

    def test_profile_update_get(self):
        response = self.client.get(reverse('frontend:accounts:edit_profile'))
        self.assertIn(response.status_code, [200, 302])


class AdminPanelViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_admin_panel(self):
        response = self.client.get(reverse('frontend:accounts:admin_panel'))
        self.assertIn(response.status_code, [200, 302])


class StaffViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_staff_add_get(self):
        response = self.client.get(reverse('frontend:accounts:add_lecturer'))
        self.assertIn(response.status_code, [200, 302])

    def test_lecturer_list(self):
        response = self.client.get(reverse('frontend:accounts:lecturer_list'))
        self.assertIn(response.status_code, [200, 302])

    def test_delete_staff(self):
        lecturer = self.create_professor_user()
        response = self.client.post(
            reverse('frontend:accounts:lecturer_delete', args=[lecturer.pk])
        )
        self.assertIn(response.status_code, [200, 302])


class StudentViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_student_add_get(self):
        response = self.client.get(reverse('frontend:accounts:add_student'))
        self.assertIn(response.status_code, [200, 302])

    def test_student_list(self):
        response = self.client.get(reverse('frontend:accounts:student_list'))
        self.assertIn(response.status_code, [200, 302])

    def test_delete_student(self):
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(student_user)
        response = self.client.post(
            reverse('frontend:accounts:student_delete', args=[student_profile.pk])
        )
        self.assertIn(response.status_code, [200, 302])


class PasswordChangeViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = self.create_user(role='direction', password='TestPass123!@#')
        self.client.force_login(self.user)

    def test_change_password_get(self):
        response = self.client.get(reverse('frontend:accounts:change_password'))
        self.assertIn(response.status_code, [200, 302])


class ErrorHandlerViewsTest(TestCase):
    def test_404_handler(self):
        response = self.client.get('/nonexistent-url-path-xyz/')
        self.assertEqual(response.status_code, 404)

"""Tests for course app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse

from course.models import Program, Course, CourseAllocation
from tests.helpers import TestDataMixin


class ProgramViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_program_list(self):
        response = self.client.get(reverse('frontend:course:programs'))
        self.assertEqual(response.status_code, 200)

    def test_program_add_get(self):
        response = self.client.get(reverse('frontend:course:add_program'))
        self.assertEqual(response.status_code, 200)

    def test_program_add_post(self):
        response = self.client.post(reverse('frontend:course:add_program'), {
            'title': 'New Program',
            'summary': 'A new program',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_program_detail(self):
        program = self.create_program()
        response = self.client.get(
            reverse('frontend:course:program_detail', args=[program.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_program_edit_get(self):
        program = self.create_program()
        response = self.client.get(
            reverse('frontend:course:edit_program', args=[program.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_program_delete(self):
        program = self.create_program()
        response = self.client.post(
            reverse('frontend:course:program_delete', args=[program.pk])
        )
        self.assertIn(response.status_code, [200, 302])


class CourseViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_course_detail(self):
        course = self.create_course()
        response = self.client.get(
            reverse('frontend:course:course_detail', args=[course.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_course_add_get(self):
        program = self.create_program()
        response = self.client.get(
            reverse('frontend:course:course_add', args=[program.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_course_add_post(self):
        program = self.create_program()
        response = self.client.post(
            reverse('frontend:course:course_add', args=[program.pk]), {
                'title': 'New Course',
                'code': 'NC001',
                'credit': 3,
                'program': program.pk,
                'level': 'bachelor',
                'year': 1,
                'semester': 'fall',
            }
        )
        self.assertIn(response.status_code, [200, 302])

    def test_course_login_required(self):
        self.client.logout()
        course = self.create_course()
        response = self.client.get(
            reverse('frontend:course:course_detail', args=[course.slug])
        )
        self.assertEqual(response.status_code, 302)


class CourseAllocationViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_allocation_form_get(self):
        response = self.client.get(reverse('frontend:course:course_allocation'))
        self.assertEqual(response.status_code, 200)

    def test_allocation_list(self):
        response = self.client.get(reverse('frontend:course:course_allocation_view'))
        self.assertEqual(response.status_code, 200)


class CourseRegistrationViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.student = self.create_student_user()
        self.create_student_profile(self.student)
        self.client.force_login(self.student)

    def test_course_registration_get(self):
        response = self.client.get(reverse('frontend:course:course_registration'))
        self.assertEqual(response.status_code, 200)

    def test_user_course_list(self):
        response = self.client.get(reverse('frontend:course:user_course_list'))
        self.assertEqual(response.status_code, 200)

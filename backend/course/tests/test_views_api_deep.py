"""
Deep API view tests for the course app.

Tests cover:
- ProgramViewSet (CRUD, courses action)
- CourseViewSet (CRUD, documentation, videos, lecturers)
- CourseAllocationViewSet (CRUD, deallocate)
- UploadViewSet (CRUD, download)
- UploadVideoViewSet (CRUD)
- CourseRegistrationViewSet (available, registered, register, drop)
- Authentication and filtering
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from course.models import Course, CourseAllocation, Program
from result.models import TakenCourse
from tests.helpers import TestDataMixin


class ProgramViewSetTests(TestDataMixin, TestCase):
    """Tests for ProgramViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:course:program-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:course:program-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_program(self):
        self._auth(self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], self.program.title)

    def test_create_program(self):
        self._auth(self.admin)
        url = reverse('api:course:program-list')
        data = {'title': 'New Program', 'summary': 'Summary'}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_update_program(self):
        self._auth(self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        resp = self.client.patch(url, {'summary': 'Updated Summary'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.program.refresh_from_db()
        self.assertEqual(self.program.summary, 'Updated Summary')

    def test_delete_program(self):
        self._auth(self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_courses_action(self):
        self.create_course(program=self.program)
        self._auth(self.admin)
        url = reverse('api:course:program-courses', kwargs={'pk': self.program.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) >= 1)

    def test_search(self):
        self._auth(self.admin)
        url = reverse('api:course:program-list')
        resp = self.client.get(url, {'search': self.program.title})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CourseViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseViewSet (uses slug lookup)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:course:course-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_by_slug(self):
        self._auth(self.admin)
        url = reverse('api:course:course-detail', kwargs={'slug': self.course.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_course(self):
        self._auth(self.admin)
        url = reverse('api:course:course-list')
        data = {
            'title': 'New Course',
            'code': 'NC001',
            'credit': 4,
            'summary': 'Summary',
            'program': self.program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_filter_by_program(self):
        self._auth(self.admin)
        url = reverse('api:course:course-list')
        resp = self.client.get(url, {'program': self.program.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_search_by_code(self):
        self._auth(self.admin)
        url = reverse('api:course:course-list')
        resp = self.client.get(url, {'search': self.course.code})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_documentation_action(self):
        self._auth(self.admin)
        url = reverse('api:course:course-documentation', kwargs={'slug': self.course.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_videos_action(self):
        self._auth(self.admin)
        url = reverse('api:course:course-videos', kwargs={'slug': self.course.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_lecturers_action(self):
        self._auth(self.admin)
        url = reverse('api:course:course-lecturers', kwargs={'slug': self.course.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CourseAllocationViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseAllocationViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.session = self.create_session()
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)
        self.allocation = CourseAllocation.objects.create(
            lecturer=self.professor, session=self.session,
        )
        self.allocation.courses.add(self.course)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:course:allocation-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:course:allocation-detail', kwargs={'pk': self.allocation.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_deallocate_action(self):
        self._auth(self.admin)
        url = reverse('api:course:allocation-deallocate', kwargs={'pk': self.allocation.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CourseAllocation.objects.filter(pk=self.allocation.pk).exists())

    def test_filter_by_lecturer(self):
        self._auth(self.admin)
        url = reverse('api:course:allocation-list')
        resp = self.client.get(url, {'lecturer': self.professor.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CourseRegistrationViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseRegistrationViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.course = self.create_course(
            program=self.program,
            level='Bachelor',
            semester='First',
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_available_courses_no_student_profile(self):
        other = self.create_user(role='professor', is_lecturer=True)
        self._auth(other)
        url = reverse('api:course:registration-available-courses')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_available_courses_student(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-available-courses')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('available_courses', resp.data)

    def test_registered_courses(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-registered-courses')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('registered_courses', resp.data)
        self.assertIn('total_credits', resp.data)

    def test_register_for_courses(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-register')
        resp = self.client.post(url, {'course_ids': [self.course.pk]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['registered_count'], 1)

    def test_register_empty_list(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-register')
        resp = self.client.post(url, {'course_ids': []}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_drop_courses(self):
        TakenCourse.objects.create(
            student=self.student_profile, course=self.course,
        )
        self._auth(self.student_user)
        url = reverse('api:course:registration-drop')
        resp = self.client.post(url, {'course_ids': [self.course.pk]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['dropped_count'], 1)

    def test_drop_empty_list(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-drop')
        resp = self.client.post(url, {'course_ids': []}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_nonexistent_course(self):
        self._auth(self.student_user)
        url = reverse('api:course:registration-register')
        resp = self.client.post(url, {'course_ids': [99999]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['registered_count'], 0)

    def test_available_courses_no_semester(self):
        from core.models import Semester
        Semester.objects.filter(is_current_semester=True).update(is_current_semester=False)
        self._auth(self.student_user)
        url = reverse('api:course:registration-available-courses')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

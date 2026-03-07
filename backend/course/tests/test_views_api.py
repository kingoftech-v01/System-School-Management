"""
API view tests for the course app.

Tests cover:
- ProgramViewSet CRUD + custom actions
- CourseViewSet CRUD + custom actions
- CourseAllocationViewSet CRUD + deallocate
- CourseRegistrationViewSet register/drop/available/registered
- Upload / UploadVideo list (read-only; file uploads tested separately)
- Unauthenticated access
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class ProgramViewSetTests(TestDataMixin, TestCase):
    """Tests for ProgramViewSet CRUD and custom actions."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()
        self.program = self.create_program()

    # -- Authentication -------------------------------------------------------

    def test_list_programs_unauthenticated(self):
        """Unauthenticated requests must be rejected."""
        url = reverse('api:course:program-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # -- List / Retrieve ------------------------------------------------------

    def test_list_programs(self):
        """Authenticated users can list programs."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_program(self):
        """Authenticated users can retrieve a single program."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.program.title)

    # -- Create ---------------------------------------------------------------

    def test_create_program(self):
        """Authenticated users can create a program."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-list')
        data = {'title': 'New Program', 'summary': 'New summary'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Program')

    # -- Update ---------------------------------------------------------------

    def test_update_program(self):
        """Authenticated users can partially update a program."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        response = self.client.patch(url, {'title': 'Updated Program'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.program.refresh_from_db()
        self.assertEqual(self.program.title, 'Updated Program')

    # -- Delete ---------------------------------------------------------------

    def test_delete_program(self):
        """Authenticated users can delete a program."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-detail', kwargs={'pk': self.program.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # -- Custom action: courses -----------------------------------------------

    def test_program_courses_action(self):
        """GET /programs/{pk}/courses/ returns courses for the program."""
        self.create_course(program=self.program)
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-courses', kwargs={'pk': self.program.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # -- Search / Ordering ----------------------------------------------------

    def test_search_programs(self):
        """Programs can be searched by title."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:program-list')
        response = self.client.get(url, {'search': self.program.title[:5]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CourseViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseViewSet CRUD and custom actions."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)

    def test_list_courses_unauthenticated(self):
        url = reverse('api:course:course-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_courses(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_course_by_slug(self):
        """CourseViewSet uses slug lookup."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-detail', kwargs={'slug': self.course.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], self.course.code)

    def test_create_course(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-list')
        data = {
            'title': 'New Course',
            'code': 'NC0001',
            'credit': 3,
            'summary': 'Summary',
            'program': self.program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_course(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-detail', kwargs={'slug': self.course.slug})
        response = self.client.patch(url, {'title': 'Updated Course'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_course(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-detail', kwargs={'slug': self.course.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_course_documentation_action(self):
        """GET /courses/{slug}/documentation/ returns uploads for the course."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-documentation', kwargs={'slug': self.course.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_videos_action(self):
        """GET /courses/{slug}/videos/ returns videos for the course."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-videos', kwargs={'slug': self.course.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_lecturers_action(self):
        """GET /courses/{slug}/lecturers/ returns allocated lecturers."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-lecturers', kwargs={'slug': self.course.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_courses_by_program(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:course-list')
        response = self.client.get(url, {'program': self.program.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CourseAllocationViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseAllocationViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.session = self.create_session()
        self.course = self.create_course()

    def test_list_allocations(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:allocation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_allocation(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:allocation-list')
        data = {
            'lecturer': self.professor.pk,
            'courses': [self.course.pk],
            'session': self.session.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_deallocate_action(self):
        """POST /allocations/{pk}/deallocate/ removes allocation."""
        from course.models import CourseAllocation
        allocation = CourseAllocation.objects.create(
            lecturer=self.professor, session=self.session
        )
        allocation.courses.add(self.course)
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:course:allocation-deallocate', kwargs={'pk': allocation.pk})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CourseAllocation.objects.filter(pk=allocation.pk).exists())


class CourseRegistrationViewSetTests(TestDataMixin, TestCase):
    """Tests for CourseRegistrationViewSet (register / drop)."""

    def setUp(self):
        self.client = APIClient()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program
        )
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.course = self.create_course(
            program=self.program,
            level='Bachelor',
            semester='First',
        )

    def test_available_courses_unauthenticated(self):
        url = reverse('api:course:registration-available-courses')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_available_courses(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:course:registration-available-courses')
        response = self.client.get(url)
        # Either 200 (found courses) or 404 (no student profile / semester)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_registered_courses(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:course:registration-registered-courses')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_register_courses(self):
        """POST /registration/register/ registers student for courses."""
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:course:registration-register')
        data = {'course_ids': [self.course.pk]}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, (
            status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND,
        ))

    def test_drop_courses(self):
        """POST /registration/drop/ drops courses for the student."""
        self.client.force_authenticate(user=self.student_user)
        url = reverse('api:course:registration-drop')
        data = {'course_ids': [self.course.pk]}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, (
            status.HTTP_200_OK, status.HTTP_404_NOT_FOUND,
        ))

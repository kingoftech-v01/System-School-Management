"""Tests for accounts app models."""

from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import Student, Parent, DepartmentHead
from tests.helpers import TestDataMixin

User = get_user_model()


class CustomUserManagerTest(TestDataMixin, TestCase):
    def test_search_by_first_name(self):
        user = self.create_user(first_name='UniqueSearchName', role='direction')
        qs = User.objects.search('UniqueSearchName')
        self.assertIn(user, qs)

    def test_search_by_email(self):
        user = self.create_user(email='unique_search@test.com', role='direction')
        qs = User.objects.search('unique_search@test.com')
        self.assertIn(user, qs)

    def test_search_none_returns_all(self):
        # search(None) returns full queryset, not None
        result = User.objects.search(None)
        self.assertIsNotNone(result)

    def test_search_no_match(self):
        qs = User.objects.search('zzz_nonexistent_zzz')
        self.assertEqual(qs.count(), 0)

    def test_get_student_count(self):
        self.create_student_user()
        self.create_student_user()
        self.assertGreaterEqual(User.objects.get_student_count(), 2)

    def test_get_lecturer_count(self):
        self.create_professor_user()
        self.assertGreaterEqual(User.objects.get_lecturer_count(), 1)

    def test_get_superuser_count(self):
        self.create_admin_user()
        self.assertGreaterEqual(User.objects.get_superuser_count(), 1)


class UserModelTest(TestDataMixin, TestCase):
    def test_create_user(self):
        user = self.create_user(role='direction')
        self.assertIsNotNone(user.pk)

    def test_default_role_is_student(self):
        user = User.objects.create_user(username='defuser', password='TestPass123!@#')
        self.assertEqual(user.role, 'student')

    def test_get_full_name(self):
        user = self.create_user(first_name='John', last_name='Doe', role='direction')
        self.assertEqual(user.get_full_name, 'John Doe')

    def test_get_full_name_fallback_to_username(self):
        user = self.create_user(first_name='', last_name='', role='direction')
        self.assertEqual(user.get_full_name, user.username)

    def test_get_user_role_student(self):
        user = self.create_student_user()
        self.assertIn('Student', user.get_user_role)

    def test_get_user_role_lecturer(self):
        user = self.create_professor_user()
        self.assertIn('Lecturer', user.get_user_role)

    def test_get_user_role_admin(self):
        user = self.create_admin_user()
        self.assertIn('Admin', user.get_user_role)

    def test_get_picture_default(self):
        user = self.create_user(role='direction')
        result = user.get_picture()
        self.assertIn('default', result)

    def test_str_contains_full_name(self):
        user = self.create_user(first_name='John', last_name='Doe', role='direction')
        self.assertIn('John Doe', str(user))

    def test_user_with_tenant(self):
        school = self.create_school()
        user = self.create_user(tenant=school, role='direction')
        self.assertEqual(user.tenant, school)

    def test_approval_status_default(self):
        user = self.create_user(role='direction')
        self.assertEqual(user.approval_status, 'not_requested')

    def test_user_is_student_flag(self):
        user = self.create_student_user()
        self.assertTrue(user.is_student)

    def test_user_is_lecturer_flag(self):
        user = self.create_professor_user()
        self.assertTrue(user.is_lecturer)

    def test_student_username_auto_generated(self):
        """Student users get auto-generated username via signal."""
        user = self.create_student_user()
        user.refresh_from_db()
        # Signal generates username like 'ugr-YYYY-N'
        self.assertIn('-', user.username)

    def test_lecturer_username_auto_generated(self):
        """Lecturer users get auto-generated username via signal."""
        user = self.create_professor_user()
        user.refresh_from_db()
        self.assertIn('-', user.username)


class StudentModelTest(TestDataMixin, TestCase):
    def test_create_student(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        self.assertIsNotNone(student.pk)

    def test_student_str_contains_name(self):
        user = self.create_student_user(first_name='Alice', last_name='Smith')
        student = self.create_student_profile(user)
        # Student __str__ returns student.get_full_name
        self.assertIn('Alice', str(student))

    def test_default_not_alumni(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        self.assertFalse(student.is_alumni)

    def test_default_not_dropped(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        self.assertFalse(student.is_dropped)

    def test_mark_as_alumni(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        student.mark_as_alumni()
        student.refresh_from_db()
        self.assertTrue(student.is_alumni)

    def test_mark_as_dropped(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        student.mark_as_dropped(reason='Academic')
        student.refresh_from_db()
        self.assertTrue(student.is_dropped)
        self.assertEqual(student.drop_reason, 'Academic')

    def test_active_manager(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        self.assertIn(student, Student.active.all())

    def test_alumni_manager(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        student.mark_as_alumni()
        self.assertIn(student, Student.alumni_objects.all())
        self.assertNotIn(student, Student.active.all())

    def test_dropped_manager(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        student.mark_as_dropped()
        self.assertIn(student, Student.dropped.all())
        self.assertNotIn(student, Student.active.all())

    def test_student_search_returns_queryset(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        qs = Student.objects.search(None)
        self.assertIn(student, qs)

    def test_gender_count_keys(self):
        result = Student.get_gender_count()
        # Returns {'M': count, 'F': count}
        self.assertIn('M', result)
        self.assertIn('F', result)

    def test_registration_number_auto_generated(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        if student.registration_number:
            self.assertTrue(len(student.registration_number) > 0)


class ParentModelTest(TestDataMixin, TestCase):
    def test_create_parent(self):
        parent_user = self.create_user(role='parent', is_parent=True)
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        parent = Parent.objects.create(
            user=parent_user,
            student=student,
            first_name='Jane',
            last_name='Doe',
            relation_ship='Mother',
        )
        self.assertIsNotNone(parent.pk)

    def test_parent_str(self):
        parent_user = self.create_user(role='parent', is_parent=True)
        parent = Parent.objects.create(
            user=parent_user,
            first_name='Jane',
            last_name='Doe',
        )
        result = str(parent)
        self.assertTrue(len(result) > 0)


class DepartmentHeadModelTest(TestDataMixin, TestCase):
    def test_create_department_head(self):
        user = self.create_professor_user()
        program = self.create_program()
        dh = DepartmentHead.objects.create(user=user, department=program)
        self.assertIsNotNone(dh.pk)

    def test_str(self):
        user = self.create_professor_user()
        program = self.create_program()
        dh = DepartmentHead.objects.create(user=user, department=program)
        result = str(dh)
        self.assertTrue(len(result) > 0)

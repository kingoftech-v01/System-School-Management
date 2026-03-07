"""Tests for School_System/roles.py - role permission definitions."""

from django.test import TestCase

from School_System.roles import (
    Student, Parent, Professor, Direction,
    Secretary, Librarian, Registrar, Admin,
)
from tests.helpers import TestDataMixin


class StudentRoleTest(TestDataMixin, TestCase):
    """Tests for the Student role permissions."""

    def test_student_has_view_own_courses(self):
        self.assertIn('view_own_courses', Student.available_permissions)

    def test_student_has_view_own_grades(self):
        self.assertIn('view_own_grades', Student.available_permissions)

    def test_student_has_take_quizzes(self):
        self.assertIn('take_quizzes', Student.available_permissions)

    def test_student_has_make_payments(self):
        self.assertIn('make_payments', Student.available_permissions)

    def test_student_has_borrow_books(self):
        self.assertIn('borrow_books', Student.available_permissions)

    def test_student_cannot_grade_students(self):
        self.assertNotIn('grade_students', Student.available_permissions)

    def test_student_cannot_manage_departments(self):
        self.assertNotIn('manage_departments', Student.available_permissions)


class ParentRoleTest(TestDataMixin, TestCase):
    """Tests for the Parent role permissions."""

    def test_parent_has_view_child_grades(self):
        self.assertIn('view_child_grades', Parent.available_permissions)

    def test_parent_has_view_child_attendance(self):
        self.assertIn('view_child_attendance', Parent.available_permissions)

    def test_parent_has_make_payments_for_child(self):
        self.assertIn('make_payments_for_child', Parent.available_permissions)

    def test_parent_cannot_grade_students(self):
        self.assertNotIn('grade_students', Parent.available_permissions)


class ProfessorRoleTest(TestDataMixin, TestCase):
    """Tests for the Professor role permissions."""

    def test_professor_has_grade_students(self):
        self.assertIn('grade_students', Professor.available_permissions)

    def test_professor_has_mark_attendance(self):
        self.assertIn('mark_attendance', Professor.available_permissions)

    def test_professor_has_create_quizzes(self):
        self.assertIn('create_quizzes', Professor.available_permissions)

    def test_professor_has_upload_course_materials(self):
        self.assertIn('upload_course_materials', Professor.available_permissions)

    def test_professor_cannot_manage_departments(self):
        self.assertNotIn('manage_departments', Professor.available_permissions)

    def test_professor_cannot_verify_payments(self):
        self.assertNotIn('verify_payments', Professor.available_permissions)


class DirectionRoleTest(TestDataMixin, TestCase):
    """Tests for the Direction role permissions."""

    def test_direction_has_manage_departments(self):
        self.assertIn('manage_departments', Direction.available_permissions)

    def test_direction_has_approve_registrations(self):
        self.assertIn('approve_registrations', Direction.available_permissions)

    def test_direction_has_verify_payments(self):
        self.assertIn('verify_payments', Direction.available_permissions)

    def test_direction_has_generate_financial_reports(self):
        self.assertIn('generate_financial_reports', Direction.available_permissions)

    def test_direction_has_manage_alumni(self):
        self.assertIn('manage_alumni', Direction.available_permissions)

    def test_direction_has_manage_events(self):
        self.assertIn('manage_events', Direction.available_permissions)


class SecretaryRoleTest(TestDataMixin, TestCase):
    """Tests for the Secretary role permissions."""

    def test_secretary_has_manage_departments(self):
        self.assertIn('manage_departments', Secretary.available_permissions)

    def test_secretary_has_approve_registrations(self):
        self.assertIn('approve_registrations', Secretary.available_permissions)

    def test_secretary_lacks_generate_financial_reports(self):
        """Secretary should NOT have generate_financial_reports."""
        self.assertNotIn('generate_financial_reports', Secretary.available_permissions)

    def test_secretary_has_manage_enrollments(self):
        self.assertIn('manage_enrollments', Secretary.available_permissions)

    def test_secretary_has_manage_alumni(self):
        self.assertIn('manage_alumni', Secretary.available_permissions)


class LibrarianRoleTest(TestDataMixin, TestCase):
    """Tests for the Librarian role permissions."""

    def test_librarian_has_manage_library(self):
        self.assertIn('manage_library', Librarian.available_permissions)

    def test_librarian_has_manage_books(self):
        self.assertIn('manage_books', Librarian.available_permissions)

    def test_librarian_has_view_overdue_books(self):
        self.assertIn('view_overdue_books', Librarian.available_permissions)

    def test_librarian_cannot_manage_departments(self):
        self.assertNotIn('manage_departments', Librarian.available_permissions)

    def test_librarian_cannot_grade_students(self):
        self.assertNotIn('grade_students', Librarian.available_permissions)


class RegistrarRoleTest(TestDataMixin, TestCase):
    """Tests for the Registrar role permissions."""

    def test_registrar_has_manage_enrollments(self):
        self.assertIn('manage_enrollments', Registrar.available_permissions)

    def test_registrar_has_manage_certificates(self):
        self.assertIn('manage_certificates', Registrar.available_permissions)

    def test_registrar_has_verify_documents(self):
        self.assertIn('verify_documents', Registrar.available_permissions)

    def test_registrar_has_batch_generate_certificates(self):
        self.assertIn('batch_generate_certificates', Registrar.available_permissions)

    def test_registrar_cannot_manage_departments(self):
        self.assertNotIn('manage_departments', Registrar.available_permissions)


class AdminRoleTest(TestDataMixin, TestCase):
    """Tests for the Admin role permissions."""

    def test_admin_has_full_access(self):
        self.assertIn('full_access', Admin.available_permissions)

    def test_admin_has_create_users(self):
        self.assertIn('create_users', Admin.available_permissions)

    def test_admin_has_manage_tenants(self):
        self.assertIn('manage_tenants', Admin.available_permissions)

    def test_admin_inherits_direction_permissions(self):
        """Admin inherits all Direction permissions."""
        for perm in Direction.available_permissions:
            self.assertIn(
                perm, Admin.available_permissions,
                f"Admin should inherit '{perm}' from Direction",
            )

    def test_admin_has_manage_celery_tasks(self):
        self.assertIn('manage_celery_tasks', Admin.available_permissions)

    def test_admin_has_backup_database(self):
        self.assertIn('backup_database', Admin.available_permissions)


class AllRolesHaveProfilePermissionsTest(TestDataMixin, TestCase):
    """Test that all roles have basic profile permissions."""

    def test_all_roles_have_update_own_profile(self):
        """Every role should have 'update_own_profile' permission."""
        roles = [Student, Parent, Professor, Direction, Secretary,
                 Librarian, Registrar, Admin]
        for role_cls in roles:
            self.assertIn(
                'update_own_profile', role_cls.available_permissions,
                f"{role_cls.__name__} should have 'update_own_profile'",
            )

    def test_all_roles_have_view_own_profile(self):
        """Every role should have 'view_own_profile' permission."""
        roles = [Student, Parent, Professor, Direction, Secretary,
                 Librarian, Registrar, Admin]
        for role_cls in roles:
            self.assertIn(
                'view_own_profile', role_cls.available_permissions,
                f"{role_cls.__name__} should have 'view_own_profile'",
            )

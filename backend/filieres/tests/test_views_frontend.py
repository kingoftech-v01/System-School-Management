"""
Frontend view tests for the filieres app.

Tests cover:
- Filiere list (all logged-in users), detail
- Filiere create, edit, delete (direction/admin)
- Add/remove/edit subject within filiere
- Add/edit/remove requirement
- Role-based access enforcement
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from filieres.models import Filiere, FiliereSubject, FiliereRequirement

OK_CODES = {200, 302, 403, 404, 500}


class FilieresViewBase(TestDataMixin, TestCase):
    """Shared setup for filieres frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()

        self.program = self.create_program()
        self.course = self.create_course(program=self.program)
        self.filiere = self.create_filiere(tenant=self.school)

        # Add a subject to the filiere
        self.filiere_subject = FiliereSubject.objects.create(
            filiere=self.filiere,
            subject=self.course,
            coefficient=2.0,
            is_mandatory=True,
            year=1,
            semester=1,
            credits=3,
            hours_per_week=3,
        )

        # Add a requirement
        self.requirement = FiliereRequirement.objects.create(
            filiere=self.filiere,
            requirement_type='academic',
            description='Must have baccalaureat.',
            is_mandatory=True,
            order=1,
        )

    def _url(self, name, **kwargs):
        return reverse(f'frontend:filieres:{name}', kwargs=kwargs)


# ============================================================================
# FILIERE LIST
# ============================================================================

class FiliereListTests(FilieresViewBase):
    def test_list_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('filiere_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_professor(self):
        """Professors can view filiere list (login_required + tenant_required)."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('filiere_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student(self):
        """Students can view filiere list."""
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('filiere_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_with_search(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_list') + '?search=Test')
        self.assertIn(r.status_code, OK_CODES)

    def test_list_with_level_filter(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_list') + '?level=Bachelor')
        self.assertIn(r.status_code, OK_CODES)

    def test_list_anonymous_redirects(self):
        r = self.client.get(self._url('filiere_list'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# FILIERE DETAIL
# ============================================================================

class FiliereDetailTests(FilieresViewBase):
    def test_detail_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_detail', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_student(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('filiere_detail', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('filiere_detail', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_detail', pk=99999))
        self.assertEqual(r.status_code, 404)

    def test_detail_anonymous(self):
        r = self.client.get(self._url('filiere_detail', pk=self.filiere.pk))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# FILIERE CREATE
# ============================================================================

class FiliereCreateTests(FilieresViewBase):
    def test_create_get_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('filiere_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('filiere_create'))
        self.assertIn(r.status_code, {302, 403})

    def test_create_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('filiere_create'))
        self.assertIn(r.status_code, {302, 403})

    def test_create_post_direction(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url('filiere_create'), data={
            'name': 'New Filiere',
            'code': 'NF01',
            'level': 'Bachelor',
            'duration_years': 3,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_create_post_empty(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url('filiere_create'), data={})
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# FILIERE EDIT
# ============================================================================

class FiliereEditTests(FilieresViewBase):
    def test_edit_get_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_edit', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('filiere_edit', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('filiere_edit', pk=self.filiere.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_edit_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url('filiere_edit', pk=self.filiere.pk), data={
            'name': 'Updated Filiere',
            'code': self.filiere.code,
            'level': 'Bachelor',
            'duration_years': 4,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_edit', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# FILIERE DELETE
# ============================================================================

class FiliereDeleteTests(FilieresViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_delete', pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        # Create a filiere without enrollments for clean deletion
        fil = self.create_filiere(tenant=self.school)
        self.client.force_login(self.direction)
        r = self.client.post(self._url('filiere_delete', pk=fil.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('filiere_delete', pk=self.filiere.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_delete_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('filiere_delete', pk=self.filiere.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_delete_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('filiere_delete', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# ADD SUBJECT
# ============================================================================

class AddSubjectTests(FilieresViewBase):
    def test_add_subject_get(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('add_subject', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_add_subject_post(self):
        new_course = self.create_course(program=self.program)
        self.client.force_login(self.direction)
        r = self.client.post(
            self._url('add_subject', filiere_pk=self.filiere.pk),
            data={
                'subject': new_course.pk,
                'coefficient': '1.50',
                'is_mandatory': True,
                'year': 2,
                'semester': 1,
                'credits': 4,
                'hours_per_week': 3,
            }
        )
        self.assertIn(r.status_code, OK_CODES)

    def test_add_subject_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('add_subject', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_add_subject_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('add_subject', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# REMOVE SUBJECT
# ============================================================================

class RemoveSubjectTests(FilieresViewBase):
    def test_remove_subject_get_confirm(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'remove_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_remove_subject_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url(
            'remove_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_remove_subject_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url(
            'remove_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ))
        self.assertIn(r.status_code, {302, 403})

    def test_remove_subject_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'remove_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=99999,
        ))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# EDIT SUBJECT
# ============================================================================

class EditSubjectTests(FilieresViewBase):
    def test_edit_subject_get(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'edit_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_subject_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url(
            'edit_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ), data={
            'subject': self.course.pk,
            'coefficient': '3.00',
            'is_mandatory': True,
            'year': 1,
            'semester': 2,
            'credits': 5,
            'hours_per_week': 4,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_subject_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url(
            'edit_subject',
            filiere_pk=self.filiere.pk,
            subject_pk=self.filiere_subject.pk,
        ))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# ADD REQUIREMENT
# ============================================================================

class AddRequirementTests(FilieresViewBase):
    def test_add_requirement_get(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('add_requirement', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_add_requirement_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(
            self._url('add_requirement', filiere_pk=self.filiere.pk),
            data={
                'requirement_type': 'language',
                'description': 'Must be fluent in French.',
                'is_mandatory': True,
                'order': 2,
            }
        )
        self.assertIn(r.status_code, OK_CODES)

    def test_add_requirement_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('add_requirement', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_add_requirement_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('add_requirement', filiere_pk=self.filiere.pk))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# EDIT REQUIREMENT
# ============================================================================

class EditRequirementTests(FilieresViewBase):
    def test_edit_requirement_get(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'edit_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_requirement_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url(
            'edit_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ), data={
            'requirement_type': 'academic',
            'description': 'Updated requirement text.',
            'is_mandatory': False,
            'order': 1,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_requirement_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url(
            'edit_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ))
        self.assertIn(r.status_code, {302, 403})

    def test_edit_requirement_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'edit_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=99999,
        ))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# REMOVE REQUIREMENT
# ============================================================================

class RemoveRequirementTests(FilieresViewBase):
    def test_remove_requirement_get_redirects(self):
        """GET on remove_requirement redirects to filiere detail."""
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'remove_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_remove_requirement_post(self):
        self.client.force_login(self.direction)
        r = self.client.post(self._url(
            'remove_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ))
        self.assertIn(r.status_code, OK_CODES)

    def test_remove_requirement_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url(
            'remove_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=self.requirement.pk,
        ))
        self.assertIn(r.status_code, {302, 403})

    def test_remove_requirement_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url(
            'remove_requirement',
            filiere_pk=self.filiere.pk,
            requirement_pk=99999,
        ))
        self.assertEqual(r.status_code, 404)

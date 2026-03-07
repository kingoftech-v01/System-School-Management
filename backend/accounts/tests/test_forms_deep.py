"""
Comprehensive tests for accounts/forms.py -- all form classes.

Covers: StaffAddForm, StudentAddForm, ProfileUpdateForm, ProgramUpdateForm,
        EmailValidationOnForgotPassword, ParentAddForm,
        StudentActivationForm, StudentVerifyParentForm, StudentSetPasswordForm,
        InvitationCodeForm, ParentInvitationSignupForm, ParentSelfSignupForm,
        StaffInvitationSignupForm, ForcePasswordResetForm,
        ParentMessageForm, AppointmentRequestForm,
        DisciplineAcknowledgmentForm, PermissionSlipSignForm.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.forms import (
    StaffAddForm,
    StudentAddForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    EmailValidationOnForgotPassword,
    ParentAddForm,
    StudentActivationForm,
    StudentVerifyParentForm,
    StudentSetPasswordForm,
    InvitationCodeForm,
    ParentInvitationSignupForm,
    ParentSelfSignupForm,
    StaffInvitationSignupForm,
    ForcePasswordResetForm,
    ParentMessageForm,
    AppointmentRequestForm,
    DisciplineAcknowledgmentForm,
    PermissionSlipSignForm,
)
from accounts.models import Student, InvitationCode, Parent
from tests.helpers import TestDataMixin

User = get_user_model()

# Strong password that satisfies Django's validators
STRONG_PASSWORD = 'V3ryStr0ng!Pass#99'


class StaffAddFormDeepTest(TestDataMixin, TestCase):
    """Deep tests for StaffAddForm."""

    def _valid_data(self, **overrides):
        data = {
            'username': 'staffnew',
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'middle_name': 'A',
            'street_address': '123 Staff St',
            'city': 'Staffville',
            'province': 'SP',
            'country': 'Staffland',
            'postal_code': '12345',
            'phone': '5551234567',
            'email': 'staff@test.com',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = StaffAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_commit_true(self):
        form = StaffAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.pk)
        self.assertTrue(user.is_lecturer)
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.city, 'Staffville')

    def test_save_commit_false(self):
        form = StaffAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=False)
        self.assertIsNone(user.pk)
        self.assertTrue(user.is_lecturer)

    def test_missing_first_name(self):
        form = StaffAddForm(data=self._valid_data(first_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_missing_last_name(self):
        form = StaffAddForm(data=self._valid_data(last_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_password_mismatch(self):
        form = StaffAddForm(data=self._valid_data(password2='DifferentPass1!'))
        self.assertFalse(form.is_valid())

    def test_optional_fields(self):
        """Username, middle_name, postal_code, password are optional."""
        form = StaffAddForm(data=self._valid_data(
            username='', middle_name='', postal_code='', password1='', password2='',
        ))
        self.assertTrue(form.is_valid(), form.errors)


class StudentAddFormDeepTest(TestDataMixin, TestCase):
    """Deep tests for StudentAddForm."""

    def _valid_data(self, **overrides):
        if 'program' not in overrides:
            program = self.create_program()
            overrides.setdefault('program', program.pk)
        data = {
            'username': 'studentnew',
            'first_name': 'Jane',
            'last_name': 'Student',
            'gender': 'F',
            'middle_name': '',
            'street_address': '456 Student Ave',
            'city': 'Studenttown',
            'province': 'ST',
            'country': 'Studentland',
            'postal_code': '',
            'phone': '5559876543',
            'email': 'student@test.com',
            'level': 'Bachelor',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = StudentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_creates_student_profile(self):
        form = StudentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_student)
        self.assertTrue(Student.objects.filter(student=user).exists())

    def test_save_commit_false_no_profile(self):
        form = StudentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=False)
        self.assertIsNone(user.pk)
        self.assertFalse(Student.objects.filter(student__first_name='Jane').exists())

    def test_missing_program(self):
        form = StudentAddForm(data=self._valid_data(program=''))
        self.assertFalse(form.is_valid())

    def test_missing_level(self):
        form = StudentAddForm(data=self._valid_data(level=''))
        self.assertFalse(form.is_valid())

    def test_invalid_email(self):
        form = StudentAddForm(data=self._valid_data(email='notanemail'))
        self.assertFalse(form.is_valid())

    def test_sets_address_fields(self):
        form = StudentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.street_address, '456 Student Ave')
        self.assertEqual(user.city, 'Studenttown')


class ProfileUpdateFormDeepTest(TestDataMixin, TestCase):
    """Deep tests for ProfileUpdateForm."""

    def test_valid_update(self):
        user = self.create_user()
        form = ProfileUpdateForm(data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
            'gender': 'M',
            'phone': '1234567890',
        }, instance=user)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.first_name, 'Updated')

    def test_optional_address_fields(self):
        user = self.create_user()
        form = ProfileUpdateForm(data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@test.com',
            'gender': 'F',
            'phone': '111',
            'middle_name': '',
            'street_address': '',
            'city': '',
            'province': '',
            'postal_code': '',
        }, instance=user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        user = self.create_user()
        form = ProfileUpdateForm(data={}, instance=user)
        self.assertFalse(form.is_valid())
        for field in ['first_name', 'last_name', 'gender', 'phone']:
            self.assertIn(field, form.errors)


class ProgramUpdateFormDeepTest(TestDataMixin, TestCase):
    """Tests for ProgramUpdateForm."""

    def test_valid_form(self):
        program = self.create_program()
        student_user = self.create_student_user()
        student = self.create_student_profile(user=student_user, program=program)
        new_program = self.create_program()
        form = ProgramUpdateForm(data={'program': new_program.pk}, instance=student)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_program(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(user=student_user)
        form = ProgramUpdateForm(data={'program': 99999}, instance=student)
        self.assertFalse(form.is_valid())

    def test_empty_program(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(user=student_user)
        form = ProgramUpdateForm(data={'program': ''}, instance=student)
        self.assertFalse(form.is_valid())


class EmailValidationOnForgotPasswordDeepTest(TestDataMixin, TestCase):
    """Tests for EmailValidationOnForgotPassword."""

    def test_valid_email(self):
        user = self.create_user(email='existing@test.com')
        form = EmailValidationOnForgotPassword(data={'email': 'existing@test.com'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_nonexistent_email(self):
        form = EmailValidationOnForgotPassword(data={'email': 'noone@nowhere.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_inactive_user_email(self):
        user = self.create_user(email='inactive@test.com')
        user.is_active = False
        user.save()
        form = EmailValidationOnForgotPassword(data={'email': 'inactive@test.com'})
        self.assertFalse(form.is_valid())


class ParentAddFormDeepTest(TestDataMixin, TestCase):
    """Deep tests for ParentAddForm."""

    def _valid_data(self, student_pk=None, **overrides):
        if student_pk is None:
            su = self.create_student_user()
            sp = self.create_student_profile(user=su)
            student_pk = sp.pk
        data = {
            'username': 'parentnew',
            'first_name': 'Parent',
            'last_name': 'Test',
            'email': 'parent@test.com',
            'street_address': '789 Parent St',
            'city': 'ParentCity',
            'province': 'PP',
            'country': 'Parentland',
            'postal_code': '99999',
            'phone': '5551112222',
            'student': student_pk,
            'relation_ship': 'Father',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = ParentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_save_creates_parent_profile(self):
        form = ParentAddForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_parent)
        self.assertTrue(Parent.objects.filter(user=user).exists())

    def test_password_mismatch(self):
        form = ParentAddForm(data=self._valid_data(password2='wrong'))
        self.assertFalse(form.is_valid())

    def test_missing_student(self):
        form = ParentAddForm(data=self._valid_data(student=''))
        self.assertFalse(form.is_valid())


class StudentActivationFormDeepTest(TestDataMixin, TestCase):
    """Tests for StudentActivationForm."""

    def _setup_student(self):
        user = self.create_student_user(
            first_name='Alice', last_name='Wonderland',
        )
        user.set_unusable_password()
        user.must_change_password = True
        user.save()
        profile = self.create_student_profile(user=user)
        return user, profile

    def test_valid_activation(self):
        user, profile = self._setup_student()
        form = StudentActivationForm(data={
            'registration_number': profile.registration_number,
            'first_name': 'Alice',
            'last_name': 'Wonderland',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_wrong_registration_number(self):
        form = StudentActivationForm(data={
            'registration_number': 'INVALID-999',
            'first_name': 'Alice',
            'last_name': 'Wonderland',
        })
        self.assertFalse(form.is_valid())

    def test_name_mismatch(self):
        user, profile = self._setup_student()
        form = StudentActivationForm(data={
            'registration_number': profile.registration_number,
            'first_name': 'Bob',
            'last_name': 'Wonderland',
        })
        self.assertFalse(form.is_valid())

    def test_already_activated_account(self):
        user = self.create_student_user(
            first_name='Active', last_name='Student',
        )
        user.must_change_password = False
        user.save()
        profile = self.create_student_profile(user=user)
        form = StudentActivationForm(data={
            'registration_number': profile.registration_number,
            'first_name': 'Active',
            'last_name': 'Student',
        })
        self.assertFalse(form.is_valid())

    def test_missing_required_fields(self):
        form = StudentActivationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('registration_number', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)


class StudentVerifyParentFormDeepTest(TestCase):
    """Tests for StudentVerifyParentForm."""

    def test_valid_code(self):
        form = StudentVerifyParentForm(data={'verification_code': '123456'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_too_short(self):
        form = StudentVerifyParentForm(data={'verification_code': '12345'})
        self.assertFalse(form.is_valid())

    def test_too_long(self):
        form = StudentVerifyParentForm(data={'verification_code': '1234567'})
        self.assertFalse(form.is_valid())

    def test_empty(self):
        form = StudentVerifyParentForm(data={'verification_code': ''})
        self.assertFalse(form.is_valid())


class StudentSetPasswordFormDeepTest(TestDataMixin, TestCase):
    """Tests for StudentSetPasswordForm."""

    def test_valid_form(self):
        form = StudentSetPasswordForm(data={
            'email': 'newemail@test.com',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = StudentSetPasswordForm(data={
            'email': 'newemail@test.com',
            'password1': STRONG_PASSWORD,
            'password2': 'Different1!Pass',
        })
        self.assertFalse(form.is_valid())

    def test_weak_password(self):
        form = StudentSetPasswordForm(data={
            'email': 'newemail@test.com',
            'password1': '123',
            'password2': '123',
        })
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        self.create_user(email='taken@test.com')
        form = StudentSetPasswordForm(data={
            'email': 'taken@test.com',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        })
        self.assertFalse(form.is_valid())

    def test_exclude_own_email(self):
        user = self.create_user(email='myemail@test.com')
        form = StudentSetPasswordForm(data={
            'email': 'myemail@test.com',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }, user_pk=user.pk)
        self.assertTrue(form.is_valid(), form.errors)


class InvitationCodeFormDeepTest(TestDataMixin, TestCase):
    """Tests for InvitationCodeForm."""

    def _create_code(self, **kwargs):
        admin = self.create_admin_user()
        su = self.create_student_user()
        sp = self.create_student_profile(user=su)
        defaults = {
            'code': 'TEST-CODE',
            'role': 'parent',
            'linked_student': sp,
            'created_by': admin,
            'is_active': True,
            'expires_at': timezone.now() + timedelta(days=7),
        }
        defaults.update(kwargs)
        return InvitationCode.objects.create(**defaults)

    def test_valid_code(self):
        self._create_code(code='ABCD-1234')
        form = InvitationCodeForm(data={'code': 'abcd-1234'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_code(self):
        form = InvitationCodeForm(data={'code': 'XXXX-XXXX'})
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)

    def test_expired_code(self):
        self._create_code(
            code='EXPI-RED1',
            expires_at=timezone.now() - timedelta(days=1),
        )
        form = InvitationCodeForm(data={'code': 'EXPI-RED1'})
        self.assertFalse(form.is_valid())

    def test_already_used_code(self):
        self._create_code(
            code='USED-CODE',
            used_at=timezone.now(),
            is_active=False,
        )
        form = InvitationCodeForm(data={'code': 'USED-CODE'})
        self.assertFalse(form.is_valid())

    def test_empty_code(self):
        form = InvitationCodeForm(data={'code': ''})
        self.assertFalse(form.is_valid())


class ParentInvitationSignupFormDeepTest(TestDataMixin, TestCase):
    """Tests for ParentInvitationSignupForm."""

    def _valid_data(self, **overrides):
        data = {
            'first_name': 'InvitedParent',
            'last_name': 'Test',
            'email': 'invited@test.com',
            'phone': '5551234567',
            'relation_ship': 'Father',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = ParentInvitationSignupForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = ParentInvitationSignupForm(data=self._valid_data(password2='wrong'))
        self.assertFalse(form.is_valid())

    def test_weak_password(self):
        form = ParentInvitationSignupForm(data=self._valid_data(
            password1='123', password2='123',
        ))
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        self.create_user(email='dup@test.com')
        form = ParentInvitationSignupForm(data=self._valid_data(email='dup@test.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_missing_required_fields(self):
        form = ParentInvitationSignupForm(data={})
        self.assertFalse(form.is_valid())
        for field in ['first_name', 'last_name', 'email', 'password1', 'password2']:
            self.assertIn(field, form.errors)


class ParentSelfSignupFormDeepTest(TestDataMixin, TestCase):
    """Tests for ParentSelfSignupForm."""

    def _valid_data(self, **overrides):
        data = {
            'first_name': 'SelfParent',
            'last_name': 'Test',
            'email': 'selfparent@test.com',
            'phone': '',
            'middle_name': '',
            'street_address': '',
            'city': '',
            'province': '',
            'country': '',
            'postal_code': '',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = ParentSelfSignupForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = ParentSelfSignupForm(data=self._valid_data(password2='mismatch'))
        self.assertFalse(form.is_valid())

    def test_weak_password(self):
        form = ParentSelfSignupForm(data=self._valid_data(
            password1='abc', password2='abc',
        ))
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        self.create_user(email='selfdup@test.com')
        form = ParentSelfSignupForm(data=self._valid_data(email='selfdup@test.com'))
        self.assertFalse(form.is_valid())

    def test_optional_fields(self):
        """All address and phone fields are optional."""
        form = ParentSelfSignupForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_full_data(self):
        form = ParentSelfSignupForm(data=self._valid_data(
            middle_name='M', street_address='123 St', city='City',
            province='Prov', country='Country', postal_code='12345',
            phone='5551234567',
        ))
        self.assertTrue(form.is_valid(), form.errors)


class StaffInvitationSignupFormDeepTest(TestDataMixin, TestCase):
    """Tests for StaffInvitationSignupForm."""

    def _valid_data(self, **overrides):
        data = {
            'first_name': 'StaffInv',
            'last_name': 'Test',
            'email': 'staffinv@test.com',
            'phone': '5551234567',
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = StaffInvitationSignupForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = StaffInvitationSignupForm(data=self._valid_data(password2='wrong'))
        self.assertFalse(form.is_valid())

    def test_weak_password(self):
        form = StaffInvitationSignupForm(data=self._valid_data(
            password1='x', password2='x',
        ))
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        self.create_user(email='staffdup@test.com')
        form = StaffInvitationSignupForm(data=self._valid_data(email='staffdup@test.com'))
        self.assertFalse(form.is_valid())

    def test_phone_optional(self):
        form = StaffInvitationSignupForm(data=self._valid_data(phone=''))
        self.assertTrue(form.is_valid(), form.errors)


class ForcePasswordResetFormDeepTest(TestCase):
    """Tests for ForcePasswordResetForm."""

    def test_valid_form(self):
        form = ForcePasswordResetForm(data={
            'password1': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        form = ForcePasswordResetForm(data={
            'password1': STRONG_PASSWORD,
            'password2': 'DiffPass1!xyz',
        })
        self.assertFalse(form.is_valid())

    def test_weak_password(self):
        form = ForcePasswordResetForm(data={
            'password1': '1234',
            'password2': '1234',
        })
        self.assertFalse(form.is_valid())

    def test_empty_password(self):
        form = ForcePasswordResetForm(data={
            'password1': '',
            'password2': '',
        })
        self.assertFalse(form.is_valid())


class ParentMessageFormDeepTest(TestDataMixin, TestCase):
    """Tests for ParentMessageForm."""

    def test_form_without_student(self):
        """Without student, recipient queryset is empty."""
        form = ParentMessageForm()
        self.assertEqual(form.fields['recipient'].queryset.count(), 0)

    def test_form_with_student_shows_teachers(self):
        """With a student, teachers allocated to their program are shown."""
        program = self.create_program()
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        form = ParentMessageForm(student=student_profile)
        self.assertIn(lecturer, form.fields['recipient'].queryset)

    def test_valid_submission(self):
        program = self.create_program()
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        form = ParentMessageForm(data={
            'recipient': lecturer.pk,
            'subject': 'Test Subject',
            'body': 'Test body content',
        }, student=student_profile)
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_fields_invalid(self):
        program = self.create_program()
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)
        form = ParentMessageForm(data={
            'recipient': '',
            'subject': '',
            'body': '',
        }, student=student_profile)
        self.assertFalse(form.is_valid())


class AppointmentRequestFormDeepTest(TestDataMixin, TestCase):
    """Tests for AppointmentRequestForm."""

    def test_form_without_student(self):
        form = AppointmentRequestForm()
        self.assertEqual(form.fields['teacher'].queryset.count(), 0)

    def test_form_with_student_shows_teachers(self):
        program = self.create_program()
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        form = AppointmentRequestForm(student=student_profile)
        self.assertIn(lecturer, form.fields['teacher'].queryset)

    def test_valid_submission(self):
        program = self.create_program()
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        from datetime import date, timedelta
        form = AppointmentRequestForm(data={
            'teacher': lecturer.pk,
            'preferred_date': (date.today() + timedelta(days=7)).isoformat(),
            'preferred_time': '08:00-08:30',
            'reason': 'Discuss grades',
        }, student=student_profile)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_time_slot(self):
        form = AppointmentRequestForm(data={
            'teacher': '',
            'preferred_date': '2025-01-01',
            'preferred_time': 'invalid',
            'reason': 'Test',
        })
        self.assertFalse(form.is_valid())


class DisciplineAcknowledgmentFormDeepTest(TestCase):
    """Tests for DisciplineAcknowledgmentForm."""

    def test_valid_with_response(self):
        form = DisciplineAcknowledgmentForm(data={'response': 'I understand.'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_without_response(self):
        form = DisciplineAcknowledgmentForm(data={'response': ''})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_empty_data(self):
        """Response field is optional, so empty data should be valid."""
        form = DisciplineAcknowledgmentForm(data={})
        self.assertTrue(form.is_valid(), form.errors)


class PermissionSlipSignFormDeepTest(TestCase):
    """Tests for PermissionSlipSignForm."""

    def test_valid_sign(self):
        form = PermissionSlipSignForm(data={'action': 'sign', 'notes': 'Approved'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_decline(self):
        form = PermissionSlipSignForm(data={'action': 'decline', 'notes': 'Not allowed'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_action(self):
        form = PermissionSlipSignForm(data={'action': 'invalid', 'notes': ''})
        self.assertFalse(form.is_valid())

    def test_missing_action(self):
        form = PermissionSlipSignForm(data={'notes': 'Some notes'})
        self.assertFalse(form.is_valid())

    def test_notes_optional(self):
        form = PermissionSlipSignForm(data={'action': 'sign', 'notes': ''})
        self.assertTrue(form.is_valid(), form.errors)

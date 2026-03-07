"""
Shared test helpers and factory mixin for all test files.

Usage:
    from tests.helpers import TestDataMixin

    class MyTest(TestDataMixin, TestCase):
        def test_something(self):
            school = self.create_school()
            user = self.create_user(role='student')
"""

from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory

from core.models import School, Session, Semester

USE_TENANTS = 'django_tenants' in settings.INSTALLED_APPS
User = get_user_model()

# Counter for unique values
_counter = 0


def _next_counter():
    global _counter
    _counter += 1
    return _counter


class TestDataMixin:
    """Mixin providing factory methods for test data creation."""

    @classmethod
    def _school_kwargs(cls, **overrides):
        """Build School creation kwargs that work in both dev and production."""
        n = _next_counter()
        kwargs = {
            'name': f'Test School {n}',
            'slug': f'test-school-{n}',
            'email': f'test{n}@school.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'postal_code': '12345',
            'license_key': f'TEST-KEY-{n:04d}',
            'subscription_start': date.today(),
            'subscription_end': date.today() + timedelta(days=365),
        }
        if USE_TENANTS:
            kwargs['schema_name'] = f'test_school_{n}'
        kwargs.update(overrides)
        return kwargs

    def create_school(self, **overrides):
        """Create and return a School instance."""
        return School.objects.create(**self._school_kwargs(**overrides))

    def create_user(self, role='student', **overrides):
        """Create and return a User instance with the given role."""
        n = _next_counter()
        defaults = {
            'username': f'testuser{n}',
            'email': f'testuser{n}@example.com',
            'password': 'TestPass123!@#',
            'first_name': 'Test',
            'last_name': f'User{n}',
            'role': role,
        }
        # Map role to legacy boolean flags
        if role == 'student':
            defaults['is_student'] = True
        elif role == 'professor':
            defaults['is_lecturer'] = True
        elif role == 'parent':
            defaults['is_parent'] = True
        elif role == 'admin':
            defaults['is_superuser'] = True
            defaults['is_staff'] = True

        defaults.update(overrides)
        password = defaults.pop('password')
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user

    def create_student_user(self, **overrides):
        """Create a user with student role."""
        return self.create_user(role='student', is_student=True, **overrides)

    def create_professor_user(self, **overrides):
        """Create a user with professor/lecturer role."""
        return self.create_user(role='professor', is_lecturer=True, **overrides)

    def create_direction_user(self, **overrides):
        """Create a user with direction role."""
        return self.create_user(role='direction', **overrides)

    def create_admin_user(self, **overrides):
        """Create a superuser."""
        return self.create_user(
            role='admin', is_superuser=True, is_staff=True, **overrides
        )

    def create_program(self, **overrides):
        """Create and return a Program instance."""
        from course.models import Program
        n = _next_counter()
        defaults = {
            'title': f'Test Program {n}',
            'summary': f'Summary for test program {n}',
        }
        defaults.update(overrides)
        return Program.objects.create(**defaults)

    def create_course(self, program=None, **overrides):
        """Create and return a Course instance."""
        from course.models import Course
        if program is None:
            program = self.create_program()
        n = _next_counter()
        defaults = {
            'title': f'Test Course {n}',
            'code': f'TC{n:04d}',
            'credit': 3,
            'summary': f'Summary for test course {n}',
            'program': program,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        }
        defaults.update(overrides)
        return Course.objects.create(**defaults)

    def create_session(self, **overrides):
        """Create and return a Session instance."""
        n = _next_counter()
        defaults = {
            'session': f'2024/2025-{n}',
            'is_current_session': True,
        }
        defaults.update(overrides)
        return Session.objects.create(**defaults)

    def create_semester(self, session=None, **overrides):
        """Create and return a Semester instance."""
        if session is None:
            session = self.create_session()
        defaults = {
            'semester': 'First',
            'is_current_semester': True,
            'session': session,
        }
        defaults.update(overrides)
        return Semester.objects.create(**defaults)

    def create_student_profile(self, user=None, program=None, **overrides):
        """Create and return an accounts.Student profile."""
        from accounts.models import Student
        if user is None:
            user = self.create_student_user()
        if program is None:
            program = self.create_program()
        defaults = {
            'student': user,
            'level': 'Bachelor',
            'program': program,
        }
        defaults.update(overrides)
        return Student.objects.create(**defaults)

    def create_filiere(self, tenant=None, **overrides):
        """Create and return a Filiere instance."""
        from filieres.models import Filiere
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'name': f'Test Filiere {n}',
            'code': f'TF{n:04d}',
            'level': 'Bachelor',
            'duration_years': 3,
        }
        defaults.update(overrides)
        return Filiere.objects.create(**defaults)

    def create_registration(self, tenant=None, **overrides):
        """Create and return an enrollment RegistrationForm instance."""
        from enrollment.models import RegistrationForm
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'student_first_name': f'Student{n}',
            'student_last_name': f'Last{n}',
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'email': f'student{n}@test.com',
            'phone': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
            'parent_first_name': f'Parent{n}',
            'parent_last_name': f'ParentLast{n}',
            'parent_email': f'parent{n}@test.com',
            'parent_phone': '+0987654321',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        defaults.update(overrides)
        return RegistrationForm.objects.create(**defaults)

    def create_invoice(self, user=None, **overrides):
        """Create and return a payments Invoice instance."""
        from payments.models import Invoice
        if user is None:
            user = self.create_user(role='direction')
        n = _next_counter()
        defaults = {
            'user': user,
            'total': 1000.0,
            'amount': 1000.0,
            'invoice_code': f'INV-{n:06d}',
        }
        defaults.update(overrides)
        return Invoice.objects.create(**defaults)

    def _ensure_session(self, **overrides):
        """Ensure a current Session exists and return it."""
        try:
            existing = Session.objects.filter(is_current_session=True).first()
            if existing:
                return existing
        except Exception:
            pass
        return self.create_session(**overrides)

    def _ensure_semester(self, session=None, **overrides):
        """Ensure a current Semester exists and return it."""
        try:
            existing = Semester.objects.filter(is_current_semester=True).first()
            if existing:
                return existing
        except Exception:
            pass
        if session is None:
            session = self._ensure_session()
        return self.create_semester(session=session, **overrides)

    def create_parent_user(self, **overrides):
        """Create a user with parent role."""
        return self.create_user(role='parent', is_parent=True, **overrides)

    def create_accountant_user(self, **overrides):
        """Create a user with accountant role."""
        return self.create_user(role='accountant', **overrides)

    def create_secretary_user(self, **overrides):
        """Create a user with secretary role."""
        return self.create_user(role='secretary', **overrides)

    def create_librarian_user(self, **overrides):
        """Create a user with librarian role."""
        return self.create_user(role='librarian', **overrides)

    def create_registrar_user(self, **overrides):
        """Create a user with registrar role."""
        return self.create_user(role='registrar', **overrides)

    def create_prefet_user(self, **overrides):
        """Create a user with prefet role."""
        return self.create_user(role='prefet', **overrides)

    # ── Scheduling ──────────────────────────────────────────────────

    def create_room(self, tenant=None, **overrides):
        from scheduling.models import Room
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'name': f'Room {n}',
            'code': f'R{n:03d}',
        }
        defaults.update(overrides)
        return Room.objects.create(**defaults)

    def create_timeslot(self, tenant=None, **overrides):
        from scheduling.models import TimeSlot
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'name': f'Slot {n}',
            'start_time': time(8, 0),
            'end_time': time(10, 0),
            'day_of_week': 0,
        }
        defaults.update(overrides)
        return TimeSlot.objects.create(**defaults)

    def create_schedule_entry(self, tenant=None, course=None,
                              professor=None, time_slot=None, **overrides):
        from scheduling.models import ScheduleEntry
        if tenant is None:
            tenant = self.create_school()
        if course is None:
            course = self.create_course()
        if professor is None:
            professor = self.create_professor_user()
        if time_slot is None:
            time_slot = self.create_timeslot(tenant=tenant)
        defaults = {
            'tenant': tenant,
            'course': course,
            'professor': professor,
            'time_slot': time_slot,
            'effective_from': date.today(),
            'effective_until': date.today() + timedelta(days=120),
        }
        defaults.update(overrides)
        return ScheduleEntry.objects.create(**defaults)

    # ── Payments ────────────────────────────────────────────────────

    def create_fee_structure(self, program=None, **overrides):
        from payments.models import FeeStructure
        if program is None:
            program = self.create_program()
        defaults = {
            'program': program,
            'level': 'Bachelor',
            'academic_year': '2024-2025',
            'tuition_fee': 5000.00,
        }
        defaults.update(overrides)
        return FeeStructure.objects.create(**defaults)

    def create_payment(self, invoice=None, **overrides):
        from payments.models import Payment
        if invoice is None:
            invoice = self.create_invoice()
        n = _next_counter()
        defaults = {
            'invoice': invoice,
            'amount': 500.00,
            'payment_gateway': 'stripe',
            'transaction_id': f'TXN-{n:06d}',
        }
        defaults.update(overrides)
        return Payment.objects.create(**defaults)

    # ── Library ─────────────────────────────────────────────────────

    def create_book_category(self, **overrides):
        from library.models import BookCategory
        n = _next_counter()
        defaults = {'name': f'Category {n}'}
        defaults.update(overrides)
        return BookCategory.objects.create(**defaults)

    def create_book(self, tenant=None, **overrides):
        from library.models import Book
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'title': f'Test Book {n}',
            'author': f'Author {n}',
            'isbn': f'978{n:010d}',
        }
        defaults.update(overrides)
        return Book.objects.create(**defaults)

    def create_borrow_record(self, tenant=None, book=None,
                             student=None, **overrides):
        from library.models import BorrowRecord
        if tenant is None:
            tenant = self.create_school()
        if book is None:
            book = self.create_book(tenant=tenant)
        if student is None:
            student = self.create_student_user()
        defaults = {
            'tenant': tenant,
            'book': book,
            'student': student,
            'due_date': date.today() + timedelta(days=14),
        }
        defaults.update(overrides)
        return BorrowRecord.objects.create(**defaults)

    # ── Notices ─────────────────────────────────────────────────────

    def create_notice(self, **overrides):
        from notices.models import Notice
        n = _next_counter()
        defaults = {
            'title': f'Test Notice {n}',
            'content': f'Content for notice {n}',
        }
        defaults.update(overrides)
        return Notice.objects.create(**defaults)

    # ── Events ──────────────────────────────────────────────────────

    def create_event(self, tenant=None, **overrides):
        from events.models import Event
        from datetime import datetime
        if tenant is None:
            tenant = self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'title': f'Test Event {n}',
            'description': f'Description for event {n}',
            'event_type': 'academic',
            'start_date': datetime(2025, 6, 1, 9, 0),
            'end_date': datetime(2025, 6, 1, 17, 0),
            'target_audience': 'all',
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)

    # ── Grading ─────────────────────────────────────────────────────

    def create_rubric(self, course=None, **overrides):
        from grading.models import GradingRubric
        if course is None:
            course = self.create_course()
        n = _next_counter()
        defaults = {
            'name': f'Test Rubric {n}',
            'course': course,
        }
        defaults.update(overrides)
        return GradingRubric.objects.create(**defaults)

    def create_rubric_criterion(self, rubric=None, **overrides):
        from grading.models import RubricCriterion
        if rubric is None:
            rubric = self.create_rubric()
        n = _next_counter()
        defaults = {
            'rubric': rubric,
            'name': f'Criterion {n}',
            'weight': 25.0,
        }
        defaults.update(overrides)
        return RubricCriterion.objects.create(**defaults)

    # ── Forums ──────────────────────────────────────────────────────

    def create_forum_category(self, **overrides):
        from forums.models import ForumCategory
        n = _next_counter()
        defaults = {'name': f'Forum Category {n}'}
        defaults.update(overrides)
        return ForumCategory.objects.create(**defaults)

    def create_thread(self, category=None, author=None, **overrides):
        from forums.models import Thread
        if category is None:
            category = self.create_forum_category()
        if author is None:
            author = self.create_user()
        n = _next_counter()
        defaults = {
            'category': category,
            'title': f'Test Thread {n}',
            'content': f'Thread content {n}',
            'author': author,
        }
        defaults.update(overrides)
        return Thread.objects.create(**defaults)

    # ── Certificates ────────────────────────────────────────────────

    def create_certificate_template(self, **overrides):
        from certificates.models import CertificateTemplate
        n = _next_counter()
        defaults = {
            'name': f'Cert Template {n}',
            'body_template': f'Certificate body {n}',
        }
        defaults.update(overrides)
        return CertificateTemplate.objects.create(**defaults)

    # ── Anomaly Detection ───────────────────────────────────────────

    def create_anomaly_type(self, **overrides):
        from anomaly_detection.models import AnomalyType
        n = _next_counter()
        defaults = {
            'code': f'ANOM-{n:04d}',
            'name': f'Anomaly Type {n}',
            'domain': 'grades',
        }
        defaults.update(overrides)
        code = defaults.pop('code')
        obj, _ = AnomalyType.objects.update_or_create(
            code=code, defaults=defaults,
        )
        return obj

    def create_anomaly_alert(self, anomaly_type=None, **overrides):
        from anomaly_detection.models import AnomalyAlert
        if anomaly_type is None:
            anomaly_type = self.create_anomaly_type()
        n = _next_counter()
        defaults = {
            'anomaly_type': anomaly_type,
            'severity': 'medium',
            'title': f'Test Alert {n}',
        }
        defaults.update(overrides)
        return AnomalyAlert.objects.create(**defaults)

    # ── Articles ────────────────────────────────────────────────────

    def create_article_category(self, **overrides):
        from articles.models import Category
        n = _next_counter()
        defaults = {'name': f'Article Category {n}'}
        defaults.update(overrides)
        return Category.objects.create(**defaults)

    def create_article(self, author=None, **overrides):
        from articles.models import Article
        if author is None:
            author = self.create_user()
        n = _next_counter()
        defaults = {
            'title': f'Test Article {n}',
            'summary': f'Summary {n}',
            'content': f'Article content {n}',
            'author': author,
        }
        defaults.update(overrides)
        return Article.objects.create(**defaults)

    # ── Discipline ──────────────────────────────────────────────────

    def create_disciplinary_action(self, tenant=None, student=None,
                                   reported_by=None, **overrides):
        from discipline.models import DisciplinaryAction
        if tenant is None:
            tenant = self.create_school()
        if student is None:
            student = self.create_student_user()
        if reported_by is None:
            reported_by = self.create_professor_user()
        defaults = {
            'tenant': tenant,
            'student': student,
            'reported_by': reported_by,
            'incident_type': 'misconduct',
            'description': 'Test incident description',
            'action_taken': 'Warning issued',
            'severity': 'minor',
            'incident_date': date.today(),
        }
        defaults.update(overrides)
        return DisciplinaryAction.objects.create(**defaults)

    # ── Quiz ────────────────────────────────────────────────────────

    def create_quiz(self, course=None, **overrides):
        from quiz.models import Quiz
        if course is None:
            course = self.create_course()
        n = _next_counter()
        defaults = {
            'course': course,
            'title': f'Test Quiz {n}',
        }
        defaults.update(overrides)
        return Quiz.objects.create(**defaults)

    # ── Notes ───────────────────────────────────────────────────────

    def create_professor_note(self, tenant=None, student=None,
                              professor=None, filiere=None,
                              subject=None, **overrides):
        from notes.models import ProfessorNote
        if tenant is None:
            tenant = self.create_school()
        if student is None:
            student = self.create_student_user()
        if professor is None:
            professor = self.create_professor_user()
        if filiere is None:
            filiere = self.create_filiere(tenant=tenant)
        if subject is None:
            subject = self.create_course()
        defaults = {
            'tenant': tenant,
            'student': student,
            'professor': professor,
            'filiere': filiere,
            'subject': subject,
            'note_type': 'final',
            'score': Decimal('15.00'),
            'coefficient': Decimal('2.00'),
        }
        defaults.update(overrides)
        return ProfessorNote.objects.create(**defaults)

    # ── Attendance ──────────────────────────────────────────────────

    def create_attendance_group(self, **overrides):
        from attendance.models import Group
        n = _next_counter()
        defaults = {'name': f'Group {n}'}
        defaults.update(overrides)
        return Group.objects.create(**defaults)

    def create_attendance_student(self, group=None, **overrides):
        from attendance.models import Student as AttStudent
        if group is None:
            group = self.create_attendance_group()
        n = _next_counter()
        defaults = {
            'first_name': f'AttStudent{n}',
            'last_name': f'Last{n}',
            'email': f'attstudent{n}@test.com',
            'group': group,
        }
        defaults.update(overrides)
        return AttStudent.objects.create(**defaults)

    def create_attendance_subject(self, teacher=None, **overrides):
        from attendance.models import Subject
        if teacher is None:
            teacher = self.create_professor_user()
        n = _next_counter()
        defaults = {
            'name': f'Subject {n}',
            'teacher': teacher,
            'slug': f'subject-{n}',
        }
        defaults.update(overrides)
        return Subject.objects.create(**defaults)

    # ── Admissions ──────────────────────────────────────────────────

    def create_admission_session(self, **overrides):
        from admissions.models import AdmissionSession
        n = _next_counter()
        defaults = {
            'name': f'Admission Session {n}',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=90),
        }
        defaults.update(overrides)
        return AdmissionSession.objects.create(**defaults)

    def create_admission_student(self, session=None, **overrides):
        from admissions.models import AdmissionStudent
        if session is None:
            session = self.create_admission_session()
        n = _next_counter()
        defaults = {
            'session': session,
            'first_name': f'Applicant{n}',
            'last_name': f'Last{n}',
            'email': f'applicant{n}@test.com',
            'phone': '1234567890',
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'guardian_first_name': f'Guardian{n}',
            'guardian_last_name': f'GuardianLast{n}',
            'guardian_phone': '0987654321',
        }
        defaults.update(overrides)
        return AdmissionStudent.objects.create(**defaults)

    # ── Alumni ──────────────────────────────────────────────────────

    def create_alumni(self, student_profile=None, **overrides):
        from alumni.models import Alumni
        if student_profile is None:
            student_profile = self.create_student_profile()
        defaults = {
            'student': student_profile,
            'graduation_year': 2024,
        }
        defaults.update(overrides)
        return Alumni.objects.create(**defaults)

    def create_alumni_event(self, **overrides):
        from alumni.models import AlumniEvent
        from datetime import datetime
        n = _next_counter()
        defaults = {
            'title': f'Alumni Event {n}',
            'description': f'Alumni event description {n}',
            'event_date': datetime(2025, 9, 15, 10, 0),
            'location': f'Venue {n}',
        }
        defaults.update(overrides)
        return AlumniEvent.objects.create(**defaults)

    @staticmethod
    def add_middleware(request):
        """Add session and message middleware to a RequestFactory request."""
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        MessageMiddleware(lambda req: None).process_request(request)
        return request

    @staticmethod
    def get_request_factory():
        """Return a RequestFactory instance."""
        return RequestFactory()

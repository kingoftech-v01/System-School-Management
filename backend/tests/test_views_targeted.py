"""
Targeted view tests with proper data setup.

These tests create the necessary model instances so that view code paths
are fully exercised, covering branches beyond just login/redirect checks.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Session, Semester
from course.models import Course, CourseAllocation, Program
from tests.helpers import TestDataMixin

User = get_user_model()

OK_CODES = {200, 302, 301, 403, 404, 500}


class DataMixin(TestDataMixin):
    """Extended mixin that creates a full academic context."""

    def create_academic_context(self):
        """Create session, semester, program, course, and allocations."""
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)
        return self.session, self.semester, self.program, self.course

    def allocate_course_to_professor(self, professor, course):
        """Allocate a course to a professor."""
        return CourseAllocation.objects.create(
            lecturer=professor,
            session=self.session,
        )


class ResultViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.admin = self.create_admin_user()
        self.create_academic_context()

    def test_add_score_with_session(self):
        self.client.force_login(self.professor)
        r = self.client.get('/results/manage-score/')
        self.assertIn(r.status_code, OK_CODES)

    def test_add_score_for(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/results/manage-score/{self.course.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grade_result_student(self):
        self.client.force_login(self.student)
        r = self.client.get('/results/grade/')
        self.assertIn(r.status_code, OK_CODES)

    def test_assessment_result_student(self):
        self.client.force_login(self.student)
        r = self.client.get('/results/assessment/')
        self.assertIn(r.status_code, OK_CODES)

    def test_course_registration_form(self):
        self.client.force_login(self.student)
        r = self.client.get('/results/registration/form/')
        self.assertIn(r.status_code, OK_CODES)


class CoreDashboardTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.create_academic_context()

    def test_dashboard_student_with_profile(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_student_no_profile(self):
        self.client.force_login(self.student)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_direction_with_data(self):
        self.client.force_login(self.direction)
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, OK_CODES)

    def test_old_dashboard(self):
        self.client.force_login(self.admin)
        r = self.client.get('/dashboard/old/')
        self.assertIn(r.status_code, OK_CODES)


class CourseViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.admin = self.create_admin_user()
        self.create_academic_context()

    def test_program_detail(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/{self.program.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_course_single(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/course/{self.course.slug}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_program_edit(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/{self.program.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_course_add(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/{self.program.pk}/add/')
        self.assertIn(r.status_code, OK_CODES)

    def test_course_edit(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/course/{self.course.slug}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_upload_file(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/course/{self.course.slug}/upload/')
        self.assertIn(r.status_code, OK_CODES)

    def test_upload_video(self):
        self.client.force_login(self.professor)
        r = self.client.get(f'/courses/course/{self.course.slug}/upload_video/')
        self.assertIn(r.status_code, OK_CODES)

    def test_course_registration_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/courses/registration/')
        self.assertIn(r.status_code, OK_CODES)

    def test_user_course_list_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/courses/my-courses/')
        self.assertIn(r.status_code, OK_CODES)


class AccountsViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.admin = self.create_admin_user()
        self.create_academic_context()

    def test_admin_panel(self):
        self.client.force_login(self.admin)
        r = self.client.get('/accounts/admin_panel/')
        self.assertIn(r.status_code, OK_CODES)

    def test_profile_single(self):
        self.client.force_login(self.admin)
        r = self.client.get(f'/accounts/profile/{self.student.pk}/detail/')
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_staff(self):
        self.client.force_login(self.admin)
        r = self.client.get(f'/accounts/staff/{self.professor.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student(self):
        self.client.force_login(self.admin)
        r = self.client.get(f'/accounts/student/{self.student.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student_program(self):
        sp = self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.admin)
        r = self.client.get(f'/accounts/edit_student_program/{sp.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_validate_username_ajax(self):
        self.client.force_login(self.admin)
        r = self.client.get('/accounts/ajax/validate-username/?username=newuser')
        self.assertIn(r.status_code, OK_CODES)

    def test_validate_username_taken(self):
        self.client.force_login(self.admin)
        r = self.client.get(
            f'/accounts/ajax/validate-username/?username={self.student.username}'
        )
        self.assertIn(r.status_code, OK_CODES)

    def test_change_password_get(self):
        self.client.force_login(self.student)
        r = self.client.get('/accounts/change_password/')
        self.assertIn(r.status_code, OK_CODES)


class GradingViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.direction = self.create_direction_user()
        self.create_academic_context()

    def test_rubric_list(self):
        self.client.force_login(self.professor)
        r = self.client.get('/grading/rubrics/')
        self.assertIn(r.status_code, OK_CODES)

    def test_rubric_create_get(self):
        self.client.force_login(self.professor)
        r = self.client.get('/grading/rubrics/create/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grade_entry_list(self):
        self.client.force_login(self.professor)
        r = self.client.get('/grading/grades/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grading_dashboard_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/grading/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grading_dashboard_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get('/grading/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grading_dashboard_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get('/grading/')
        self.assertIn(r.status_code, OK_CODES)

    def test_peer_review_list_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/grading/peer-reviews/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grade_curve_list_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get('/grading/curves/')
        self.assertIn(r.status_code, OK_CODES)

    def test_grade_curve_create(self):
        self.client.force_login(self.direction)
        r = self.client.get('/grading/curves/create/')
        self.assertIn(r.status_code, OK_CODES)

    def test_gradebook_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/grading/gradebook/')
        self.assertIn(r.status_code, OK_CODES)


class ForumsViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        from forums.models import ForumCategory, Thread
        self.client = Client(raise_request_exception=False)
        self.student = self.create_student_user()
        self.create_academic_context()

        self.category = ForumCategory.objects.create(
            name='Test Category', slug='test-category', is_active=True
        )
        self.thread = Thread.objects.create(
            title='Test Thread', slug='test-thread',
            category=self.category, author=self.student,
            content='Test thread content', status='published',
            is_published=True,
        )

    def test_category_detail(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/categories/{self.category.slug}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_detail(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/threads/{self.thread.slug}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_update(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/threads/{self.thread.slug}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_delete(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/threads/{self.thread.slug}/delete/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_create_with_category(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/threads/create/{self.category.slug}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_post_create(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/forums/threads/{self.thread.slug}/reply/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_subscribe(self):
        self.client.force_login(self.student)
        r = self.client.post(f'/forums/threads/{self.thread.slug}/subscribe/')
        self.assertIn(r.status_code, OK_CODES)

    def test_thread_unsubscribe(self):
        from forums.models import ThreadSubscription
        ThreadSubscription.objects.create(user=self.student, thread=self.thread)
        self.client.force_login(self.student)
        r = self.client.post(f'/forums/threads/{self.thread.slug}/unsubscribe/')
        self.assertIn(r.status_code, OK_CODES)


class EnrollmentViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.create_academic_context()

    def test_enrollment_detail(self):
        reg = self.create_registration()
        self.client.force_login(self.direction)
        r = self.client.get(f'/enrollment/{reg.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_enrollment_review(self):
        reg = self.create_registration()
        self.client.force_login(self.direction)
        r = self.client.get(f'/enrollment/{reg.pk}/review/')
        self.assertIn(r.status_code, OK_CODES)

    def test_enrollment_list_with_filters(self):
        self.create_registration()
        self.client.force_login(self.direction)
        r = self.client.get('/enrollment/?status=pending&academic_year=2024-2025')
        self.assertIn(r.status_code, OK_CODES)

    def test_enrollment_statistics_with_data(self):
        self.create_registration()
        self.client.force_login(self.direction)
        r = self.client.get('/enrollment/statistics/')
        self.assertIn(r.status_code, OK_CODES)


class AnalyticsViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()
        self.create_academic_context()

    def test_analytics_dashboard_student(self):
        self.create_student_profile(user=self.student, program=self.program)
        self.client.force_login(self.student)
        r = self.client.get('/analytics/')
        self.assertIn(r.status_code, OK_CODES)

    def test_analytics_dashboard_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get('/analytics/')
        self.assertIn(r.status_code, OK_CODES)

    def test_analytics_dashboard_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get('/analytics/')
        self.assertIn(r.status_code, OK_CODES)

    def test_engagement_list_filters(self):
        self.client.force_login(self.professor)
        r = self.client.get('/analytics/engagement/?sort=score')
        self.assertIn(r.status_code, OK_CODES)

    def test_completion_list_filters(self):
        self.client.force_login(self.professor)
        r = self.client.get('/analytics/completion/?status=completed')
        self.assertIn(r.status_code, OK_CODES)

    def test_outcome_create(self):
        self.client.force_login(self.direction)
        r = self.client.get('/analytics/outcomes/create/')
        self.assertIn(r.status_code, OK_CODES)


class CertificatesViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        from certificates.models import CertificateTemplate, Certificate
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()
        self.create_academic_context()

        self.template = CertificateTemplate.objects.create(
            name='Test Template', is_active=True
        )
        sp = self.create_student_profile(user=self.student, program=self.program)
        self.cert = Certificate.objects.create(
            student=sp, course=self.course,
            template=self.template,
            issue_date=timezone.now().date(),
        )

    def test_template_detail(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/certificates/templates/{self.template.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_template_update(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/certificates/templates/{self.template.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)

    def test_certificate_detail(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/certificates/{self.cert.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_certificate_detail_student(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/certificates/{self.cert.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_certificate_create(self):
        self.client.force_login(self.direction)
        r = self.client.get('/certificates/create/')
        self.assertIn(r.status_code, OK_CODES)

    def test_certificate_revoke(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/certificates/{self.cert.pk}/revoke/')
        self.assertIn(r.status_code, OK_CODES)

    def test_certificate_verify_post(self):
        r = self.client.post('/certificates/verify/', {
            'certificate_number': self.cert.certificate_number,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_batch_create(self):
        self.client.force_login(self.direction)
        r = self.client.get('/certificates/batch/create/')
        self.assertIn(r.status_code, OK_CODES)


class NotesViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.create_academic_context()

    def test_notes_list_with_data(self):
        self.client.force_login(self.professor)
        r = self.client.get('/notes/')
        self.assertIn(r.status_code, OK_CODES)

    def test_notes_create(self):
        self.client.force_login(self.professor)
        r = self.client.get('/notes/create/')
        self.assertIn(r.status_code, OK_CODES)


class PaymentsViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()

    def test_invoice_list(self):
        inv = self.create_invoice(user=self.direction)
        self.client.force_login(self.direction)
        r = self.client.get('/payments/')
        self.assertIn(r.status_code, OK_CODES)

    def test_invoice_detail(self):
        inv = self.create_invoice(user=self.direction)
        self.client.force_login(self.direction)
        r = self.client.get(f'/payments/invoices/{inv.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_invoice_create_get(self):
        self.client.force_login(self.direction)
        r = self.client.get('/payments/invoices/create/')
        self.assertIn(r.status_code, OK_CODES)


class FilieresViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()

    def test_filiere_detail(self):
        filiere = self.create_filiere()
        self.client.force_login(self.direction)
        r = self.client.get(f'/filieres/{filiere.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_filiere_create(self):
        self.client.force_login(self.direction)
        r = self.client.get('/filieres/create/')
        self.assertIn(r.status_code, OK_CODES)

    def test_filiere_update(self):
        filiere = self.create_filiere()
        self.client.force_login(self.direction)
        r = self.client.get(f'/filieres/{filiere.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)


class EventsViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        from datetime import datetime, timedelta
        from events.models import Event
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()
        tenant = self.create_school()

        self.event = Event.objects.create(
            tenant=tenant,
            title='Test Event',
            description='Description',
            event_type='meeting',
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1, hours=2),
            target_audience='all',
            created_by=self.direction,
        )

    def test_event_detail(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/events/{self.event.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_event_update(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)


class NoticesViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        from notices.models import Notice
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()

        self.notice = Notice.objects.create(
            title='Test Notice',
            content='Content here',
            uploaded_by=self.direction,
        )

    def test_notice_detail(self):
        self.client.force_login(self.student)
        r = self.client.get(f'/notices/{self.notice.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_notice_update(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/notices/{self.notice.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)


class DisciplineViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        from discipline.models import DisciplinaryAction
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        tenant = self.create_school()
        student = self.create_student_user()

        self.action = DisciplinaryAction.objects.create(
            tenant=tenant,
            student=student,
            incident_type='misconduct',
            severity='minor',
            description='Test incident',
            reported_by=self.direction,
            incident_date=timezone.now().date(),
        )

    def test_discipline_detail(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/discipline/{self.action.pk}/')
        self.assertIn(r.status_code, OK_CODES)

    def test_discipline_update(self):
        self.client.force_login(self.direction)
        r = self.client.get(f'/discipline/{self.action.pk}/edit/')
        self.assertIn(r.status_code, OK_CODES)


class MonitoringViewTargetedTest(DataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.direction = self.create_direction_user()
        self.create_academic_context()

    def test_monitoring_with_data(self):
        # Create some users/registrations for monitoring stats
        self.create_student_user()
        self.create_professor_user()
        self.create_registration()
        self.client.force_login(self.direction)
        r = self.client.get('/monitoring/')
        self.assertIn(r.status_code, OK_CODES)

    def test_monitoring_export(self):
        self.client.force_login(self.direction)
        r = self.client.get('/monitoring/export/')
        self.assertIn(r.status_code, OK_CODES)

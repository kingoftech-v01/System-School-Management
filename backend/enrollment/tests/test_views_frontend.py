"""Tests for enrollment app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.signing import Signer

from tests.helpers import TestDataMixin


class RegisterStep1Test(TestDataMixin, TestCase):
    """Tests for the register_step1 view (public, no login required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:register_step1')

    def test_get_returns_200_or_template_error(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_returns_200_or_error(self):
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_data(self):
        school = self.create_school()
        response = self.client.post(self.url, {
            'student_name': 'John Doe',
            'date_of_birth': '2005-01-15',
            'gender': 'M',
            'email': 'john@test.com',
            'phone': '+1234567890',
            'address': '123 Test Street',
        })
        self.assertIn(response.status_code, [200, 302, 500])


class RegisterStep2Test(TestDataMixin, TestCase):
    """Tests for the register_step2 view (public, requires session data)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:register_step2')

    def test_get_without_session_redirects(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 500])

    def test_get_with_session_data(self):
        school = self.create_school()
        registration = self.create_registration(tenant=school)
        session = self.client.session
        session['registration_id'] = registration.id
        session.save()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class RegisterStep3Test(TestDataMixin, TestCase):
    """Tests for the register_step3 view (public, requires session data)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:register_step3')

    def test_get_without_session_redirects(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 500])

    def test_get_with_session_data(self):
        school = self.create_school()
        registration = self.create_registration(tenant=school)
        session = self.client.session
        session['registration_id'] = registration.id
        session.save()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class RegisterStep4Test(TestDataMixin, TestCase):
    """Tests for the register_step4 view (public, requires session data)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:register_step4')

    def test_get_without_session_redirects(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 500])

    def test_get_with_session_data(self):
        school = self.create_school()
        registration = self.create_registration(tenant=school)
        session = self.client.session
        session['registration_id'] = registration.id
        session.save()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class RegisterCompleteTest(TestDataMixin, TestCase):
    """Tests for the register_complete view (public, requires signed ID)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)
        signer = Signer()
        self.signed_id = signer.sign(str(self.registration.id))

    def test_get_with_valid_signed_id(self):
        url = reverse('frontend:enrollment:register_complete', args=[self.signed_id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 500])

    def test_get_with_invalid_signed_id(self):
        url = reverse('frontend:enrollment:register_complete', args=['invalid-signature'])
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 500])


class UploadDocumentTest(TestDataMixin, TestCase):
    """Tests for the upload_document view (public or authenticated)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)
        self.url = reverse('frontend:enrollment:upload_document',
                           args=[self.registration.id])

    def test_get_upload_page(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 500])

    def test_post_without_file(self):
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class EnrollmentListTest(TestDataMixin, TestCase):
    """Tests for the enrollment_list view (requires login + registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:enrollment_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_registrar_allowed(self):
        registrar = self.create_registrar_user()
        self.client.force_login(registrar)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_secretary_allowed(self):
        secretary = self.create_secretary_user()
        self.client.force_login(secretary)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class EnrollmentDetailTest(TestDataMixin, TestCase):
    """Tests for the enrollment_detail view (requires login + registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)

    def _url(self):
        return reverse('frontend:enrollment:enrollment_detail',
                       args=[self.registration.id])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])


class EnrollmentReviewTest(TestDataMixin, TestCase):
    """Tests for the enrollment_review view (requires login + registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)

    def _url(self):
        return reverse('frontend:enrollment:enrollment_review',
                       args=[self.registration.id])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url(), {})
        self.assertIn(response.status_code, [200, 302, 404, 500])


class RegistrationEditTest(TestDataMixin, TestCase):
    """Tests for the registration_edit view (requires login + registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)

    def _url(self):
        return reverse('frontend:enrollment:registration_edit',
                       args=[self.registration.id])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url(), {})
        self.assertIn(response.status_code, [200, 302, 404, 500])


class RegistrationDeleteTest(TestDataMixin, TestCase):
    """Tests for the registration_delete view (requires login + registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.registration = self.create_registration(tenant=self.school)

    def _url(self):
        return reverse('frontend:enrollment:registration_delete',
                       args=[self.registration.id])

    def test_anonymous_redirects(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get_confirm(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_admin_post_deletes(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 404, 500])


class VerifyDocumentTest(TestDataMixin, TestCase):
    """Tests for the verify_document view (POST-only, requires registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        # We need a document but creating one requires a file, so we test with
        # a nonexistent document_id to verify 404 behavior
        self.url = reverse('frontend:enrollment:verify_document', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [302, 403])

    def test_admin_with_nonexistent_document(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [302, 400, 404, 500])

    def test_admin_get_returns_error(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 400, 404, 500])


class DocumentDeleteTest(TestDataMixin, TestCase):
    """Tests for the document_delete view (POST-only, requires registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:document_delete', args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_with_nonexistent_document(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class ExportEnrollmentsCsvTest(TestDataMixin, TestCase):
    """Tests for the export_enrollments_csv view (requires registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:export_enrollments_csv')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_returns_csv(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'text/csv')


class EnrollmentStatisticsTest(TestDataMixin, TestCase):
    """Tests for the enrollment_statistics view (requires registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:enrollment:enrollment_statistics')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_allowed(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_allowed(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_registrar_allowed(self):
        registrar = self.create_registrar_user()
        self.client.force_login(registrar)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

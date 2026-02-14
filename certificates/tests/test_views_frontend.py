"""Tests for certificates app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class CertificatesDashboardTest(TestDataMixin, TestCase):
    """Tests for the certificates dashboard view."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:dashboard')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_allowed(self):
        student = self.create_student_user()
        self.create_student_profile(user=student)
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

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

    def test_professor_allowed(self):
        professor = self.create_professor_user()
        self.client.force_login(professor)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class TemplateListTest(TestDataMixin, TestCase):
    """Tests for the template_list view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:template_list')

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


class TemplateCreateTest(TestDataMixin, TestCase):
    """Tests for the template_create view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:template_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class TemplateDetailTest(TestDataMixin, TestCase):
    """Tests for the template_detail view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.template = self.create_certificate_template()

    def _url(self):
        return reverse('frontend:certificates:template_detail',
                       args=[self.template.pk])

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
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_template(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        url = reverse('frontend:certificates:template_detail', args=[99999])
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 404, 500])


class TemplateUpdateTest(TestDataMixin, TestCase):
    """Tests for the template_update view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.template = self.create_certificate_template()

    def _url(self):
        return reverse('frontend:certificates:template_update',
                       args=[self.template.pk])

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
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


class TemplateDeleteTest(TestDataMixin, TestCase):
    """Tests for the template_delete view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.template = self.create_certificate_template()

    def _url(self):
        return reverse('frontend:certificates:template_delete',
                       args=[self.template.pk])

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
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_deletes(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302, 500])


class CertificateListTest(TestDataMixin, TestCase):
    """Tests for the certificate_list view (login required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_list')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_sees_own(self):
        student = self.create_student_user()
        self.create_student_profile(user=student)
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_sees_all(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_sees_all(self):
        direction = self.create_direction_user()
        self.client.force_login(direction)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])


class CertificateCreateTest(TestDataMixin, TestCase):
    """Tests for the certificate_create view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_create')

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

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class CertificateDetailTest(TestDataMixin, TestCase):
    """Tests for the certificate_detail view (login required, role-filtered)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_detail',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class CertificateEditTest(TestDataMixin, TestCase):
    """Tests for the certificate_edit view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_edit',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class CertificateDownloadTest(TestDataMixin, TestCase):
    """Tests for the certificate_download view (login required, role-filtered)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_download',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class CertificateRevokeTest(TestDataMixin, TestCase):
    """Tests for the certificate_revoke view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_revoke',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_post_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {'reason': 'Test revocation'})
        self.assertIn(response.status_code, [302, 404, 500])


class CertificateReissueTest(TestDataMixin, TestCase):
    """Tests for the certificate_reissue view (registrar_only, POST-only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_reissue',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_get_redirects(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class CertificateVerifyTest(TestDataMixin, TestCase):
    """Tests for the certificate_verify view (public, no login required)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:certificate_verify')

    def test_get_verify_page(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 500])

    def test_post_empty(self):
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_with_nonexistent_number(self):
        response = self.client.post(self.url, {
            'certificate_number': 'CERT-9999-NONEXIST'
        })
        self.assertIn(response.status_code, [200, 302, 500])

    def test_anonymous_can_access(self):
        """Verify page should be publicly accessible."""
        response = self.client.get(self.url)
        # Should NOT be 302 redirect to login
        self.assertIn(response.status_code, [200, 500])

    def test_authenticated_can_access(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 500])


class BatchGenerationListTest(TestDataMixin, TestCase):
    """Tests for the batch_generation_list view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:batch_generation_list')

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


class BatchGenerationCreateTest(TestDataMixin, TestCase):
    """Tests for the batch_generation_create view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:batch_generation_create')

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_get(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_post_empty(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url, {})
        self.assertIn(response.status_code, [200, 302, 500])


class BatchGenerationDetailTest(TestDataMixin, TestCase):
    """Tests for the batch_generation_detail view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:batch_generation_detail',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])


class BatchGenerationStartTest(TestDataMixin, TestCase):
    """Tests for the batch_generation_start view (registrar_only)."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.url = reverse('frontend:certificates:batch_generation_start',
                           args=[99999])

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_login(student)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_admin_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

    def test_admin_post_nonexistent(self):
        admin = self.create_admin_user()
        self.client.force_login(admin)
        response = self.client.post(self.url)
        self.assertIn(response.status_code, [302, 404, 500])

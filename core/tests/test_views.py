"""Tests for core app frontend views."""

from django.test import TestCase, Client
from django.urls import reverse

from core.models import Session, Semester, NewsAndEvents
from tests.helpers import TestDataMixin


class HomeViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()

    def test_login_required(self):
        response = self.client.get(reverse('frontend:core:home'))
        self.assertEqual(response.status_code, 302)

    def test_home_view_authenticated(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('frontend:core:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_context(self):
        self.client.force_login(self.admin)
        NewsAndEvents.objects.create(title='Test Item', posted_as='News')
        response = self.client.get(reverse('frontend:core:home'))
        self.assertEqual(response.status_code, 200)


class UnifiedDashboardTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_required(self):
        response = self.client.get(reverse('frontend:core:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_student_dashboard(self):
        user = self.create_student_user()
        self.client.force_login(user)
        response = self.client.get(reverse('frontend:core:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_professor_dashboard(self):
        user = self.create_professor_user()
        self.client.force_login(user)
        response = self.client.get(reverse('frontend:core:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard(self):
        user = self.create_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse('frontend:core:dashboard'))
        self.assertEqual(response.status_code, 200)


class SessionViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_session_list(self):
        response = self.client.get(reverse('frontend:core:session_list'))
        self.assertEqual(response.status_code, 200)

    def test_session_add_get(self):
        response = self.client.get(reverse('frontend:core:add_session'))
        self.assertEqual(response.status_code, 200)

    def test_session_add_post(self):
        response = self.client.post(reverse('frontend:core:add_session'), {
            'session': '2025/2026',
            'is_current_session': True,
        })
        self.assertIn(response.status_code, [200, 302])

    def test_session_update(self):
        session = self.create_session()
        response = self.client.get(
            reverse('frontend:core:edit_session', args=[session.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_session_delete(self):
        session = self.create_session()
        response = self.client.post(
            reverse('frontend:core:delete_session', args=[session.pk])
        )
        self.assertIn(response.status_code, [200, 302])


class SemesterViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_semester_list(self):
        response = self.client.get(reverse('frontend:core:semester_list'))
        self.assertEqual(response.status_code, 200)

    def test_semester_add_get(self):
        response = self.client.get(reverse('frontend:core:add_semester'))
        self.assertEqual(response.status_code, 200)

    def test_semester_add_post(self):
        session = self.create_session()
        response = self.client.post(reverse('frontend:core:add_semester'), {
            'semester': 'First',
            'is_current_semester': True,
            'session': session.pk,
        })
        self.assertIn(response.status_code, [200, 302])


class PostViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = self.create_admin_user()
        self.client.force_login(self.admin)

    def test_post_add_get(self):
        response = self.client.get(reverse('frontend:core:add_item'))
        self.assertEqual(response.status_code, 200)

    def test_post_add_post(self):
        response = self.client.post(reverse('frontend:core:add_item'), {
            'title': 'New Post',
            'summary': 'A summary',
            'posted_as': 'News',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_edit_post(self):
        item = NewsAndEvents.objects.create(
            title='Edit Me', posted_as='News'
        )
        response = self.client.get(
            reverse('frontend:core:edit_post', args=[item.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        item = NewsAndEvents.objects.create(
            title='Delete Me', posted_as='News'
        )
        response = self.client.post(
            reverse('frontend:core:delete_post', args=[item.pk])
        )
        self.assertIn(response.status_code, [200, 302])

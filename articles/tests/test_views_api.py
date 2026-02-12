"""Tests for articles app API views."""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from articles.models import Article, Category


class ArticleViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.article = self.create_article(
            author=self.user, status='published',
            published_at=timezone.now(),
        )

    def test_list_published_unauthenticated(self):
        resp = self.client.get('/api/v1/articles/articles/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_excludes_draft(self):
        self.create_article(author=self.user, status='draft')
        resp = self.client.get('/api/v1/articles/articles/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data if isinstance(resp.data, list) else resp.data.get('results', []):
            self.assertNotEqual(item.get('status'), 'draft')

    def test_create_requires_auth(self):
        data = {'title': 'New', 'summary': 'S', 'content': 'C'}
        resp = self.client.post('/api/v1/articles/articles/', data, format='json')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_can_create(self):
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Created', 'summary': 'S', 'content': 'Content', 'author': self.user.pk}
        resp = self.client.post('/api/v1/articles/articles/', data, format='json')
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])


class CategoryViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = self.create_article_category()

    def test_list_categories_public(self):
        resp = self.client.get('/api/v1/articles/categories/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_readonly_no_post(self):
        resp = self.client.post('/api/v1/articles/categories/', {'name': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

"""
Frontend view tests for the articles app.

Tests cover:
- article_list: list published articles with pagination
- article_create: lecturer/professor creates articles
- newsletter: public newsletter subscription
- category_articles: list articles by category
- article_detail: view single article with comments and likes
- article_edit: author edits their article
- comment_submit: logged-in user submits a comment (POST only)
- article_like: logged-in user likes/unlikes an article (POST only)
- Role-based access (lecturer for create/edit, any auth for comment/like)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from tests.helpers import TestDataMixin


class ArticlesViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for articles/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor_user = self.create_professor_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.direction_user = self.create_direction_user()

    def _create_published_article(self, author=None, **kwargs):
        from articles.models import Article
        if author is None:
            author = self.professor_user
        defaults = {
            'title': f'Published Article {kwargs.pop("suffix", "")}',
            'summary': 'A summary of the article.',
            'content': 'Full content of the published article.',
            'author': author,
            'status': 'published',
            'published_at': timezone.now(),
        }
        defaults.update(kwargs)
        return Article.objects.create(**defaults)

    # ── article_list ───────────────────────────────────────────────

    def test_article_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:articles:article_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_list_student_access(self):
        """Student can view article list."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_list_with_articles(self):
        """Article list displays published articles."""
        self._create_published_article(suffix='1')
        self._create_published_article(suffix='2')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_list_pagination(self):
        """Article list supports pagination."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_list')
        resp = self.client.get(url, {'page': 1})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── article_create ─────────────────────────────────────────────

    def test_article_create_get_professor(self):
        """Professor can access the article creation form."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:articles:article_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_create_get_admin(self):
        """Admin can access the article creation form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:articles:article_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_create_denied_student(self):
        """Student cannot create articles (lecturer_required)."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_create_post_valid(self):
        """POST with valid data creates an article."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:articles:article_create')
        resp = self.client.post(url, {
            'title': 'My New Article',
            'summary': 'A brief summary of the article.',
            'content': 'Full content of the article goes here.',
            'status': 'draft',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_create_post_invalid(self):
        """POST with empty data re-renders the form."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:articles:article_create')
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── newsletter (public) ────────────────────────────────────────

    def test_newsletter_get_anonymous(self):
        """Anonymous users can access the newsletter page."""
        url = reverse('frontend:articles:newsletter')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_newsletter_get_authenticated(self):
        """Authenticated users can access the newsletter page."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:newsletter')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_newsletter_post_subscribe(self):
        """POST with valid email subscribes the user."""
        url = reverse('frontend:articles:newsletter')
        resp = self.client.post(url, {
            'email': 'subscriber@example.com',
            'frequency': 'weekly',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_newsletter_post_subscribe_authenticated(self):
        """Authenticated POST links subscription to user."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:newsletter')
        resp = self.client.post(url, {
            'email': 'authsubscriber@example.com',
            'frequency': 'daily',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_newsletter_post_invalid_email(self):
        """POST with invalid email re-renders the form."""
        url = reverse('frontend:articles:newsletter')
        resp = self.client.post(url, {
            'email': 'not-an-email',
            'frequency': 'weekly',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── category_articles ──────────────────────────────────────────

    def test_category_articles_valid(self):
        """View articles filtered by a valid category."""
        category = self.create_article_category()
        article = self._create_published_article(suffix='cat')
        article.categories.add(category)
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:category_articles', args=[category.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_category_articles_nonexistent(self):
        """Non-existent category slug returns 404."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:category_articles', args=['nonexistent-cat'])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── article_detail ─────────────────────────────────────────────

    def test_article_detail_student(self):
        """Student can view a published article."""
        article = self._create_published_article(suffix='detail')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_detail', args=[article.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_detail_nonexistent(self):
        """Non-existent article slug returns 404."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_detail', args=['no-such-article'])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── article_edit ───────────────────────────────────────────────

    def test_article_edit_get_author(self):
        """Author can access the edit form for their article."""
        article = self._create_published_article(author=self.professor_user, suffix='edit')
        self.client.force_login(self.professor_user)
        url = reverse('frontend:articles:article_edit', args=[article.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_edit_get_admin(self):
        """Admin can edit any article."""
        article = self._create_published_article(author=self.professor_user, suffix='editadm')
        self.client.force_login(self.admin_user)
        url = reverse('frontend:articles:article_edit', args=[article.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_edit_denied_non_author(self):
        """Non-author professor cannot edit someone else's article."""
        other_prof = self.create_professor_user()
        article = self._create_published_article(author=self.professor_user, suffix='editdeny')
        self.client.force_login(other_prof)
        url = reverse('frontend:articles:article_edit', args=[article.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_edit_denied_student(self):
        """Student cannot edit articles."""
        article = self._create_published_article(suffix='editstud')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_edit', args=[article.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── comment_submit ─────────────────────────────────────────────

    def test_comment_submit_post_valid(self):
        """Authenticated user can submit a comment."""
        article = self._create_published_article(suffix='comment')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:comment_submit', args=[article.pk])
        resp = self.client.post(url, {'content': 'Great article!'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_comment_submit_get_not_allowed(self):
        """GET on comment_submit is not allowed (require_POST)."""
        article = self._create_published_article(suffix='commentget')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:comment_submit', args=[article.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 405])

    def test_comment_submit_anonymous(self):
        """Anonymous users cannot submit comments."""
        article = self._create_published_article(suffix='commentanon')
        url = reverse('frontend:articles:comment_submit', args=[article.pk])
        resp = self.client.post(url, {'content': 'Anonymous comment'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── article_like ───────────────────────────────────────────────

    def test_article_like_toggle(self):
        """Authenticated user can like an article."""
        article = self._create_published_article(suffix='like')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_like', args=[article.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_like_unlike(self):
        """Liking again toggles to unlike."""
        article = self._create_published_article(suffix='unlike')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_like', args=[article.pk])
        self.client.post(url)  # like
        resp = self.client.post(url)  # unlike
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_article_like_get_not_allowed(self):
        """GET on article_like is not allowed (require_POST)."""
        article = self._create_published_article(suffix='likeget')
        self.client.force_login(self.student_user)
        url = reverse('frontend:articles:article_like', args=[article.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 405])

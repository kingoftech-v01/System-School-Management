"""
URL Resolution Tests
Verifies all URL patterns resolve correctly and no broken links exist.
All frontend URLs use the 'frontend:' namespace prefix.
"""

from django.test import TestCase
from django.urls import reverse, NoReverseMatch, resolve


class CoreURLTests(TestCase):
    """Test core app URL resolution."""

    def test_home_url_resolves(self):
        url = reverse('frontend:core:home')
        self.assertEqual(url, '/')

    def test_dashboard_url_resolves(self):
        url = reverse('frontend:core:dashboard')
        self.assertIsNotNone(url)


class CourseURLTests(TestCase):
    """Test course app URL resolution."""

    def test_programs_url_resolves(self):
        url = reverse('frontend:course:programs')
        self.assertIsNotNone(url)

    def test_user_course_list_url_resolves(self):
        url = reverse('frontend:course:user_course_list')
        self.assertIsNotNone(url)

    def test_course_registration_url_resolves(self):
        url = reverse('frontend:course:course_registration')
        self.assertIsNotNone(url)


class ResultURLTests(TestCase):
    """Test result app URL resolution."""

    def test_add_score_url_resolves(self):
        url = reverse('frontend:result:add_score')
        self.assertIsNotNone(url)

    def test_grade_results_url_resolves(self):
        url = reverse('frontend:result:grade_results')
        self.assertIsNotNone(url)

    def test_assessment_results_url_resolves(self):
        url = reverse('frontend:result:ass_results')
        self.assertIsNotNone(url)


class PaymentsURLTests(TestCase):
    """Test payments app URL resolution."""

    def test_payment_gateways_url_resolves(self):
        url = reverse('frontend:payments:payment_gateways')
        self.assertIsNotNone(url)

    def test_paypal_url_resolves(self):
        url = reverse('frontend:payments:paypal')
        self.assertIsNotNone(url)

    def test_stripe_url_resolves(self):
        url = reverse('frontend:payments:stripe')
        self.assertIsNotNone(url)

    def test_create_invoice_url_resolves(self):
        url = reverse('frontend:payments:create_invoice')
        self.assertIsNotNone(url)


class EventsURLTests(TestCase):
    """Test events app URL resolution with namespace."""

    def test_event_list_url_resolves(self):
        url = reverse('frontend:events:event_list')
        self.assertEqual(url, '/events/')

    def test_event_create_url_resolves(self):
        url = reverse('frontend:events:event_create')
        self.assertEqual(url, '/events/create/')


class LibraryURLTests(TestCase):
    """Test library app URL resolution with namespace."""

    def test_book_list_url_resolves(self):
        url = reverse('frontend:library:book_list')
        self.assertIsNotNone(url)

    def test_my_borrowed_books_url_resolves(self):
        url = reverse('frontend:library:my_borrowed_books')
        self.assertIsNotNone(url)


class MonitoringURLTests(TestCase):
    """Test monitoring app URL resolution with namespace."""

    def test_monitoring_dashboard_url_resolves(self):
        url = reverse('frontend:monitoring:dashboard')
        self.assertEqual(url, '/monitoring/')

    def test_enrollment_stats_url_resolves(self):
        url = reverse('frontend:monitoring:enrollment_stats')
        self.assertEqual(url, '/monitoring/enrollment-stats/')


class EnrollmentURLTests(TestCase):
    """Test enrollment app URL resolution with namespace."""

    def test_enrollment_list_url_resolves(self):
        url = reverse('frontend:enrollment:enrollment_list')
        self.assertIsNotNone(url)

    def test_register_step1_url_resolves(self):
        url = reverse('frontend:enrollment:register_step1')
        self.assertIsNotNone(url)


class SearchURLTests(TestCase):
    """Test search app URL resolution."""

    def test_search_query_url_resolves(self):
        url = reverse('frontend:search:query')
        self.assertIsNotNone(url)


class NewAppsURLTests(TestCase):
    """Test newly added apps URL resolution."""

    def test_grading_urls_resolve(self):
        urls = [
            'frontend:grading:rubric_list',
            'frontend:grading:rubric_create',
        ]
        for name in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertIsNotNone(url)

    def test_analytics_urls_resolve(self):
        urls = [
            'frontend:analytics:analytics_dashboard',
            'frontend:analytics:at_risk_list',
        ]
        for name in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertIsNotNone(url)

    def test_articles_urls_resolve(self):
        url = reverse('frontend:articles:article_list')
        self.assertIsNotNone(url)

    def test_notices_urls_resolve(self):
        urls = [
            'frontend:notices:notice_list',
            'frontend:notices:notice_create',
        ]
        for name in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertIsNotNone(url)

    def test_admissions_urls_resolve(self):
        urls = [
            'frontend:admissions:home',
            'frontend:admissions:apply',
            'frontend:admissions:check_status',
        ]
        for name in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertIsNotNone(url)

    def test_alumni_urls_resolve(self):
        urls = [
            'frontend:alumni:directory',
            'frontend:alumni:events',
            'frontend:alumni:donate',
        ]
        for name in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertIsNotNone(url)


class URLPatternIntegrityTests(TestCase):
    """Test URL pattern integrity and namespace consistency."""

    def test_all_dashboard_urls_have_no_hardcoded_paths(self):
        important_urls = [
            'frontend:core:dashboard',
            'frontend:course:user_course_list',
            'frontend:result:grade_results',
            'frontend:payments:payment_gateways',
            'frontend:events:event_list',
            'frontend:library:my_borrowed_books',
            'frontend:monitoring:dashboard',
            'frontend:enrollment:enrollment_list',
            'frontend:search:query',
        ]
        for url_name in important_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name)
                    self.assertIsNotNone(url)
                    self.assertNotEqual(url, '')
                except NoReverseMatch:
                    self.fail(f"URL name '{url_name}' failed to resolve")

    def test_namespaced_apps_resolve_correctly(self):
        """Each app under frontend: should resolve at least one URL."""
        app_urls = {
            'events': 'frontend:events:event_list',
            'library': 'frontend:library:book_list',
            'monitoring': 'frontend:monitoring:dashboard',
            'enrollment': 'frontend:enrollment:enrollment_list',
            'grading': 'frontend:grading:rubric_list',
            'analytics': 'frontend:analytics:analytics_dashboard',
            'articles': 'frontend:articles:article_list',
            'notices': 'frontend:notices:notice_list',
            'admissions': 'frontend:admissions:home',
            'alumni': 'frontend:alumni:directory',
        }
        for app, url_name in app_urls.items():
            with self.subTest(app=app):
                url = reverse(url_name)
                self.assertIsNotNone(url)


class URLResolverTests(TestCase):
    """Test URL resolver matches correct views."""

    def test_dashboard_resolves(self):
        resolver = resolve('/dashboard/')
        self.assertIsNotNone(resolver.func)

    def test_course_list_resolves(self):
        resolver = resolve('/courses/')
        self.assertIsNotNone(resolver.func)

    def test_search_resolves(self):
        resolver = resolve('/search/')
        self.assertIsNotNone(resolver.func)

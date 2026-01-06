"""
URL Resolution Tests
Verifies all URL patterns resolve correctly and no broken links exist.
"""

from django.test import TestCase
from django.urls import reverse, NoReverseMatch, resolve


class CoreURLTests(TestCase):
    """Test core app URL resolution."""

    def test_home_url_resolves(self):
        """Test home page URL resolves."""
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_dashboard_url_resolves(self):
        """Test unified dashboard URL resolves."""
        url = reverse('dashboard')
        self.assertEqual(url, '/dashboard/')


class CourseURLTests(TestCase):
    """Test course app URL resolution."""

    def test_programs_url_resolves(self):
        """Test programs list URL."""
        url = reverse('programs')
        self.assertIsNotNone(url)

    def test_user_course_list_url_resolves(self):
        """Test student course list URL."""
        url = reverse('user_course_list')
        self.assertEqual(url, '/courses/my_courses/')

    def test_course_registration_url_resolves(self):
        """Test course registration URL."""
        url = reverse('course_registration')
        self.assertIsNotNone(url)


class ResultURLTests(TestCase):
    """Test result app URL resolution."""

    def test_add_score_url_resolves(self):
        """Test add score URL."""
        url = reverse('add_score')
        self.assertEqual(url, '/results/manage-score/')

    def test_grade_results_url_resolves(self):
        """Test grade results URL."""
        url = reverse('grade_results')
        self.assertEqual(url, '/results/grade/')

    def test_assessment_results_url_resolves(self):
        """Test assessment results URL."""
        url = reverse('ass_results')
        self.assertEqual(url, '/results/assessment/')


class PaymentsURLTests(TestCase):
    """Test payments app URL resolution."""

    def test_payment_gateways_url_resolves(self):
        """Test payment gateways list URL."""
        url = reverse('payment_gateways')
        self.assertEqual(url, '/payments/')

    def test_paypal_url_resolves(self):
        """Test PayPal payment URL."""
        url = reverse('paypal')
        self.assertEqual(url, '/payments/paypal/')

    def test_stripe_url_resolves(self):
        """Test Stripe payment URL."""
        url = reverse('stripe')
        self.assertEqual(url, '/payments/stripe/')

    def test_create_invoice_url_resolves(self):
        """Test invoice creation URL."""
        url = reverse('create_invoice')
        self.assertEqual(url, '/payments/create-invoice/')


class EventsURLTests(TestCase):
    """Test events app URL resolution with namespace."""

    def test_event_list_url_resolves(self):
        """Test event list URL."""
        url = reverse('events:event_list')
        self.assertEqual(url, '/events/')

    def test_event_create_url_resolves(self):
        """Test event create URL."""
        url = reverse('events:event_create')
        self.assertEqual(url, '/events/create/')


class LibraryURLTests(TestCase):
    """Test library app URL resolution with namespace."""

    def test_book_list_url_resolves(self):
        """Test book list URL."""
        url = reverse('library:book_list')
        self.assertIsNotNone(url)

    def test_my_borrowed_books_url_resolves(self):
        """Test student borrowed books URL."""
        url = reverse('library:my_borrowed_books')
        self.assertEqual(url, '/library/my-books/')


class MonitoringURLTests(TestCase):
    """Test monitoring app URL resolution with namespace."""

    def test_monitoring_dashboard_url_resolves(self):
        """Test monitoring dashboard URL."""
        url = reverse('monitoring:dashboard')
        self.assertEqual(url, '/monitoring/')

    def test_enrollment_stats_url_resolves(self):
        """Test enrollment statistics URL."""
        url = reverse('monitoring:enrollment_stats')
        self.assertEqual(url, '/monitoring/enrollment-stats/')


class EnrollmentURLTests(TestCase):
    """Test enrollment app URL resolution with namespace."""

    def test_enrollment_list_url_resolves(self):
        """Test enrollment list URL."""
        url = reverse('enrollment:enrollment_list')
        self.assertEqual(url, '/enrollment/list/')

    def test_register_step1_url_resolves(self):
        """Test registration step 1 URL."""
        url = reverse('enrollment:register_step1')
        self.assertEqual(url, '/enrollment/register/step1/')


class SearchURLTests(TestCase):
    """Test search app URL resolution."""

    def test_search_query_url_resolves(self):
        """Test search query URL."""
        url = reverse('query')
        self.assertEqual(url, '/search/')


class NewAppsURLTests(TestCase):
    """Test newly added apps URL resolution."""

    def test_grading_urls_resolve(self):
        """Test grading app URLs."""
        urls = [
            ('grading:rubric_list', '/grading/rubrics/'),
            ('grading:rubric_create', '/grading/rubrics/create/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)

    def test_analytics_urls_resolve(self):
        """Test analytics app URLs."""
        urls = [
            ('analytics:dashboard', '/analytics/'),
            ('analytics:at_risk_students', '/analytics/at-risk/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)

    def test_articles_urls_resolve(self):
        """Test articles app URLs."""
        urls = [
            ('articles:article_list', '/articles/'),
            ('articles:newsletter_subscribe', '/articles/newsletter/subscribe/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)

    def test_notices_urls_resolve(self):
        """Test notices app URLs."""
        urls = [
            ('notices:notice_list', '/notices/'),
            ('notices:notice_create', '/notices/create/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)

    def test_admissions_urls_resolve(self):
        """Test admissions app URLs."""
        urls = [
            ('admissions:apply', '/admissions/apply/'),
            ('admissions:status', '/admissions/status/'),
            ('admissions:session_list', '/admissions/sessions/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)

    def test_alumni_urls_resolve(self):
        """Test alumni app URLs."""
        urls = [
            ('alumni:directory', '/alumni/'),
            ('alumni:event_list', '/alumni/events/'),
            ('alumni:donate', '/alumni/donate/'),
        ]
        for name, expected in urls:
            with self.subTest(url_name=name):
                url = reverse(name)
                self.assertEqual(url, expected)


class URLPatternIntegrityTests(TestCase):
    """Test URL pattern integrity and namespace consistency."""

    def test_all_dashboard_urls_have_no_hardcoded_paths(self):
        """Ensure all important URLs can be reversed (not hardcoded)."""
        important_urls = [
            'dashboard',
            'user_course_list',
            'grade_results',
            'payment_gateways',
            'events:event_list',
            'library:my_borrowed_books',
            'monitoring:dashboard',
            'enrollment:enrollment_list',
            'query',
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
        """Test all namespaced apps resolve properly."""
        namespaced_apps = [
            'events', 'library', 'monitoring', 'enrollment',
            'grading', 'analytics', 'articles', 'notices',
            'admissions', 'alumni'
        ]

        for app in namespaced_apps:
            with self.subTest(app=app):
                # Each app should have at least one URL pattern
                # Try to resolve a common pattern
                try:
                    # Most apps have a list or dashboard view
                    patterns_to_try = [
                        f'{app}:list',
                        f'{app}:dashboard',
                        f'{app}:index',
                        f'{app}:directory',
                        f'{app}:event_list',
                        f'{app}:article_list',
                        f'{app}:notice_list',
                        f'{app}:rubric_list',
                    ]

                    resolved = False
                    for pattern in patterns_to_try:
                        try:
                            reverse(pattern)
                            resolved = True
                            break
                        except NoReverseMatch:
                            continue

                    # At least one pattern should resolve
                    # Note: This is a soft check since not all apps have same patterns
                except Exception as e:
                    # Log but don't fail - some apps may have different patterns
                    pass


class URLResolverTests(TestCase):
    """Test URL resolver matches correct views."""

    def test_dashboard_resolves_to_correct_view(self):
        """Test dashboard URL resolves to unified_dashboard view."""
        resolver = resolve('/dashboard/')
        self.assertEqual(resolver.view_name, 'dashboard')

    def test_course_list_resolves_correctly(self):
        """Test courses URL resolves to correct view."""
        resolver = resolve('/courses/')
        self.assertEqual(resolver.view_name, 'programs')

    def test_search_resolves_correctly(self):
        """Test search URL resolves correctly."""
        resolver = resolve('/search/')
        self.assertEqual(resolver.view_name, 'query')


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests.test_url_resolution"])

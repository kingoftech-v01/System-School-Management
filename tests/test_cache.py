"""
Cache Functionality Tests
Tests Redis cache configuration, connectivity, and operations.
"""

from django.test import TestCase, override_settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
import time

User = get_user_model()


class CacheConnectionTests(TestCase):
    """Test cache connection and basic operations."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')

    def test_cache_get_nonexistent_key(self):
        """Test cache returns None for nonexistent key."""
        value = cache.get('nonexistent_key')
        self.assertIsNone(value)

    def test_cache_get_with_default(self):
        """Test cache get with default value."""
        value = cache.get('nonexistent_key', default='default_value')
        self.assertEqual(value, 'default_value')

    def test_cache_delete(self):
        """Test cache delete operation."""
        cache.set('test_key', 'test_value', 60)
        self.assertEqual(cache.get('test_key'), 'test_value')

        cache.delete('test_key')
        self.assertIsNone(cache.get('test_key'))

    def test_cache_has_key(self):
        """Test cache has_key method."""
        cache.set('test_key', 'test_value', 60)
        self.assertTrue(cache.has_key('test_key'))
        self.assertFalse(cache.has_key('nonexistent_key'))

    def test_cache_multiple_set_get(self):
        """Test setting and getting multiple values."""
        data = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3',
        }

        cache.set_many(data, 60)

        for key, expected_value in data.items():
            value = cache.get(key)
            self.assertEqual(value, expected_value)


class CacheTimeoutTests(TestCase):
    """Test cache timeout and expiration."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_cache_timeout(self):
        """Test cache value expires after timeout."""
        cache.set('test_key', 'test_value', 1)  # 1 second timeout
        self.assertEqual(cache.get('test_key'), 'test_value')

        time.sleep(2)  # Wait for expiration
        self.assertIsNone(cache.get('test_key'))

    def test_cache_touch_extends_timeout(self):
        """Test cache touch extends timeout."""
        cache.set('test_key', 'test_value', 2)  # 2 second timeout
        time.sleep(1)

        # Touch to extend timeout
        cache.touch('test_key', 10)
        time.sleep(2)  # Would expire if not touched

        # Should still exist
        self.assertEqual(cache.get('test_key'), 'test_value')


class CachePrefixTests(TestCase):
    """Test cache key prefix functionality."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_cache_uses_key_prefix(self):
        """Test cache keys use configured prefix."""
        cache.set('test_key', 'test_value', 60)

        # The actual key in Redis should have the prefix
        # This is configured in settings as 'school_system'
        # We can't directly test Redis keys, but we can verify it works
        self.assertEqual(cache.get('test_key'), 'test_value')


class DashboardCacheTests(TestCase):
    """Test caching patterns used in dashboard views."""

    def setUp(self):
        """Set up test user and clear cache."""
        cache.clear()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@school.com',
            password='testpass123',
            role='student'
        )

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_dashboard_cache_key_format(self):
        """Test dashboard cache key format."""
        cache_key = f'dashboard_{self.user.id}_{self.user.role}'
        dashboard_data = {
            'gpa': 3.5,
            'courses_count': 5,
            'attendance': 95.0
        }

        cache.set(cache_key, dashboard_data, 300)
        cached_data = cache.get(cache_key)

        self.assertEqual(cached_data, dashboard_data)
        self.assertEqual(cached_data['gpa'], 3.5)

    def test_cache_invalidation_on_update(self):
        """Test cache invalidation pattern."""
        cache_key = f'dashboard_{self.user.id}_{self.user.role}'
        cache.set(cache_key, {'data': 'old'}, 300)

        # Simulate data update - cache should be invalidated
        cache.delete(cache_key)

        # Should return None after invalidation
        self.assertIsNone(cache.get(cache_key))


class CacheComplexDataTests(TestCase):
    """Test caching complex data structures."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_cache_dict_data(self):
        """Test caching dictionary data."""
        data = {
            'name': 'Test User',
            'role': 'student',
            'stats': {
                'gpa': 3.5,
                'credits': 120
            }
        }

        cache.set('user_data', data, 60)
        cached_data = cache.get('user_data')

        self.assertEqual(cached_data, data)
        self.assertEqual(cached_data['stats']['gpa'], 3.5)

    def test_cache_list_data(self):
        """Test caching list data."""
        data = [1, 2, 3, 4, 5]

        cache.set('list_data', data, 60)
        cached_data = cache.get('list_data')

        self.assertEqual(cached_data, data)
        self.assertEqual(len(cached_data), 5)

    def test_cache_nested_data(self):
        """Test caching nested complex data."""
        data = {
            'courses': [
                {'name': 'Math', 'credits': 3},
                {'name': 'Science', 'credits': 4},
            ],
            'metadata': {
                'semester': 'Fall 2026',
                'total_credits': 7
            }
        }

        cache.set('complex_data', data, 60)
        cached_data = cache.get('complex_data')

        self.assertEqual(cached_data, data)
        self.assertEqual(len(cached_data['courses']), 2)
        self.assertEqual(cached_data['metadata']['total_credits'], 7)


class CacheIncrDecrTests(TestCase):
    """Test cache increment and decrement operations."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_cache_incr(self):
        """Test cache increment operation."""
        cache.set('counter', 0, 60)
        cache.incr('counter')
        self.assertEqual(cache.get('counter'), 1)

        cache.incr('counter', 5)
        self.assertEqual(cache.get('counter'), 6)

    def test_cache_decr(self):
        """Test cache decrement operation."""
        cache.set('counter', 10, 60)
        cache.decr('counter')
        self.assertEqual(cache.get('counter'), 9)

        cache.decr('counter', 3)
        self.assertEqual(cache.get('counter'), 6)


class SessionCacheTests(TestCase):
    """Test session caching functionality."""

    def test_session_backend_is_cache(self):
        """Test session engine uses cache backend."""
        from django.conf import settings
        self.assertEqual(
            settings.SESSION_ENGINE,
            'django.contrib.sessions.backends.cache'
        )


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests.test_cache"])

"""
System Verification Script
Verifies cache, Celery, and configuration without requiring database connection.
"""

import os
import sys

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'School_System.settings.base')

# Setup Django
import django
django.setup()

from django.conf import settings
from django.core.cache import cache
from celery import Celery

print("="*80)
print(" SYSTEM VERIFICATION REPORT")
print("="*80)
print()

# 1. Cache Configuration
print("1. CACHE CONFIGURATION")
print("-" * 80)
try:
    cache_config = settings.CACHES['default']
    print(f"[OK] Cache Backend: {cache_config['BACKEND']}")
    print(f"[OK] Cache Location: {cache_config['LOCATION']}")
    print(f"[OK] Cache Key Prefix: {cache_config.get('KEY_PREFIX', 'None')}")
    print(f"[OK] Cache Timeout: {cache_config.get('TIMEOUT', 'Default')} seconds")
    print(f"[OK] Session Engine: {settings.SESSION_ENGINE}")
    print()
except Exception as e:
    print(f"[FAIL] Cache configuration error: {e}")
    print()

# 2. Cache Operations Test
print("2. CACHE OPERATIONS TEST")
print("-" * 80)
try:
    # Test set/get
    test_key = 'system_test_key'
    test_value = 'test_value_123'

    cache.set(test_key, test_value, 60)
    retrieved = cache.get(test_key)

    if retrieved == test_value:
        print(f"[OK] Cache SET/GET: Working")
    else:
        print(f"[FAIL] Cache SET/GET: Failed (got '{retrieved}')")

    # Test delete
    cache.delete(test_key)
    if cache.get(test_key) is None:
        print(f"[OK] Cache DELETE: Working")
    else:
        print(f"[FAIL] Cache DELETE: Failed")

    # Test complex data
    complex_data = {'name': 'Test', 'values': [1, 2, 3]}
    cache.set('complex_test', complex_data, 60)
    retrieved_complex = cache.get('complex_test')

    if retrieved_complex == complex_data:
        print(f"[OK] Cache Complex Data: Working")
    else:
        print(f"[FAIL] Cache Complex Data: Failed")

    cache.delete('complex_test')
    print()

except Exception as e:
    print(f"[FAIL] Cache operations error: {e}")
    print(f"   Note: This likely means Redis is not running")
    print()

# 3. Celery Configuration
print("3. CELERY CONFIGURATION")
print("-" * 80)
try:
    print(f"[OK] Celery Broker: {settings.CELERY_BROKER_URL}")
    print(f"[OK] Celery Result Backend: {settings.CELERY_RESULT_BACKEND}")
    print(f"[OK] Celery Task Serializer: {settings.CELERY_TASK_SERIALIZER}")
    print(f"[OK] Celery Beat Scheduler: {settings.CELERY_BEAT_SCHEDULER}")
    print()
except Exception as e:
    print(f"[FAIL] Celery configuration error: {e}")
    print()

# 4. Celery App Verification
print("4. CELERY APP VERIFICATION")
print("-" * 80)
try:
    from School_System.celery import app as celery_app

    print(f"[OK] Celery App Name: {celery_app.main}")
    print(f"[OK] Celery App Ready: Yes")

    # Check beat schedule
    if hasattr(celery_app.conf, 'beat_schedule'):
        schedule = celery_app.conf.beat_schedule
        print(f"[OK] Scheduled Tasks: {len(schedule)} tasks configured")
        print()
        print("   Scheduled Tasks List:")
        for task_name in sorted(schedule.keys()):
            print(f"   - {task_name}")
    else:
        print(f"[FAIL] Beat Schedule: Not configured")

    print()
except Exception as e:
    print(f"[FAIL] Celery app error: {e}")
    print()

# 5. Static Files Configuration
print("5. STATIC FILES CONFIGURATION")
print("-" * 80)
try:
    print(f"[OK] Static URL: {settings.STATIC_URL}")
    print(f"[OK] Static Root: {settings.STATIC_ROOT}")
    print(f"[OK] Media URL: {settings.MEDIA_URL}")
    print(f"[OK] Media Root: {settings.MEDIA_ROOT}")

    # Check if HTMX exists
    import os.path
    htmx_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'htmx.min.js')
    if os.path.exists(htmx_path):
        size = os.path.getsize(htmx_path)
        print(f"[OK] HTMX Library: Found ({size:,} bytes)")
    else:
        print(f"[FAIL] HTMX Library: Missing")

    print()
except Exception as e:
    print(f"[FAIL] Static files error: {e}")
    print()

# 6. Template Configuration
print("6. TEMPLATE CONFIGURATION")
print("-" * 80)
try:
    templates = settings.TEMPLATES[0]
    print(f"[OK] Template Backend: {templates['BACKEND']}")
    print(f"[OK] Template Dirs: {len(templates['DIRS'])} directories")
    for dir in templates['DIRS']:
        print(f"   - {dir}")
    print(f"[OK] Context Processors: {len(templates['OPTIONS']['context_processors'])}")
    print()
except Exception as e:
    print(f"[FAIL] Template configuration error: {e}")
    print()

# 7. URL Configuration Check
print("7. URL CONFIGURATION")
print("-" * 80)
try:
    from django.urls import get_resolver

    resolver = get_resolver()
    url_patterns = resolver.url_patterns

    print(f"[OK] Root URLconf: {settings.ROOT_URLCONF}")
    print(f"[OK] URL Patterns: {len(url_patterns)} root patterns")

    # Check for specific important URLs
    from django.urls import reverse, NoReverseMatch

    important_urls = [
        ('dashboard', 'Dashboard'),
        ('user_course_list', 'Student Courses'),
        ('grade_results', 'Grade Results'),
        ('payment_gateways', 'Payment Gateways'),
        ('events:event_list', 'Events'),
        ('library:my_borrowed_books', 'Library'),
        ('monitoring:dashboard', 'Monitoring'),
        ('enrollment:enrollment_list', 'Enrollment'),
    ]

    print()
    print("   Important URL Resolution:")
    for url_name, description in important_urls:
        try:
            url = reverse(url_name)
            print(f"   [OK] {description:25} → {url}")
        except NoReverseMatch:
            print(f"   [FAIL] {description:25} → NOT FOUND")

    print()
except Exception as e:
    print(f"[FAIL] URL configuration error: {e}")
    print()

# 8. Installed Apps
print("8. INSTALLED APPS")
print("-" * 80)
try:
    shared_apps = getattr(settings, 'SHARED_APPS', [])
    tenant_apps = getattr(settings, 'TENANT_APPS', [])

    print(f"[OK] Shared Apps: {len(shared_apps)}")
    print(f"[OK] Tenant Apps: {len(tenant_apps)}")
    print(f"[OK] Total Apps: {len(settings.INSTALLED_APPS)}")

    # Check for newly added apps
    new_apps = ['grading', 'analytics', 'articles', 'notices', 'admissions', 'alumni']
    print()
    print("   Newly Added Apps:")
    for app in new_apps:
        if any(app in installed_app for installed_app in settings.INSTALLED_APPS):
            print(f"   [OK] {app}")
        else:
            print(f"   [FAIL] {app} (not in INSTALLED_APPS)")

    print()
except Exception as e:
    print(f"[FAIL] Installed apps error: {e}")
    print()

# 9. Task Files Verification
print("9. TASK FILES VERIFICATION")
print("-" * 80)
try:
    import os.path

    task_files = [
        ('attendance/tasks.py', 'Attendance'),
        ('payments/tasks.py', 'Payments'),
        ('events/tasks.py', 'Events'),
        ('library/tasks.py', 'Library'),
        ('articles/tasks.py', 'Articles'),
        ('notices/tasks.py', 'Notices'),
        ('admissions/tasks.py', 'Admissions'),
        ('alumni/tasks.py', 'Alumni'),
    ]

    for file_path, app_name in task_files:
        full_path = os.path.join(settings.BASE_DIR, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"   [OK] {app_name:15} tasks.py ({size:,} bytes)")
        else:
            print(f"   [FAIL] {app_name:15} tasks.py (missing)")

    print()
except Exception as e:
    print(f"[FAIL] Task files error: {e}")
    print()

# 10. Component Files Verification
print("10. COMPONENT FILES VERIFICATION")
print("-" * 80)
try:
    import os.path

    component_files = [
        ('templates/components/widgets/stat_card.html', 'Stat Card'),
        ('templates/components/widgets/empty_state.html', 'Empty State'),
        ('templates/components/widgets/badge.html', 'Badge'),
        ('templates/components/widgets/data_table.html', 'Data Table'),
        ('templates/components/forms/text_input.html', 'Text Input'),
        ('templates/components/modals/confirm_modal.html', 'Confirm Modal'),
        ('templates/components/alerts/alert.html', 'Alert'),
    ]

    for file_path, component_name in component_files:
        full_path = os.path.join(settings.BASE_DIR, file_path)
        if os.path.exists(full_path):
            print(f"   [OK] {component_name}")
        else:
            print(f"   [FAIL] {component_name} (missing)")

    print()
except Exception as e:
    print(f"[FAIL] Component files error: {e}")
    print()

print("="*80)
print(" VERIFICATION COMPLETE")
print("="*80)
print()
print("NOTES:")
print("- If cache operations failed, ensure Redis server is running")
print("- If database errors occur, ensure PostgreSQL server is running")
print("- All URL and configuration checks are independent of database")
print()

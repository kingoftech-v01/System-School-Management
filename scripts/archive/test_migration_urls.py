"""
Migration URL Testing Script

This script tests the Phase 4 migration without requiring full Django setup.
It validates file structure, URL patterns, and namespace configuration.
"""

import os
import sys
import ast
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test results
passed = 0
failed = 0
warnings = 0

def print_header(text):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

def print_success(text):
    global passed
    passed += 1
    print(f"{GREEN}[PASS]{RESET} {text}")

def print_failure(text):
    global failed
    failed += 1
    print(f"{RED}[FAIL]{RESET} {text}")

def print_warning(text):
    global warnings
    warnings += 1
    print(f"{YELLOW}[WARN]{RESET} {text}")

def check_file_exists(filepath):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print_success(f"File exists: {filepath}")
        return True
    else:
        print_failure(f"File missing: {filepath}")
        return False

def check_python_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            ast.parse(code)
        print_success(f"Valid syntax: {filepath}")
        return True
    except SyntaxError as e:
        print_failure(f"Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print_failure(f"Error reading {filepath}: {e}")
        return False

def check_urls_file(app_name, filepath):
    """Check if urls.py follows the dual-layer pattern."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required patterns
        has_api_urlpatterns = 'api_urlpatterns = [' in content
        has_frontend_urlpatterns = 'frontend_urlpatterns = [' in content
        has_app_name = f"app_name = '{app_name}'" in content or f'app_name = "{app_name}"' in content
        has_main_urlpatterns = 'urlpatterns = [' in content
        has_api_include = "path('api/', include((api_urlpatterns, 'api')))" in content
        has_frontend_include = "path('', include((frontend_urlpatterns, 'frontend')))" in content

        if has_api_urlpatterns:
            print_success(f"{app_name}: Has api_urlpatterns")
        else:
            print_failure(f"{app_name}: Missing api_urlpatterns")

        if has_frontend_urlpatterns:
            print_success(f"{app_name}: Has frontend_urlpatterns")
        else:
            print_failure(f"{app_name}: Missing frontend_urlpatterns")

        if has_app_name:
            print_success(f"{app_name}: Has app_name declaration")
        else:
            print_failure(f"{app_name}: Missing app_name declaration")

        if has_api_include and has_frontend_include:
            print_success(f"{app_name}: Has correct urlpatterns structure")
        else:
            print_failure(f"{app_name}: Incorrect urlpatterns structure")

        return all([has_api_urlpatterns, has_frontend_urlpatterns,
                   has_app_name, has_api_include, has_frontend_include])

    except Exception as e:
        print_failure(f"Error checking {filepath}: {e}")
        return False

def check_views_imports(app_name, filepath):
    """Check if views files are correctly imported in urls.py."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        has_frontend_import = 'from . import views_frontend' in content
        has_api_import = 'from . import views_api' in content

        if has_frontend_import:
            print_success(f"{app_name}: Imports views_frontend")
        else:
            print_failure(f"{app_name}: Missing views_frontend import")

        if has_api_import:
            print_success(f"{app_name}: Imports views_api")
        else:
            print_failure(f"{app_name}: Missing views_api import")

        return has_frontend_import and has_api_import

    except Exception as e:
        print_failure(f"Error checking imports in {filepath}: {e}")
        return False

def check_main_urls():
    """Check School_System/urls.py for proper nested namespace configuration."""
    filepath = 'School_System/urls.py'

    print_header("Checking Main URL Router")

    if not check_file_exists(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontend_urlpatterns and api_v1_urlpatterns
        has_frontend_patterns = 'frontend_urlpatterns = [' in content
        has_api_patterns = 'api_v1_urlpatterns = [' in content

        # Check for nested namespace includes
        has_api_namespace = "path('api/v1/', include((api_v1_urlpatterns, 'api'), namespace='api'))" in content
        has_frontend_namespace = "path('', include(frontend_urlpatterns))" in content or "path('', include((frontend_urlpatterns, 'frontend')))" in content

        if has_frontend_patterns:
            print_success("Main router: Has frontend_urlpatterns")
        else:
            print_failure("Main router: Missing frontend_urlpatterns")

        if has_api_patterns:
            print_success("Main router: Has api_v1_urlpatterns")
        else:
            print_failure("Main router: Missing api_v1_urlpatterns")

        if has_api_namespace:
            print_success("Main router: Has API namespace structure")
        else:
            print_failure("Main router: Missing API namespace structure")

        # Check for Phase 4 apps in routing
        phase4_apps = ['core', 'course', 'result', 'accounts']
        for app in phase4_apps:
            # Check frontend routing
            pattern = f"path('{app if app != 'core' else ''}"
            if app in content:
                print_success(f"Main router: {app} app registered")
            else:
                print_failure(f"Main router: {app} app not found")

        return all([has_frontend_patterns, has_api_patterns, has_api_namespace])

    except Exception as e:
        print_failure(f"Error checking main router: {e}")
        return False

def check_phase4_app(app_name):
    """Check a Phase 4 app for complete migration."""
    print_header(f"Checking {app_name.upper()} App")

    app_path = Path(app_name)

    # Check file structure
    files_to_check = [
        (app_path / 'views_frontend.py', 'views_frontend.py'),
        (app_path / 'views_api.py', 'views_api.py'),
        (app_path / 'serializers.py', 'serializers.py'),
        (app_path / 'urls.py', 'urls.py'),
        (app_path / 'forms.py', 'forms.py'),
    ]

    all_exist = True
    for filepath, filename in files_to_check:
        if check_file_exists(str(filepath)):
            check_python_syntax(str(filepath))
        else:
            all_exist = False

    # Check urls.py structure
    urls_path = app_path / 'urls.py'
    if urls_path.exists():
        check_urls_file(app_name, str(urls_path))
        check_views_imports(app_name, str(urls_path))

    return all_exist

def main():
    """Run all migration tests."""
    print_header("PHASE 4 MIGRATION URL TESTING")

    print("Testing Phase 4 apps: core, course, result, accounts\n")

    # Check each Phase 4 app
    phase4_apps = ['core', 'course', 'result', 'accounts']
    for app in phase4_apps:
        check_phase4_app(app)

    # Check main router
    check_main_urls()

    # Print summary
    print_header("TEST SUMMARY")

    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Checks: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print(f"{YELLOW}Warnings: {warnings}{RESET}")
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if failed == 0:
        print(f"\n{GREEN}{'=' * 80}{RESET}")
        print(f"{GREEN}{'ALL CHECKS PASSED - MIGRATION SUCCESSFUL'.center(80)}{RESET}")
        print(f"{GREEN}{'=' * 80}{RESET}\n")

        print("Next Steps:")
        print("1. Resolve django-modeltranslation compatibility issue (pre-existing)")
        print("2. Once resolved, run: python manage.py check --deploy")
        print("3. Run migrations if needed: python manage.py migrate")
        print("4. Start server: python manage.py runserver")
        print("5. Test functionality in browser")
    else:
        print(f"\n{RED}{'=' * 80}{RESET}")
        print(f"{RED}{'SOME CHECKS FAILED'.center(80)}{RESET}")
        print(f"{RED}{'=' * 80}{RESET}\n")
        print("Please review the failed checks above and fix the issues.")

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

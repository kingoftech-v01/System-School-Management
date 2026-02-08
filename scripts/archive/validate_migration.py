#!/usr/bin/env python
"""
Migration Validation Script
Tests the URL and View Convention migration without requiring full Django setup.
"""

import os
import re
from pathlib import Path

print("=" * 80)
print("URL AND VIEW CONVENTION MIGRATION - VALIDATION REPORT")
print("=" * 80)
print()

# Define apps and their expected files
PHASE_4_APPS = {
    'core': {
        'views_frontend.py': True,
        'views_api.py': True,
        'serializers.py': True,
        'urls.py': True,
        'forms.py': True,
    },
    'course': {
        'views_frontend.py': True,
        'views_api.py': True,
        'serializers.py': True,
        'urls.py': True,
        'forms.py': True,
    },
    'result': {
        'views_frontend.py': True,
        'views_api.py': True,
        'serializers.py': True,
        'urls.py': True,
    },
    'accounts': {
        'views_frontend.py': True,
        'views_api.py': True,
        'serializers.py': True,
        'urls.py': True,
        'forms.py': True,
    },
}

total_checks = 0
passed_checks = 0

print("1. FILE STRUCTURE VALIDATION")
print("-" * 80)

for app_name, expected_files in PHASE_4_APPS.items():
    print(f"\n{app_name.upper()} App:")
    for file_name, required in expected_files.items():
        total_checks += 1
        file_path = Path(app_name) / file_name
        exists = file_path.exists()
        
        if exists:
            passed_checks += 1
            status = "OK"
            size = file_path.stat().st_size
            print(f"  [{status}] {file_name:25} ({size:,} bytes)")
        else:
            status = "MISSING" if required else "OPTIONAL"
            print(f"  [{status}] {file_name:25}")

print("\n" + "=" * 80)
print("2. URL CONFIGURATION VALIDATION")
print("-" * 80)

for app_name in PHASE_4_APPS.keys():
    total_checks += 1
    urls_file = Path(app_name) / 'urls.py'
    
    if urls_file.exists():
        content = urls_file.read_text(encoding='utf-8')
        
        # Check for app_name declaration
        has_app_name = "app_name = " in content
        
        # Check for dual-layer structure
        has_api_urlpatterns = "api_urlpatterns = [" in content
        has_frontend_urlpatterns = "frontend_urlpatterns = [" in content
        has_api_router = "api_router = DefaultRouter()" in content
        
        if has_app_name and has_api_urlpatterns and has_frontend_urlpatterns:
            passed_checks += 1
            print(f"\n{app_name.upper()}:")
            print(f"  [OK] app_name declared")
            print(f"  [OK] API urlpatterns found")
            print(f"  [OK] Frontend urlpatterns found")
            if has_api_router:
                print(f"  [OK] DRF Router configured")
        else:
            print(f"\n{app_name.upper()}:")
            if not has_app_name:
                print(f"  [MISSING] app_name declaration")
            if not has_api_urlpatterns:
                print(f"  [MISSING] api_urlpatterns")
            if not has_frontend_urlpatterns:
                print(f"  [MISSING] frontend_urlpatterns")

print("\n" + "=" * 80)
print("3. MAIN ROUTER VALIDATION")
print("-" * 80)

total_checks += 1
main_urls = Path('School_System') / 'urls.py'

if main_urls.exists():
    content = main_urls.read_text(encoding='utf-8')
    
    has_frontend_patterns = "frontend_urlpatterns = [" in content
    has_api_patterns = "api_v1_urlpatterns = [" in content
    has_api_namespace = "namespace='api'" in content
    has_frontend_include = "path('', include((frontend_urlpatterns, 'frontend')))" in content
    
    if all([has_frontend_patterns, has_api_patterns, has_api_namespace]):
        passed_checks += 1
        print("[OK] Main router (School_System/urls.py):")
        print("  [OK] frontend_urlpatterns declared")
        print("  [OK] api_v1_urlpatterns declared")
        print("  [OK] Nested namespace structure")
    else:
        print("[ERROR] Main router has issues:")
        if not has_frontend_patterns:
            print("  [MISSING] frontend_urlpatterns")
        if not has_api_patterns:
            print("  [MISSING] api_v1_urlpatterns")
        if not has_api_namespace:
            print("  [MISSING] API namespace")
else:
    print("[ERROR] School_System/urls.py not found")

print("\n" + "=" * 80)
print("4. PYTHON SYNTAX VALIDATION")
print("-" * 80)

import py_compile

files_to_check = []
for app_name in PHASE_4_APPS.keys():
    files_to_check.extend([
        f"{app_name}/views_frontend.py",
        f"{app_name}/views_api.py",
        f"{app_name}/serializers.py",
        f"{app_name}/urls.py",
    ])
files_to_check.append("School_System/urls.py")

syntax_errors = []
for file_path in files_to_check:
    total_checks += 1
    if Path(file_path).exists():
        try:
            py_compile.compile(file_path, doraise=True)
            passed_checks += 1
            print(f"  [OK] {file_path}")
        except py_compile.PyCompileError as e:
            syntax_errors.append((file_path, str(e)))
            print(f"  [ERROR] {file_path}: {e}")
    else:
        print(f"  [SKIP] {file_path} (not found)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Checks: {total_checks}")
print(f"Passed: {passed_checks}")
print(f"Failed: {total_checks - passed_checks}")
print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
print()

if syntax_errors:
    print("SYNTAX ERRORS FOUND:")
    for file_path, error in syntax_errors:
        print(f"  - {file_path}: {error}")
    print()

if passed_checks == total_checks:
    print("STATUS: ALL CHECKS PASSED")
    print()
    print("Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run Django checks: python manage.py check")
    print("3. Start server: python manage.py runserver")
else:
    print("STATUS: SOME CHECKS FAILED")
    print(f"Please review the {total_checks - passed_checks} failed check(s) above.")

print("=" * 80)

"""
Create superuser if none exists.
Management command to create default admin user.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'School_System.settings.base')
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def create_superuser():
    """Create superuser if none exists."""
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@school.com')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')

    if User.objects.filter(is_superuser=True).exists():
        print("[INFO] Superuser already exists, skipping creation")
        return

    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='System',
            last_name='Administrator',
            role='admin'
        )
        print(f"[OK] Superuser created successfully: {username}")
        print(f"[INFO] Email: {email}")
        print(f"[WARNING] Please change the default password after first login!")
    except IntegrityError as e:
        print(f"[FAIL] Could not create superuser: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == '__main__':
    create_superuser()

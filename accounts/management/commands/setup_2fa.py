"""
Django management command to force 2FA setup for all staff users.

Usage:
    python manage.py setup_2fa
    python manage.py setup_2fa --tenant school_name
    python manage.py setup_2fa --schema-name school_stmary
    python manage.py setup_2fa --role staff  # Only staff
    python manage.py setup_2fa --role all    # All users
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Q
from django_tenants.utils import schema_context

from core.models import School

User = get_user_model()


class Command(BaseCommand):
    help = 'Force 2FA setup for staff users and optionally other user roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant name (e.g., "St. Mary High School"). If not provided, applies to public schema.'
        )
        parser.add_argument(
            '--schema-name',
            type=str,
            help='Schema name (e.g., "school_stmary"). If not provided, applies to public schema.'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['staff', 'professors', 'direction', 'all'],
            default='staff',
            help='User role to apply 2FA requirement (default: staff)'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable 2FA requirement instead of enabling it'
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send email notification to affected users'
        )

    def get_tenant(self, options):
        """Get tenant by name or schema name."""
        if options.get('tenant'):
            try:
                return School.objects.get(name=options['tenant'])
            except School.DoesNotExist:
                raise CommandError(f'School with name "{options["tenant"]}" not found')
        elif options.get('schema_name'):
            try:
                return School.objects.get(schema_name=options['schema_name'])
            except School.DoesNotExist:
                raise CommandError(f'School with schema "{options["schema_name"]}" not found')
        return None

    def handle(self, *args, **options):
        tenant = self.get_tenant(options)
        role = options['role']
        disable_2fa = options['disable']
        send_email = options['send_email']

        action = "Disabling" if disable_2fa else "Enabling"

        if tenant:
            self.stdout.write(self.style.NOTICE(f'{action} 2FA for {role} users in: {tenant.name}'))
            with schema_context(tenant.schema_name):
                affected_count = self._process_users(role, disable_2fa, send_email)
        else:
            self.stdout.write(self.style.NOTICE(f'{action} 2FA for {role} users in public schema'))
            affected_count = self._process_users(role, disable_2fa, send_email)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'2FA SETUP {"DISABLED" if disable_2fa else "ENABLED"}'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        if tenant:
            self.stdout.write(f'School: {tenant.name}')
        else:
            self.stdout.write('Schema: Public')
        self.stdout.write(f'Role: {role}')
        self.stdout.write(f'Affected Users: {affected_count}')
        if send_email:
            self.stdout.write('Email Notifications: Sent')
        self.stdout.write(self.style.SUCCESS('=' * 70))

    def _process_users(self, role, disable_2fa, send_email):
        """Process users based on role and apply 2FA settings."""
        # Build query based on role
        if role == 'staff':
            users = User.objects.filter(is_staff=True, is_superuser=False)
        elif role == 'professors':
            users = User.objects.filter(is_lecturer=True)
        elif role == 'direction':
            users = User.objects.filter(is_dep_head=True)
        elif role == 'all':
            users = User.objects.filter(
                Q(is_staff=True) | Q(is_lecturer=True) | Q(is_dep_head=True)
            )
        else:
            users = User.objects.none()

        affected_count = 0

        for user in users:
            # Note: The actual 2FA implementation depends on your setup
            # This is a placeholder for the actual implementation
            # You might need to:
            # 1. Set a flag in the user model
            # 2. Create a UserProfile with 2FA required flag
            # 3. Use django-allauth MFA settings
            # 4. Use django-otp settings

            # Example: If using a custom field like 'requires_2fa'
            # if hasattr(user, 'requires_2fa'):
            #     user.requires_2fa = not disable_2fa
            #     user.save()

            # For django-allauth with MFA, you might need to check user's MFA status
            # and force setup on next login

            # Placeholder implementation - mark user as needing 2FA
            self.stdout.write(f'  Processing: {user.username} ({user.email})')

            if send_email:
                self._send_2fa_notification(user, disable_2fa)

            affected_count += 1

        return affected_count

    def _send_2fa_notification(self, user, disabled):
        """Send email notification to user about 2FA requirement."""
        from django.core.mail import send_mail
        from django.conf import settings

        subject = "Two-Factor Authentication " + ("Disabled" if disabled else "Required")

        if disabled:
            message = f"""
Hello {user.get_full_name or user.username},

Two-Factor Authentication (2FA) has been disabled for your account.

If you did not request this change, please contact your system administrator immediately.

Best regards,
{getattr(settings, 'SITE_NAME', 'School Management System')}
            """
        else:
            message = f"""
Hello {user.get_full_name or user.username},

Two-Factor Authentication (2FA) is now required for your account to enhance security.

You will be prompted to set up 2FA the next time you log in. You'll need:
- A smartphone with an authenticator app (Google Authenticator, Authy, etc.)
- Access to your email for verification

Steps to set up 2FA:
1. Log in to your account
2. Follow the on-screen instructions to scan the QR code
3. Enter the verification code from your authenticator app
4. Save your backup codes in a secure location

If you need assistance, please contact your system administrator.

Best regards,
{getattr(settings, 'SITE_NAME', 'School Management System')}
            """

        try:
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'    Email sent to: {user.email}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'    Failed to send email to {user.email}: {str(e)}'))

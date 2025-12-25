"""
Django management command to create a new school tenant.

Usage:
    python manage.py create_tenant --name "School Name" --domain school.localhost --admin admin@school.com
"""

import secrets
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from core.models import School, Domain, Session, Semester
from course.models import Program
from accounts.models import Student

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new school tenant with domain mapping and initial setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='School name (e.g., "St. Mary High School")'
        )
        parser.add_argument(
            '--domain',
            type=str,
            required=True,
            help='Domain for the school (e.g., "stmary.localhost" or "stmary.example.com")'
        )
        parser.add_argument(
            '--admin',
            type=str,
            required=True,
            help='Admin email address'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            help='Admin password (will be auto-generated if not provided)'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='School contact email (defaults to admin email)'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='+1-000-000-0000',
            help='School phone number'
        )
        parser.add_argument(
            '--address',
            type=str,
            default='123 School Street',
            help='School address'
        )
        parser.add_argument(
            '--city',
            type=str,
            default='City',
            help='School city'
        )
        parser.add_argument(
            '--country',
            type=str,
            default='USA',
            help='School country'
        )
        parser.add_argument(
            '--postal-code',
            type=str,
            default='00000',
            help='School postal code'
        )
        parser.add_argument(
            '--subscription-type',
            type=str,
            choices=['monthly', 'yearly'],
            default='monthly',
            help='Subscription type'
        )
        parser.add_argument(
            '--max-students',
            type=int,
            default=500,
            help='Maximum number of students allowed'
        )
        parser.add_argument(
            '--max-staff',
            type=int,
            default=50,
            help='Maximum number of staff members allowed'
        )
        parser.add_argument(
            '--skip-demo-data',
            action='store_true',
            help='Skip creating demo programs/filieres'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        name = options['name']
        domain = options['domain']
        admin_email = options['admin']
        admin_password = options.get('admin_password') or secrets.token_urlsafe(16)

        # Validate inputs
        if School.objects.filter(name=name).exists():
            raise CommandError(f'School with name "{name}" already exists')

        if Domain.objects.filter(domain=domain).exists():
            raise CommandError(f'Domain "{domain}" already exists')

        slug = slugify(name)
        if School.objects.filter(slug=slug).exists():
            slug = f"{slug}-{secrets.token_hex(4)}"

        self.stdout.write(self.style.NOTICE(f'Creating tenant for school: {name}'))

        # Generate license key
        license_key = f"SCH-{secrets.token_hex(16).upper()}"

        # Calculate subscription dates
        subscription_start = datetime.now().date()
        if options['subscription_type'] == 'yearly':
            subscription_end = subscription_start + timedelta(days=365)
        else:
            subscription_end = subscription_start + timedelta(days=30)

        # Create the tenant (School)
        school = School.objects.create(
            name=name,
            slug=slug,
            schema_name=f"school_{slug}",
            description=f"Tenant schema for {name}",
            email=options.get('email') or admin_email,
            phone=options['phone'],
            address=options['address'],
            city=options['city'],
            country=options['country'],
            postal_code=options['postal_code'],
            license_key=license_key,
            subscription_type=options['subscription_type'],
            subscription_start=subscription_start,
            subscription_end=subscription_end,
            is_active=True,
            max_students=options['max_students'],
            max_staff=options['max_staff']
        )

        self.stdout.write(self.style.SUCCESS(f'Created school tenant: {school.name}'))
        self.stdout.write(f'  - Schema: {school.schema_name}')
        self.stdout.write(f'  - License Key: {license_key}')

        # Create domain mapping
        domain_obj = Domain.objects.create(
            domain=domain,
            tenant=school,
            is_primary=True
        )

        self.stdout.write(self.style.SUCCESS(f'Created domain: {domain}'))

        # Switch to the tenant schema to create tenant-specific data
        with schema_context(school.schema_name):
            # Create superuser for this tenant
            admin_username = admin_email.split('@')[0]

            # Check if user already exists
            if User.objects.filter(username=admin_username).exists():
                admin_username = f"{admin_username}_{secrets.token_hex(3)}"

            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                last_name='User',
                is_staff=True,
                is_superuser=True
            )

            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_username}'))
            self.stdout.write(f'  - Email: {admin_email}')
            if not options.get('admin_password'):
                self.stdout.write(self.style.WARNING(f'  - Password: {admin_password}'))
                self.stdout.write(self.style.WARNING('    (Please save this password securely!)'))

            # Create academic year (Session)
            current_year = datetime.now().year
            session_name = f"{current_year}/{current_year + 1}"
            session = Session.objects.create(
                session=session_name,
                is_current_session=True,
                next_session_begins=datetime(current_year + 1, 9, 1).date()
            )

            self.stdout.write(self.style.SUCCESS(f'Created academic session: {session_name}'))

            # Create semesters
            semesters_data = [
                ('First', True, datetime(current_year, 9, 1).date()),
                ('Second', False, datetime(current_year + 1, 1, 15).date()),
                ('Third', False, datetime(current_year + 1, 5, 1).date()),
            ]

            for sem_name, is_current, next_begins in semesters_data:
                Semester.objects.create(
                    semester=sem_name,
                    is_current_semester=is_current,
                    session=session,
                    next_semester_begins=next_begins
                )

            self.stdout.write(self.style.SUCCESS('Created semesters: First, Second, Third'))

            # Create sample programs/filieres if not skipped
            if not options['skip_demo_data']:
                programs_data = [
                    ('Science', 'Science and Mathematics program'),
                    ('Arts', 'Arts and Humanities program'),
                    ('Commerce', 'Commerce and Business Studies'),
                    ('Technology', 'Information Technology and Computer Science'),
                    ('General', 'General education program'),
                ]

                for prog_title, prog_summary in programs_data:
                    Program.objects.create(
                        title=prog_title,
                        summary=prog_summary
                    )

                self.stdout.write(self.style.SUCCESS(f'Created {len(programs_data)} sample programs/filieres'))

        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('TENANT CREATION SUCCESSFUL'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'School Name: {school.name}')
        self.stdout.write(f'Domain: {domain}')
        self.stdout.write(f'Admin Username: {admin_username}')
        self.stdout.write(f'Admin Email: {admin_email}')
        if not options.get('admin_password'):
            self.stdout.write(self.style.WARNING(f'Admin Password: {admin_password}'))
        self.stdout.write(f'License Key: {license_key}')
        self.stdout.write(f'Subscription: {options["subscription_type"]} (until {subscription_end})')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Access the school at: http://{}'.format(domain))
        self.stdout.write('  2. Login with the admin credentials above')
        self.stdout.write('  3. Run: python manage.py create_demo_data --tenant {} (optional)'.format(school.schema_name))
        self.stdout.write(self.style.SUCCESS('=' * 70))

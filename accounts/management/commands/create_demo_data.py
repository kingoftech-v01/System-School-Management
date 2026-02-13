"""
Django management command to create comprehensive demo/beta data for testing.

Usage:
    python manage.py create_demo_data --schema-name school_stmary
    python manage.py create_demo_data --tenant "St. Mary High School"
    python manage.py create_demo_data --students 200 --professors 25
    python manage.py create_demo_data --apps accounts,course,library
    python manage.py create_demo_data --seed 42
"""

import importlib
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import School, Session, Semester
from course.models import Program, Course
from faker import Faker


# Ordered list of (phase_name, [(app_label, module_path)])
DEMO_DATA_PHASES = [
    ('Phase 1 - Users', [
        ('accounts', 'accounts.demo_data'),
    ]),
    ('Phase 2 - Course & Enrollment', [
        ('course', 'course.demo_data'),
        ('enrollment', 'enrollment.demo_data'),
        ('admissions', 'admissions.demo_data'),
    ]),
    ('Phase 3 - Academics', [
        ('result', 'result.demo_data'),
        ('grading', 'grading.demo_data'),
        ('notes', 'notes.demo_data'),
        ('attendance', 'attendance.demo_data'),
        ('quiz', 'quiz.demo_data'),
        ('scheduling', 'scheduling.demo_data'),
    ]),
    ('Phase 4 - Community', [
        ('forums', 'forums.demo_data'),
        ('articles', 'articles.demo_data'),
        ('notices', 'notices.demo_data'),
        ('events', 'events.demo_data'),
    ]),
    ('Phase 5 - Administration', [
        ('library', 'library.demo_data'),
        ('payments', 'payments.demo_data'),
        ('certificates', 'certificates.demo_data'),
        ('discipline', 'discipline.demo_data'),
        ('safeguarding', 'safeguarding.demo_data'),
        ('analytics', 'analytics.demo_data'),
        ('anomaly_detection', 'anomaly_detection.demo_data'),
        ('reports', 'reports.demo_data'),
        ('audit', 'audit.demo_data'),
    ]),
]


class Command(BaseCommand):
    help = 'Create comprehensive demo/beta data for a school tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant', type=str,
            help='Tenant name (e.g., "St. Mary High School")'
        )
        parser.add_argument(
            '--schema-name', type=str,
            help='Schema name (e.g., "school_stmary")'
        )
        parser.add_argument(
            '--students', type=int, default=150,
            help='Number of students to create (default: 150)'
        )
        parser.add_argument(
            '--professors', type=int, default=20,
            help='Number of professors to create (default: 20)'
        )
        parser.add_argument(
            '--parents', type=int, default=20,
            help='Number of parents to create (default: 20)'
        )
        parser.add_argument(
            '--apps', type=str, default='',
            help='Comma-separated list of apps to generate data for (default: all)'
        )
        parser.add_argument(
            '--seed', type=str, default='random',
            help='Random seed for reproducibility (default: random)'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.verbosity = options.get('verbosity', 1)

        # Initialize Faker
        fake = Faker()
        if options['seed'] != 'random':
            Faker.seed(int(options['seed']))
            import random
            random.seed(int(options['seed']))

        # Resolve tenant
        tenant = self._resolve_tenant(options)

        # Determine which apps to include
        apps_filter = set()
        if options['apps']:
            apps_filter = set(options['apps'].split(','))

        # Shared context dict
        context = {
            'students_count': options['students'],
            'professors_count': options['professors'],
            'parents_count': options['parents'],
        }

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('DEMO DATA GENERATION'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'School: {tenant.name}')
        self.stdout.write(f'Students: {options["students"]}, Professors: {options["professors"]}, Parents: {options["parents"]}')
        self.stdout.write('')

        use_tenants = self._is_multi_tenant()

        def _run():
            self._verify_prerequisites()
            context['session'] = Session.objects.filter(is_current_session=True).first()
            context['semester'] = Semester.objects.filter(is_current_semester=True).first()
            context['programs'] = list(Program.objects.all())
            context['courses'] = list(Course.objects.all())
            context['tenant'] = tenant
            self._check_existing_data()
            return self._run_phases(apps_filter, tenant, fake, context)

        if use_tenants and hasattr(tenant, 'schema_name'):
            from django_tenants.utils import schema_context
            with schema_context(tenant.schema_name):
                total_created = _run()
        else:
            total_created = _run()

        # Final summary
        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('DEMO DATA CREATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Total records created: {total_created}')
        self.stdout.write(f'Time elapsed: {elapsed:.1f}s')
        self.stdout.write('')
        self.stdout.write('Login Credentials (all demo users):')
        self.stdout.write('  Password: password123')
        self.stdout.write('')
        self.stdout.write('  Professors:  prof1..prof{}  |  professor1@school.edu..professor{}@school.edu'.format(
            options['professors'], options['professors']
        ))
        self.stdout.write('  Students:    student1..student{}  |  student1@school.edu..student{}@school.edu'.format(
            options['students'], options['students']
        ))
        self.stdout.write('  Parents:     parent1..parent{}  |  parent1@email.com..parent{}@email.com'.format(
            options['parents'], options['parents']
        ))
        self.stdout.write('  Staff:       direction1..3, accountant1..2, secretary1..2, librarian1, registrar1, prefet1')
        self.stdout.write('               Emails: {role}{n}@school.edu (e.g. direction1@school.edu)')
        self.stdout.write(self.style.SUCCESS('=' * 70))

    def _is_multi_tenant(self):
        return 'django_tenants' in settings.INSTALLED_APPS

    def _run_phases(self, apps_filter, tenant, fake, context):
        total_created = 0
        for phase_name, apps in DEMO_DATA_PHASES:
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE(f'=== {phase_name} ==='))

            for app_label, module_path in apps:
                if apps_filter and app_label not in apps_filter:
                    if self.verbosity >= 2:
                        self.stdout.write(f'  [{app_label}] Skipped (not in --apps)')
                    continue

                count = self._load_app_demo_data(
                    app_label, module_path, tenant, fake, context
                )
                total_created += count
        return total_created

    def _resolve_tenant(self, options):
        if options.get('tenant'):
            try:
                return School.objects.get(name=options['tenant'])
            except School.DoesNotExist:
                raise CommandError(f'School "{options["tenant"]}" not found')
        elif options.get('schema_name'):
            try:
                return School.objects.get(schema_name=options['schema_name'])
            except School.DoesNotExist:
                raise CommandError(f'Schema "{options["schema_name"]}" not found')
            except Exception:
                pass  # In dev mode, schema_name field may not exist

        # Fallback: use first available school
        tenant = School.objects.first()
        if tenant:
            self.stdout.write(f'No tenant specified, using: {tenant.name}')
            return tenant
        raise CommandError('No school found. Create a tenant first.')

    def _verify_prerequisites(self):
        session = Session.objects.filter(is_current_session=True).first()
        if not session:
            raise CommandError(
                'No active session found. Run seed_initial_data first.'
            )
        semester = Semester.objects.filter(is_current_semester=True).first()
        if not semester:
            raise CommandError(
                'No active semester found. Run seed_initial_data first.'
            )
        if not Program.objects.exists():
            raise CommandError(
                'No programs found. Run seed_initial_data first.'
            )

    def _check_existing_data(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username__startswith='prof').exists():
            self.stdout.write(self.style.WARNING(
                'WARNING: Demo data may already exist (found users with "prof" prefix). '
                'Running again will create duplicates.'
            ))

    def _load_app_demo_data(self, app_label, module_path, tenant, fake, context):
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            if self.verbosity >= 1:
                self.stdout.write(self.style.WARNING(
                    f'  [{app_label}] No demo_data module found, skipping ({e})'
                ))
            return 0

        try:
            result = module.generate(
                tenant=tenant,
                stdout=self.stdout,
                verbosity=self.verbosity,
                context=context,
                fake=fake,
            )
            context[app_label] = result
            count = result.get('_total', 0) if result else 0
            return count
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'  [{app_label}] ERROR: {e}'
            ))
            raise

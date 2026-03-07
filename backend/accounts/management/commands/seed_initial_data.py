"""
Management command to seed initial/reference data for a school tenant.

This seeds foundational lookup/configuration data (NOT demo/beta data)
so a new school doesn't start from zero. Each app gets 15+ reference records.

Usage (multi-tenant / production):
    python manage.py seed_initial_data --tenant "St. Mary High School"
    python manage.py seed_initial_data --schema-name school_stmary

Usage (selective apps):
    python manage.py seed_initial_data --schema-name school_stmary --apps core,course,forums

Usage (export to JSON after seeding):
    python manage.py seed_initial_data --schema-name school_stmary --export-fixtures
"""

import importlib
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from core.models import School


# Ordered list of (app_label, module_path, needs_tenant)
SEED_REGISTRY = [
    # Phase 1: No dependencies
    ('core', 'core.seed_data', False),
    ('course', 'course.seed_data', False),
    # Phase 2: Independent apps
    ('forums', 'forums.seed_data', False),
    ('articles', 'articles.seed_data', False),
    ('library', 'library.seed_data', False),
    ('notices', 'notices.seed_data', False),
    ('attendance', 'attendance.seed_data', False),
    ('admissions', 'admissions.seed_data', False),
    ('certificates', 'certificates.seed_data', False),
    # Phase 3: Dependent on Phase 1 and/or tenant
    ('scheduling', 'scheduling.seed_data', True),
    ('filieres', 'filieres.seed_data', True),
    ('payments', 'payments.seed_data', False),
    ('grading', 'grading.seed_data', False),
]

# Apps whose data can be exported to JSON fixtures
EXPORTABLE_MODELS = {
    'core': ['core.Session', 'core.Semester'],
    'course': ['course.Program', 'course.Course'],
    'forums': ['forums.ForumCategory', 'forums.Tag'],
    'articles': ['articles.Category'],
    'library': ['library.BookCategory', 'library.Publisher'],
    'notices': ['notices.NotifyGroup'],
    'attendance': ['attendance.Group'],
    'admissions': ['admissions.AdmissionSession'],
    'certificates': ['certificates.CertificateTemplate'],
    'scheduling': ['scheduling.Room', 'scheduling.TimeSlot'],
    'filieres': ['filieres.Filiere', 'filieres.FiliereSubject', 'filieres.FiliereRequirement'],
    'payments': ['payments.FeeStructure'],
    'grading': ['grading.GradingRubric', 'grading.RubricCriterion'],
}


class Command(BaseCommand):
    help = 'Seed initial/reference data for a school tenant (NOT demo data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='School name to seed data for',
        )
        parser.add_argument(
            '--schema-name',
            type=str,
            help='Schema name of the tenant',
        )
        parser.add_argument(
            '--apps',
            type=str,
            help='Comma-separated list of app labels to seed (default: all)',
        )
        parser.add_argument(
            '--export-fixtures',
            action='store_true',
            help='Export seeded data to JSON fixture files after seeding',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.verbosity = options.get('verbosity', 1)

        # Determine tenant
        tenant = self._resolve_tenant(options)

        # Determine which apps to seed
        seed_list = self._get_seed_list(options)

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SEEDING INITIAL DATA'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if tenant:
            self.stdout.write(f'Tenant: {tenant.name}')

        self.stdout.write(f'Apps: {", ".join(app for app, _, _ in seed_list)}')
        self.stdout.write('')

        # Run seeders
        use_tenants = self._is_multi_tenant()
        context = {}

        if use_tenants and tenant:
            from django_tenants.utils import schema_context
            with schema_context(tenant.schema_name):
                self._run_seeders(seed_list, tenant, context)
        else:
            self._run_seeders(seed_list, tenant, context)

        # Export fixtures if requested
        if options.get('export_fixtures'):
            self._export_fixtures(seed_list, tenant, use_tenants)

        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'SEEDING COMPLETE ({elapsed:.1f}s)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def _resolve_tenant(self, options):
        """Resolve the tenant from command arguments."""
        tenant_name = options.get('tenant')
        schema_name = options.get('schema_name')

        if tenant_name:
            try:
                return School.objects.get(name=tenant_name)
            except School.DoesNotExist:
                raise CommandError(f'School "{tenant_name}" not found')
        elif schema_name:
            try:
                return School.objects.get(schema_name=schema_name)
            except School.DoesNotExist:
                raise CommandError(f'Schema "{schema_name}" not found')
            except Exception:
                # In dev mode, schema_name field may not exist
                pass

        # Try to get the first available school
        tenant = School.objects.first()
        if tenant:
            self.stdout.write(f'No tenant specified, using: {tenant.name}')
            return tenant

        self.stdout.write(self.style.WARNING(
            'No tenant found. Models requiring a tenant FK will be skipped. '
            'Run create_tenant first, then re-run this command.'
        ))
        return None

    def _is_multi_tenant(self):
        """Check if the project is running in multi-tenant mode."""
        return 'django_tenants' in settings.INSTALLED_APPS

    def _get_seed_list(self, options):
        """Filter SEED_REGISTRY based on --apps argument."""
        app_filter = options.get('apps')
        if app_filter:
            selected = [a.strip() for a in app_filter.split(',')]
            filtered = [
                (app, mod, needs_tenant)
                for app, mod, needs_tenant in SEED_REGISTRY
                if app in selected
            ]
            unknown = set(selected) - {app for app, _, _ in SEED_REGISTRY}
            if unknown:
                raise CommandError(
                    f'Unknown app(s): {", ".join(unknown)}. '
                    f'Available: {", ".join(app for app, _, _ in SEED_REGISTRY)}'
                )
            return filtered
        return list(SEED_REGISTRY)

    def _run_seeders(self, seed_list, tenant, context):
        """Execute each seed module in order."""
        for app_label, module_path, needs_tenant in seed_list:
            self.stdout.write(self.style.MIGRATE_HEADING(f'[{app_label}]'))
            try:
                module = importlib.import_module(module_path)
                result = module.seed(
                    tenant=tenant,
                    stdout=self.stdout,
                    verbosity=self.verbosity,
                    context=context,
                )
                context[app_label] = result
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR: {e}'))
                context[app_label] = {}

    def _export_fixtures(self, seed_list, tenant, use_tenants):
        """Export seeded data to JSON fixture files."""
        import os

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Exporting fixtures...'))

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))

        for app_label, _, _ in seed_list:
            models = EXPORTABLE_MODELS.get(app_label)
            if not models:
                continue

            # Create fixtures directory
            app_fixture_dir = os.path.join(base_dir, app_label, 'fixtures')
            os.makedirs(app_fixture_dir, exist_ok=True)

            fixture_path = os.path.join(app_fixture_dir, 'initial_data.json')

            try:
                with open(fixture_path, 'w') as f:
                    call_command(
                        'dumpdata',
                        *models,
                        indent=2,
                        stdout=f,
                    )
                self.stdout.write(f'  {app_label}/fixtures/initial_data.json')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  {app_label}: export failed - {e}'))

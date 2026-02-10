"""
Management command to generate invitation codes for parent/staff registration.

Usage:
    # Generate a parent invitation linked to a student
    python manage.py generate_invitation_codes --role parent --student-reg 24-CS-001 --email parent@email.com

    # Generate staff invitation codes
    python manage.py generate_invitation_codes --role professor --count 5

    # Generate direction invitation codes with specific expiry
    python manage.py generate_invitation_codes --role direction --email director@school.com --expiry-days 14
"""

from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings

from accounts.models import InvitationCode, Student, User


class Command(BaseCommand):
    help = 'Generate invitation codes for parent or staff registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            required=True,
            choices=['parent', 'professor', 'direction', 'secretary', 'librarian', 'registrar'],
            help='Role for the invitation code',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of codes to generate (default: 1)',
        )
        parser.add_argument(
            '--student-reg',
            type=str,
            default=None,
            help='Student registration number to link (for parent codes)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default=None,
            help='Email to associate with the invitation',
        )
        parser.add_argument(
            '--expiry-days',
            type=int,
            default=None,
            help=f'Days until expiry (default: {getattr(settings, "INVITATION_CODE_EXPIRY_DAYS", 7)})',
        )
        parser.add_argument(
            '--created-by',
            type=str,
            default=None,
            help='Username of the user creating the codes',
        )

    def handle(self, *args, **options):
        role = options['role']
        count = options['count']
        student_reg = options['student_reg']
        email = options['email']
        expiry_days = options['expiry_days'] or getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created_by_username = options['created_by']

        # Resolve linked student
        linked_student = None
        if student_reg:
            if role != 'parent':
                raise CommandError('--student-reg can only be used with --role parent')
            try:
                linked_student = Student.objects.get(registration_number=student_reg)
            except Student.DoesNotExist:
                raise CommandError(f'No student found with registration number: {student_reg}')

        # Resolve created_by user
        created_by = None
        if created_by_username:
            try:
                created_by = User.objects.get(username=created_by_username)
            except User.DoesNotExist:
                raise CommandError(f'No user found with username: {created_by_username}')

        expires_at = timezone.now() + timedelta(days=expiry_days)

        self.stdout.write(f'\nGenerating {count} invitation code(s) for role: {role}')
        self.stdout.write(f'Expires: {expires_at.strftime("%Y-%m-%d %H:%M")}\n')

        codes = []
        for i in range(count):
            code = InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role=role,
                linked_student=linked_student,
                created_by=created_by,
                expires_at=expires_at,
                sent_to_email=email if i == 0 else None,
            )
            codes.append(code)
            student_info = f' -> {linked_student}' if linked_student else ''
            self.stdout.write(self.style.SUCCESS(f'  {code.code}{student_info}'))

        self.stdout.write(f'\n{len(codes)} code(s) generated successfully.')

        if email:
            self.stdout.write(f'Email associated: {email}')

"""
Django management command to create realistic demo data for a school tenant.

Usage:
    python manage.py create_demo_data --tenant school_name
    python manage.py create_demo_data --schema-name school_stmary
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from faker import Faker

from core.models import School, Session, Semester, NewsAndEvents
from course.models import Program, Course, CourseAllocation
from accounts.models import Student, Parent, DepartmentHead
from result.models import TakenCourse
from payments.models import Invoice

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Create realistic demo data for a school tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant name (e.g., "St. Mary High School")'
        )
        parser.add_argument(
            '--schema-name',
            type=str,
            help='Schema name (e.g., "school_stmary")'
        )
        parser.add_argument(
            '--professors',
            type=int,
            default=5,
            help='Number of professors to create (default: 5)'
        )
        parser.add_argument(
            '--students',
            type=int,
            default=10,
            help='Number of students to create (default: 10)'
        )
        parser.add_argument(
            '--parents',
            type=int,
            default=5,
            help='Number of parents to create (default: 5)'
        )
        parser.add_argument(
            '--direction-members',
            type=int,
            default=3,
            help='Number of direction members to create (default: 3)'
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
        else:
            raise CommandError('Please provide either --tenant or --schema-name')

    @transaction.atomic
    def handle(self, *args, **options):
        tenant = self.get_tenant(options)

        self.stdout.write(self.style.NOTICE(f'Creating demo data for: {tenant.name}'))
        self.stdout.write(f'Schema: {tenant.schema_name}')

        # Switch to tenant schema
        with schema_context(tenant.schema_name):
            # Get current session and semester
            session = Session.objects.filter(is_current_session=True).first()
            if not session:
                raise CommandError('No active session found. Please create a session first.')

            semester = Semester.objects.filter(is_current_semester=True).first()
            if not semester:
                raise CommandError('No active semester found. Please create a semester first.')

            # Get or create programs
            programs = list(Program.objects.all())
            if not programs:
                self.stdout.write(self.style.WARNING('No programs found. Creating sample programs...'))
                programs = self._create_programs()

            # Create professors
            self.stdout.write(self.style.NOTICE(f'Creating {options["professors"]} professors...'))
            professors = self._create_professors(options['professors'])
            self.stdout.write(self.style.SUCCESS(f'Created {len(professors)} professors'))

            # Create courses
            self.stdout.write(self.style.NOTICE('Creating courses...'))
            courses = self._create_courses(programs, session)
            self.stdout.write(self.style.SUCCESS(f'Created {len(courses)} courses'))

            # Allocate courses to professors
            self.stdout.write(self.style.NOTICE('Allocating courses to professors...'))
            allocations = self._allocate_courses(professors, courses, session)
            self.stdout.write(self.style.SUCCESS(f'Created {len(allocations)} course allocations'))

            # Create students
            self.stdout.write(self.style.NOTICE(f'Creating {options["students"]} students...'))
            students = self._create_students(options['students'], programs)
            self.stdout.write(self.style.SUCCESS(f'Created {len(students)} students'))

            # Create parents
            self.stdout.write(self.style.NOTICE(f'Creating {options["parents"]} parents...'))
            parents = self._create_parents(options['parents'], students)
            self.stdout.write(self.style.SUCCESS(f'Created {len(parents)} parents'))

            # Create direction members
            self.stdout.write(self.style.NOTICE(f'Creating {options["direction_members"]} direction members...'))
            direction = self._create_direction_members(options['direction_members'], programs)
            self.stdout.write(self.style.SUCCESS(f'Created {len(direction)} direction members'))

            # Create student enrollments and grades
            self.stdout.write(self.style.NOTICE('Creating student course enrollments and grades...'))
            enrollments = self._create_student_enrollments(students, courses)
            self.stdout.write(self.style.SUCCESS(f'Created {len(enrollments)} course enrollments'))

            # Create payment records
            self.stdout.write(self.style.NOTICE('Creating payment records...'))
            invoices = self._create_invoices(students)
            self.stdout.write(self.style.SUCCESS(f'Created {len(invoices)} invoice records'))

            # Create news and events
            self.stdout.write(self.style.NOTICE('Creating news and events...'))
            news_count = self._create_news_and_events()
            self.stdout.write(self.style.SUCCESS(f'Created {news_count} news and events'))

        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('DEMO DATA CREATION SUCCESSFUL'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'School: {tenant.name}')
        self.stdout.write(f'Professors: {len(professors)}')
        self.stdout.write(f'Students: {len(students)}')
        self.stdout.write(f'Parents: {len(parents)}')
        self.stdout.write(f'Direction Members: {len(direction)}')
        self.stdout.write(f'Courses: {len(courses)}')
        self.stdout.write(f'Course Allocations: {len(allocations)}')
        self.stdout.write(f'Student Enrollments: {len(enrollments)}')
        self.stdout.write(f'Invoices: {len(invoices)}')
        self.stdout.write('')
        self.stdout.write('Sample Login Credentials:')
        if professors:
            prof = professors[0]
            self.stdout.write(f'  Professor: {prof.username} / password123')
        if students:
            student_user = students[0].student
            self.stdout.write(f'  Student: {student_user.username} / password123')
        if parents:
            parent = parents[0]
            self.stdout.write(f'  Parent: {parent.user.username} / password123')
        self.stdout.write(self.style.SUCCESS('=' * 70))

    def _create_programs(self):
        """Create sample programs."""
        programs_data = [
            ('Science', 'Science and Mathematics program'),
            ('Arts', 'Arts and Humanities program'),
            ('Commerce', 'Commerce and Business Studies'),
        ]
        programs = []
        for title, summary in programs_data:
            program = Program.objects.create(title=title, summary=summary)
            programs.append(program)
        return programs

    def _create_professors(self, count):
        """Create professor users."""
        professors = []
        for i in range(count):
            username = f"prof{i+1}"
            email = f"professor{i+1}@school.edu"

            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_lecturer=True,
                is_staff=True,
                gender=random.choice(['M', 'F']),
                phone=fake.phone_number()[:20],
                address=fake.address()[:60]
            )
            professors.append(user)
        return professors

    def _create_courses(self, programs, session):
        """Create courses for each program."""
        courses = []
        subjects = [
            'Mathematics', 'Physics', 'Chemistry', 'Biology', 'English',
            'History', 'Geography', 'Computer Science', 'Economics', 'Art',
            'Physical Education', 'Music', 'French', 'Spanish', 'Literature'
        ]

        for program in programs:
            # Create 3-5 courses per program
            num_courses = random.randint(3, 5)
            selected_subjects = random.sample(subjects, num_courses)

            for subject in selected_subjects:
                code = f"{program.title[:3].upper()}{random.randint(100, 999)}"
                course = Course.objects.create(
                    title=f"{subject} - {program.title}",
                    code=code,
                    credit=random.choice([2, 3, 4]),
                    summary=f"{subject} course for {program.title} program",
                    program=program,
                    level=random.choice(['Bachelor', 'Master']),
                    year=random.randint(1, 4),
                    semester=random.choice(['First', 'Second', 'Third']),
                    is_elective=random.choice([True, False])
                )
                courses.append(course)
        return courses

    def _allocate_courses(self, professors, courses, session):
        """Allocate courses to professors."""
        allocations = []
        courses_per_prof = len(courses) // len(professors) + 1

        for i, professor in enumerate(professors):
            start_idx = i * courses_per_prof
            end_idx = start_idx + courses_per_prof
            prof_courses = courses[start_idx:end_idx]

            if prof_courses:
                allocation = CourseAllocation.objects.create(
                    lecturer=professor,
                    session=session
                )
                allocation.courses.set(prof_courses)
                allocations.append(allocation)

        return allocations

    def _create_students(self, count, programs):
        """Create student users and Student records."""
        students = []
        for i in range(count):
            username = f"student{i+1}"
            email = f"student{i+1}@school.edu"

            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_student=True,
                gender=random.choice(['M', 'F']),
                phone=fake.phone_number()[:20],
                address=fake.address()[:60]
            )

            program = random.choice(programs)
            student = Student.objects.create(
                student=user,
                level=random.choice(['Bachelor', 'Master']),
                program=program
            )
            students.append(student)

        return students

    def _create_parents(self, count, students):
        """Create parent users and link to students."""
        parents = []
        available_students = list(students)

        for i in range(min(count, len(students))):
            username = f"parent{i+1}"
            email = f"parent{i+1}@email.com"

            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_parent=True,
                gender=random.choice(['M', 'F']),
                phone=fake.phone_number()[:20],
                address=fake.address()[:60]
            )

            student = available_students.pop(0)
            parent = Parent.objects.create(
                user=user,
                student=student,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                email=user.email,
                relation_ship=random.choice(['Father', 'Mother', 'Brother', 'Sister', 'Grand mother', 'Grand father'])
            )
            parents.append(parent)

        return parents

    def _create_direction_members(self, count, programs):
        """Create direction member users."""
        direction_members = []
        roles = ['Director', 'Vice Director', 'Academic Coordinator', 'Admin Manager']

        for i in range(count):
            username = f"direction{i+1}"
            email = f"direction{i+1}@school.edu"

            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_dep_head=True,
                is_staff=True,
                gender=random.choice(['M', 'F']),
                phone=fake.phone_number()[:20],
                address=fake.address()[:60]
            )

            if programs:
                dept_head = DepartmentHead.objects.create(
                    user=user,
                    department=random.choice(programs)
                )
                direction_members.append(dept_head)

        return direction_members

    def _create_student_enrollments(self, students, courses):
        """Create course enrollments and grades for students."""
        enrollments = []

        for student in students:
            # Each student takes 3-6 courses
            num_courses = random.randint(3, min(6, len(courses)))
            student_courses = random.sample(courses, num_courses)

            for course in student_courses:
                # Generate random grades
                assignment = Decimal(random.uniform(0, 10))
                mid_exam = Decimal(random.uniform(0, 20))
                quiz = Decimal(random.uniform(0, 10))
                attendance = Decimal(random.uniform(0, 10))
                final_exam = Decimal(random.uniform(0, 50))

                taken_course = TakenCourse.objects.create(
                    student=student,
                    course=course,
                    assignment=assignment,
                    mid_exam=mid_exam,
                    quiz=quiz,
                    attendance=attendance,
                    final_exam=final_exam
                )
                enrollments.append(taken_course)

        return enrollments

    def _create_invoices(self, students):
        """Create payment invoices for students."""
        invoices = []

        for student in students:
            # Create 1-3 invoices per student
            num_invoices = random.randint(1, 3)

            for i in range(num_invoices):
                total = random.uniform(500, 2000)
                amount_paid = random.uniform(0, total)
                is_complete = amount_paid >= total

                invoice = Invoice.objects.create(
                    user=student.student,
                    total=total,
                    amount=amount_paid,
                    payment_complete=is_complete,
                    invoice_code=f"INV-{fake.random_number(digits=8)}"
                )
                invoices.append(invoice)

        return invoices

    def _create_news_and_events(self):
        """Create sample news and events."""
        news_titles = [
            "School Registration Open",
            "New Academic Year Begins",
            "Mid-term Examination Schedule",
            "Parent-Teacher Meeting Announcement",
            "Holiday Notice"
        ]

        event_titles = [
            "Annual Sports Day",
            "Science Fair 2025",
            "Cultural Festival",
            "Graduation Ceremony",
            "Alumni Meetup"
        ]

        count = 0

        for title in news_titles:
            NewsAndEvents.objects.create(
                title=title,
                summary=fake.text(200),
                posted_as='News'
            )
            count += 1

        for title in event_titles:
            NewsAndEvents.objects.create(
                title=title,
                summary=fake.text(200),
                posted_as='Event'
            )
            count += 1

        return count

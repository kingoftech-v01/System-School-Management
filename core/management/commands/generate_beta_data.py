"""
Management command to generate comprehensive beta/test data for all apps.
Usage: python manage.py generate_beta_data [--users N] [--clear]
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from faker import Faker

# Import all models
from accounts.models import User, Student, Parent
from core.models import Session, Semester, NewsAndEvents, School
from course.models import Program, Course, CourseAllocation, Upload, UploadVideo
from result.models import TakenCourse
from enrollment.models import RegistrationForm
from attendance.models import Attendance, AttendanceReport
from library.models import Book, BorrowRecord
from events.models import Event
from discipline.models import DisciplinaryAction
from certificates.models import CertificateTemplate, Certificate, BatchCertificateGeneration
from forums.models import ForumCategory, Thread, Post, Tag
from analytics.models import StudentEngagement, AtRiskStudent, CourseCompletion, LearningOutcome, OutcomeMeasurement, ActivityLog
from grading.models import GradingRubric, RubricCriterion, RubricGrade, PeerReview, GradeCurve
from quiz.models import Quiz, Question, MCQuestion, Choice, Sitting
from payments.models import Payment, PaymentPlan, Invoice
from dailystat.models import DailyAttendanceStat

User = get_user_model()
fake = Faker()

USE_TENANTS = 'django_tenants' in settings.INSTALLED_APPS


class Command(BaseCommand):
    help = 'Generate comprehensive beta data for all apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of students to generate (default: 50)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def get_or_create_school(self):
        """Get or create a default school for development."""
        school_kwargs = {
            'name': 'Beta Test School',
            'slug': 'beta-test-school',
            'email': 'contact@betatest.edu',
            'phone': '1234567890',
            'address': '123 Education St',
            'city': 'Test City',
            'postal_code': '12345',
            'license_key': 'BETA-TEST-KEY',
            'subscription_start': timezone.now().date(),
            'subscription_end': timezone.now().date() + timedelta(days=365),
        }
        if USE_TENANTS:
            school_kwargs['schema_name'] = 'beta_test_school'

        school, created = School.objects.get_or_create(
            slug='beta-test-school',
            defaults=school_kwargs
        )
        if created:
            self.stdout.write('  Created default school for beta data')
        return school

    def handle(self, *args, **options):
        num_students = options['users']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('BETA DATA GENERATION STARTING'))
        self.stdout.write(self.style.SUCCESS('='*70))

        if clear_data:
            self.stdout.write(self.style.WARNING('\nClearing existing data...'))
            self.clear_data()

        with transaction.atomic():
            # 0. Get or create school
            school = self.get_or_create_school()

            # 1. Create sessions and semesters
            self.stdout.write('\n1. Creating academic sessions and semesters...')
            session, semester = self.create_sessions_and_semesters()

            # 2. Create programs and courses
            self.stdout.write('2. Creating programs and courses...')
            programs, courses = self.create_programs_and_courses()

            # 3. Create users (students, lecturers, parents, staff)
            self.stdout.write(f'3. Creating {num_students} students, lecturers, and parents...')
            students, lecturers, parents = self.create_users(num_students, programs)

            # 4. Allocate courses to lecturers
            self.stdout.write('4. Allocating courses to lecturers...')
            allocations = self.create_course_allocations(courses, lecturers, session)

            # 5. Enroll students in courses
            self.stdout.write('5. Enrolling students in courses...')
            self.enroll_students(students, courses, session, semester)

            # 6. Generate attendance records
            self.stdout.write('6. Generating attendance records...')
            self.create_attendance_records(students, courses, session, semester)

            # 7. Generate grades and results
            self.stdout.write('7. Generating grades and results...')
            self.create_grades(students, courses, session, semester)

            # 8. Generate library data
            self.stdout.write('8. Creating library books and borrow records...')
            books = self.create_library_data(students, school)

            # 9. Generate events
            self.stdout.write('9. Creating events...')
            events = self.create_events(students, school)

            # 10. Generate news and updates
            self.stdout.write('10. Creating news and announcements...')
            self.create_news()

            # 11. Generate disciplinary records
            self.stdout.write('11. Creating disciplinary records...')
            self.create_disciplinary_actions(students, lecturers)

            # 12. Generate certificates
            self.stdout.write('12. Creating certificates and templates...')
            self.create_certificates(students, courses)

            # 13. Generate forum data
            self.stdout.write('13. Creating forum categories, threads, and posts...')
            self.create_forum_data(students, lecturers)

            # 14. Generate analytics data
            self.stdout.write('14. Creating analytics and engagement data...')
            self.create_analytics_data(students, courses)

            # 15. Generate grading rubrics
            self.stdout.write('15. Creating grading rubrics and peer reviews...')
            self.create_grading_data(students, courses, lecturers)

            # 16. Generate quizzes
            self.stdout.write('16. Creating quizzes and questions...')
            self.create_quiz_data(courses, students)

            # 17. Generate payments
            self.stdout.write('17. Creating payment records...')
            self.create_payment_data(students, session)

            # 18. Generate daily stats
            self.stdout.write('18. Creating daily attendance statistics...')
            self.create_daily_stats(students, courses)

            # 19. Upload sample files
            self.stdout.write('19. Creating sample course uploads...')
            self.create_uploads(courses, lecturers)

        self.stdout.write(self.style.SUCCESS('\n'+'='*70))
        self.stdout.write(self.style.SUCCESS('BETA DATA GENERATION COMPLETED'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS(f'\nGenerated data for {num_students} students!'))
        self.stdout.write(self.style.SUCCESS('\nLogin credentials:'))
        self.stdout.write(self.style.SUCCESS('  Admin: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('  Direction: director / director123'))
        self.stdout.write(self.style.SUCCESS('  Student: student1 / student123'))
        self.stdout.write(self.style.SUCCESS('  Lecturer: lecturer1 / lecturer123'))
        self.stdout.write(self.style.SUCCESS('  Parent: parent1 / parent123'))

    def clear_data(self):
        """Clear all existing data except superusers"""
        models_to_clear = [
            DailyAttendanceStat, OutcomeMeasurement, LearningOutcome, CourseCompletion,
            AtRiskStudent, StudentEngagement, ActivityLog, Post, Thread, ForumCategory,
            Tag, PeerReview, RubricGrade, RubricCriterion, GradingRubric, GradeCurve,
            Sitting, Choice, Question, Quiz, Payment, PaymentPlan, Certificate, BatchCertificateGeneration,
            CertificateTemplate, DisciplinaryAction, Event,
            BorrowRecord, Book, AttendanceReport, Attendance,
            TakenCourse, CourseAllocation, UploadVideo, Upload, RegistrationForm,
            Course, Program, NewsAndEvents, Parent, Student,
        ]

        for model in models_to_clear:
            count = model.objects.all().delete()[0]
            if count > 0:
                self.stdout.write(f'  Cleared {count} {model.__name__} records')

        # Clear non-superuser users
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING('  Data cleared successfully!\n'))

    def create_sessions_and_semesters(self):
        """Create academic sessions and semesters"""
        # Create current and past sessions
        current_year = datetime.now().year
        sessions = []
        for year in range(current_year - 2, current_year + 2):
            session, _ = Session.objects.get_or_create(
                session=f'{year}/{year+1}',
                defaults={'is_current_session': year == current_year}
            )
            sessions.append(session)

        # Create semesters for current session
        current_session = Session.objects.get(is_current_session=True)
        first_sem, _ = Semester.objects.get_or_create(
            semester='First',
            session=current_session,
            defaults={'is_current_semester': True}
        )
        second_sem, _ = Semester.objects.get_or_create(
            semester='Second',
            session=current_session,
            defaults={'is_current_semester': False}
        )

        self.stdout.write(f'  ✓ Created {len(sessions)} sessions and 2 semesters')
        return current_session, first_sem

    def create_programs_and_courses(self):
        """Create academic programs and courses"""
        # Create programs
        programs_data = [
            {'title': 'Computer Science', 'summary': 'Bachelor of Science in Computer Science'},
            {'title': 'Information Technology', 'summary': 'Bachelor of Science in Information Technology'},
            {'title': 'Software Engineering', 'summary': 'Bachelor of Software Engineering'},
            {'title': 'Data Science', 'summary': 'Bachelor of Science in Data Science'},
            {'title': 'Cybersecurity', 'summary': 'Bachelor of Science in Cybersecurity'},
        ]

        programs = []
        for data in programs_data:
            program, _ = Program.objects.get_or_create(
                title=data['title'],
                defaults={'summary': data['summary'], 'is_current': True}
            )
            programs.append(program)

        # Create courses for each program
        course_prefixes = {
            'Computer Science': 'CS',
            'Information Technology': 'IT',
            'Software Engineering': 'SE',
            'Data Science': 'DS',
            'Cybersecurity': 'CYB',
        }

        course_names = [
            'Introduction to Programming', 'Data Structures', 'Algorithms',
            'Database Systems', 'Web Development', 'Mobile Development',
            'Software Engineering', 'Operating Systems', 'Computer Networks',
            'Artificial Intelligence', 'Machine Learning', 'Cloud Computing',
        ]

        courses = []
        for program in programs:
            prefix = course_prefixes[program.title]
            for i, name in enumerate(course_names[:8], 1):  # 8 courses per program
                level = '100' if i <= 2 else ('200' if i <= 4 else ('300' if i <= 6 else '400'))
                course, _ = Course.objects.get_or_create(
                    code=f'{prefix}{level}{i:02d}',
                    defaults={
                        'title': f'{name} ({program.title})',
                        'credit': random.choice([2, 3, 4]),
                        'level': level,
                        'semester': random.choice(['First', 'Second']),
                        'is_elective': random.choice([True, False]),
                        'summary': fake.paragraph(),
                        'program': program,
                    }
                )
                courses.append(course)

        self.stdout.write(f'  ✓ Created {len(programs)} programs and {len(courses)} courses')
        return programs, courses

    def create_users(self, num_students, programs):
        """Create users: students, lecturers, parents, admin"""
        # Create admin user
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@school.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_active': True,
            }
        )
        if _:
            admin.set_password('admin123')
            admin.save()

        # Create direction user
        director, _ = User.objects.get_or_create(
            username='director',
            defaults={
                'email': 'director@school.com',
                'first_name': 'John',
                'last_name': 'Director',
                'role': 'direction',
                'is_staff': True,
                'is_active': True,
            }
        )
        if _:
            director.set_password('director123')
            director.save()

        # Create lecturers
        lecturers = []
        for i in range(1, 11):  # 10 lecturers
            user, created = User.objects.get_or_create(
                username=f'lecturer{i}',
                defaults={
                    'email': f'lecturer{i}@school.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': 'lecturer',
                    'phone': fake.phone_number()[:15],
                    'address': fake.address(),
                    'picture': None,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('lecturer123')
                user.save()
            lecturers.append(user)

        # Create students
        students = []
        levels = ['100', '200', '300', '400']
        for i in range(1, num_students + 1):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@school.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': 'student',
                    'phone': fake.phone_number()[:15],
                    'address': fake.address(),
                    'picture': None,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('student123')
                user.save()

            # Create student profile
            student, _ = Student.objects.get_or_create(
                student=user,
                defaults={
                    'level': random.choice(levels),
                    'program': random.choice(programs),
                }
            )
            students.append(student)

        # Create parents for students
        parents = []
        for i, student in enumerate(students[:20], 1):  # Parents for first 20 students
            user, created = User.objects.get_or_create(
                username=f'parent{i}',
                defaults={
                    'email': f'parent{i}@school.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': 'parent',
                    'phone': fake.phone_number()[:15],
                    'address': fake.address(),
                    'is_active': True,
                }
            )
            if created:
                user.set_password('parent123')
                user.save()

            parent, _ = Parent.objects.get_or_create(
                user=user,
                student=student,
                defaults={
                    'relation_ship': random.choice(['Father', 'Mother', 'Guardian']),
                }
            )
            parents.append(parent)

        self.stdout.write(f'  ✓ Created {len(students)} students, {len(lecturers)} lecturers, {len(parents)} parents')
        return students, lecturers, parents

    def create_course_allocations(self, courses, lecturers, session):
        """Allocate courses to lecturers"""
        allocations = []
        for course in courses:
            lecturer = random.choice(lecturers)
            allocation, _ = CourseAllocation.objects.get_or_create(
                lecturer=lecturer,
                courses=course,
                session=session,
            )
            allocations.append(allocation)

        self.stdout.write(f'  ✓ Allocated {len(allocations)} courses to lecturers')
        return allocations

    def enroll_students(self, students, courses, session, semester):
        """Enroll students in courses"""
        enrollments = 0
        for student in students:
            # Each student takes 4-6 courses per semester
            level_courses = [c for c in courses if c.level == student.level]
            selected_courses = random.sample(level_courses, min(random.randint(4, 6), len(level_courses)))

            for course in selected_courses:
                TakenCourse.objects.get_or_create(
                    student=student,
                    course=course,
                    session=session,
                    semester=semester,
                )
                enrollments += 1

                # Create registration form
                RegistrationForm.objects.get_or_create(
                    student=student,
                    level=student.level,
                    defaults={
                        'status': random.choice(['approved', 'approved', 'approved', 'pending']),
                    }
                )

        self.stdout.write(f'  ✓ Created {enrollments} course enrollments')

    def create_attendance_records(self, students, courses, session, semester):
        """Generate attendance records"""
        attendance_count = 0
        # Create attendance for the past 30 days
        for days_ago in range(30):
            date = timezone.now().date() - timedelta(days=days_ago)
            if date.weekday() >= 5:  # Skip weekends
                continue

            # Create attendance sessions for 2-3 courses per day
            daily_courses = random.sample(list(courses), min(3, len(courses)))
            for course in daily_courses:
                attendance, _ = Attendance.objects.get_or_create(
                    subject=course,
                    date=date,
                    session=session,
                    semester=semester,
                )

                # Mark attendance for enrolled students
                enrolled_students = Student.objects.filter(
                    student__takencourse__course=course,
                    student__takencourse__session=session
                ).distinct()

                for student in enrolled_students:
                    # 80% present, 15% absent, 5% late
                    status = random.choices(
                        ['present', 'absent', 'late'],
                        weights=[80, 15, 5]
                    )[0]

                    AttendanceReport.objects.get_or_create(
                        student=student,
                        attendance=attendance,
                        defaults={'status': status}
                    )
                    attendance_count += 1

        self.stdout.write(f'  ✓ Created {attendance_count} attendance records')

    def create_grades(self, students, courses, session, semester):
        """Generate grades for students"""
        grades_count = 0
        grade_choices = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        grade_points = [4.0, 4.0, 3.7, 3.3, 3.0, 2.7, 2.3, 2.0, 1.7, 1.0, 0.0]

        for student in students:
            taken_courses = TakenCourse.objects.filter(
                student=student,
                session=session,
                semester=semester
            )

            for taken_course in taken_courses:
                # Generate realistic scores
                ca = random.randint(15, 30)  # Out of 30
                exam = random.randint(35, 70)  # Out of 70
                total = ca + exam
                grade_idx = min(int((100 - total) / 10), len(grade_choices) - 1)

                taken_course.ca = ca
                taken_course.exam = exam
                taken_course.total = total
                taken_course.grade = grade_choices[grade_idx]
                taken_course.comment = 'Good' if total >= 70 else ('Fair' if total >= 50 else 'Needs improvement')
                taken_course.save()
                grades_count += 1

        self.stdout.write(f'  ✓ Created {grades_count} grade records')

    def create_library_data(self, students, school):
        """Create library books and borrow records"""
        # Create books
        books = []
        for i in range(100):
            book, _ = Book.objects.get_or_create(
                isbn=fake.isbn13(),
                defaults={
                    'tenant': school,
                    'title': fake.catch_phrase(),
                    'author': fake.name(),
                    'quantity': random.randint(1, 10),
                    'available': random.randint(1, 10),
                    'shelf_location': f'{random.choice("ABCDEFGH")}{random.randint(1, 20)}',
                }
            )
            books.append(book)

        # Create borrow records
        borrows = 0
        for student in random.sample(students, min(30, len(students))):
            for _ in range(random.randint(1, 3)):
                book = random.choice(books)
                borrowed_at = fake.date_time_between(start_date='-60d', end_date='-1d', tzinfo=timezone.get_current_timezone())
                due_date = (borrowed_at + timedelta(days=14)).date()
                returned = random.choice([True, True, True, False])  # 75% returned
                status = 'returned' if returned else ('overdue' if due_date < timezone.now().date() else 'borrowed')

                BorrowRecord.objects.get_or_create(
                    tenant=school,
                    student=student.student,
                    book=book,
                    borrowed_at=borrowed_at,
                    defaults={
                        'due_date': due_date,
                        'returned_at': borrowed_at + timedelta(days=random.randint(1, 20)) if returned else None,
                        'status': status,
                        'fine_amount': Decimal('0.00') if returned and (borrowed_at + timedelta(days=random.randint(1, 14))) <= due_date else Decimal(random.randint(0, 500)),
                    }
                )
                borrows += 1

        self.stdout.write(f'  ✓ Created {len(books)} books and {borrows} borrow records')
        return books

    def create_events(self, students, school):
        """Create events"""
        events = []
        event_types = ['exam', 'holiday', 'meeting', 'activity', 'ceremony', 'deadline']
        target_audiences = ['all', 'students', 'parents', 'staff']

        for i in range(15):
            title = fake.catch_phrase()[:200]
            start_date = fake.date_time_between(start_date='-30d', end_date='+60d', tzinfo=timezone.get_current_timezone())
            event, _ = Event.objects.get_or_create(
                tenant=school,
                title=title,
                start_date=start_date,
                defaults={
                    'description': fake.paragraph(),
                    'event_type': random.choice(event_types),
                    'end_date': start_date + timedelta(hours=random.randint(1, 8)),
                    'location': fake.address()[:100],
                    'target_audience': random.choice(target_audiences),
                    'send_reminder': random.choice([True, False]),
                    'reminder_sent': False,
                }
            )
            events.append(event)

        self.stdout.write(f'  ✓ Created {len(events)} events')
        return events

    def create_news(self):
        """Create news and announcements"""
        news_count = 0
        for i in range(10):
            NewsAndEvents.objects.get_or_create(
                title=fake.sentence()[:200],
                defaults={
                    'summary': fake.paragraph(),
                    'posted_as': random.choice(['important', 'notification', 'announcement']),
                }
            )
            news_count += 1

        self.stdout.write(f'  ✓ Created {news_count} news items')

    def create_disciplinary_actions(self, students, lecturers):
        """Create disciplinary records"""
        actions = 0
        for _ in range(20):
            DisciplinaryAction.objects.create(
                student=random.choice(students),
                action_type=random.choice(['warning', 'suspension', 'probation', 'expulsion']),
                severity=random.choice(['minor', 'moderate', 'serious', 'critical']),
                description=fake.paragraph(),
                reported_by=random.choice(lecturers),
                action_date=fake.date_time_between(start_date='-90d', end_date='now', tzinfo=timezone.get_current_timezone()),
                is_resolved=random.choice([True, False]),
            )
            actions += 1

        self.stdout.write(f'  ✓ Created {actions} disciplinary records')

    def create_certificates(self, students, courses):
        """Create certificate templates and certificates"""
        # Create templates
        template, _ = CertificateTemplate.objects.get_or_create(
            name='Course Completion Certificate',
            defaults={
                'description': 'Standard certificate for course completion',
                'is_active': True,
            }
        )

        # Issue certificates to 30% of students
        certs = 0
        for student in random.sample(students, int(len(students) * 0.3)):
            course = random.choice(courses)
            Certificate.objects.get_or_create(
                student=student,
                course=course,
                template=template,
                defaults={
                    'certificate_number': f'CERT{student.id:04d}{course.id:04d}',
                    'status': 'issued',
                    'is_revoked': False,
                }
            )
            certs += 1

        self.stdout.write(f'  ✓ Created certificate template and {certs} certificates')

    def create_forum_data(self, students, lecturers):
        """Create forum categories, threads, and posts"""
        # Create categories
        categories = []
        cat_names = ['General Discussion', 'Academic Help', 'Announcements', 'Events', 'Off-Topic']
        for name in cat_names:
            cat, _ = ForumCategory.objects.get_or_create(
                name=name,
                defaults={'description': fake.paragraph()}
            )
            categories.append(cat)

        # Create threads and posts
        threads_count = 0
        posts_count = 0
        all_users = list(User.objects.filter(role__in=['student', 'lecturer']))

        for _ in range(30):
            thread, created = Thread.objects.get_or_create(
                title=fake.sentence()[:200],
                defaults={
                    'category': random.choice(categories),
                    'author': random.choice(all_users),
                    'is_pinned': random.choice([False, False, False, True]),
                    'is_locked': random.choice([False, False, False, False, True]),
                }
            )
            if created:
                threads_count += 1

                # Create posts for thread
                for _ in range(random.randint(1, 10)):
                    Post.objects.create(
                        thread=thread,
                        author=random.choice(all_users),
                        content=fake.paragraph(),
                    )
                    posts_count += 1

        self.stdout.write(f'  ✓ Created {len(categories)} categories, {threads_count} threads, {posts_count} posts')

    def create_analytics_data(self, students, courses):
        """Create analytics and engagement data"""
        engagements = 0
        at_risk = 0
        completions = 0

        for student in students:
            student_courses = TakenCourse.objects.filter(student=student)

            for taken in student_courses:
                # Engagement
                for days_ago in range(0, 30, 3):
                    StudentEngagement.objects.get_or_create(
                        student=student,
                        course=taken.course,
                        date=timezone.now().date() - timedelta(days=days_ago),
                        defaults={
                            'login_count': random.randint(0, 5),
                            'total_time_minutes': random.randint(10, 180),
                            'pages_viewed': random.randint(5, 50),
                            'engagement_score': random.uniform(0, 100),
                        }
                    )
                    engagements += 1

                # Course completion
                CourseCompletion.objects.get_or_create(
                    student=student,
                    course=taken.course,
                    defaults={
                        'completion_percentage': Decimal(random.uniform(30, 100)),
                        'is_completed': random.choice([True, False]),
                        'started_at': timezone.now() - timedelta(days=60),
                        'last_activity': timezone.now() - timedelta(days=random.randint(0, 10)),
                    }
                )
                completions += 1

            # At-risk students (10% of students)
            if random.random() < 0.1:
                AtRiskStudent.objects.get_or_create(
                    student=student,
                    course=random.choice(list(student_courses)).course if student_courses else courses[0],
                    defaults={
                        'risk_level': random.choice(['low', 'medium', 'high']),
                        'risk_score': Decimal(random.uniform(0, 100)),
                        'risk_factors': fake.paragraph(),
                        'is_active': True,
                    }
                )
                at_risk += 1

        self.stdout.write(f'  ✓ Created {engagements} engagement records, {completions} completions, {at_risk} at-risk records')

    def create_grading_data(self, students, courses, lecturers):
        """Create grading rubrics and grades"""
        rubrics = []
        for course in random.sample(courses, min(15, len(courses))):
            rubric, _ = GradingRubric.objects.get_or_create(
                name=f'{course.title} Rubric',
                course=course,
                defaults={
                    'description': fake.paragraph(),
                    'max_score': Decimal('100.00'),
                    'is_active': True,
                    'created_by': random.choice(lecturers),
                }
            )
            rubrics.append(rubric)

            # Create criteria
            criteria_names = ['Content Quality', 'Organization', 'Critical Thinking', 'Presentation']
            for name in criteria_names:
                RubricCriterion.objects.get_or_create(
                    rubric=rubric,
                    name=name,
                    defaults={
                        'description': fake.sentence(),
                        'max_points': Decimal('25.00'),
                        'weight': Decimal('0.25'),
                    }
                )

        # Create grades for students
        grades_count = 0
        for rubric in rubrics:
            enrolled = Student.objects.filter(
                student__takencourse__course=rubric.course
            ).distinct()[:20]

            for student in enrolled:
                RubricGrade.objects.get_or_create(
                    student=student,
                    rubric=rubric,
                    defaults={
                        'total_score': Decimal(random.uniform(50, 100)),
                        'percentage': Decimal(random.uniform(50, 100)),
                        'graded_by': random.choice(lecturers),
                    }
                )
                grades_count += 1

        self.stdout.write(f'  ✓ Created {len(rubrics)} rubrics and {grades_count} rubric grades')

    def create_quiz_data(self, courses, students):
        """Create quizzes and questions"""
        quizzes_count = 0
        for course in random.sample(courses, min(10, len(courses))):
            quiz, _ = Quiz.objects.get_or_create(
                title=f'{course.title} Quiz',
                defaults={
                    'description': fake.paragraph(),
                    'course': course,
                    'pass_mark': random.randint(40, 60),
                    'single_attempt': random.choice([True, False]),
                    'draft': False,
                }
            )
            quizzes_count += 1

            # Create questions
            for i in range(5):
                question, _ = MCQuestion.objects.get_or_create(
                    quiz=quiz,
                    content=f'Question {i+1}: {fake.sentence()}',
                    defaults={
                        'figure': None,
                        'explanation': fake.paragraph(),
                    }
                )

                # Create choices
                for j in range(4):
                    Choice.objects.get_or_create(
                        question=question,
                        choice_text=f'Option {chr(65+j)}: {fake.sentence()}',
                        defaults={'correct': j == 0}  # First option is correct
                    )

        self.stdout.write(f'  ✓ Created {quizzes_count} quizzes')

    def create_payment_data(self, students, session):
        """Create payment records"""
        payments_count = 0
        invoices_count = 0

        for student in students:
            # Create invoice for student
            amount = Decimal(random.choice([50000, 75000, 100000]))
            invoice, created = Invoice.objects.get_or_create(
                user=student.student,
                student=student,
                defaults={
                    'total': float(amount),
                    'amount': float(amount),
                    'payment_complete': random.choice([True, True, False]),
                    'invoice_code': f'INV-{student.id}-{session.id}',
                    'due_date': timezone.now().date() + timedelta(days=30),
                }
            )
            if created:
                invoices_count += 1

            # Create payment for invoice if payment is complete
            if invoice.payment_complete:
                Payment.objects.get_or_create(
                    invoice=invoice,
                    transaction_id=fake.uuid4()[:20],
                    defaults={
                        'amount': amount,
                        'payment_gateway': random.choice(['cash', 'bank_transfer', 'stripe']),
                        'status': 'completed',
                    }
                )
                payments_count += 1

        self.stdout.write(f'  ✓ Created {invoices_count} invoices and {payments_count} payment records')

    def create_daily_stats(self, students, courses):
        """Create daily attendance statistics"""
        stats_count = 0
        for days_ago in range(30):
            date = timezone.now().date() - timedelta(days=days_ago)
            if date.weekday() >= 5:
                continue

            # 10% of students have absences each day
            for student in random.sample(students, int(len(students) * 0.1)):
                stat, _ = DailyAttendanceStat.objects.get_or_create(
                    student=student,
                    date=date,
                )
                # Add subjects
                student_courses = Course.objects.filter(
                    takencourse__student=student
                )[:random.randint(1, 3)]
                stat.subjects.set(student_courses)
                stats_count += 1

        self.stdout.write(f'  ✓ Created {stats_count} daily attendance stats')

    def create_uploads(self, courses, lecturers):
        """Create sample course material uploads"""
        uploads_count = 0
        for course in random.sample(courses, min(20, len(courses))):
            # Course files
            for i in range(random.randint(1, 5)):
                Upload.objects.get_or_create(
                    title=f'{course.code} - Lecture {i+1} Notes',
                    course=course,
                    defaults={
                        'file': None,  # Would need actual files
                        'updated_date': timezone.now() - timedelta(days=random.randint(1, 60)),
                    }
                )
                uploads_count += 1

            # Video uploads
            for i in range(random.randint(0, 2)):
                UploadVideo.objects.get_or_create(
                    title=f'{course.code} - Lecture {i+1} Video',
                    course=course,
                    defaults={
                        'video': None,  # Would need actual video files
                        'date_uploaded': timezone.now() - timedelta(days=random.randint(1, 60)),
                    }
                )

        self.stdout.write(f'  ✓ Created {uploads_count} file uploads')

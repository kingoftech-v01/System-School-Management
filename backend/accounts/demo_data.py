"""Demo data generator for accounts app: Users, Students, Parents, Staff."""

import random
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.utils import timezone

from .models import Student, Parent, DepartmentHead, InvitationCode
from .models import ParentTeacherMessage, ParentTeacherAppointment, PermissionSlip
from .signals import post_save_account_receiver

User = get_user_model()


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    # Disconnect post_save signal to prevent username/password overwriting and email sending
    post_save.disconnect(post_save_account_receiver, sender=User)

    try:
        return _generate(tenant, stdout, verbosity, context, fake)
    finally:
        # Always reconnect the signal
        post_save.connect(post_save_account_receiver, sender=User)


def _generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    programs = context.get('programs', [])
    total = 0

    # 1. Professors
    professors_count = context.get('professors_count', 20)
    professors = []
    for i in range(professors_count):
        user = User.objects.create_user(
            username=f'prof{i + 1}',
            email=f'professor{i + 1}@school.edu',
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='professor',
            is_lecturer=True,
            is_staff=True,
            gender=random.choice(['M', 'F']),
            phone=fake.phone_number()[:20],
            street_address=fake.street_address()[:100],
            city=fake.city()[:50],
            province=fake.state()[:50],
            date_of_birth=fake.date_of_birth(minimum_age=28, maximum_age=65),
        )
        professors.append(user)
    total += len(professors)

    # 2. Students
    students_count = context.get('students_count', 150)
    students = []
    for i in range(students_count):
        user = User.objects.create_user(
            username=f'student{i + 1}',
            email=f'student{i + 1}@school.edu',
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='student',
            is_student=True,
            gender=random.choice(['M', 'F']),
            phone=fake.phone_number()[:20],
            street_address=fake.street_address()[:100],
            city=fake.city()[:50],
            province=fake.state()[:50],
            date_of_birth=fake.date_of_birth(minimum_age=16, maximum_age=30),
        )
        program = random.choice(programs)
        student = Student.objects.create(
            student=user,
            level=random.choice(['Bachelor', 'Master']),
            program=program,
        )
        students.append(student)
    total += len(students)

    # 3. Parents
    parents_count = context.get('parents_count', 20)
    parents = []
    for i in range(parents_count):
        user = User.objects.create_user(
            username=f'parent{i + 1}',
            email=f'parent{i + 1}@email.com',
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='parent',
            is_parent=True,
            gender=random.choice(['M', 'F']),
            phone=fake.phone_number()[:20],
        )
        linked_student = students[i % len(students)]
        parent = Parent.objects.create(
            user=user,
            student=linked_student,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email=user.email,
            relation_ship=random.choice([
                'Father', 'Mother', 'Brother', 'Sister',
                'Grand mother', 'Grand father',
            ]),
        )
        parents.append(parent)
    total += len(parents)

    # 4. Staff users
    staff_roles = [
        ('direction', 'direction', 3),
        ('accountant', 'accountant', 2),
        ('secretary', 'secretary', 2),
        ('librarian', 'librarian', 1),
        ('registrar', 'registrar', 1),
        ('prefet', 'prefet', 1),
    ]
    staff_users = []
    for role_name, role_field, count in staff_roles:
        for i in range(count):
            user = User.objects.create_user(
                username=f'{role_name}{i + 1}',
                email=f'{role_name}{i + 1}@school.edu',
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=role_field,
                is_staff=True,
                gender=random.choice(['M', 'F']),
                phone=fake.phone_number()[:20],
            )
            staff_users.append(user)
    total += len(staff_users)

    # 5. Department heads
    dept_heads = []
    for i, program in enumerate(programs[:min(5, len(programs))]):
        if i < len(professors):
            dh = DepartmentHead.objects.create(
                user=professors[i],
                department=program,
            )
            dept_heads.append(dh)
    total += len(dept_heads)

    # 6. Invitation codes
    inv_codes = []
    for i in range(10):
        code = InvitationCode.objects.create(
            code=f'{fake.bothify("????-????").upper()}',
            role=random.choice([
                'parent', 'professor', 'prefet', 'accountant',
                'secretary', 'librarian', 'registrar', 'direction',
            ]),
            is_active=random.choice([True, True, True, False]),
            expires_at=timezone.now() + timedelta(days=random.randint(7, 90)),
            created_by=staff_users[0] if staff_users else professors[0],
        )
        inv_codes.append(code)
    total += len(inv_codes)

    # 7. Parent-teacher messages
    messages = []
    for i in range(30):
        parent = random.choice(parents)
        prof = random.choice(professors)
        student = parent.student
        parent_initiated = random.choice([True, False])
        if parent_initiated:
            sender, recipient = parent.user, prof
        else:
            sender, recipient = prof, parent.user
        msg = ParentTeacherMessage.objects.create(
            sender=sender,
            recipient=recipient,
            student=student,
            subject=fake.sentence(nb_words=6),
            body=fake.paragraph(nb_sentences=3),
            is_read=random.choice([True, False]),
            parent_initiated=parent_initiated,
        )
        messages.append(msg)
    total += len(messages)

    # 8. Parent-teacher appointments
    appointments = []
    used_slots = set()
    time_slots = [
        '08:00-08:30', '08:30-09:00', '09:00-09:30', '09:30-10:00',
        '10:00-10:30', '10:30-11:00', '11:00-11:30', '11:30-12:00',
        '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00',
        '15:00-15:30', '15:30-16:00',
    ]
    for i in range(15):
        parent = random.choice(parents)
        prof = random.choice(professors)
        date = fake.date_between(start_date='-30d', end_date='+30d')
        slot = random.choice(time_slots)
        key = (prof.pk, date, slot)
        if key in used_slots:
            continue
        used_slots.add(key)
        appt = ParentTeacherAppointment.objects.create(
            parent=parent,
            teacher=prof,
            student=parent.student,
            date=date,
            time_slot=slot,
            status=random.choice(['requested', 'confirmed', 'cancelled', 'completed']),
            reason=fake.sentence(nb_words=8),
        )
        appointments.append(appt)
    total += len(appointments)

    # 9. Permission slips
    slips = []
    for i in range(10):
        student = random.choice(students)
        parent = random.choice(parents)
        slip = PermissionSlip.objects.create(
            student=student,
            created_by=random.choice(professors),
            title=random.choice([
                'Field Trip Permission', 'Sports Day Permission',
                'Science Fair Participation', 'Cultural Event',
                'Community Service', 'Lab Activity Consent',
                'Library Off-Campus Visit', 'Swimming Pool Access',
                'Photography/Video Consent', 'Guest Speaker Event',
            ]),
            description=fake.paragraph(nb_sentences=2),
            deadline=fake.date_between(start_date='+1d', end_date='+30d'),
            status=random.choice(['pending', 'signed', 'declined', 'expired']),
        )
        if slip.status == 'signed':
            slip.signed_by = parent
            slip.signed_at = timezone.now() - timedelta(days=random.randint(1, 10))
            slip.save()
        slips.append(slip)
    total += len(slips)

    if stdout and verbosity >= 1:
        stdout.write(f'  [accounts] Created {total} records')
        stdout.write(f'    Professors: {len(professors)}, Students: {len(students)}, '
                     f'Parents: {len(parents)}, Staff: {len(staff_users)}')

    return {
        'professors': professors,
        'students': students,
        'parents': parents,
        'staff_users': staff_users,
        'dept_heads': dept_heads,
        '_total': total,
    }

"""Demo data generator for attendance app: Subjects, Attendance, Reports, Stats."""

import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from accounts.models import Parent
from .models import Group, Student as AttStudent, Subject, Attendance, AttendanceReport
from .models import DailyAttendanceStat, AbsenceNotification


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    acct_students = context['accounts']['students']
    professors = context['accounts']['professors']
    parents = context['accounts']['parents']
    total = 0

    # Use existing groups from seed data
    groups = list(Group.objects.all())
    if not groups:
        # Create a few groups if seed data wasn't run
        for name in ['CS Year 1 Group A', 'BA Year 1 Group A', 'ME Year 1 Group A']:
            groups.append(Group.objects.create(name=name))

    # 1. Attendance Students (maps to accounts students)
    att_students = []
    for i, acct_student in enumerate(acct_students[:150]):
        user = acct_student.student  # The User object
        group = groups[i % len(groups)]
        try:
            att_s = AttStudent.objects.create(
                first_name=user.first_name,
                last_name=user.last_name,
                email=f'att_{user.email}',  # Unique email
                group=group,
            )
            att_students.append(att_s)
        except Exception:
            pass  # Email unique constraint
    total += len(att_students)

    # 2. Subjects (15)
    subject_names = [
        'Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science',
        'English', 'History', 'Geography', 'Economics', 'Art',
        'Physical Education', 'Music', 'French', 'Philosophy', 'Literature',
    ]
    subjects = []
    for i, name in enumerate(subject_names):
        teacher = professors[i % len(professors)]
        subj = Subject.objects.create(
            name=name,
            teacher=teacher,
        )
        # Link groups to subject
        subj.group.set(random.sample(groups, min(3, len(groups))))
        subjects.append(subj)
    total += len(subjects)

    # 3. Attendance records (200)
    attendances = []
    start_date = timezone.now().date() - timedelta(days=90)
    for i in range(200):
        subj = random.choice(subjects)
        date = start_date + timedelta(days=random.randint(0, 90))
        att = Attendance.objects.create(
            subject=subj,
            date=date,
        )
        attendances.append(att)
    total += len(attendances)

    # 4. Attendance reports (~1000)
    reports = []
    absence_reasons = [
        'unexcused', 'medical', 'family_emergency',
        'court_date', 'suspension', 'school_event', 'other',
    ]
    for att in attendances:
        # Pick a subset of students for this attendance
        num_students = min(random.randint(10, 30), len(att_students))
        chosen = random.sample(att_students, num_students)

        for att_student in chosen:
            status = random.choices(
                ['present', 'absent', 'late'],
                weights=[0.8, 0.12, 0.08],
                k=1
            )[0]
            try:
                report = AttendanceReport.objects.create(
                    attendance=att,
                    student=att_student,
                    status=status,
                    absence_reason=random.choice(absence_reasons) if status != 'present' else 'unexcused',
                    absence_notes=fake.sentence() if status != 'present' and random.random() < 0.3 else '',
                    excused=random.choice([True, False]) if status != 'present' else False,
                )
                reports.append(report)
            except Exception:
                pass  # unique_together violation
    total += len(reports)

    # 5. Daily attendance stats (200)
    stats = []
    for att in attendances[:200]:
        subj = att.subject
        for group in subj.group.all()[:1]:  # One group per attendance
            present = random.randint(15, 30)
            absent_cnt = random.randint(0, 5)
            late = random.randint(0, 3)
            total_s = present + absent_cnt + late
            try:
                stat = DailyAttendanceStat.objects.create(
                    subject=subj,
                    group=group,
                    date=att.date,
                    total_students=total_s,
                    present_count=present,
                    absent_count=absent_cnt,
                    late_count=late,
                    attendance_percentage=Decimal(str(round(present / total_s * 100, 2))) if total_s else Decimal('0'),
                )
                stats.append(stat)
            except Exception:
                pass  # unique_together
    total += len(stats)

    # 6. Absence notifications (50)
    notifications = []
    absent_reports = [r for r in reports if r.status == 'absent'][:50]
    for report in absent_reports:
        if parents:
            notif = AbsenceNotification.objects.create(
                attendance_report=report,
                parent=random.choice(parents),
                method=random.choice(['email', 'sms', 'in_app']),
                delivered=random.choice([True, True, False]),
                parent_acknowledged=random.choice([True, False]),
            )
            notifications.append(notif)
    total += len(notifications)

    if stdout and verbosity >= 1:
        stdout.write(f'  [attendance] Created {total} records '
                     f'(students: {len(att_students)}, subjects: {len(subjects)}, '
                     f'attendances: {len(attendances)}, reports: {len(reports)}, '
                     f'stats: {len(stats)}, notifications: {len(notifications)})')

    return {
        'att_students': att_students,
        'subjects': subjects,
        '_total': total,
    }

"""Demo data generator for scheduling app: ScheduleEntries, Availability, Exceptions."""

import random
from datetime import timedelta
from django.utils import timezone

from core.models import Session, Semester
from filieres.models import Filiere
from .models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)


COLORS = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d',
          '#6610f2', '#e83e8c', '#fd7e14', '#20c997']


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    professors = context['accounts']['professors']
    students = context['accounts']['students']
    courses = context.get('courses', [])
    session = context.get('session')
    semester = context.get('semester')
    total = 0

    rooms = list(Room.objects.filter(is_active=True))
    time_slots = list(TimeSlot.objects.filter(is_active=True, slot_type='class'))
    filieres = list(Filiere.objects.all())

    if not rooms or not time_slots:
        if stdout:
            stdout.write('  [scheduling] No rooms or time slots found, skipping')
        return {'_total': 0}

    # 1. Professor availability (100)
    availabilities = []
    prefs = ['unavailable', 'avoid', 'neutral', 'preferred']
    for prof in professors:
        sample_slots = random.sample(time_slots, min(5, len(time_slots)))
        for ts in sample_slots:
            try:
                av = ProfessorAvailability.objects.create(
                    professor=prof,
                    time_slot=ts,
                    preference=random.choice(prefs),
                )
                availabilities.append(av)
            except Exception:
                pass  # unique_together
    total += len(availabilities)

    # 2. Timetable generation records (2)
    generations = []
    for status in ['completed', 'completed']:
        gen = TimetableGeneration.objects.create(
            tenant=tenant,
            session=session,
            semester=semester,
            created_by=random.choice(professors),
            status=status,
            config={'max_hours_per_day': 6, 'prefer_morning': True},
            entries_created=random.randint(40, 80),
            conflicts_found=random.randint(0, 5),
            conflict_details={},
            is_published=True,
            started_at=timezone.now() - timedelta(days=30),
            completed_at=timezone.now() - timedelta(days=29),
        )
        generations.append(gen)
    total += len(generations)

    # 3. Schedule entries (60)
    entries = []
    used_slots = set()
    for i in range(60):
        course = random.choice(courses)
        prof = random.choice(professors)
        room = random.choice(rooms)
        ts = random.choice(time_slots)
        filiere = random.choice(filieres) if filieres else None

        key = (room.pk, ts.pk)
        if key in used_slots:
            continue
        used_slots.add(key)

        entry = ScheduleEntry.objects.create(
            tenant=tenant,
            course=course,
            professor=prof,
            room=room,
            time_slot=ts,
            filiere=filiere,
            session=session,
            semester=semester,
            generation=generations[0] if generations else None,
            group_name=f'Group {chr(65 + (i % 3))}',
            effective_from=fake.date_between(start_date='-90d', end_date='-60d'),
            effective_until=fake.date_between(start_date='+30d', end_date='+90d'),
            recurrence='weekly',
            status='active',
            color=random.choice(COLORS),
            is_locked=random.choice([True, False, False]),
        )
        entries.append(entry)
    total += len(entries)

    # 4. Schedule exceptions (15)
    exceptions = []
    for i in range(min(15, len(entries))):
        entry = entries[i]
        exc_type = random.choice([
            'cancellation', 'room_change', 'substitution', 'reschedule',
        ])
        try:
            exc = ScheduleException.objects.create(
                tenant=tenant,
                schedule_entry=entry,
                exception_type=exc_type,
                date=fake.date_between(start_date='-30d', end_date='+30d'),
                new_room=random.choice(rooms) if exc_type == 'room_change' else None,
                substitute_professor=random.choice(professors) if exc_type == 'substitution' else None,
                reason=fake.sentence(),
                is_approved=random.choice([True, True, False]),
                approved_by=random.choice(professors) if random.random() < 0.6 else None,
                notify_students=True,
                notification_sent=random.choice([True, False]),
            )
            exceptions.append(exc)
        except Exception:
            pass  # unique_together
    total += len(exceptions)

    # 5. Substitution requests (5)
    sub_requests = []
    for i in range(min(5, len(entries))):
        entry = entries[i]
        req_prof = entry.professor
        sub_prof = random.choice([p for p in professors if p != req_prof])
        sr = SubstitutionRequest.objects.create(
            tenant=tenant,
            schedule_entry=entry,
            requesting_professor=req_prof,
            suggested_substitute=sub_prof,
            date=fake.date_between(start_date='-15d', end_date='+15d'),
            reason=fake.sentence(),
            status=random.choice(['pending', 'approved', 'rejected', 'fulfilled']),
        )
        sub_requests.append(sr)
    total += len(sub_requests)

    # 6. Schedule notifications (30)
    notifications = []
    all_users = professors + [s.student for s in students[:20]]
    for i in range(30):
        n = ScheduleNotification.objects.create(
            tenant=tenant,
            recipient=random.choice(all_users),
            related_entry=random.choice(entries) if entries else None,
            notification_type=random.choice([
                'cancellation', 'room_change', 'substitution',
                'reschedule', 'new_event', 'reminder',
            ]),
            title=fake.sentence(nb_words=6),
            message=fake.paragraph(nb_sentences=2),
            is_read=random.choice([True, False]),
            email_sent=random.choice([True, True, False]),
        )
        notifications.append(n)
    total += len(notifications)

    if stdout and verbosity >= 1:
        stdout.write(f'  [scheduling] Created {total} records '
                     f'(availability: {len(availabilities)}, entries: {len(entries)}, '
                     f'exceptions: {len(exceptions)}, notifications: {len(notifications)})')

    return {'entries': entries, '_total': total}

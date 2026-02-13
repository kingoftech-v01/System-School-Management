"""Demo data generator for events app: Events."""

import random
from datetime import timedelta
from django.utils import timezone

from .models import Event


EVENT_DATA = [
    ('Midterm Exams Week', 'exam', 'all'),
    ('Final Exams Period', 'exam', 'all'),
    ('Fall Break', 'holiday', 'all'),
    ('Winter Holiday', 'holiday', 'all'),
    ('Spring Break', 'holiday', 'all'),
    ('Faculty Meeting', 'meeting', 'staff'),
    ('Department Heads Meeting', 'meeting', 'staff'),
    ('Parent-Teacher Conference', 'meeting', 'parents'),
    ('Science Fair', 'activity', 'students'),
    ('Sports Day', 'activity', 'all'),
    ('Graduation Ceremony', 'ceremony', 'all'),
    ('New Student Orientation', 'ceremony', 'students'),
    ('Scholarship Application Deadline', 'deadline', 'students'),
    ('Course Registration Deadline', 'deadline', 'students'),
    ('Annual Cultural Festival', 'activity', 'all'),
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    staff = context['accounts']['staff_users']
    professors = context['accounts']['professors']
    creators = professors + staff[:3]
    total = 0

    events = []
    for title, event_type, audience in EVENT_DATA:
        start = timezone.now() + timedelta(days=random.randint(-60, 120))
        duration = timedelta(days=random.randint(1, 7))

        event = Event.objects.create(
            tenant=tenant,
            title=title,
            description=fake.paragraph(nb_sentences=3),
            event_type=event_type,
            start_date=start,
            end_date=start + duration,
            location=random.choice([
                'Main Auditorium', 'Sports Complex', 'Conference Room A',
                'Amphitheatre 1', 'Library Hall', 'Room 101', 'Online',
            ]),
            target_audience=audience,
            send_reminder=random.choice([True, False]),
            reminder_sent=False,
            created_by=random.choice(creators),
        )
        events.append(event)
    total += len(events)

    if stdout and verbosity >= 1:
        stdout.write(f'  [events] Created {total} records')

    return {'events': events, '_total': total}

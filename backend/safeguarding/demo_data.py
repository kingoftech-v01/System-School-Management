"""Demo data generator for safeguarding app: Incidents, Attachments, VisitorLogs, CaseNotes."""

import random
from datetime import timedelta
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Incident, IncidentAttachment, VisitorLog, StudentCaseNote


INCIDENT_TITLES = [
    'Minor playground injury', 'Student illness during class',
    'Suspicious visitor reported', 'Property damage in lab',
    'Verbal altercation between students', 'Fire alarm activation',
    'Medical emergency in sports field', 'Lost personal belongings',
    'Unauthorized entry attempt', 'Student welfare concern',
]

VISITOR_PURPOSES = [
    'Parent meeting with teacher', 'Document delivery',
    'Inspection visit', 'Maintenance work', 'Guest lecture',
    'Career fair participation', 'Student pickup',
    'Administrative inquiry', 'Campus tour',
    'Volunteer orientation', 'Media interview',
    'Safety audit', 'IT equipment installation',
    'Counselor appointment', 'Library donation',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    reporters = professors + staff[:3]

    # 1. Incidents (10)
    incidents = []
    for i, title in enumerate(INCIDENT_TITLES):
        inc = Incident.objects.create(
            tenant=tenant,
            incident_type=random.choice([
                'security', 'medical', 'accident', 'theft', 'vandalism',
                'confrontation', 'behavioral', 'other',
            ]),
            title=title,
            description=fake.paragraph(nb_sentences=4),
            severity=random.choice(['low', 'medium', 'high', 'critical']),
            status=random.choice(['open', 'investigating', 'action_taken', 'closed']),
            incident_date=fake.date_between(start_date='-90d', end_date='today'),
            incident_time=fake.time_object(),
            location=random.choice([
                'Classroom 101', 'Playground', 'Library', 'Lab',
                'Cafeteria', 'Main entrance', 'Sports field', 'Parking lot',
            ]),
            reported_by=random.choice(reporters),
            actions_taken=fake.paragraph(nb_sentences=2) if random.random() < 0.6 else '',
            follow_up_needed=random.choice([True, False]),
        )
        # Link some students
        linked_students = random.sample(students, min(random.randint(1, 3), len(students)))
        inc.students_involved.set(linked_students)
        incidents.append(inc)
    total += len(incidents)

    # 2. Incident attachments (5)
    attachments = []
    for i in range(5):
        att = IncidentAttachment.objects.create(
            incident=random.choice(incidents),
            file=ContentFile(
                b'%PDF-1.4 Incident report',
                name=f'incident_report_{i + 1}.pdf'
            ),
            description=f'Supporting document #{i + 1}',
            uploaded_by=random.choice(reporters),
        )
        attachments.append(att)
    total += len(attachments)

    # 3. Visitor logs (15)
    visitors = []
    for i, purpose in enumerate(VISITOR_PURPOSES):
        time_in = timezone.now() - timedelta(days=random.randint(0, 90), hours=random.randint(0, 8))
        v = VisitorLog.objects.create(
            tenant=tenant,
            visitor_name=fake.name(),
            visitor_type=random.choice([
                'parent', 'contractor', 'government', 'inspector', 'other',
            ]),
            organization=fake.company()[:200] if random.random() < 0.5 else '',
            id_verified=random.choice([True, True, False]),
            phone=fake.phone_number()[:30],
            purpose=purpose,
            time_in=time_in,
            time_out=time_in + timedelta(hours=random.randint(1, 4)) if random.random() < 0.8 else None,
            host_staff=random.choice(reporters),
            logged_by=random.choice(staff) if staff else random.choice(reporters),
        )
        visitors.append(v)
    total += len(visitors)

    # 4. Student case notes (10)
    case_notes = []
    for i in range(10):
        cn = StudentCaseNote.objects.create(
            tenant=tenant,
            student=random.choice(students),
            category=random.choice([
                'academic', 'behavioral', 'family', 'medical',
                'legal', 'counseling', 'general',
            ]),
            confidentiality=random.choice(['standard', 'restricted', 'highly_restricted']),
            title=fake.sentence(nb_words=6),
            content=fake.paragraph(nb_sentences=4),
            follow_up_date=fake.date_between(start_date='+1d', end_date='+30d') if random.random() < 0.5 else None,
            follow_up_completed=random.choice([True, False]),
            related_incident=random.choice(incidents) if random.random() < 0.3 else None,
            created_by=random.choice(reporters),
        )
        case_notes.append(cn)
    total += len(case_notes)

    if stdout and verbosity >= 1:
        stdout.write(f'  [safeguarding] Created {total} records '
                     f'(incidents: {len(incidents)}, visitors: {len(visitors)}, case_notes: {len(case_notes)})')

    return {'incidents': incidents, '_total': total}

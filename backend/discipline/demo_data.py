"""Demo data generator for discipline app: DisciplinaryActions."""

import random
from datetime import timedelta
from django.utils import timezone

from .models import DisciplinaryAction


INCIDENT_TYPES = [
    'Unauthorized absence', 'Disruptive behavior in class', 'Academic dishonesty',
    'Vandalism of school property', 'Bullying', 'Late arrival to class',
    'Unauthorized use of phone', 'Dress code violation', 'Fighting',
    'Insubordination',
]

ACTIONS_TAKEN = [
    'Verbal warning issued', 'Written warning placed in file',
    'Parent meeting scheduled', 'Detention assigned',
    'Community service hours assigned', 'Suspension for 2 days',
    'Probation for remainder of semester', 'Counseling referral',
    'Loss of privileges', 'Behavioral contract established',
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    student_users = [s.student for s in students]
    reporters = professors + staff[:3]

    actions = []
    for i in range(10):
        incident_date = fake.date_between(start_date='-90d', end_date='today')
        is_resolved = random.choice([True, True, False])

        action = DisciplinaryAction.objects.create(
            tenant=tenant,
            student=random.choice(student_users),
            reported_by=random.choice(reporters),
            incident_type=INCIDENT_TYPES[i],
            description=fake.paragraph(nb_sentences=3),
            action_taken=ACTIONS_TAKEN[i],
            severity=random.choice(['minor', 'moderate', 'serious', 'critical']),
            incident_date=incident_date,
            resolution_date=incident_date + timedelta(days=random.randint(1, 14)) if is_resolved else None,
            is_resolved=is_resolved,
            parent_acknowledged=random.choice([True, False]),
            parent_response=fake.sentence() if random.random() < 0.4 else '',
        )
        actions.append(action)
    total += len(actions)

    if stdout and verbosity >= 1:
        stdout.write(f'  [discipline] Created {total} records')

    return {'actions': actions, '_total': total}

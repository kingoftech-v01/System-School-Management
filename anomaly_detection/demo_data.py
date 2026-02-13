"""Demo data generator for anomaly_detection app: AnomalyAlerts."""

import random
from django.utils import timezone

from .models import AnomalyType, AnomalyAlert


ALERT_DATA = [
    ('Sudden grade jump detected', 'grade'),
    ('Unusual login pattern', 'login'),
    ('Abnormal payment amount', 'payment'),
    ('Duplicate enrollment attempt', 'enrollment'),
    ('Suspicious grade change', 'grade'),
    ('After-hours login detected', 'login'),
    ('Large fee discrepancy', 'payment'),
    ('Grade distribution anomaly', 'academic'),
    ('Multiple failed login attempts', 'login'),
    ('Unauthorized grade modification', 'grade'),
    ('Enrollment cap exceeded', 'enrollment'),
    ('Payment reversal pattern', 'payment'),
    ('Attendance data inconsistency', 'academic'),
    ('Unusual exam score pattern', 'grade'),
    ('Concurrent session detected', 'login'),
    ('Late registration without approval', 'enrollment'),
    ('Grade below threshold', 'academic'),
    ('Bulk grade submission anomaly', 'grade'),
    ('Payment deadline breach', 'payment'),
    ('Repeated course registration', 'enrollment'),
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    total = 0

    anomaly_types = list(AnomalyType.objects.all())
    if not anomaly_types:
        if stdout:
            stdout.write('  [anomaly_detection] No anomaly types found, skipping')
        return {'_total': 0}

    all_users = [s.student for s in students[:20]] + professors + staff[:3]

    # Anomaly alerts (20)
    alerts = []
    for i, (title, domain) in enumerate(ALERT_DATA):
        matching_types = [t for t in anomaly_types if t.domain == domain]
        a_type = random.choice(matching_types) if matching_types else random.choice(anomaly_types)

        alert = AnomalyAlert.objects.create(
            anomaly_type=a_type,
            user=random.choice(all_users),
            severity=random.choice(['low', 'medium', 'high', 'critical']),
            status=random.choice(['new', 'acknowledged', 'resolved', 'false_positive']),
            title=title,
            details={'description': fake.sentence(), 'value': random.randint(1, 100)},
            email_sent=random.choice([True, False]),
            acknowledged_by=random.choice(staff) if random.random() < 0.4 else None,
            resolved_by=random.choice(staff) if random.random() < 0.3 else None,
            notes=fake.sentence() if random.random() < 0.3 else '',
        )
        alerts.append(alert)
    total += len(alerts)

    if stdout and verbosity >= 1:
        stdout.write(f'  [anomaly_detection] Created {total} records')

    return {'_total': total}

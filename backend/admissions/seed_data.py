"""
Initial/reference data for the Admissions app.
Seeds: AdmissionSessions.
"""
from datetime import date


SESSIONS_DATA = [
    {
        'name': '2025-2026 Admissions',
        'start_date': date(2025, 6, 1),
        'end_date': date(2025, 9, 30),
        'is_active': True,
    },
    {
        'name': '2026-2027 Admissions',
        'start_date': date(2026, 6, 1),
        'end_date': date(2026, 9, 30),
        'is_active': False,
    },
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed AdmissionSessions."""
    from .models import AdmissionSession

    results = {'sessions': []}
    created_count = 0
    existed_count = 0

    for data in SESSIONS_DATA:
        obj, created = AdmissionSession.objects.get_or_create(
            name=data['name'],
            defaults={
                'start_date': data['start_date'],
                'end_date': data['end_date'],
                'is_active': data['is_active'],
            },
        )
        if created:
            created_count += 1
        else:
            existed_count += 1
        results['sessions'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  AdmissionSession: {created_count} created, {existed_count} already existed')

    return results

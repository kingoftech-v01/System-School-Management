"""
Initial/reference data for the Core app.
Seeds: Sessions, Semesters.
"""
from datetime import date


SESSIONS_DATA = [
    {
        'session': '2024/2025',
        'is_current_session': False,
        'next_session_begins': date(2025, 9, 1),
    },
    {
        'session': '2025/2026',
        'is_current_session': True,
        'next_session_begins': date(2026, 9, 1),
    },
    {
        'session': '2026/2027',
        'is_current_session': False,
        'next_session_begins': date(2027, 9, 1),
    },
]

SEMESTERS_DATA = [
    ('First', True),
    ('Second', False),
    ('Third', False),
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed Sessions and Semesters."""
    from .models import Session, Semester

    results = {'sessions': [], 'semesters': []}
    session_created = 0
    session_existed = 0
    semester_created = 0
    semester_existed = 0

    # Seed Sessions
    for data in SESSIONS_DATA:
        obj, created = Session.objects.get_or_create(
            session=data['session'],
            defaults={
                'is_current_session': data['is_current_session'],
                'next_session_begins': data['next_session_begins'],
            },
        )
        if created:
            session_created += 1
        else:
            session_existed += 1
        results['sessions'].append(obj)

    # Seed Semesters for each Session
    for session_obj in results['sessions']:
        is_current_session = session_obj.is_current_session
        for sem_name, is_first in SEMESTERS_DATA:
            obj, created = Semester.objects.get_or_create(
                semester=sem_name,
                session=session_obj,
                defaults={
                    'is_current_semester': is_first and is_current_session,
                },
            )
            if created:
                semester_created += 1
            else:
                semester_existed += 1
            results['semesters'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  Session: {session_created} created, {session_existed} already existed')
        stdout.write(f'  Semester: {semester_created} created, {semester_existed} already existed')

    return results

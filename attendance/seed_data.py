"""
Initial/reference data for the Attendance app.
Seeds: Groups (class groups).
"""

GROUPS_DATA = [
    'CS Year 1 Group A',
    'CS Year 1 Group B',
    'CS Year 2 Group A',
    'BA Year 1 Group A',
    'BA Year 1 Group B',
    'BA Year 2 Group A',
    'ME Year 1 Group A',
    'EE Year 1 Group A',
    'MED Year 1 Group A',
    'LAW Year 1 Group A',
    'MATH Year 1 Group A',
    'PHY Year 1 Group A',
    'ECON Year 1 Group A',
    'PSY Year 1 Group A',
    'EDU Year 1 Group A',
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed attendance Groups."""
    from .models import Group

    results = {'groups': []}
    created_count = 0
    existed_count = 0

    for name in GROUPS_DATA:
        obj, created = Group.objects.get_or_create(name=name)
        if created:
            created_count += 1
        else:
            existed_count += 1
        results['groups'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  Group: {created_count} created, {existed_count} already existed')

    return results

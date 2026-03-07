"""
Initial/reference data for the Notices app.
Seeds: NotifyGroups.
"""

GROUPS_DATA = [
    {'name': 'All Students', 'description': 'All enrolled students across all programs'},
    {'name': 'All Staff', 'description': 'All staff members including professors and administrative personnel'},
    {'name': 'All Parents', 'description': 'All registered parents and guardians'},
    {'name': 'All Professors', 'description': 'All teaching faculty members'},
    {'name': 'Year 1 Students', 'description': 'All first-year students across programs'},
    {'name': 'Year 2 Students', 'description': 'All second-year students across programs'},
    {'name': 'Year 3 Students', 'description': 'All third-year students across programs'},
    {'name': 'Year 4 Students', 'description': 'All fourth-year students across programs'},
    {'name': 'Administration', 'description': 'Administrative staff and school direction'},
    {'name': 'Academic Council', 'description': 'Members of the academic council'},
    {'name': 'Student Council', 'description': 'Student government representatives'},
    {'name': 'Library Staff', 'description': 'Library personnel and librarians'},
    {'name': 'Laboratory Staff', 'description': 'Lab technicians and laboratory managers'},
    {'name': 'Sports Department', 'description': 'Sports coaches and physical education staff'},
    {'name': 'Financial Services', 'description': 'Accounting and financial services team'},
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed NotifyGroups."""
    from .models import NotifyGroup

    results = {'groups': []}
    created_count = 0
    existed_count = 0

    for data in GROUPS_DATA:
        obj, created = NotifyGroup.objects.get_or_create(
            name=data['name'],
            defaults={'description': data['description']},
        )
        if created:
            created_count += 1
        else:
            existed_count += 1
        results['groups'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  NotifyGroup: {created_count} created, {existed_count} already existed')

    return results

"""
Initial/reference data for the Articles app.
Seeds: Categories (hierarchical MPTT).
"""

# (name, description, parent_name or None)
CATEGORIES_DATA = [
    ('News', 'Latest news and updates', None),
    ('Academics', 'Academic programs, courses, and research', None),
    ('Sports', 'Sports teams, events, and achievements', None),
    ('Culture & Arts', 'Cultural events, performances, and artistic showcases', None),
    ('Science & Technology', 'Scientific discoveries and technological innovations', None),
    ('Campus Life', 'Daily life, facilities, and community on campus', None),
    ('Alumni', 'Alumni stories, events, and networking', None),
    # Sub-categories
    ('Announcements', 'Official school announcements', 'News'),
    ('Press Releases', 'Official press releases and media statements', 'News'),
    ('Research', 'Research projects and publications', 'Academics'),
    ('Achievements', 'Academic awards and recognitions', 'Academics'),
    ('Football', 'Football team news and matches', 'Sports'),
    ('Basketball', 'Basketball team news and matches', 'Sports'),
    ('Athletics', 'Track and field events and competitions', 'Sports'),
    ('Music', 'Music performances, concerts, and programs', 'Culture & Arts'),
    ('Theater', 'Theater productions and drama events', 'Culture & Arts'),
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed article Categories (hierarchical)."""
    from .models import Category

    results = {'categories': []}
    created_count = 0
    existed_count = 0

    # First pass: create top-level categories
    category_map = {}
    for name, description, parent_name in CATEGORIES_DATA:
        if parent_name is None:
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            else:
                existed_count += 1
            category_map[name] = obj
            results['categories'].append(obj)

    # Second pass: create sub-categories
    for name, description, parent_name in CATEGORIES_DATA:
        if parent_name is not None:
            parent = category_map.get(parent_name)
            if not parent:
                continue
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'parent': parent,
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            else:
                existed_count += 1
            category_map[name] = obj
            results['categories'].append(obj)

    # Rebuild MPTT tree
    Category.objects.rebuild()

    if stdout and verbosity >= 1:
        stdout.write(f'  Category: {created_count} created, {existed_count} already existed')

    return results

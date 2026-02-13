"""
Initial/reference data for the Library app.
Seeds: BookCategories (hierarchical MPTT), Publishers.
"""

# (name, description, parent_name or None)
CATEGORIES_DATA = [
    ('Science', 'Natural and physical sciences', None),
    ('Mathematics', 'Pure and applied mathematics', None),
    ('Literature', 'Fiction, non-fiction, and literary criticism', None),
    ('History', 'World and regional history', None),
    ('Technology', 'Computing, engineering, and applied sciences', None),
    ('Business', 'Business, finance, and management', None),
    ('Arts', 'Visual arts, music, and performing arts', None),
    ('Reference', 'Encyclopedias, dictionaries, and reference materials', None),
    # Sub-categories
    ('Physics', 'Classical and modern physics', 'Science'),
    ('Chemistry', 'Organic, inorganic, and physical chemistry', 'Science'),
    ('Biology', 'Life sciences and ecology', 'Science'),
    ('Computer Science', 'Programming, algorithms, and software', 'Technology'),
    ('Engineering', 'Mechanical, electrical, and civil engineering', 'Technology'),
    ('Economics', 'Micro and macroeconomics', 'Business'),
    ('Management', 'Business management and leadership', 'Business'),
    ('Fiction', 'Novels, short stories, and creative writing', 'Literature'),
    ('Poetry', 'Poems and poetic works', 'Literature'),
]

PUBLISHERS_DATA = [
    {'name': 'Pearson Education', 'country': 'United States', 'website': 'https://www.pearson.com', 'email': 'contact@pearson.com'},
    {'name': 'McGraw-Hill Education', 'country': 'United States', 'website': 'https://www.mheducation.com', 'email': 'contact@mheducation.com'},
    {'name': 'Oxford University Press', 'country': 'United Kingdom', 'website': 'https://www.oup.com', 'email': 'contact@oup.com'},
    {'name': 'Cambridge University Press', 'country': 'United Kingdom', 'website': 'https://www.cambridge.org', 'email': 'contact@cambridge.org'},
    {'name': 'Wiley', 'country': 'United States', 'website': 'https://www.wiley.com', 'email': 'contact@wiley.com'},
    {'name': 'Springer Nature', 'country': 'Germany', 'website': 'https://www.springernature.com', 'email': 'contact@springernature.com'},
    {'name': 'Elsevier', 'country': 'Netherlands', 'website': 'https://www.elsevier.com', 'email': 'contact@elsevier.com'},
    {'name': 'Macmillan Education', 'country': 'United Kingdom', 'website': 'https://www.macmillaneducation.com', 'email': 'contact@macmillaneducation.com'},
    {'name': 'Cengage Learning', 'country': 'United States', 'website': 'https://www.cengage.com', 'email': 'contact@cengage.com'},
    {'name': 'Houghton Mifflin Harcourt', 'country': 'United States', 'website': 'https://www.hmhco.com', 'email': 'contact@hmhco.com'},
    {'name': 'Scholastic', 'country': 'United States', 'website': 'https://www.scholastic.com', 'email': 'contact@scholastic.com'},
    {'name': 'Thomson Reuters', 'country': 'United States', 'website': 'https://www.thomsonreuters.com', 'email': 'contact@thomsonreuters.com'},
    {'name': 'Penguin Random House', 'country': 'United States', 'website': 'https://www.penguinrandomhouse.com', 'email': 'contact@penguinrandomhouse.com'},
    {'name': 'HarperCollins', 'country': 'United States', 'website': 'https://www.harpercollins.com', 'email': 'contact@harpercollins.com'},
    {'name': 'Simon & Schuster', 'country': 'United States', 'website': 'https://www.simonandschuster.com', 'email': 'contact@simonandschuster.com'},
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed BookCategories (hierarchical) and Publishers."""
    from .models import BookCategory, Publisher

    results = {'categories': [], 'publishers': []}
    cat_created = 0
    cat_existed = 0
    pub_created = 0
    pub_existed = 0

    # First pass: create top-level categories
    category_map = {}
    for name, description, parent_name in CATEGORIES_DATA:
        if parent_name is None:
            obj, created = BookCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True,
                },
            )
            if created:
                cat_created += 1
            else:
                cat_existed += 1
            category_map[name] = obj
            results['categories'].append(obj)

    # Second pass: create sub-categories
    for name, description, parent_name in CATEGORIES_DATA:
        if parent_name is not None:
            parent = category_map.get(parent_name)
            if not parent:
                continue
            obj, created = BookCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'parent': parent,
                    'is_active': True,
                },
            )
            if created:
                cat_created += 1
            else:
                cat_existed += 1
            category_map[name] = obj
            results['categories'].append(obj)

    # Rebuild MPTT tree
    BookCategory.objects.rebuild()

    # Seed Publishers
    for data in PUBLISHERS_DATA:
        obj, created = Publisher.objects.get_or_create(
            name=data['name'],
            defaults={
                'country': data['country'],
                'website': data['website'],
                'email': data['email'],
            },
        )
        if created:
            pub_created += 1
        else:
            pub_existed += 1
        results['publishers'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  BookCategory: {cat_created} created, {cat_existed} already existed')
        stdout.write(f'  Publisher: {pub_created} created, {pub_existed} already existed')

    return results

"""
Initial/reference data for the Forums app.
Seeds: ForumCategories, Tags.
"""

CATEGORIES_DATA = [
    {'name': 'General Discussion', 'description': 'Open discussions on any topic', 'icon': 'fa-comments', 'order': 1},
    {'name': 'Academic Help', 'description': 'Get help with coursework and academics', 'icon': 'fa-graduation-cap', 'order': 2},
    {'name': 'Homework & Assignments', 'description': 'Discuss homework problems and assignment questions', 'icon': 'fa-book', 'order': 3},
    {'name': 'Exam Preparation', 'description': 'Tips, resources, and discussions for exam prep', 'icon': 'fa-pencil-alt', 'order': 4},
    {'name': 'Campus Life', 'description': 'Everything about life on campus', 'icon': 'fa-university', 'order': 5},
    {'name': 'Sports & Recreation', 'description': 'Sports teams, fitness, and recreational activities', 'icon': 'fa-futbol', 'order': 6},
    {'name': 'Technology', 'description': 'Tech discussions, tools, and software', 'icon': 'fa-laptop', 'order': 7},
    {'name': 'Career & Jobs', 'description': 'Career advice, internships, and job opportunities', 'icon': 'fa-briefcase', 'order': 8},
    {'name': 'Study Groups', 'description': 'Find and form study groups', 'icon': 'fa-users', 'order': 9},
    {'name': 'Library Resources', 'description': 'Discuss library resources and recommendations', 'icon': 'fa-book-open', 'order': 10},
    {'name': 'Events & Activities', 'description': 'School events, clubs, and extracurricular activities', 'icon': 'fa-calendar', 'order': 11},
    {'name': 'Student Government', 'description': 'Student council discussions and governance', 'icon': 'fa-gavel', 'order': 12},
    {'name': 'Health & Wellness', 'description': 'Physical and mental health resources and discussions', 'icon': 'fa-heart', 'order': 13},
    {'name': 'International Students', 'description': 'Support and community for international students', 'icon': 'fa-globe', 'order': 14},
    {'name': 'Feedback & Suggestions', 'description': 'Share feedback and suggestions for improvement', 'icon': 'fa-lightbulb', 'order': 15},
]

TAGS_DATA = [
    {'name': 'question', 'description': 'A question seeking answers', 'color': '#17a2b8'},
    {'name': 'discussion', 'description': 'Open discussion topic', 'color': '#6c757d'},
    {'name': 'announcement', 'description': 'Official announcement', 'color': '#ffc107'},
    {'name': 'help', 'description': 'Request for help', 'color': '#dc3545'},
    {'name': 'tutorial', 'description': 'Tutorial or how-to guide', 'color': '#28a745'},
    {'name': 'resource', 'description': 'Shared resource or material', 'color': '#007bff'},
    {'name': 'solved', 'description': 'Issue has been resolved', 'color': '#28a745'},
    {'name': 'urgent', 'description': 'Time-sensitive matter', 'color': '#dc3545'},
    {'name': 'poll', 'description': 'Community poll or vote', 'color': '#6610f2'},
    {'name': 'study-group', 'description': 'Study group formation', 'color': '#fd7e14'},
    {'name': 'project', 'description': 'Project-related discussion', 'color': '#20c997'},
    {'name': 'exam', 'description': 'Exam-related content', 'color': '#e83e8c'},
    {'name': 'research', 'description': 'Research topic or paper', 'color': '#6f42c1'},
    {'name': 'off-topic', 'description': 'Not directly academic', 'color': '#6c757d'},
    {'name': 'tips', 'description': 'Helpful tips and advice', 'color': '#17a2b8'},
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed ForumCategories and Tags."""
    from .models import ForumCategory, Tag

    results = {'categories': [], 'tags': []}
    cat_created = 0
    cat_existed = 0
    tag_created = 0
    tag_existed = 0

    for data in CATEGORIES_DATA:
        obj, created = ForumCategory.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'icon': data['icon'],
                'order': data['order'],
                'is_active': True,
            },
        )
        if created:
            cat_created += 1
        else:
            cat_existed += 1
        results['categories'].append(obj)

    for data in TAGS_DATA:
        obj, created = Tag.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'color': data['color'],
            },
        )
        if created:
            tag_created += 1
        else:
            tag_existed += 1
        results['tags'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  ForumCategory: {cat_created} created, {cat_existed} already existed')
        stdout.write(f'  Tag: {tag_created} created, {tag_existed} already existed')

    return results

"""
Initial/reference data for the Course app.
Seeds: Programs, Courses.
"""

PROGRAMS_DATA = [
    {'title': 'Computer Science', 'summary': 'Study of computation, algorithms, and software systems'},
    {'title': 'Business Administration', 'summary': 'Management, finance, and organizational leadership'},
    {'title': 'Mechanical Engineering', 'summary': 'Design and manufacturing of mechanical systems'},
    {'title': 'Electrical Engineering', 'summary': 'Study of electrical circuits, electronics, and power systems'},
    {'title': 'Civil Engineering', 'summary': 'Design and construction of infrastructure'},
    {'title': 'Medicine', 'summary': 'Medical science and clinical practice'},
    {'title': 'Law', 'summary': 'Study of legal systems, regulations, and justice'},
    {'title': 'Mathematics', 'summary': 'Pure and applied mathematical sciences'},
    {'title': 'Physics', 'summary': 'Study of matter, energy, and fundamental forces'},
    {'title': 'Chemistry', 'summary': 'Study of substances, compounds, and chemical reactions'},
    {'title': 'Biology', 'summary': 'Study of living organisms and ecosystems'},
    {'title': 'Economics', 'summary': 'Study of production, distribution, and consumption'},
    {'title': 'Psychology', 'summary': 'Study of mind, behavior, and mental processes'},
    {'title': 'Education', 'summary': 'Teaching methods, pedagogy, and curriculum design'},
    {'title': 'Literature', 'summary': 'Study of written works, literary analysis, and criticism'},
]

# (code, title, credit, program_title, level, year, semester, is_elective)
COURSES_DATA = [
    ('CS101', 'Introduction to Programming', 4, 'Computer Science', 'bachelor', 1, 'fall', False),
    ('CS201', 'Data Structures and Algorithms', 4, 'Computer Science', 'bachelor', 2, 'fall', False),
    ('CS202', 'Computer Networks', 3, 'Computer Science', 'bachelor', 2, 'spring', False),
    ('CS301', 'Database Systems', 3, 'Computer Science', 'bachelor', 3, 'spring', False),
    ('BA101', 'Principles of Management', 3, 'Business Administration', 'bachelor', 1, 'fall', False),
    ('BA201', 'Financial Accounting', 3, 'Business Administration', 'bachelor', 2, 'spring', False),
    ('BA301', 'Marketing Strategy', 3, 'Business Administration', 'bachelor', 3, 'spring', True),
    ('ME101', 'Engineering Mechanics', 4, 'Mechanical Engineering', 'bachelor', 1, 'fall', False),
    ('EE101', 'Circuit Analysis', 4, 'Electrical Engineering', 'bachelor', 1, 'fall', False),
    ('MATH101', 'Calculus I', 4, 'Mathematics', 'bachelor', 1, 'fall', False),
    ('MATH201', 'Linear Algebra', 3, 'Mathematics', 'bachelor', 2, 'fall', False),
    ('PHY101', 'General Physics I', 4, 'Physics', 'bachelor', 1, 'fall', False),
    ('CHEM101', 'General Chemistry', 4, 'Chemistry', 'bachelor', 1, 'fall', False),
    ('BIO101', 'General Biology', 4, 'Biology', 'bachelor', 1, 'fall', False),
    ('ECON101', 'Microeconomics', 3, 'Economics', 'bachelor', 1, 'fall', False),
    ('PSY101', 'Introduction to Psychology', 3, 'Psychology', 'bachelor', 1, 'fall', False),
    ('LAW101', 'Constitutional Law', 3, 'Law', 'bachelor', 1, 'fall', False),
    ('MED101', 'Human Anatomy', 4, 'Medicine', 'bachelor', 1, 'fall', False),
    ('EDU101', 'Foundations of Education', 3, 'Education', 'bachelor', 1, 'fall', False),
    ('LIT101', 'World Literature', 3, 'Literature', 'bachelor', 1, 'fall', True),
]


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed Programs and Courses."""
    from .models import Program, Course

    results = {'programs': [], 'courses': []}
    prog_created = 0
    prog_existed = 0
    course_created = 0
    course_existed = 0

    # Build a lookup for programs by title
    program_map = {}

    # Seed Programs
    for data in PROGRAMS_DATA:
        obj, created = Program.objects.get_or_create(
            title=data['title'],
            defaults={'summary': data['summary']},
        )
        if created:
            prog_created += 1
        else:
            prog_existed += 1
        results['programs'].append(obj)
        program_map[data['title']] = obj

    # Seed Courses
    for code, title, credit, prog_title, level, year, semester, is_elective in COURSES_DATA:
        program = program_map.get(prog_title)
        if not program:
            continue
        obj, created = Course.objects.get_or_create(
            code=code,
            defaults={
                'title': title,
                'credit': credit,
                'program': program,
                'level': level,
                'year': year,
                'semester': semester,
                'is_elective': is_elective,
                'summary': f'{title} - {program.title} program',
            },
        )
        if created:
            course_created += 1
        else:
            course_existed += 1
        results['courses'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  Program: {prog_created} created, {prog_existed} already existed')
        stdout.write(f'  Course: {course_created} created, {course_existed} already existed')

    return results

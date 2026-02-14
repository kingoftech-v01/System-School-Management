"""
Initial/reference data for the Filieres app.
Seeds: Filieres, FiliereSubjects, FiliereRequirements.
Requires: tenant (School instance), courses from course/seed_data.
"""
from decimal import Decimal


# (code, name, description, level, duration_years, capacity)
FILIERES_DATA = [
    ('CS', 'Computer Science', 'Study of computation, algorithms, and software systems', 'Bachelor', 3, 120),
    ('BA', 'Business Administration', 'Management, finance, and organizational leadership', 'Bachelor', 3, 100),
    ('ME', 'Mechanical Engineering', 'Design and manufacturing of mechanical systems', 'Bachelor', 4, 80),
    ('EE', 'Electrical Engineering', 'Study of electrical circuits, electronics, and power systems', 'Bachelor', 4, 80),
    ('CE', 'Civil Engineering', 'Design and construction of infrastructure', 'Bachelor', 4, 80),
    ('MED', 'Medicine', 'Medical science and clinical practice', 'Bachelor', 6, 60),
    ('LAW', 'Law', 'Study of legal systems, regulations, and justice', 'Bachelor', 4, 100),
    ('MATH', 'Mathematics', 'Pure and applied mathematical sciences', 'Bachelor', 3, 60),
    ('PHY', 'Physics', 'Study of matter, energy, and fundamental forces', 'Bachelor', 3, 60),
    ('CHEM', 'Chemistry', 'Study of substances, compounds, and chemical reactions', 'Bachelor', 3, 60),
    ('BIO', 'Biology', 'Study of living organisms and ecosystems', 'Bachelor', 3, 60),
    ('ECON', 'Economics', 'Study of production, distribution, and consumption', 'Bachelor', 3, 80),
    ('PSY', 'Psychology', 'Study of mind, behavior, and mental processes', 'Bachelor', 3, 80),
    ('EDU', 'Education', 'Teaching methods, pedagogy, and curriculum design', 'Bachelor', 3, 100),
    ('LIT', 'Literature', 'Study of written works, literary analysis, and criticism', 'Bachelor', 3, 60),
]

# Mapping: filiere_code -> list of (course_code, coefficient, is_mandatory, year, semester, credits, hours_per_week)
SUBJECTS_MAP = {
    'CS': [
        ('CS101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('CS201', Decimal('3.00'), True, 2, 1, 4, 4),
        ('CS202', Decimal('2.50'), True, 2, 2, 3, 3),
        ('CS301', Decimal('2.50'), True, 3, 1, 3, 3),
        ('MATH101', Decimal('2.00'), True, 1, 1, 4, 4),
    ],
    'BA': [
        ('BA101', Decimal('3.00'), True, 1, 1, 3, 3),
        ('BA201', Decimal('3.00'), True, 2, 2, 3, 3),
        ('BA301', Decimal('2.00'), False, 3, 2, 3, 3),
        ('ECON101', Decimal('2.50'), True, 1, 1, 3, 3),
    ],
    'ME': [
        ('ME101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('MATH101', Decimal('2.50'), True, 1, 1, 4, 4),
        ('PHY101', Decimal('2.50'), True, 1, 2, 4, 4),
    ],
    'EE': [
        ('EE101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('MATH101', Decimal('2.50'), True, 1, 1, 4, 4),
        ('PHY101', Decimal('2.50'), True, 1, 2, 4, 4),
    ],
    'MATH': [
        ('MATH101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('MATH201', Decimal('3.00'), True, 2, 1, 3, 3),
        ('PHY101', Decimal('2.00'), True, 1, 2, 4, 4),
    ],
    'PHY': [
        ('PHY101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('MATH101', Decimal('2.50'), True, 1, 1, 4, 4),
        ('MATH201', Decimal('2.00'), True, 2, 1, 3, 3),
    ],
    'CHEM': [
        ('CHEM101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('MATH101', Decimal('2.00'), True, 1, 1, 4, 4),
        ('PHY101', Decimal('2.00'), True, 1, 2, 4, 4),
    ],
    'BIO': [
        ('BIO101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('CHEM101', Decimal('2.50'), True, 1, 2, 4, 4),
    ],
    'ECON': [
        ('ECON101', Decimal('3.00'), True, 1, 1, 3, 3),
        ('MATH101', Decimal('2.00'), True, 1, 1, 4, 4),
        ('BA101', Decimal('2.00'), True, 1, 2, 3, 3),
    ],
    'PSY': [
        ('PSY101', Decimal('3.00'), True, 1, 1, 3, 3),
        ('BIO101', Decimal('2.00'), True, 1, 2, 4, 4),
    ],
    'LAW': [
        ('LAW101', Decimal('3.00'), True, 1, 1, 3, 3),
    ],
    'MED': [
        ('MED101', Decimal('3.00'), True, 1, 1, 4, 4),
        ('BIO101', Decimal('2.50'), True, 1, 2, 4, 4),
        ('CHEM101', Decimal('2.00'), True, 1, 2, 4, 4),
    ],
    'EDU': [
        ('EDU101', Decimal('3.00'), True, 1, 1, 3, 3),
        ('PSY101', Decimal('2.00'), True, 1, 2, 3, 3),
    ],
    'LIT': [
        ('LIT101', Decimal('3.00'), True, 1, 1, 3, 3),
    ],
    'CE': [
        ('MATH101', Decimal('2.50'), True, 1, 1, 4, 4),
        ('PHY101', Decimal('2.50'), True, 1, 2, 4, 4),
    ],
}

# Requirements: (requirement_type, description, is_mandatory, order)
DEFAULT_REQUIREMENTS = [
    ('academic', 'High school diploma or equivalent qualification', True, 1),
    ('language', 'Proficiency in the language of instruction', True, 2),
]

EXTRA_REQUIREMENTS = {
    'MED': [('exam', 'Entrance examination in Biology and Chemistry', True, 3)],
    'LAW': [('exam', 'Entrance examination in General Knowledge and Logic', True, 3)],
    'ME': [('academic', 'Strong background in Mathematics and Physics', True, 3)],
    'EE': [('academic', 'Strong background in Mathematics and Physics', True, 3)],
    'CE': [('academic', 'Strong background in Mathematics and Physics', True, 3)],
}


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed Filieres, FiliereSubjects, FiliereRequirements. Requires tenant and course context."""
    from .models import Filiere, FiliereSubject, FiliereRequirement
    from course.models import Course

    if not tenant:
        if stdout:
            stdout.write('  [SKIP] Filieres: No tenant provided (required for Filiere)')
        return {'filieres': [], 'subjects': [], 'requirements': []}

    results = {'filieres': [], 'subjects': [], 'requirements': []}
    fil_created = 0
    fil_existed = 0
    sub_created = 0
    sub_existed = 0
    req_created = 0
    req_existed = 0

    # Build course lookup
    course_map = {}
    for course in Course.objects.all():
        course_map[course.code] = course

    # Seed Filieres
    filiere_map = {}
    for code, name, desc, level, duration, capacity in FILIERES_DATA:
        obj, created = Filiere.objects.get_or_create(
            tenant=tenant,
            code=code,
            defaults={
                'name': name,
                'description': desc,
                'level': level,
                'duration_years': duration,
                'capacity': capacity,
                'is_active': True,
            },
        )
        if created:
            fil_created += 1
        else:
            fil_existed += 1
        filiere_map[code] = obj
        results['filieres'].append(obj)

    # Seed FiliereSubjects
    for fil_code, subjects in SUBJECTS_MAP.items():
        filiere = filiere_map.get(fil_code)
        if not filiere:
            continue
        for course_code, coeff, mandatory, year, semester, credits, hours in subjects:
            course = course_map.get(course_code)
            if not course:
                continue
            obj, created = FiliereSubject.objects.get_or_create(
                filiere=filiere,
                subject=course,
                year=year,
                semester=semester,
                defaults={
                    'coefficient': coeff,
                    'is_mandatory': mandatory,
                    'credits': credits,
                    'hours_per_week': hours,
                },
            )
            if created:
                sub_created += 1
            else:
                sub_existed += 1
            results['subjects'].append(obj)

    # Seed FiliereRequirements
    for fil_code, filiere in filiere_map.items():
        for req_type, desc, mandatory, order in DEFAULT_REQUIREMENTS:
            obj, created = FiliereRequirement.objects.get_or_create(
                filiere=filiere,
                requirement_type=req_type,
                description=desc,
                defaults={
                    'is_mandatory': mandatory,
                    'order': order,
                },
            )
            if created:
                req_created += 1
            else:
                req_existed += 1
            results['requirements'].append(obj)

        # Extra requirements for specific filieres
        for req_type, desc, mandatory, order in EXTRA_REQUIREMENTS.get(fil_code, []):
            obj, created = FiliereRequirement.objects.get_or_create(
                filiere=filiere,
                requirement_type=req_type,
                description=desc,
                defaults={
                    'is_mandatory': mandatory,
                    'order': order,
                },
            )
            if created:
                req_created += 1
            else:
                req_existed += 1
            results['requirements'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  Filiere: {fil_created} created, {fil_existed} already existed')
        stdout.write(f'  FiliereSubject: {sub_created} created, {sub_existed} already existed')
        stdout.write(f'  FiliereRequirement: {req_created} created, {req_existed} already existed')

    return results

"""
Initial/reference data for the Grading app.
Seeds: GradingRubrics, RubricCriteria.
Requires: Courses from course/seed_data.
"""
from decimal import Decimal


# (rubric_name, description, course_code, max_score, passing_score)
RUBRICS_DATA = [
    ('Programming Assignment Rubric', 'Standard rubric for programming assignments', 'CS101', Decimal('100.00'), Decimal('60.00')),
    ('Programming Exam Rubric', 'Rubric for programming course exams', 'CS101', Decimal('100.00'), Decimal('50.00')),
    ('Data Structures Project Rubric', 'Rubric for data structures projects', 'CS201', Decimal('100.00'), Decimal('60.00')),
    ('Networking Lab Rubric', 'Rubric for computer networking lab work', 'CS202', Decimal('100.00'), Decimal('60.00')),
    ('Database Project Rubric', 'Rubric for database system projects', 'CS301', Decimal('100.00'), Decimal('60.00')),
    ('Management Case Study Rubric', 'Rubric for business case study analysis', 'BA101', Decimal('100.00'), Decimal('60.00')),
    ('Accounting Problem Set Rubric', 'Rubric for accounting exercises', 'BA201', Decimal('100.00'), Decimal('50.00')),
    ('Marketing Presentation Rubric', 'Rubric for marketing strategy presentations', 'BA301', Decimal('100.00'), Decimal('60.00')),
    ('Engineering Design Rubric', 'Rubric for engineering design projects', 'ME101', Decimal('100.00'), Decimal('60.00')),
    ('Circuit Lab Report Rubric', 'Rubric for circuit analysis lab reports', 'EE101', Decimal('100.00'), Decimal('60.00')),
    ('Calculus Problem Set Rubric', 'Rubric for calculus problem sets', 'MATH101', Decimal('100.00'), Decimal('50.00')),
    ('Physics Lab Report Rubric', 'Rubric for physics laboratory reports', 'PHY101', Decimal('100.00'), Decimal('60.00')),
    ('Chemistry Lab Report Rubric', 'Rubric for chemistry laboratory reports', 'CHEM101', Decimal('100.00'), Decimal('60.00')),
    ('Essay Writing Rubric', 'General rubric for academic essays', 'LIT101', Decimal('100.00'), Decimal('60.00')),
    ('Research Paper Rubric', 'Rubric for research papers and thesis', 'PSY101', Decimal('100.00'), Decimal('60.00')),
]

# Criteria templates by rubric type
CRITERIA_TEMPLATES = {
    'programming': [
        ('Correctness', 'Code produces correct output for all test cases', Decimal('40.00'), Decimal('10.00'), 0),
        ('Code Quality', 'Clean, readable, and well-structured code', Decimal('25.00'), Decimal('10.00'), 1),
        ('Documentation', 'Clear comments and documentation', Decimal('20.00'), Decimal('10.00'), 2),
        ('Testing', 'Adequate test coverage and edge cases', Decimal('15.00'), Decimal('10.00'), 3),
    ],
    'lab_report': [
        ('Methodology', 'Proper experimental methodology and procedure', Decimal('30.00'), Decimal('10.00'), 0),
        ('Data Analysis', 'Accurate data collection and analysis', Decimal('30.00'), Decimal('10.00'), 1),
        ('Results & Discussion', 'Clear presentation and interpretation of results', Decimal('25.00'), Decimal('10.00'), 2),
        ('Formatting', 'Proper formatting, citations, and presentation', Decimal('15.00'), Decimal('10.00'), 3),
    ],
    'case_study': [
        ('Analysis', 'Depth and quality of analysis', Decimal('35.00'), Decimal('10.00'), 0),
        ('Application of Theory', 'Proper application of management theories', Decimal('25.00'), Decimal('10.00'), 1),
        ('Recommendations', 'Quality and feasibility of recommendations', Decimal('25.00'), Decimal('10.00'), 2),
        ('Presentation', 'Clear writing and professional presentation', Decimal('15.00'), Decimal('10.00'), 3),
    ],
    'problem_set': [
        ('Correctness', 'Correct final answers', Decimal('40.00'), Decimal('10.00'), 0),
        ('Methodology', 'Proper mathematical approach and formulas', Decimal('30.00'), Decimal('10.00'), 1),
        ('Work Shown', 'Clear step-by-step working', Decimal('20.00'), Decimal('10.00'), 2),
        ('Presentation', 'Neat and organized presentation', Decimal('10.00'), Decimal('10.00'), 3),
    ],
    'essay': [
        ('Thesis & Argument', 'Clear thesis statement and logical argumentation', Decimal('30.00'), Decimal('10.00'), 0),
        ('Evidence & Support', 'Quality of evidence and textual support', Decimal('25.00'), Decimal('10.00'), 1),
        ('Analysis', 'Depth of critical analysis and interpretation', Decimal('25.00'), Decimal('10.00'), 2),
        ('Writing Quality', 'Grammar, style, and academic conventions', Decimal('20.00'), Decimal('10.00'), 3),
    ],
    'presentation': [
        ('Content', 'Quality and depth of content presented', Decimal('35.00'), Decimal('10.00'), 0),
        ('Delivery', 'Clear communication and presentation skills', Decimal('25.00'), Decimal('10.00'), 1),
        ('Visual Aids', 'Effective use of slides and visual materials', Decimal('20.00'), Decimal('10.00'), 2),
        ('Q&A', 'Ability to answer questions and defend points', Decimal('20.00'), Decimal('10.00'), 3),
    ],
    'design': [
        ('Design Quality', 'Innovation and quality of engineering design', Decimal('35.00'), Decimal('10.00'), 0),
        ('Technical Accuracy', 'Correct application of engineering principles', Decimal('30.00'), Decimal('10.00'), 1),
        ('Documentation', 'Technical drawings and documentation quality', Decimal('20.00'), Decimal('10.00'), 2),
        ('Feasibility', 'Practical feasibility and cost considerations', Decimal('15.00'), Decimal('10.00'), 3),
    ],
}

# Map rubric names to criteria templates
RUBRIC_CRITERIA_MAP = {
    'Programming Assignment Rubric': 'programming',
    'Programming Exam Rubric': 'problem_set',
    'Data Structures Project Rubric': 'programming',
    'Networking Lab Rubric': 'lab_report',
    'Database Project Rubric': 'programming',
    'Management Case Study Rubric': 'case_study',
    'Accounting Problem Set Rubric': 'problem_set',
    'Marketing Presentation Rubric': 'presentation',
    'Engineering Design Rubric': 'design',
    'Circuit Lab Report Rubric': 'lab_report',
    'Calculus Problem Set Rubric': 'problem_set',
    'Physics Lab Report Rubric': 'lab_report',
    'Chemistry Lab Report Rubric': 'lab_report',
    'Essay Writing Rubric': 'essay',
    'Research Paper Rubric': 'essay',
}


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed GradingRubrics and RubricCriteria. Requires courses."""
    from .models import GradingRubric, RubricCriterion
    from course.models import Course

    results = {'rubrics': [], 'criteria': []}
    rubric_created = 0
    rubric_existed = 0
    crit_created = 0
    crit_existed = 0

    # Build course lookup
    course_map = {}
    for course in Course.objects.all():
        course_map[course.code] = course

    for name, description, course_code, max_score, passing_score in RUBRICS_DATA:
        course = course_map.get(course_code)
        if not course:
            continue

        rubric, created = GradingRubric.objects.get_or_create(
            name=name,
            course=course,
            defaults={
                'description': description,
                'max_score': max_score,
                'passing_score': passing_score,
                'is_active': True,
                'allow_partial_credit': True,
            },
        )
        if created:
            rubric_created += 1
        else:
            rubric_existed += 1
        results['rubrics'].append(rubric)

        # Create criteria for this rubric
        template_key = RUBRIC_CRITERIA_MAP.get(name)
        if template_key and created:
            criteria_data = CRITERIA_TEMPLATES.get(template_key, [])
            for crit_name, crit_desc, weight, max_pts, order in criteria_data:
                crit, crit_new = RubricCriterion.objects.get_or_create(
                    rubric=rubric,
                    name=crit_name,
                    defaults={
                        'description': crit_desc,
                        'weight': weight,
                        'max_points': max_pts,
                        'order': order,
                    },
                )
                if crit_new:
                    crit_created += 1
                else:
                    crit_existed += 1
                results['criteria'].append(crit)

    if stdout and verbosity >= 1:
        stdout.write(f'  GradingRubric: {rubric_created} created, {rubric_existed} already existed')
        stdout.write(f'  RubricCriterion: {crit_created} created, {crit_existed} already existed')

    return results

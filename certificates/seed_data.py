"""
Initial/reference data for the Certificates app.
Seeds: CertificateTemplates.
"""
from django.core.files.base import ContentFile


TEMPLATES_DATA = [
    {
        'name': 'Course Completion Certificate',
        'description': 'Awarded upon successful completion of a course',
        'title_text': 'Certificate of Course Completion',
        'body_template': 'This is to certify that {student_name} has successfully completed the course "{course_name}" with a grade of {grade} on {date}.',
        'signature_1_name': 'Course Instructor',
        'signature_1_title': 'Professor',
        'signature_2_name': 'Academic Dean',
        'signature_2_title': 'Dean of Academics',
    },
    {
        'name': 'Program Completion Certificate',
        'description': 'Awarded upon completion of an academic program',
        'title_text': 'Certificate of Program Completion',
        'body_template': 'This is to certify that {student_name} has successfully completed the "{course_name}" program on {date}.',
        'signature_1_name': 'Program Director',
        'signature_1_title': 'Director',
        'signature_2_name': 'School Director',
        'signature_2_title': 'Director General',
    },
    {
        'name': 'Degree Certificate',
        'description': 'Official degree certificate for graduating students',
        'title_text': 'Degree Certificate',
        'body_template': 'The Board of Trustees hereby confers upon {student_name} the degree, having fulfilled all requirements with a GPA of {grade}, this {date}.',
        'signature_1_name': 'Academic Dean',
        'signature_1_title': 'Dean of Academics',
        'signature_2_name': 'School Director',
        'signature_2_title': 'Director General',
    },
    {
        'name': 'Honor Roll Certificate',
        'description': 'Recognition for students on the Honor Roll',
        'title_text': 'Honor Roll Certificate',
        'body_template': 'This certifies that {student_name} has been placed on the Honor Roll for outstanding academic achievement with a GPA of {grade} on {date}.',
        'signature_1_name': 'Academic Dean',
        'signature_1_title': 'Dean of Academics',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Academic Excellence Award',
        'description': 'Award for exceptional academic performance',
        'title_text': 'Academic Excellence Award',
        'body_template': 'This award is presented to {student_name} in recognition of exceptional academic excellence in "{course_name}" on {date}.',
        'signature_1_name': 'Department Head',
        'signature_1_title': 'Head of Department',
        'signature_2_name': 'Academic Dean',
        'signature_2_title': 'Dean of Academics',
    },
    {
        'name': 'Perfect Attendance Certificate',
        'description': 'Recognition for perfect attendance',
        'title_text': 'Perfect Attendance Certificate',
        'body_template': 'This certifies that {student_name} has achieved perfect attendance for the academic period ending {date}.',
        'signature_1_name': 'Class Advisor',
        'signature_1_title': 'Advisor',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': "Dean's List Certificate",
        'description': "Recognition for Dean's List students",
        'title_text': "Dean's List Certificate",
        'body_template': "This certifies that {student_name} has been named to the Dean's List for outstanding academic performance with a GPA of {grade} on {date}.",
        'signature_1_name': 'Academic Dean',
        'signature_1_title': 'Dean of Academics',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Research Achievement Certificate',
        'description': 'Recognition for research contributions',
        'title_text': 'Research Achievement Certificate',
        'body_template': 'This certifies that {student_name} has made significant contributions to research in "{course_name}" on {date}.',
        'signature_1_name': 'Research Supervisor',
        'signature_1_title': 'Professor',
        'signature_2_name': 'Research Director',
        'signature_2_title': 'Director of Research',
    },
    {
        'name': 'Community Service Certificate',
        'description': 'Recognition for community service',
        'title_text': 'Community Service Certificate',
        'body_template': 'This certifies that {student_name} has completed community service hours and demonstrated commitment to service on {date}.',
        'signature_1_name': 'Community Coordinator',
        'signature_1_title': 'Coordinator',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Sports Achievement Certificate',
        'description': 'Recognition for sports achievements',
        'title_text': 'Sports Achievement Certificate',
        'body_template': 'This certifies that {student_name} has demonstrated outstanding athletic achievement in sports on {date}.',
        'signature_1_name': 'Sports Director',
        'signature_1_title': 'Director of Sports',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Student Leadership Certificate',
        'description': 'Recognition for student leadership',
        'title_text': 'Student Leadership Certificate',
        'body_template': 'This certifies that {student_name} has demonstrated exceptional leadership qualities and service to the student body on {date}.',
        'signature_1_name': 'Student Affairs Director',
        'signature_1_title': 'Director',
        'signature_2_name': 'School Director',
        'signature_2_title': 'Director General',
    },
    {
        'name': 'Internship Completion Certificate',
        'description': 'Confirmation of internship completion',
        'title_text': 'Internship Completion Certificate',
        'body_template': 'This certifies that {student_name} has successfully completed an internship program in "{course_name}" on {date}.',
        'signature_1_name': 'Internship Coordinator',
        'signature_1_title': 'Coordinator',
        'signature_2_name': 'Academic Dean',
        'signature_2_title': 'Dean of Academics',
    },
    {
        'name': 'Workshop Participation Certificate',
        'description': 'Confirmation of workshop attendance',
        'title_text': 'Certificate of Participation',
        'body_template': 'This certifies that {student_name} participated in the workshop "{course_name}" on {date}.',
        'signature_1_name': 'Workshop Facilitator',
        'signature_1_title': 'Facilitator',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Professional Development Certificate',
        'description': 'Recognition of professional development',
        'title_text': 'Professional Development Certificate',
        'body_template': 'This certifies that {student_name} has completed a professional development program in "{course_name}" on {date}.',
        'signature_1_name': 'Program Coordinator',
        'signature_1_title': 'Coordinator',
        'signature_2_name': '',
        'signature_2_title': '',
    },
    {
        'name': 'Special Recognition Certificate',
        'description': 'Special recognition for unique achievements',
        'title_text': 'Special Recognition Certificate',
        'body_template': 'This special recognition is awarded to {student_name} for outstanding contribution and achievement on {date}.',
        'signature_1_name': 'School Director',
        'signature_1_title': 'Director General',
        'signature_2_name': '',
        'signature_2_title': '',
    },
]

PLACEHOLDER_HTML = """<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<div style="text-align:center; padding:50px; border:2px solid #333; margin:20px;">
    <h1>{title}</h1>
    <p>{body}</p>
    <div style="margin-top:50px;">
        <p>____________________</p>
        <p>Authorized Signature</p>
    </div>
</div>
</body>
</html>"""


def seed(tenant=None, stdout=None, verbosity=1, context=None):
    """Seed CertificateTemplates."""
    from .models import CertificateTemplate

    results = {'templates': []}
    created_count = 0
    existed_count = 0

    for data in TEMPLATES_DATA:
        obj, created = CertificateTemplate.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'title_text': data['title_text'],
                'body_template': data['body_template'],
                'signature_1_name': data['signature_1_name'],
                'signature_1_title': data['signature_1_title'],
                'signature_2_name': data['signature_2_name'],
                'signature_2_title': data['signature_2_title'],
                'orientation': 'landscape',
                'page_size': 'A4',
                'is_active': True,
            },
        )
        if created:
            # Save a placeholder template file
            html = PLACEHOLDER_HTML.format(
                title=data['title_text'],
                body=data['body_template'],
            )
            filename = data['name'].lower().replace(' ', '_').replace("'", '') + '.html'
            obj.template_file.save(filename, ContentFile(html.encode()), save=True)
            created_count += 1
        else:
            existed_count += 1
        results['templates'].append(obj)

    if stdout and verbosity >= 1:
        stdout.write(f'  CertificateTemplate: {created_count} created, {existed_count} already existed')

    return results

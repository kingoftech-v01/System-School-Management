"""Demo data generator for enrollment app: RegistrationForms, Documents, StatusHistory."""

import random
from django.core.files.base import ContentFile

from filieres.models import Filiere
from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    filieres = list(Filiere.objects.all())
    reviewers = staff + professors[:3]
    total = 0

    # 1. Registration forms (30)
    statuses = ['pending', 'under_review', 'approved', 'rejected', 'enrolled']
    registrations = []
    for i in range(30):
        status = random.choice(statuses)
        reg = RegistrationForm.objects.create(
            tenant=tenant,
            student_first_name=fake.first_name(),
            student_middle_name=fake.first_name() if random.random() < 0.3 else '',
            student_last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=15, maximum_age=25),
            gender=random.choice(['M', 'F']),
            nationality=fake.country()[:100],
            email=f'applicant{i + 1}@email.com',
            phone=fake.phone_number()[:20],
            street_address=fake.street_address()[:255],
            city=fake.city()[:100],
            province=fake.state()[:100],
            country=fake.country()[:100],
            postal_code=fake.postcode()[:20],
            parent_first_name=fake.first_name(),
            parent_middle_name='',
            parent_last_name=fake.last_name(),
            parent_email=f'parent_applicant{i + 1}@email.com',
            parent_phone=fake.phone_number()[:20],
            parent_relationship=random.choice(['father', 'mother', 'guardian']),
            filiere=random.choice(filieres) if filieres else None,
            academic_year='2025-2026',
            level=random.choice(['Bachelor', 'Master']),
            previous_school=fake.company()[:200],
            enrollment_type=random.choice(['new', 'transfer', 're_enrollment']),
            status=status,
            reviewed_by=random.choice(reviewers) if status != 'pending' else None,
            review_notes=fake.sentence() if status not in ('pending',) else '',
            rejection_reason=fake.sentence() if status == 'rejected' else '',
            special_needs=fake.sentence() if random.random() < 0.1 else '',
            medical_information=fake.sentence() if random.random() < 0.1 else '',
        )
        registrations.append(reg)
    total += len(registrations)

    # 2. Enrollment documents (2 per registration)
    doc_types = [
        'birth_certificate', 'photo', 'transcript', 'transfer_letter',
        'medical_certificate', 'id_card', 'parent_id', 'other',
    ]
    documents = []
    for reg in registrations:
        num_docs = random.randint(1, 3)
        chosen_types = random.sample(doc_types, min(num_docs, len(doc_types)))
        for doc_type in chosen_types:
            doc = EnrollmentDocument.objects.create(
                registration=reg,
                document_type=doc_type,
                file=ContentFile(
                    b'%PDF-1.4 Demo document',
                    name=f'{doc_type}_{reg.pk}.pdf'
                ),
                description=f'{doc_type.replace("_", " ").title()} for {reg.student_first_name}',
                is_verified=reg.status in ('approved', 'enrolled'),
                verified_by=random.choice(reviewers) if reg.status in ('approved', 'enrolled') else None,
            )
            documents.append(doc)
    total += len(documents)

    # 3. Status history (2 per registration)
    history = []
    status_flow = {
        'pending': [],
        'under_review': [('pending', 'under_review')],
        'approved': [('pending', 'under_review'), ('under_review', 'approved')],
        'rejected': [('pending', 'under_review'), ('under_review', 'rejected')],
        'enrolled': [('pending', 'under_review'), ('under_review', 'approved'), ('approved', 'enrolled')],
    }
    for reg in registrations:
        transitions = status_flow.get(reg.status, [])
        for old_s, new_s in transitions:
            h = EnrollmentStatusHistory.objects.create(
                registration=reg,
                old_status=old_s,
                new_status=new_s,
                changed_by=random.choice(reviewers),
                notes=fake.sentence() if random.random() < 0.5 else '',
            )
            history.append(h)
    total += len(history)

    if stdout and verbosity >= 1:
        stdout.write(f'  [enrollment] Created {total} records '
                     f'(registrations: {len(registrations)}, docs: {len(documents)}, history: {len(history)})')

    return {
        'registrations': registrations,
        'documents': documents,
        '_total': total,
    }

"""Demo data generator for certificates app: Certificates, Verifications, BatchGeneration."""

import random
from decimal import Decimal
from django.utils import timezone

from .models import CertificateTemplate, Certificate, CertificateVerification, BatchCertificateGeneration


GRADE_LETTERS = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C']


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    professors = context['accounts']['professors']
    courses = context.get('courses', [])
    total = 0

    templates = list(CertificateTemplate.objects.filter(is_active=True))
    if not templates:
        if stdout:
            stdout.write('  [certificates] No templates found, skipping')
        return {'_total': 0}

    # 1. Certificates (30)
    certificates = []
    used_pairs = set()
    for i in range(30):
        student = random.choice(students)
        course = random.choice(courses)
        key = (student.pk, course.pk)
        if key in used_pairs:
            continue
        used_pairs.add(key)

        status = random.choices(
            ['issued', 'generated', 'pending'],
            weights=[0.6, 0.2, 0.2],
            k=1
        )[0]

        try:
            cert = Certificate.objects.create(
                student=student,
                course=course,
                template=random.choice(templates),
                issue_date=fake.date_between(start_date='-180d', end_date='today'),
                completion_date=fake.date_between(start_date='-200d', end_date='-30d'),
                grade=random.choice(GRADE_LETTERS),
                gpa=Decimal(str(round(random.uniform(2.5, 4.0), 2))),
                credits=Decimal(str(course.credit)),
                status=status,
                issued_by=random.choice(professors) if status == 'issued' else None,
            )
            certificates.append(cert)
        except Exception:
            pass  # unique_together
    total += len(certificates)

    # 2. Certificate verifications (15)
    verifications = []
    issued_certs = [c for c in certificates if c.status == 'issued']
    for cert in issued_certs[:15]:
        v = CertificateVerification.objects.create(
            certificate=cert,
            verification_method=random.choice(['qr_code', 'number', 'hash']),
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            verified_by_user=random.choice(professors) if random.random() < 0.5 else None,
            is_valid=True,
            verification_notes='Verified successfully' if random.random() < 0.7 else '',
        )
        verifications.append(v)
    total += len(verifications)

    # 3. Batch certificate generation (3)
    batches = []
    for i in range(min(3, len(courses))):
        course = courses[i]
        b = BatchCertificateGeneration.objects.create(
            course=course,
            template=random.choice(templates),
            min_grade='C',
            min_gpa=Decimal('2.0'),
            total_students=random.randint(20, 50),
            processed_count=random.randint(15, 50),
            success_count=random.randint(10, 45),
            failure_count=random.randint(0, 5),
            status='completed',
            initiated_by=random.choice(professors),
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        batches.append(b)
    total += len(batches)

    if stdout and verbosity >= 1:
        stdout.write(f'  [certificates] Created {total} records '
                     f'(certs: {len(certificates)}, verifications: {len(verifications)}, batches: {len(batches)})')

    return {'certificates': certificates, '_total': total}

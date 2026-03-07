"""Demo data generator for admissions app: AdmissionStudents, CounselingComments, Payments."""

import random
from decimal import Decimal

from .models import AdmissionSession, AdmissionStudent, CounselingComment, AdmissionPayment


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    programs = context.get('programs', [])
    professors = context['accounts']['professors']
    staff = context['accounts']['staff_users']
    reviewers = staff + professors[:3]
    total = 0

    sessions = list(AdmissionSession.objects.all())
    if not sessions:
        if stdout:
            stdout.write('  [admissions] No admission sessions found, skipping')
        return {'_total': 0}

    active_session = next((s for s in sessions if s.is_active), sessions[0])

    # 1. Admission students (30)
    statuses = ['pending', 'under_review', 'counseling', 'payment_pending', 'admitted', 'rejected']
    applicants = []
    for i in range(30):
        status = random.choice(statuses)
        app = AdmissionStudent.objects.create(
            session=active_session,
            first_name=fake.first_name(),
            middle_name=fake.first_name() if random.random() < 0.3 else '',
            last_name=fake.last_name(),
            email=f'admission{i + 1}@email.com',
            phone=fake.phone_number()[:20],
            date_of_birth=fake.date_of_birth(minimum_age=15, maximum_age=25),
            gender=random.choice(['M', 'F', 'O']),
            nationality=fake.country()[:100],
            street_address=fake.street_address()[:255],
            city=fake.city()[:100],
            province=fake.state()[:100],
            country=fake.country()[:100],
            postal_code=fake.postcode()[:20],
            guardian_first_name=fake.first_name(),
            guardian_middle_name='',
            guardian_last_name=fake.last_name(),
            guardian_phone=fake.phone_number()[:20],
            guardian_email=fake.email(),
            program=random.choice(programs) if programs else None,
            previous_school=fake.company()[:200],
            previous_grade=random.choice(['A', 'B+', 'B', 'C+', 'C', 'D']),
            exam_scores={'math': random.randint(50, 100), 'english': random.randint(50, 100)},
            status=status,
            reviewed_by=random.choice(reviewers) if status not in ('pending',) else None,
            counselor=random.choice(professors) if status == 'counseling' else None,
            application_fee_paid=status in ('payment_pending', 'admitted'),
            admitted=status == 'admitted',
            admission_date=fake.date_between(start_date='-60d', end_date='today') if status == 'admitted' else None,
            rejection_reason=fake.sentence() if status == 'rejected' else '',
        )
        applicants.append(app)
    total += len(applicants)

    # 2. Counseling comments (20)
    comments = []
    counseling_apps = [a for a in applicants if a.status in ('counseling', 'admitted', 'payment_pending')]
    for i in range(min(20, len(counseling_apps) * 3)):
        app = random.choice(counseling_apps) if counseling_apps else random.choice(applicants)
        c = CounselingComment.objects.create(
            application=app,
            counselor=random.choice(professors),
            comment=fake.paragraph(nb_sentences=3),
            is_recommendation=random.choice([True, False]),
        )
        comments.append(c)
    total += len(comments)

    # 3. Admission payments (15)
    payments = []
    paid_apps = [a for a in applicants if a.application_fee_paid]
    for app in paid_apps[:15]:
        try:
            p = AdmissionPayment.objects.create(
                application=app,
                amount=Decimal(random.choice(['50.00', '75.00', '100.00'])),
                transaction_id=f'ADM-TXN-{fake.uuid4()[:12].upper()}',
                payment_method=random.choice(['stripe', 'bank_transfer', 'cash']),
                verified=random.choice([True, False]),
                verified_by=random.choice(staff) if random.random() < 0.5 else None,
            )
            payments.append(p)
        except Exception:
            pass  # Skip if OneToOne already exists
    total += len(payments)

    if stdout and verbosity >= 1:
        stdout.write(f'  [admissions] Created {total} records '
                     f'(applicants: {len(applicants)}, comments: {len(comments)}, payments: {len(payments)})')

    return {
        'applicants': applicants,
        '_total': total,
    }

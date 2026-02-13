"""Demo data generator for payments app: Invoices, PaymentPlans, Installments, Payments, Receipts."""

import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from .models import FeeStructure, Invoice, PaymentPlan, Installment, Payment, PaymentVerification, Receipt


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    staff = context['accounts']['staff_users']
    semester = context.get('semester')
    total = 0

    fee_structures = list(FeeStructure.objects.filter(is_active=True))

    # 1. Invoices (one per student, ~150)
    invoices = []
    for student in students:
        user = student.student
        fs = None
        if fee_structures:
            matching = [f for f in fee_structures if f.program == student.program]
            fs = matching[0] if matching else random.choice(fee_structures)

        fee_total = Decimal('0')
        if fs:
            fee_total = fs.tuition_fee + fs.registration_fee + fs.library_fee + fs.lab_fee + fs.sports_fee + fs.other_fees
        else:
            fee_total = Decimal(str(random.randint(1000, 5000)))

        paid_ratio = random.choice([0, 0.25, 0.5, 0.75, 1.0])
        amount_paid = round(float(fee_total) * paid_ratio, 2)
        is_complete = paid_ratio >= 1.0

        invoice = Invoice.objects.create(
            user=user,
            student=student,
            fee_structure=fs,
            total=fee_total,
            amount=Decimal(str(amount_paid)),
            payment_complete=is_complete,
            invoice_code=f'INV-{timezone.now().year}-{student.pk:05d}',
            due_date=(timezone.now() + timedelta(days=random.randint(14, 90))).date(),
            semester=semester,
            description=f'Tuition and fees for {student.program.title if student.program else "N/A"}',
        )
        invoices.append(invoice)
    total += len(invoices)

    # 2. Payment plans (30 invoices get plans)
    plans = []
    plan_invoices = random.sample(invoices, min(30, len(invoices)))
    for invoice in plan_invoices:
        num_installments = random.choice([2, 3, 4])
        installment_amount = round(float(invoice.total) / num_installments, 2)

        try:
            plan = PaymentPlan.objects.create(
                invoice=invoice,
                total_amount=invoice.total,
                number_of_installments=num_installments,
                installment_amount=Decimal(str(installment_amount)),
            )
            plans.append(plan)
        except Exception:
            continue  # OneToOne
    total += len(plans)

    # 3. Installments (3 per plan ~90)
    installments = []
    for plan in plans:
        for n in range(1, plan.number_of_installments + 1):
            due = (timezone.now() + timedelta(days=30 * n)).date()
            is_paid = random.random() < 0.6
            inst = Installment.objects.create(
                payment_plan=plan,
                installment_number=n,
                amount=plan.installment_amount,
                due_date=due,
                paid=is_paid,
                paid_date=fake.date_between(start_date='-30d', end_date='today') if is_paid else None,
            )
            installments.append(inst)
    total += len(installments)

    # 4. Payments (100)
    payments = []
    paid_invoices = [inv for inv in invoices if float(inv.amount) > 0]
    for i in range(min(100, len(paid_invoices))):
        invoice = paid_invoices[i]
        status = random.choices(
            ['completed', 'pending', 'processing', 'failed'],
            weights=[0.7, 0.1, 0.1, 0.1],
            k=1
        )[0]

        payment = Payment.objects.create(
            invoice=invoice,
            amount=invoice.amount if invoice.amount else Decimal('100.00'),
            payment_gateway=random.choice(['stripe', 'bank_transfer', 'cash']),
            transaction_id=f'TXN-{fake.uuid4()[:12].upper()}',
            status=status,
        )
        payments.append(payment)
    total += len(payments)

    # 5. Payment verifications (50)
    verifications = []
    completed_payments = [p for p in payments if p.status == 'completed']
    for payment in completed_payments[:50]:
        try:
            v = PaymentVerification.objects.create(
                payment=payment,
                verified_by=random.choice(staff) if staff else None,
                verification_status=random.choice(['verified', 'verified', 'pending']),
                verification_notes=fake.sentence() if random.random() < 0.3 else '',
                verified_at=timezone.now() - timedelta(days=random.randint(0, 30)),
            )
            verifications.append(v)
        except Exception:
            pass  # OneToOne
    total += len(verifications)

    # 6. Receipts (50)
    receipts = []
    for i, payment in enumerate(completed_payments[:50]):
        try:
            r = Receipt.objects.create(
                payment=payment,
                receipt_number=f'RCP-{timezone.now().year}-{i + 1:05d}',
                sent_to_email=random.choice([True, False]),
            )
            receipts.append(r)
        except Exception:
            pass  # OneToOne
    total += len(receipts)

    if stdout and verbosity >= 1:
        stdout.write(f'  [payments] Created {total} records '
                     f'(invoices: {len(invoices)}, plans: {len(plans)}, '
                     f'installments: {len(installments)}, payments: {len(payments)}, '
                     f'receipts: {len(receipts)})')

    return {'invoices': invoices, 'payments': payments, '_total': total}

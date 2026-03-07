# Payments App Architecture

## Overview

The `payments` app manages the complete financial lifecycle of the school management
system: fee structures per program/level/year, invoice generation, payment processing
through multiple gateways (Stripe, PayPal, Coinbase, Paylike, GoPay), installment
payment plans, multi-step payment verification, and receipt generation. It exposes
both a Django template frontend and a DRF REST API with role-based access control.

---

## Model Relationships

### Entity-Relationship Summary

```text
course.Program ──1:N──> FeeStructure ──1:N──> Invoice
core.Semester ──1:N──> Invoice (nullable)
accounts.User ──1:N──> Invoice (user FK)
accounts.Student ──1:N──> Invoice (student FK, nullable)
Invoice ──1:1──> PaymentPlan ──1:N──> Installment
Invoice ──1:N──> Payment
Installment ──0..1:N──> Payment (optional FK)
Payment ──1:1──> PaymentVerification
Payment ──1:1──> Receipt
accounts.User ──1:N──> PaymentVerification (verified_by FK)
```

### Full Model Diagram

```text
                  course.Program
                       |
                       | 1:N (program FK)
                       v
                  FeeStructure
                  - program FK ──────────────> course.Program
                  - level (CharField, LEVEL_CHOICES)
                  - academic_year (CharField)
                  - tuition_fee (Decimal)
                  - registration_fee (Decimal)
                  - library_fee (Decimal)
                  - lab_fee (Decimal)
                  - sports_fee (Decimal)
                  - other_fees (Decimal)
                  - is_active (Boolean)
                  - unique_together: [program, level, academic_year]
                       |
                       | 1:N (fee_structure FK, nullable)
                       v
    accounts.User ──> Invoice <── core.Semester
    (user FK)         - user FK ─────────────> AUTH_USER_MODEL
    accounts.Student  - student FK ──────────> accounts.Student (nullable)
    (student FK)      - fee_structure FK ────> FeeStructure (nullable)
                      - semester FK ─────────> core.Semester (nullable)
                      - total (Decimal, nullable)
                      - amount (Decimal, nullable)
                      - payment_complete (Boolean)
                      - invoice_code (CharField)
                      - due_date (Date, nullable)
                      - description (Text)
                           |
              +────────────+────────────+
              |                         |
              | 1:1                     | 1:N
              v                         v
         PaymentPlan                 Payment
         - invoice 1:1 ──> Invoice   - invoice FK ──> Invoice
         - total_amount              - installment FK ──> Installment (nullable)
         - number_of_installments    - amount (Decimal)
         - installment_amount        - payment_gateway (stripe|braintree|bank_transfer|cash)
              |                      - transaction_id (unique)
              | 1:N                  - status (pending|processing|completed|failed|refunded)
              v                           |
         Installment              +───────+───────+
         - payment_plan FK        |               |
         - installment_number     | 1:1           | 1:1
         - amount (Decimal)       v               v
         - due_date          PaymentVerification  Receipt
         - paid (Boolean)    - payment 1:1        - payment 1:1
         - paid_date         - verified_by FK     - receipt_number (unique)
                               ──> AUTH_USER_MODEL - pdf_file (FileField)
                             - verification_status - generated_at
                               (pending|verified|  - sent_to_email
                                rejected)
                             - verification_notes
                             - verified_at
```

### Model Details

#### FeeStructure

- **Purpose**: Defines fee breakdowns per program, level, and academic year
- **Key Fields**: `program` (FK), `level`, `academic_year`, `tuition_fee`, `registration_fee`, `library_fee`, `lab_fee`, `sports_fee`, `other_fees`, `is_active`
- **Constraints**: `unique_together = [program, level, academic_year]`
- **Indexes**: `(program, level, academic_year)`, `(is_active, -academic_year)`
- **Methods**: `get_total_fee()` -- sums all 6 fee component fields
- **Ordering**: `-academic_year`, `program`, `level`

#### Invoice

- **Purpose**: Represents a bill issued to a student
- **Key Fields**: `user` (FK), `student` (FK, nullable), `fee_structure` (FK, nullable), `semester` (FK, nullable), `total`, `amount`, `payment_complete`, `invoice_code`, `due_date`, `description`
- **Indexes**: `(student, -created_at)`, `(payment_complete, due_date)`
- **Methods**: `is_overdue()` -- returns True if past `due_date` and not paid
- **Ordering**: `-created_at`
- **Notes**: Both `user` and `student` FKs exist; `user` points to `AUTH_USER_MODEL` while `student` points to `accounts.Student`

#### PaymentPlan

- **Purpose**: Allows splitting an invoice into multiple installments
- **Key Fields**: `invoice` (OneToOne), `total_amount`, `number_of_installments`, `installment_amount`
- **Methods**: `get_paid_installments()`, `get_remaining_installments()`, `get_remaining_amount()`
- **Relationship**: OneToOne with Invoice; has many Installments

#### Installment

- **Purpose**: Single payment within a PaymentPlan
- **Key Fields**: `payment_plan` (FK), `installment_number`, `amount`, `due_date`, `paid`, `paid_date`
- **Constraints**: `unique_together = [payment_plan, installment_number]`
- **Methods**: `is_overdue()` -- returns True if past `due_date` and not paid
- **Ordering**: `installment_number`

#### Payment

- **Purpose**: Records a payment transaction against an invoice
- **Key Fields**: `invoice` (FK), `installment` (FK, nullable), `amount`, `payment_gateway`, `transaction_id` (unique), `status`
- **Gateway Choices**: `stripe`, `braintree`, `bank_transfer`, `cash`
- **Status Choices**: `pending`, `processing`, `completed`, `failed`, `refunded`
- **Indexes**: `(invoice, -payment_date)`, `(status, -payment_date)`, `(transaction_id)`
- **Ordering**: `-payment_date`

#### PaymentVerification

- **Purpose**: Multi-step approval workflow for payments (e.g., manual/bank payments)
- **Key Fields**: `payment` (OneToOne), `verified_by` (FK, nullable), `verification_status`, `verification_notes`, `verified_at`
- **Status Choices**: `pending`, `verified`, `rejected`
- **Methods**: `verify(user, notes)` -- atomically sets verified + Payment.status='completed'; `reject(user, notes)` -- atomically sets rejected + Payment.status='failed'
- **Ordering**: `-created_at`

#### Receipt

- **Purpose**: Auto-generated PDF receipt for completed payments
- **Key Fields**: `payment` (OneToOne), `receipt_number` (unique), `pdf_file` (FileField, upload to `receipts/%Y/%m/%d/`), `sent_to_email`
- **Ordering**: `-generated_at`

### Payment Status Lifecycle

```text
pending ──> processing ──> completed ──> refunded
   |              |
   v              v
 failed <─────────+
   |
   v
 pending (retry)
```

### Verification Status Lifecycle

```text
pending ──> verified   (sets payment.status = 'completed')
   |
   +──> rejected       (sets payment.status = 'failed')
```

---

## View Access Patterns per Role

### Frontend Views (views_frontend.py)

| View | URL Pattern | Decorator(s) | Allowed Roles | Inline Checks |
| ------ | ------------- | -------------- | --------------- | --------------- |
| `PaymentGetwaysView` | `/` | `@login_required` | All authenticated | Ownership: `invoice.user == request.user` or parent-of-student |
| `payment_paypal` | `/paypal/` | `@login_required` | All authenticated | None (context helper only) |
| `payment_stripe` | `/stripe/` | `@login_required` | All authenticated | None (context helper only) |
| `payment_coinbase` | `/coinbase/` | `@login_required` | All authenticated | None (context helper only) |
| `payment_paylike` | `/paylike/` | `@login_required` | All authenticated | None (context helper only) |
| `stripe_charge` | `/stripe-charge/` (POST) | `@login_required` | Owner or parent | `invoice.user == request.user`, parent check, superuser bypass |
| `gopay_charge` | `/gopay-charge/` (POST) | `@login_required` | All authenticated | None |
| `payment_succeed` | `/payment-succeed/`, `/completed/` | `@login_required` | All authenticated | None |
| `paymentComplete` | `/complete/` (POST/AJAX) | `@login_required` | Owner or parent | `invoice.user == request.user`, parent check, superuser bypass |
| `create_invoice` | `/create-invoice/` | `@login_required` + `@accountant_allowed` (2FA) | **accountant**, **direction**, **admin** | 2FA enforcement |
| `invoice_detail` | `/invoice-detail/<id>/` | `@login_required` | Owner, parent, superuser | Inline ownership + parent check |
| `fee_structure_list` | `/fee-structures/` | `@login_required` + `@accountant_allowed` (2FA) | **accountant**, **direction**, **admin** | 2FA enforcement |
| `fee_structure_create` | `/fee-structures/create/` | `@login_required` + `@accountant_allowed` (2FA) | **accountant**, **direction**, **admin** | 2FA enforcement |
| `fee_structure_edit` | `/fee-structures/<pk>/edit/` | `@login_required` + `@accountant_allowed` (2FA) | **accountant**, **direction**, **admin** | 2FA enforcement |
| `fee_structure_delete` | `/fee-structures/<pk>/delete/` | `@login_required` + `@accountant_allowed` (2FA) | **accountant**, **direction**, **admin** | 2FA enforcement |
| `student_invoices` | `/my-invoices/` | `@login_required` + `@student_required` | **student** | Filtered to `user=request.user` |
| `student_payment_history` | `/my-payments/` | `@login_required` + `@student_required` | **student** | Filtered to `invoice__user=request.user` |

### API ViewSets (views_api.py)

| ViewSet | URL Prefix | Permission Classes | Queryset Scoping | Filters |
| --------- | ----------- | ------------------- | ------------------ | --------- |
| `FeeStructureViewSet` | `/fee-structures/` | `IsAuthenticated` + `IsAccountantOrDirectionUser` | All | program, level, academic_year, is_active |
| `InvoiceViewSet` | `/invoices/` | `IsAuthenticated` + (`IsStudentOrParent` \| `IsAccountantOrDirectionUser`) | Role-scoped (see below) | student, payment_complete, semester |
| `PaymentPlanViewSet` | `/payment-plans/` | `IsAuthenticated` + `IsAccountantOrDirectionUser` | All | -- |
| `InstallmentViewSet` | `/installments/` | `IsAuthenticated` + `IsAccountantOrDirectionUser` | All | payment_plan, paid |
| `PaymentViewSet` | `/payments/` | `IsAuthenticated` + `IsAccountantOrDirectionUser` | All | invoice, status, payment_gateway |
| `PaymentVerificationViewSet` | `/verifications/` | `IsAuthenticated` + `IsAccountantOrDirectionUser` | All | verification_status |
| `ReceiptViewSet` | `/receipts/` (read-only) | `IsAuthenticated` | All | -- |

#### InvoiceViewSet Queryset Scoping

```text
if user.is_staff or user.is_superuser:
    -> All invoices
elif user.role in ('accountant', 'direction', 'admin'):
    -> All invoices
elif user.is_parent:
    -> Invoices for linked children (via Parent model)
else (student):
    -> Only own invoices (user=request.user)
```

### Complete Role Access Matrix

```text
                     FeeStruct  Invoice   PayPlan  Installmt  Payment  Verific. Receipt  PayGateway
                     CRUD       CRUD      CRUD     CRUD       CRUD     CRUD     Read     Use
  +──────────────+──────────+──────────+────────+──────────+────────+────────+────────+──────────+
  | student      |    -     | Read own |   -    |    -     |   -    |   -    |  Yes   | Yes(own) |
  | professor    |    -     |    -     |   -    |    -     |   -    |   -    |  Yes   |    -     |
  | direction    |  CRUD*   |  CRUD*   | CRUD*  |  CRUD*   | CRUD*  | CRUD*  |  Yes   |    -     |
  | parent       |    -     |Read child|   -    |    -     |   -    |   -    |  Yes   |Yes(child)|
  | admin        |  CRUD*   |  CRUD*   | CRUD*  |  CRUD*   | CRUD*  | CRUD*  |  Yes   |    -     |
  | prefet       |    -     |    -     |   -    |    -     |   -    |   -    |  Yes   |    -     |
  | accountant   |  CRUD*   |  CRUD*   | CRUD*  |  CRUD*   | CRUD*  | CRUD*  |  Yes   |    -     |
  | secretary    |    -     |    -     |   -    |    -     |   -    |   -    |  Yes   |    -     |
  | librarian    |    -     |    -     |   -    |    -     |   -    |   -    |  Yes   |    -     |
  | registrar    |    -     |    -     |   -    |    -     |   -    |   -    |  Yes   |    -     |
  +──────────────+──────────+──────────+────────+──────────+────────+────────+────────+──────────+

  * = Requires 2FA for frontend views (@accountant_allowed includes @require_2fa)
  "Read own" = Student sees only invoices where user=self
  "Read child" = Parent sees only invoices for linked children (via Parent model)
  "Yes(own)" = Student can pay their own invoices through gateway
  "Yes(child)" = Parent can pay invoices for their linked children through gateway
```

### Decorator Definitions (from accounts/decorators.py)

| Decorator | Wraps | Effective Roles |
| ----------- | ------- | ----------------- |
| `@accountant_allowed` | `@require_2fa` + `@role_required('direction', 'admin', 'accountant')` | direction, admin, accountant (2FA required) |
| `@student_required` | `@role_required('student')` | student only |
| `@direction_only` | `@role_required('secretary', 'direction', 'admin')` | secretary, direction, admin |

### API Permission Classes (from accounts/permissions.py)

| Permission Class | Grants Access To |
| ----------------- | ----------------- |
| `IsAccountantOrDirectionUser` | accountant, direction, admin, is_staff, is_superuser |
| `IsStudentOrParent` | is_student, is_parent, is_staff, is_superuser |
| `IsAuthenticated` | Any authenticated user |

### Inline Ownership Checks (beyond decorators)

Several views perform additional inline authorization:

- **`PaymentGetwaysView.get_context_data`**: Checks invoice ownership via `user=request.user`, then falls back to parent-of-student check via `Parent.objects.filter(user=request.user)`.
- **`stripe_charge`**: Verifies `invoice.user == request.user` or `is_superuser`, then checks parent-student relationship via `Parent.objects.filter(user=request.user, student__student=invoice.user)`.
- **`paymentComplete`**: Same ownership check as `stripe_charge`.
- **`invoice_detail`**: Owner, parent-of-student, or superuser.
- **`InvoiceViewSet.get_queryset`**: Scopes queryset by role -- staff/accountant/direction/admin see all; parents see linked children's; students see only their own.

---

## Business Logic Workflows

### 1. Invoice Creation (Accountant/Direction/Admin with 2FA)

```text
Accountant navigates to /payments/create-invoice/ (GET)
    |
    v
Page shows active FeeStructures + existing invoices for user
    |
    v
Accountant selects student + fee structure, submits (POST)
    |
    ├── Validate: fee_structure_id and student_id present
    ├── Lookup: Student.objects.get(pk=student_id)
    ├── Lookup: FeeStructure.objects.get(pk=fee_structure_id, is_active=True)
    ├── Derive amount: fee_structure.get_total_fee()
    |     (server-side only -- no user-supplied amount accepted)
    |
    v
Invoice.objects.create(
    user = student.student,          # The User linked to Student
    student = student,               # The Student record
    fee_structure = fee_structure,
    amount = get_total_fee(),
    total = get_total_fee(),
    invoice_code = uuid4()
)
    |
    ├── Store invoice_code in session["invoice_session"]
    └── Redirect to payment_gateways
```

### 2. Stripe Payment Flow

```text
Student/Parent visits PaymentGetwaysView (GET)
    |
    v
Session contains invoice_code -> look up Invoice
    |
    ├── Validate ownership: invoice.user == request.user
    |   OR Parent.objects.filter(user=request.user, student__student=invoice.user)
    ├── Display amount, gateway options, Stripe publishable key
    |
    v
Student clicks "Pay with Stripe" -> POST to stripe_charge
    |
    ├── Validate: invoice_code in session
    ├── Validate: invoice.user == request.user (or parent, or superuser)
    ├── Validate: invoice.payment_complete is False (prevent double-pay)
    ├── Validate: stripeToken present in POST
    ├── Calculate: amount = int(invoice.amount * 100) (convert to cents)
    ├── Validate: amount > 0
    |
    v
stripe.Charge.create(
    amount = amount_cents,
    currency = "eur",
    description = "Payment for invoice {invoice_code}",
    source = stripeToken,
    idempotency_key = "charge-{invoice_code}"
)
    |
    ├── charge.status == "succeeded"
    |       |
    |       v
    |   ATOMIC TRANSACTION:
    |       invoice.payment_complete = True
    |       invoice.save()
    |       Payment.objects.create(
    |           invoice = invoice,
    |           amount = invoice.amount,
    |           payment_gateway = 'stripe',
    |           transaction_id = charge.id,
    |           status = 'completed'
    |       )
    |       del session["invoice_session"]
    |       -> Redirect to /payments/completed/
    |
    └── charge failed or CardError/StripeError
            -> messages.error() + redirect to gateway page
```

### 3. Payment Verification Workflow

```text
PaymentVerification created with status='pending'
    |
    ├── verify(user, notes):
    |       ATOMIC TRANSACTION:
    |           verification_status = 'verified'
    |           verified_by = user
    |           verification_notes = notes
    |           verified_at = timezone.now()
    |           save()
    |           payment.status = 'completed'
    |           payment.save()
    |
    └── reject(user, notes):
            ATOMIC TRANSACTION:
                verification_status = 'rejected'
                verified_by = user
                verification_notes = notes
                verified_at = timezone.now()
                save()
                payment.status = 'failed'
                payment.save()
```

### 4. Installment Payment Plan Flow

```text
Invoice (amount=3000.00)
    |
    v
PaymentPlan created:
    total_amount = 3000.00
    number_of_installments = 3
    installment_amount = 1000.00
    |
    v
Installments generated:
    Installment #1: amount=1000.00, due_date=2025-02-01, paid=False
    Installment #2: amount=1000.00, due_date=2025-03-01, paid=False
    Installment #3: amount=1000.00, due_date=2025-04-01, paid=False
    |
    v
Payment recorded for installment:
    Payment.objects.create(
        invoice = invoice,
        installment = installment_1,   # links to specific installment
        amount = 1000.00,
        payment_gateway = 'stripe',
        transaction_id = '...',
        status = 'completed'
    )
    installment_1.paid = True
    installment_1.paid_date = today
    |
    v
PaymentPlan helper queries:
    get_paid_installments()      = 1
    get_remaining_installments() = 2
    get_remaining_amount()       = 2000.00
```

### 5. Fee Structure Total Calculation

```text
FeeStructure.get_total_fee() =
    tuition_fee         (e.g., 5000.00)
  + registration_fee    (e.g.,  100.00)
  + library_fee         (e.g.,   50.00)
  + lab_fee             (e.g.,  200.00)
  + sports_fee          (e.g.,   30.00)
  + other_fees          (e.g.,   20.00)
  = total               (e.g., 5400.00)
```

### 6. Parent Payment Flow (via accounts/views_parent.py)

```text
Parent navigates to parent_child_invoices
    |
    ├── get_active_child(request) -> (parent, student)
    ├── Invoice.objects.filter(student=student) with paid/unpaid filters
    |
    v
Parent clicks "Pay" on an unpaid invoice
    |
    v
parent_make_payment(request, invoice_id)
    |
    ├── Validate: student == active child
    ├── Lookup: Invoice.objects.get(pk=invoice_id, student=student)
    ├── Check: invoice.payment_complete == False
    ├── Store: session['invoice_session'] = invoice.invoice_code
    |
    v
Redirect -> frontend:payments:payment_gateways
    |
    v
(Standard Stripe/PayPal flow with parent ownership check)
```

### Validation Rules

- All monetary fields use `MinValueValidator(Decimal('0.00'))` -- no negative amounts
- `FeeStructure` unique per `(program, level, academic_year)`
- `Payment.transaction_id` is globally unique
- `Installment` unique per `(payment_plan, installment_number)`
- `Receipt.receipt_number` is globally unique
- `PaymentPlanForm` validates: `installment_amount * number_of_installments == total_amount` (within 0.01 tolerance)

---

## Dependencies (Both Directions)

### Outbound: This App Depends On

| Dependency | What Is Used | Where |
| ----------- | ------------- | ------- |
| `accounts.models.Student` | Invoice.student FK; student lookup in `create_invoice` | models.py, views_frontend.py |
| `accounts.models.Parent` | Ownership checks (parent-pays-for-child) | views_frontend.py (inline imports) |
| `accounts.models.User` (AUTH_USER_MODEL) | Invoice.user FK, PaymentVerification.verified_by FK | models.py |
| `accounts.decorators` | `direction_only`, `accountant_allowed`, `student_required` | views_frontend.py |
| `accounts.permissions` | `IsDirectionUser`, `IsAccountantOrDirectionUser`, `IsStudentOrParent` | views_api.py |
| `course.models.Program` | FeeStructure.program FK (string reference `'course.Program'`) | models.py |
| `core.models.Semester` | Invoice.semester FK (string reference `'core.Semester'`) | models.py |
| `django.conf.settings` | `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `AUTH_USER_MODEL`, `LEVEL_CHOICES` | views_frontend.py, models.py |
| `stripe` (third-party) | `stripe.Charge.create`, `stripe.error.CardError`, `stripe.error.StripeError` | views_frontend.py |
| `gopay` (third-party, optional) | `gopay.payments`, `gopay.enums` (conditionally imported) | views_frontend.py |
| `celery` | `@shared_task` decorator | tasks.py |

### Inbound: Apps That Depend On This App

| Consumer App | What They Import | Purpose |
| ------------- | ----------------- | --------- |
| `accounts.views_parent` | `Invoice`, `Payment` | Parent dashboard: pending invoices for child, child invoice listing, child payment history, parent-make-payment flow |
| `accounts.views_frontend` | `PaymentRecord` (stale reference) | Accountant dashboard widget |
| `accounts.views` | `PaymentRecord` (stale reference) | Dashboard context |
| `core.views` | `Invoice` | Direction dashboard: total/paid invoice counts |
| `core.views_frontend` | `Invoice`, `Payment`, `FeeStructure` | Direction dashboard: payment collection rate; Accountant dashboard: invoice stats, overdue counts, financial totals (billed/collected/outstanding), recent payments |
| `anomaly_detection.detectors.payment` | `Payment`, `Invoice` (via `payments.models`) | 4 detectors: `PaymentAmountMismatchDetector`, `DoublePaymentDetector`, `PaymentStatusReversalDetector`, `InvoiceFeeStructureMismatchDetector` |
| `core.management.commands.generate_beta_data` | `Payment`, `PaymentPlan`, `Invoice` | Demo/beta data generation |
| `accounts.management.commands.create_demo_data` | `Invoice` | Demo data seeding |
| Various test modules | All models, forms, tasks, serializers | Unit and integration tests |

### Dependency Diagram

```text
                  +────────────+
                  |   stripe   |  (third-party)
                  +─────+──────+
                        ^
                        |
                  +─────+──────+
  +──────────+    |  PAYMENTS  |    +───────────+
  | accounts |<───|  app       |───>|  course   |
  | .models  |    |            |    | .models   |
  | .decos   |    +─────+──────+    | (Program) |
  | .perms   |          |          +───────────+
  +──────+───+          |
         ^              |          +───────────+
         |              +─────────>|   core    |
         |                         | .models   |
         |                         | (Semester) |
         |                         +───────────+
         |
         |    +──────────────────────+
         |    | anomaly_detection    |
         |    | .detectors.payment   |
         |    | (reads Payment,      |
         |    |  Invoice models)     |
         |    +──────────────────────+
         |              ^
         |              |
         |    +---------+──────────+
         |    | payments.models    |
         |    | (consumed by       |
         |    |  anomaly_detection)|
         |    +────────────────────+
         |
  +──────+───────────────+    +──────────────────+
  | accounts.views_parent|    | core.views_      |
  | (reads Invoice,      |    | frontend         |
  |  Payment)            |    | (reads Invoice,  |
  +──────────────────────+    |  Payment,        |
                              |  FeeStructure)   |
                              +──────────────────+
```

---

## Data Flow Diagrams

### 1. End-to-End Payment Data Flow

```text
  +-----------+      +────────────+      +────────────+      +──────────+
  | Admin/    |      | FeeStructure|      |            |      | Student/ |
  | Accountant|─────>| (config)   |─────>|  Invoice   |<─────| Parent   |
  | (CRUD)    |      |            |      | (billing)  |      | (views)  |
  +-----------+      +────────────+      +──────+─────+      +──────────+
                                                |
                          +─────────────────────+──────────────────+
                          |                     |                  |
                          v                     v                  v
                   +────────────+        +────────────+    +────────────+
                   | PaymentPlan|        |  Payment   |    |  Session   |
                   | (install-  |        |  Gateway   |    |  Storage   |
                   |  ments)    |        | (Stripe/   |    | (invoice_  |
                   +──────+─────+        |  PayPal/   |    |  session)  |
                          |              |  etc.)     |    +────────────+
                          v              +──────+─────+
                   +────────────+               |
                   | Installment|               v
                   | records    |        +────────────+
                   +────────────+        |  Payment   |
                                         |  record    |
                                         +──────+─────+
                                                |
                                      +─────────+──────────+
                                      |                    |
                                      v                    v
                               +────────────+       +────────────+
                               |  Payment   |       |  Receipt   |
                               | Verificat. |       | (PDF gen)  |
                               +────────────+       +────────────+
```

### 2. Session-Based Invoice Flow

The payment gateway views use Django sessions (`session["invoice_session"]`) to track
which invoice is being paid. This bridges the create-invoice and pay-invoice flows:

```text
  create_invoice (accountant)           parent_make_payment (parent)
       |                                        |
       v                                        v
  session["invoice_session"]            session["invoice_session"]
  = invoice.invoice_code                = invoice.invoice_code
       |                                        |
       +───────────────────+────────────────────+
                           |
                           v
                  PaymentGetwaysView
                  (reads session, validates ownership,
                   renders gateway selection page)
                           |
                           v
                  stripe_charge / paymentComplete
                  (reads session, processes payment)
                           |
                           v
                  On success: del session["invoice_session"]
                  Redirect -> payment_succeed
```

### 3. Anomaly Detection Data Flow

The `anomaly_detection` app monitors payment data for suspicious patterns:

```text
  Payment/Invoice changes
       |
       v
  +───────────────────────────────────────────+
  | anomaly_detection.detectors.payment       |
  |─────────────────────────────────────────--|
  | PaymentAmountMismatchDetector             |  payment.amount != invoice.amount
  | DoublePaymentDetector                     |  >1 completed payment per invoice
  | PaymentStatusReversalDetector             |  invalid status transitions
  |   Valid: pending->processing->completed   |
  |          completed->refunded              |
  |          failed->pending/processing       |
  | InvoiceFeeStructureMismatchDetector       |  invoice.amount != fee_structure total
  +───────────────────────────────────────────+
       |
       v
  AnomalyAlert records (in anomaly_detection app)
```

### 4. Dashboard Data Flows (Read Paths)

```text
  Direction Dashboard                    Accountant Dashboard
  (core/views_frontend.py)              (core/views_frontend.py)
           |                                      |
           v                                      v
  Invoice.objects.filter(               Invoice.objects.all()
    tenant=..., session=...             .aggregate(
  ).count()                                Sum('amount'),
  Invoice.objects.filter(                  Sum('amount', filter=Q(payment_complete=True))
    ..., status='paid'                  )
  ).count()                             Payment.objects.select_related('invoice', 'invoice__user')
           |                              .order_by('-payment_date')[:10]
           v                             FeeStructure.objects.filter(is_active=True).count()
  payment_collection_rate =                       |
  paid / total * 100                              v
                                        total_billed, total_collected, total_outstanding,
                                        overdue_invoices, collection_rate, recent_payments,
                                        active_fee_structures
```

### 5. Parent Dashboard Data Flow

```text
  Parent Dashboard (accounts/views_parent.py)
           |
           v
  get_active_child(request) -> (parent, student)
           |
           +── pending_invoices:
           |     Invoice.objects.filter(student=student, payment_complete=False)
           |       .order_by('-created_at')[:5]
           |
           +── child invoices page:
           |     Invoice.objects.filter(student=student)
           |       .select_related('fee_structure', 'semester')
           |       with paid/unpaid filter
           |
           +── child payment history:
                 Payment.objects.filter(invoice__student=student, status='completed')
                   .select_related('invoice')
```

---

## Serializer Computed Fields

| Serializer | Computed Field | Source |
| ------------ | --------------- | -------- |
| `FeeStructureSerializer` | `program_name` | `program.title` (read-only) |
| `FeeStructureSerializer` | `total_fee` | `get_total_fee()` (SerializerMethodField) |
| `InvoiceSerializer` | `student_name` | `student.user.get_full_name` (read-only, nullable) |
| `InvoiceSerializer` | `is_overdue` | `is_overdue()` (SerializerMethodField) |
| `PaymentPlanSerializer` | `remaining_installments` | `get_remaining_installments()` (SerializerMethodField) |
| `PaymentPlanSerializer` | `remaining_amount` | `get_remaining_amount()` (SerializerMethodField) |
| `InstallmentSerializer` | `is_overdue` | `is_overdue()` (SerializerMethodField) |
| `PaymentSerializer` | `invoice_code` | `invoice.invoice_code` (read-only) |
| `PaymentSerializer` | `status_display` | `get_status_display()` (read-only) |
| `PaymentVerificationSerializer` | `payment_transaction_id` | `payment.transaction_id` (read-only) |
| `PaymentVerificationSerializer` | `verified_by_name` | `verified_by.get_full_name` (read-only, nullable) |
| `ReceiptSerializer` | `payment_amount` | `payment.amount` (read-only) |

---

## Forms

| Form | Model | Fields | Custom Validation |
| ------ | ------- | -------- | ------------------- |
| `InvoiceForm` | `Invoice` | `student`, `fee_structure`, `amount`, `due_date`, `semester`, `description` | Standard ModelForm |
| `FeeStructureForm` | `FeeStructure` | `program`, `level`, `academic_year`, 6 fee fields, `is_active` | Standard ModelForm |
| `PaymentForm` | `Payment` | `invoice`, `amount`, `payment_gateway`, `transaction_id` | Standard ModelForm (not used in any view) |
| `PaymentPlanForm` | `PaymentPlan` | `invoice`, `total_amount`, `number_of_installments`, `installment_amount` | `clean()`: validates `total_amount == installment_amount * number_of_installments` (0.01 tolerance) -- not used in any view |

---

## Celery Tasks

Three async tasks are defined in `payments/tasks.py` but are currently stubs (TODO):

| Task | Intended Schedule | Purpose |
| ------ | ------------------ | --------- |
| `send_payment_reminders` | 1st of month, 9 AM | Email reminders for unpaid invoices |
| `process_failed_payments` | Daily, 2 AM | Retry failed payment transactions |
| `generate_monthly_invoices` | 1st of month | Auto-generate recurring invoices |

---

## Templates

All templates in `templates/payments/`:

| Template | Used By | Purpose |
| ---------- | --------- | --------- |
| `payment_gateways.html` | `PaymentGetwaysView` | Gateway selection page (Stripe, PayPal, etc.) |
| `paypal.html` | `payment_paypal` | PayPal payment form |
| `stripe.html` | `payment_stripe` | Stripe payment form |
| `coinbase.html` | `payment_coinbase` | Coinbase payment form |
| `paylike.html` | `payment_paylike` | Paylike payment form |
| `payment_succeed.html` | `payment_succeed` | Payment success confirmation |
| `student_invoices.html` | `student_invoices` | Student's invoice list with paid/unpaid filter |
| `payment_history.html` | `student_payment_history` | Student's completed payment history |
| `fee_structure_list.html` | `fee_structure_list` | Fee structure listing (accountant/direction/admin) |
| `fee_structure_form.html` | `fee_structure_create`, `fee_structure_edit` | Fee structure create/edit form |
| `fee_structure_confirm_delete.html` | `fee_structure_delete` | Fee structure deletion confirmation |

---

## URL Routing Structure

```text
/payments/                                  -> PaymentGetwaysView (gateway selection)
/payments/paypal/                           -> payment_paypal
/payments/stripe/                           -> payment_stripe
/payments/coinbase/                         -> payment_coinbase
/payments/paylike/                          -> payment_paylike
/payments/stripe-charge/                    -> stripe_charge (POST)
/payments/gopay-charge/                     -> gopay_charge (POST)
/payments/payment-succeed/                  -> payment_succeed
/payments/complete/                         -> paymentComplete (AJAX/POST)
/payments/completed/                        -> payment_succeed (alias)
/payments/create-invoice/                   -> create_invoice
/payments/invoice-detail/<int:id>/          -> invoice_detail
/payments/fee-structures/                   -> fee_structure_list
/payments/fee-structures/create/            -> fee_structure_create
/payments/fee-structures/<int:pk>/edit/     -> fee_structure_edit
/payments/fee-structures/<int:pk>/delete/   -> fee_structure_delete
/payments/my-invoices/                      -> student_invoices
/payments/my-payments/                      -> student_payment_history

API (via DefaultRouter):
/api/.../fee-structures/     -> FeeStructureViewSet (CRUD)
/api/.../invoices/           -> InvoiceViewSet (CRUD, scoped)
/api/.../payment-plans/      -> PaymentPlanViewSet (CRUD)
/api/.../installments/       -> InstallmentViewSet (CRUD)
/api/.../payments/           -> PaymentViewSet (CRUD)
/api/.../verifications/      -> PaymentVerificationViewSet (CRUD)
/api/.../receipts/           -> ReceiptViewSet (read-only)
```

---

## Security Considerations

1. **2FA Enforcement**: All accountant-accessible frontend views (`@accountant_allowed`) enforce two-factor authentication via `@require_2fa` before granting access. This covers invoice creation, fee structure CRUD, and all financial management views.

2. **Ownership Validation**: Payment gateway views validate that the requesting user either owns the invoice (`invoice.user == request.user`) or is a parent of the student linked to the invoice (via `Parent` model lookup). Superusers bypass this check.

3. **Idempotency**: Stripe charges use `idempotency_key=f"charge-{invoice.invoice_code}"` to prevent duplicate charges on network retries.

4. **Double-Payment Prevention**: `stripe_charge` checks `invoice.payment_complete` before processing and uses `transaction.atomic()` when marking the invoice as paid and creating the Payment record.

5. **Server-Side Amount Derivation**: `create_invoice` derives the payment amount from `fee_structure.get_total_fee()` -- it does not accept a user-supplied amount from POST data.

6. **Atomic Verification**: `PaymentVerification.verify()` and `reject()` both use `transaction.atomic()` to update verification status and payment status together, preventing inconsistent states.

7. **Scoped API Querysets**: `InvoiceViewSet.get_queryset()` scopes results by role -- students see only their own, parents see linked children's, staff/accountant/direction/admin see all.

---

## Known Issues / Technical Notes

- `gopay` is conditionally imported with a `GOPAY_AVAILABLE` flag; `gopay_charge` uses hardcoded placeholder credentials and a fixed 150 CZK amount.
- `PaymentGetwaysView` is a CBV using `@method_decorator(login_required)` while all other views are FBVs.
- `_get_invoice_context()` builds context from session but does NOT validate ownership -- only used by placeholder gateway pages (paypal, stripe, coinbase, paylike, payment_succeed).
- `paymentComplete` reads `request.body` on line 287 regardless of whether the request is AJAX/POST, which can cause errors on GET.
- `invoice_detail` URL uses `<int:id>` but the view function signature is `def invoice_detail(request, slug)` -- parameter name mismatch.
- `admin.py` contains only the default import with no model registrations.
- All 3 Celery tasks are stubs that return None.
- `PaymentForm` and `PaymentPlanForm` are defined in forms.py but not used in any view.
- `accounts.views_frontend` and `accounts.views` reference `PaymentRecord` which does not exist in payments.models (stale reference).

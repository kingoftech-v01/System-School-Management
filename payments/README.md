# Payments App

Payment processing with Stripe integration, GoPay support, fee structure management, and invoice lifecycle.

## Description

The payments app handles the full financial lifecycle of the school management system: fee structure definition per program/level/year, invoice generation for students, payment processing through multiple gateways (Stripe, GoPay), installment payment plans, payment verification workflows, and receipt generation. It provides both Django template-based frontend views and a full DRF REST API.

## Main Features

- **Fee Structure Management**: CRUD for fee structures by program, level, and academic year (direction/accountant only)
- **Invoice Lifecycle**: Create invoices from fee structures, track payment status, overdue detection
- **Payment Gateways**: Selection page for Stripe, PayPal, Coinbase, Paylike (PayPal/Coinbase/Paylike are placeholders)
- **Stripe Charge**: Process payments via Stripe API with ownership validation and double-payment prevention
- **GoPay Integration**: Conditional GoPay payment processing (placeholder credentials)
- **Payment Plans**: Installment-based payment plans with per-installment tracking
- **Payment Verification**: Multi-step approval workflow (pending -> verified/rejected) with atomic operations
- **Receipts**: Auto-generated PDF receipt model with email tracking
- **Student Views**: Personal invoice list and payment history views
- **Celery Tasks**: Stub tasks for payment reminders, failed payment retry, and monthly invoice generation
- **REST API**: Full CRUD API for all models via DRF ViewSets with role-based permissions

## User Roles

| Role | Frontend Access | API Access |
|------|----------------|------------|
| student | View own invoices, payment history, pay invoices via gateway | Read own invoices (IsStudentOrParent) |
| professor | No payment-specific access | No access |
| direction | Fee structure CRUD, create invoices, all financial views | Full CRUD on all resources (IsAccountantOrDirectionUser) |
| parent | View/pay child's invoices (ownership check via Parent model) | Read child's invoices (IsStudentOrParent) |
| admin | Full access to all views (superuser bypass) | Full CRUD on all resources |
| prefet | No payment-specific access | No access |
| accountant | Fee structure CRUD, create invoices, all financial views (via @accountant_allowed) | Full CRUD on all resources (IsAccountantOrDirectionUser) |
| secretary | No payment-specific frontend access (not in @accountant_allowed) | No access (not in IsAccountantOrDirectionUser) |
| librarian | No payment-specific access | No access |
| registrar | No payment-specific access | No access |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| FeeStructure | fee_structure_create (accountant_allowed) | fee_structure_list (accountant_allowed) | fee_structure_edit (accountant_allowed) | fee_structure_delete (accountant_allowed) |
| Invoice | create_invoice (accountant_allowed) | student_invoices (student), invoice_detail (owner/parent/admin) | paymentComplete (mark paid) | No |
| PaymentPlan | No frontend views | No frontend views | No frontend views | No frontend views |
| Installment | No frontend views | No frontend views | No frontend views | No frontend views |
| Payment | Via stripe_charge/gopay_charge | student_payment_history (student) | No | No |
| PaymentVerification | No frontend views | No frontend views | No frontend views | No frontend views |
| Receipt | No frontend views | No frontend views | No frontend views | No frontend views |

## API Endpoints

All API endpoints are under `/api/v1/payments/` and require authentication.

| Endpoint | ViewSet | Methods | Permission | Filters |
|----------|---------|---------|------------|---------|
| `fee-structures/` | FeeStructureViewSet | list, create, retrieve, update, destroy | IsAccountantOrDirectionUser | program, level, academic_year, is_active + search + ordering |
| `invoices/` | InvoiceViewSet | list, create, retrieve, update, destroy | IsStudentOrParent \| IsAccountantOrDirectionUser | student, payment_complete, semester + search + ordering |
| `payment-plans/` | PaymentPlanViewSet | list, create, retrieve, update, destroy | IsAccountantOrDirectionUser | -- |
| `installments/` | InstallmentViewSet | list, create, retrieve, update, destroy | IsAccountantOrDirectionUser | payment_plan, paid + ordering |
| `payments/` | PaymentViewSet | list, create, retrieve, update, destroy | IsAccountantOrDirectionUser | invoice, status, payment_gateway + ordering |
| `verifications/` | PaymentVerificationViewSet | list, create, retrieve, update, destroy | IsAccountantOrDirectionUser | verification_status + ordering |
| `receipts/` | ReceiptViewSet | list, retrieve (read-only) | IsAuthenticated | ordering |

### API Queryset Scoping (InvoiceViewSet)

- **staff/superuser**: All invoices
- **accountant/direction/admin roles**: All invoices
- **parent**: Invoices for their children (via Parent model lookup)
- **student/other**: Only own invoices (`user=request.user`)

## File Structure

```text
payments/
  __init__.py
  apps.py               -- AppConfig (name="payments")
  models.py             -- 7 models: FeeStructure, Invoice, PaymentPlan, Installment, Payment, PaymentVerification, Receipt
  views_frontend.py     -- Django template views (gateway pages, fee structure CRUD, student views)
  views_api.py          -- DRF ViewSets for all models
  urls.py               -- Frontend + API URL routing with api_router (DefaultRouter)
  forms.py              -- InvoiceForm, FeeStructureForm, PaymentForm, PaymentPlanForm
  serializers.py        -- DRF serializers for all 7 models with computed fields
  tasks.py              -- 3 Celery task stubs (reminders, retry, generation)
  admin.py              -- Empty (no models registered in Django admin)
  README.md
  TODO.md
  ARCHITECTURE.md
  migrations/
    0001_initial.py
    0002_alter_invoice_amount_alter_invoice_total.py
  tests/
    __init__.py
    test_models.py           -- Model unit tests (FeeStructure, Invoice, PaymentPlan, Installment, Payment, PaymentVerification, Receipt)
    test_serializers.py      -- Serializer tests for all 7 serializers
    test_forms.py            -- Form validation tests (InvoiceForm, FeeStructureForm, PaymentPlanForm)
    test_views_frontend.py   -- Frontend view tests (gateways, stripe, gopay, invoices, fee structure CRUD, student views)
    test_views_api.py        -- API ViewSet tests (fee structures, invoices, payments, receipts)
    test_tasks.py            -- Celery task stub tests
    test_admin.py            -- Admin module import test
```

## Configuration

### Required Settings

| Setting | Purpose | Location |
|---------|---------|----------|
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key for frontend | `settings.base` |
| `STRIPE_SECRET_KEY` | Stripe secret key for charges | `settings.base` |
| `LEVEL_CHOICES` | Academic level options for FeeStructure | `settings.base` |

### Required Packages

| Package | Purpose | Notes |
|---------|---------|-------|
| `stripe` | Payment processing | Required import in views_frontend.py |
| `gopay` | GoPay gateway | Optional, conditional import with `GOPAY_AVAILABLE` flag |
| `djangorestframework` | REST API | ViewSets, serializers, permissions |
| `django-filter` | API filtering | DjangoFilterBackend on ViewSets |
| `celery` | Async tasks | Task stubs for reminders, retry, generation |

### Decorators Used (from accounts.decorators)

| Decorator | Allowed Roles | 2FA Required | Used On |
|-----------|---------------|--------------|---------|
| `@login_required` | All authenticated users | No | All views |
| `@accountant_allowed` | direction, admin, accountant | Yes | Fee structure CRUD, create_invoice |
| `@student_required` | student | No | student_invoices, student_payment_history |

### DRF Permission Classes (from accounts.permissions)

| Permission | Allowed Roles |
|------------|---------------|
| `IsAccountantOrDirectionUser` | accountant, direction, admin + staff/superuser |
| `IsStudentOrParent` | student, parent + staff/superuser |
| `IsAuthenticated` | All authenticated users |

## Models

- `FeeStructure` -- program FK (course.Program), level, academic_year, tuition_fee, registration_fee, library_fee, lab_fee, sports_fee, other_fees, is_active, created_at, updated_at; unique_together=[program, level, academic_year]; method: get_total_fee()
- `Invoice` -- user FK (AUTH_USER_MODEL), student FK (accounts.Student, nullable), fee_structure FK (FeeStructure, nullable), total, amount, payment_complete, invoice_code, due_date, semester FK (core.Semester, nullable), description, created_at, updated_at; method: is_overdue()
- `PaymentPlan` -- invoice OneToOne (Invoice), total_amount, number_of_installments, installment_amount, created_at; methods: get_paid_installments(), get_remaining_installments(), get_remaining_amount()
- `Installment` -- payment_plan FK (PaymentPlan), installment_number, amount, due_date, paid, paid_date; unique_together=[payment_plan, installment_number]; method: is_overdue()
- `Payment` -- invoice FK (Invoice), installment FK (Installment, nullable), amount, payment_gateway (stripe/braintree/bank_transfer/cash), transaction_id (unique), status (pending/processing/completed/failed/refunded), payment_date, updated_at
- `PaymentVerification` -- payment OneToOne (Payment), verified_by FK (AUTH_USER_MODEL, nullable), verification_status (pending/verified/rejected), verification_notes, verified_at, created_at; methods: verify(user, notes), reject(user, notes) -- both atomic
- `Receipt` -- payment OneToOne (Payment), receipt_number (unique), pdf_file (FileField), generated_at, sent_to_email

## Known Issues

- **URL/View mismatch**: `invoice_detail` URL uses `<int:id>` but view function parameter is `slug` -- this will cause a TypeError at runtime
- GoPay credentials are placeholder strings in code (should use env vars)
- Stripe currency is hardcoded to "eur" in `stripe_charge`
- PayPal, Coinbase, Paylike views are placeholder pages (render template only)
- `paymentComplete` reads `request.body` outside the AJAX/POST conditional block -- crashes on GET requests
- `admin.py` is empty -- no models are registered in Django admin
- All 3 Celery tasks are unimplemented stubs (`pass` only)

## Dependencies

- `stripe` (payment processing)
- `gopay` (optional, conditional import)
- `accounts` (User, Student, Parent, decorators, permissions)
- `course` (Program model via FeeStructure FK)
- `core` (Semester model via Invoice FK)

## URL Namespace

- Frontend: `payments:frontend:<view_name>` (from main urls.py `payments` -> internal `frontend`)
- API: `api:v1:payments:<resource-name>` (from main urls.py api_v1 -> `payments`)

# Payments - TODO

## Backend

- [x] Add `@login_required` decorator to all payment views -- all views now have `@login_required`
- [x] Replace hardcoded amount=500 in `stripe_charge` with dynamic amount from invoice session -- now uses `int(invoice.amount * 100)`
- [x] Replace hardcoded total=26 in `create_invoice` with actual calculated total -- now derives amount from `fee_structure.get_total_fee()`
- [x] Replace deprecated `request.is_ajax()` in `paymentComplete` with `request.headers.get('X-Requested-With') == 'XMLHttpRequest'`
- [x] Add fee structure list view (direction only) using existing FeeStructure model -- `fee_structure_list` with search/filter/pagination
- [x] Add fee structure create/edit/delete views (direction only) -- `fee_structure_create`, `fee_structure_edit`, `fee_structure_delete`
- [x] Add student invoice list view showing personal invoices and payment status -- `student_invoices` with status filter
- [x] Add payment history list view for students -- `student_payment_history` with pagination
- [ ] Register all 7 models in `admin.py` -- currently empty (`from django.contrib import admin` only)
- [ ] Add `AppConfig.default_auto_field` in `apps.py` to suppress Django 3.2+ warnings
- [ ] Add parent invoice list view so parents can see invoices for their children without going through the gateway page

## Frontend

- [x] Add invoice list page for students to see their payment history -- `student_invoices` template
- [x] Add fee structure display page showing current fees by type -- `fee_structure_list` template
- [x] Add payment status indicator on invoice detail (paid/unpaid badge) -- invoice detail shows `payment_complete`
- [ ] Remove or implement PayPal, Coinbase, Paylike placeholder pages -- currently render empty templates
- [ ] Add payment plan management UI (create plans, view installments, mark paid) -- models exist but no frontend views
- [ ] Add payment verification UI for accountants/direction to verify/reject payments
- [ ] Add receipt download/view page linked to completed payments

## Sidebar

- [ ] Expand Payments from single link to expandable menu with sub-links: "Payment Gateway", "My Invoices" (students), "Fee Structure" (direction/accountant), "Payment History" (students)

## Security

- [x] **CRITICAL**: Most views lack `@login_required` -- all views now have `@login_required` or `@method_decorator(login_required)`
- [x] **CRITICAL**: Invoice IDOR: `invoice_detail` accessible by any user without ownership check -- now checks `invoice.user == request.user` with parent fallback
- [x] **CRITICAL**: `paymentComplete` marks ANY invoice as paid without verifying ownership -- now checks `invoice.user == request.user` with parent fallback
- [x] **CRITICAL**: `stripe_charge` hardcodes amount=500 and currency="eur" -- amount is now dynamic from invoice; currency still hardcoded (see below)
- [x] `create_invoice` hardcodes total=26 -- now uses `fee_structure.get_total_fee()`
- [ ] Stripe currency is hardcoded to "eur" in `stripe_charge` (views_frontend.py:164) -- should be configurable per school/tenant
- [ ] GoPay credentials are placeholder strings in code (views_frontend.py:207-209) -- move to environment variables
- [ ] GoPay amount is hardcoded to 150 CZK (views_frontend.py:245) -- should use invoice amount
- [ ] GoPay callback URLs are hardcoded placeholder strings (views_frontend.py:256-257) -- use `reverse()` or settings
- [ ] `paymentComplete` (views_frontend.py:287) reads `request.body` outside the AJAX/POST conditional -- crashes on GET requests with empty body
- [ ] `paymentComplete` (views_frontend.py:285-286) saves `payment_complete=True` but does not create a `Payment` record -- inconsistent with `stripe_charge` which creates both
- [ ] Receipt ViewSet (views_api.py:84) uses `IsAuthenticated` only -- any authenticated user can list all receipts, no ownership scoping
- [ ] PaymentForm in forms.py is defined but never used in any view

## API

- [ ] Add queryset scoping to `PaymentViewSet` -- currently returns all payments regardless of user role
- [ ] Add queryset scoping to `PaymentPlanViewSet` -- currently returns all plans regardless of user role
- [ ] Add queryset scoping to `InstallmentViewSet` -- currently returns all installments regardless of user role
- [ ] Add queryset scoping to `PaymentVerificationViewSet` -- currently returns all verifications regardless of user role
- [ ] Add queryset scoping to `ReceiptViewSet` -- currently returns all receipts to any authenticated user
- [ ] Add custom actions to `InvoiceViewSet` for marking invoices paid / generating payment links
- [ ] Add custom action to `PaymentVerificationViewSet` for verify/reject workflows
- [ ] Add `SearchFilter` to ViewSets that currently lack it (PaymentPlanViewSet, PaymentVerificationViewSet)

## Testing

- [ ] Add test for `invoice_detail` URL/view parameter mismatch -- URL uses `<int:id>` but view expects `slug`
- [ ] Add integration test for full Stripe payment flow (mock `stripe.Charge.create`)
- [ ] Add test for parent accessing child's invoice via `invoice_detail`
- [ ] Add test for parent accessing child's invoice via `PaymentGetwaysView`
- [ ] Add test for `paymentComplete` GET request crash (reads `request.body` unconditionally)
- [ ] Add test for `paymentComplete` POST with valid invoice session and ownership
- [ ] Add test for duplicate payment prevention in `stripe_charge`
- [ ] Add negative amount validation tests for all models with `MinValueValidator`
- [ ] Add test for `PaymentPlanForm.clean()` mismatch validation (existing test exists, extend edge cases)

## URL Issues

- [ ] **BUG**: `invoice_detail` URL pattern uses `<int:id>` but view function parameter is `slug` -- causes TypeError at runtime; fix URL to `<slug:slug>` or rename view parameter to `id`

## Celery Tasks

- [ ] `tasks.py:18` TODO: "Implement payment reminder logic" -- implement `send_payment_reminders` to email students with overdue invoices
- [ ] `tasks.py:28` TODO: "Implement failed payment retry logic" -- implement `process_failed_payments` to retry pending/failed payments
- [ ] `tasks.py:38` TODO: "Implement monthly invoice generation" -- implement `generate_monthly_invoices` using FeeStructure to auto-create invoices

## Admin Registration

- [ ] Register `FeeStructure` in admin with list_display, list_filter, search_fields
- [ ] Register `Invoice` in admin with list_display (user, amount, payment_complete, created_at), list_filter
- [ ] Register `PaymentPlan` in admin with inline `Installment` entries
- [ ] Register `Payment` in admin with list_display (transaction_id, amount, status, payment_date)
- [ ] Register `PaymentVerification` in admin with list_display and verification status filter
- [ ] Register `Receipt` in admin with list_display (receipt_number, payment, generated_at)

## Documentation

- [x] Create ARCHITECTURE.md documenting model relationships, view patterns, and data flows

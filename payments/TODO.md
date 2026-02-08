# Payments - TODO

## Backend

- [ ] Add `@login_required` decorator to all payment views -- currently most are unprotected
- [ ] Replace hardcoded amount=500 in `stripe_charge` with dynamic amount from invoice session
- [ ] Replace hardcoded total=26 in `create_invoice` with actual calculated total
- [ ] Replace deprecated `request.is_ajax()` in `paymentComplete` with `request.headers.get('X-Requested-With') == 'XMLHttpRequest'`
- [ ] Add fee structure list view (direction only) using existing FeeStructure model
- [ ] Add fee structure create/edit/delete views (direction only)
- [ ] Add student invoice list view showing personal invoices and payment status
- [ ] Add payment history list view for students

## Frontend

- [ ] Add invoice list page for students to see their payment history
- [ ] Add fee structure display page showing current fees by type
- [ ] Add payment status indicator on invoice detail (paid/unpaid badge)
- [ ] Remove or implement PayPal, Coinbase, Paylike placeholder pages

## Sidebar

- [ ] Expand Payments from single link to expandable menu with sub-links: "Payment Gateway", "My Invoices" (students), "Fee Structure" (direction)

## Security

- [ ] **CRITICAL**: Most views lack `@login_required` -- unprotected payment endpoints accessible to anonymous users
- [ ] **CRITICAL**: Invoice IDOR: `invoice_detail` (views_frontend.py:194) accessible by any user without ownership check -- add `invoice.user == request.user` verification
- [ ] **CRITICAL**: `paymentComplete` (views_frontend.py:158-166) marks ANY invoice as paid without verifying `invoice.user == request.user`
- [ ] **CRITICAL**: `stripe_charge` hardcodes amount=500 and currency="eur" (views_frontend.py:68) -- use dynamic amount from invoice
- [ ] `create_invoice` hardcodes total=26 (views_frontend.py:179) -- use calculated total from fee structure
- [ ] `paymentComplete` uses deprecated `request.is_ajax()` (views_frontend.py:158)
- [ ] GoPay credentials are placeholder strings in code -- move to environment variables
- [ ] Stripe SECRET_KEY loaded from settings but should use env vars only

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] `tasks.py:18` TODO: "Implement payment reminder logic" -- implement this Celery task
- [ ] `tasks.py:28` TODO: "Implement failed payment retry logic" -- implement this Celery task
- [ ] `tasks.py:38` TODO: "Implement monthly invoice generation" -- implement this Celery task

# Payments App

Payment processing with Stripe integration, GoPay support, and invoice management.

## Description

The payments app handles payment processing with multiple gateway options. It includes a payment gateway selection page, Stripe charge processing, GoPay integration, and invoice creation. The app has models for fee structures, invoices, payment plans, installments, payments, receipts, and verification, though many of these models do not yet have frontend views.

## Main Features

- **Payment Gateways**: Selection page for Stripe, PayPal, Coinbase, Paylike
- **Stripe Charge**: Process payments via Stripe API
- **GoPay Integration**: Conditional GoPay payment processing
- **Invoice Creation**: Create invoices with session storage
- **Payment Completion**: Callback handler for marking invoices as paid

## User Roles

| Role | Permissions |
|------|------------|
| all users | Access payment views (most views lack @login_required) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Invoice | Yes | Yes (detail) | Yes (mark complete) | No |
| FeeStructure | No views | No views | No views | No views |
| PaymentPlan | No views | No views | No views | No views |
| Payment | Via gateway | No list | No | No |
| Receipt | No views | No views | No views | No views |

## Known Issues

- **CRITICAL**: Most views lack `@login_required` -- unprotected payment endpoints accessible to anonymous users
- **CRITICAL**: Invoice IDOR -- `invoice_detail` accessible by any user without ownership check
- **CRITICAL**: `paymentComplete` marks ANY invoice as paid without verifying `invoice.user == request.user`
- **CRITICAL**: `stripe_charge` hardcodes amount=500 and currency="eur"
- `create_invoice` hardcodes total=26
- `paymentComplete` uses deprecated `request.is_ajax()`
- GoPay credentials are placeholder strings in code (should use env vars)
- Stripe SECRET_KEY should use env vars only
- PayPal, Coinbase, Paylike views are empty placeholders (render templates only)

## Models

- `FeeStructure` -- tenant FK, name, amount, description, academic_year, fee_type
- `Invoice` -- user FK, amount, total, invoice_code, payment_complete, created_at
- `PaymentPlan` -- student FK, invoice FK, plan_type, installment_count
- `Installment` -- payment_plan FK, amount, due_date, is_paid
- `Payment` -- invoice FK, amount, method, transaction_id, status
- `PaymentVerification` -- payment FK, verified_by FK, verification_date
- `Receipt` -- payment FK, receipt_number, generated_at

## Dependencies

- `stripe` (payment processing)
- `gopay` (optional, conditional import)

## URL Namespace

- Frontend: `frontend:payments:<view_name>`
- API: `api:v1:payments:<resource-name>`

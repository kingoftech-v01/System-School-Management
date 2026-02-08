# Admissions App

Student admission workflow management with application tracking, counseling, and payment verification.

## Description

The admissions app manages the complete student admission pipeline from application submission through counseling to final admission or rejection. It includes models for admission sessions, student applications, counseling comments, and admission payments.

**Status: All frontend views are currently placeholders returning "Coming soon in Phase 5" text responses.**

## Main Features (Planned)

- **Admission Sessions**: Create and manage admission periods with start/end dates
- **Applications**: Multi-step application with personal, guardian, and academic info
- **Document Upload**: Transcript and birth certificate upload with file validation
- **Status Tracking**: Pipeline stages (pending, under_review, counseling, payment_pending, admitted, rejected)
- **Counseling**: Counselor assignment and comment tracking with recommendations
- **Payment Verification**: Track application fees with multiple payment methods

## User Roles

| Role | Permissions |
|------|------------|
| admin/direction | Manage sessions, review applications, assign counselors |
| professor | May serve as counselor |
| student/public | Submit applications, check status |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| AdmissionSession | API only | Placeholder | API only | API only |
| AdmissionStudent | Placeholder | Placeholder | API only | API only |
| CounselingComment | Placeholder | N/A | N/A | N/A |
| AdmissionPayment | N/A | N/A | N/A | N/A |

## Models

- `AdmissionSession` -- admission period with start/end dates
- `AdmissionStudent` -- application with personal info, program, status, documents
- `CounselingComment` -- counselor feedback with recommendation
- `AdmissionPayment` -- application fee payment tracking

## Dependencies

- `course` (Program model for program selection)
- `accounts` (User model for counselor/reviewer assignment)

## URL Namespace

- Frontend: `frontend:admissions:<view_name>`
- API: `api:v1:admissions:<resource-name>`

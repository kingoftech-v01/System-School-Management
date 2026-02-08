# Enrollment App

Multi-step student registration with document management, review workflow, and statistics.

## Description

The enrollment app handles the complete student enrollment process through a 4-step public registration form, document upload and verification, direction-side review and approval workflow, CSV export, and enrollment statistics with charts. The registration flow collects student info, parent info, academic info, and additional details across four steps using session-based state management.

## Main Features

- **Multi-Step Registration**: 4-step public form (student info, parent info, academic info, additional info)
- **Document Upload**: Upload enrollment documents with verification by direction staff
- **Registration Complete**: Confirmation page with email notification via Celery task
- **Enrollment List**: Direction-side paginated list with comprehensive filtering (name, email, status, type, year, filiere, date range)
- **Enrollment Detail**: Full registration details with documents and status history timeline
- **Enrollment Review**: Approve/reject registrations with notes and status history tracking
- **Document Verification**: Verify uploaded documents with status tracking
- **CSV Export**: Export filtered enrollment data to CSV
- **Enrollment Statistics**: Analytics with breakdowns by status, type, filiere, level, gender, and monthly trends

## User Roles

| Role | Permissions |
|------|------------|
| direction | List, detail, review, verify documents, export, statistics |
| public (unauthenticated) | Register (4-step form), upload documents |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| RegistrationForm | Yes (4-step) | Yes (list + detail) | Yes (review) | No |
| EnrollmentDocument | Yes (upload) | Yes (via detail) | Yes (verify) | No |
| EnrollmentStatusHistory | Automatic | Yes (via detail) | N/A | N/A |

## Models

- `RegistrationForm` -- tenant FK, student_name, email, phone, date_of_birth, parent_name, filiere FK, academic_year, level, enrollment_type, status, reviewed_by FK, enrolled_user FK
- `EnrollmentDocument` -- registration FK, document_type, file, is_verified, verified_by FK
- `EnrollmentStatusHistory` -- registration FK, old_status, new_status, changed_by FK, notes

## Dependencies

- `accounts` (User model, role decorators)
- `core` (School for tenant)
- `filieres` (Filiere model for program selection)
- `django-ratelimit`, Celery (for email tasks)

## URL Namespace

- Frontend: `frontend:enrollment:<view_name>`
- API: `api:v1:enrollment:<resource-name>`

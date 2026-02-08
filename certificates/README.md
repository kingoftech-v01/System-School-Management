# Certificates App

PDF certificate generation with templates, digital verification, and batch issuance.

## Description

The certificates app manages the complete certificate lifecycle: template design, individual issuance, PDF download, public verification by certificate number, and batch generation for an entire course. Templates support custom backgrounds, signatures, orientation, and page size. Certificates include SHA-256 hash signatures and QR codes for verification.

## Main Features

- **Certificate Templates**: Full CRUD (create, list, detail, edit, delete) with file upload
- **Certificate Issuance**: Create individual certificates linked to student + course
- **Certificate Viewing**: Role-based list (students see own, staff see all) with filtering
- **Certificate Download**: PDF file download with permission checks
- **Certificate Revocation**: Revoke with reason and audit trail
- **Public Verification**: Verify certificate by number (no login required, rate-limited)
- **Batch Generation**: Create batch jobs for course-wide certificate generation with progress tracking
- **Dashboard**: Role-based dashboard (student: my certificates, staff: system statistics)

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full access: templates, issuance, revocation, batch generation |
| student | View and download own certificates |
| public | Verify certificates by number |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| CertificateTemplate | Yes | Yes (list + detail) | Yes | Yes |
| Certificate | Yes | Yes (list + detail) | No (no edit) | No (only revoke) |
| CertificateVerification | Automatic | Yes (via detail) | N/A | N/A |
| BatchCertificateGeneration | Yes | Yes (list + detail) | No | No |

## Models

- `CertificateTemplate` -- title, body_template, background_image, signatures, orientation, page_size
- `Certificate` -- student FK, course FK, certificate_number, grade, gpa, hash_signature, qr_code, status
- `CertificateVerification` -- certificate FK, verified_by, verification_method, ip_address
- `BatchCertificateGeneration` -- course FK, template FK, total/processed/failed counts, status

## Dependencies

- `accounts` (Student model, User model)
- `course` (Course model)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:certificates:<view_name>`
- API: `api:v1:certificates:<resource-name>`

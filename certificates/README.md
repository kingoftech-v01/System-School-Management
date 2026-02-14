# Certificates App

PDF certificate generation with templates, digital verification, and batch issuance.

## Description

The certificates app manages the complete certificate lifecycle: template design, individual issuance, PDF download, public verification by certificate number, and batch generation for an entire course. Templates support custom backgrounds, signatures, orientation, and page size. Certificates include SHA-256 hash signatures and QR codes for verification. Celery tasks handle batch generation, integrity verification, notification emails, and cleanup of old verification records.

## Main Features

- **Certificate Templates**: Full CRUD (create, list, detail, edit, delete) with file upload for backgrounds and signatures
- **Certificate Issuance**: Create individual certificates linked to student + course with auto-generated certificate numbers
- **Certificate Editing**: Edit issued certificate details (grade, completion date, GPA, credits)
- **Certificate Viewing**: Role-based list (students see own, staff see all) with filtering by course, status, and revocation
- **Certificate Download**: PDF file download with ownership permission checks
- **Certificate Revocation**: Revoke with reason and audit trail, plus reissue capability
- **Public Verification**: Verify certificate by number (no login required, rate-limited at 50/hour)
- **Batch Generation**: Create batch jobs for course-wide certificate generation with progress tracking
- **Dashboard**: Role-based dashboard (student: my certificates, staff: system statistics)
- **Celery Tasks**: Background batch generation, certificate notification, integrity verification, verification cleanup, expiry reminders

## User Roles

| Role | Templates (CRUD) | Issue Certificates | View Certificates | Download | Revoke / Reissue | Batch Generation | Dashboard | Public Verify |
| ---- | ---------------- | ------------------ | ----------------- | -------- | ---------------- | ---------------- | --------- | ------------- |
| student | -- | -- | Own only | Own only | -- | -- | Own certs | Yes |
| professor | -- | -- | All (staff) | All (staff) | -- | -- | Stats | Yes |
| direction | Full | Yes | All | All | Yes | Full | Stats | Yes |
| admin | Full | Yes | All | All | Yes | Full | Stats | Yes |
| registrar | Full | Yes | All | All | Yes | Full | Stats | Yes |
| secretary | Full | Yes | All | All | Yes | Full | Stats | Yes |
| parent | -- | -- | -- | -- | -- | -- | -- | Yes |
| prefet | -- | -- | All (staff) | All (staff) | -- | -- | Stats | Yes |
| accountant | -- | -- | All (staff) | All (staff) | -- | -- | Stats | Yes |
| librarian | -- | -- | All (staff) | All (staff) | -- | -- | Stats | Yes |
| public | -- | -- | -- | -- | -- | -- | -- | Yes |

**Frontend access control**: Template CRUD, certificate issuance, revocation, reissue, and batch generation use the `@registrar_only` decorator, which permits `registrar`, `secretary`, `direction`, and `admin` roles. Certificate list, detail, download, and dashboard use `@login_required` with role-based filtering in the view logic. Public verification has no login requirement.

**API access control**: Uses DRF permission classes (`CanManageTemplates`, `CanIssueCertificates`, `CanRevokeCertificates`, `IsStudentOrStaffReadOnly`). Template reads are public (safe methods allowed for anyone); writes require `is_staff`. Certificate CRUD requires authentication; students see only their own. Verification endpoints (`verify`, `verify_by_number`) use `AllowAny`.

## CRUD Summary

| Entity | Create | Read | Update | Delete |
| ------ | ------ | ---- | ------ | ------ |
| CertificateTemplate | Yes | Yes (list + detail) | Yes | Yes |
| Certificate | Yes | Yes (list + detail) | Yes (edit view) | No (only revoke/reissue) |
| CertificateVerification | Automatic (on verify) | Yes (via detail, API) | N/A | Automatic (cleanup task) |
| BatchCertificateGeneration | Yes | Yes (list + detail) | No | No |

## Models

### CertificateTemplate

- **Purpose**: Certificate design templates with layout configuration
- **Key Fields**: `name` (unique), `description`, `template_file` (FileField), `background_image` (ImageField), `title_text` (default: "Certificate of Completion"), `body_template` (with placeholders: `{student_name}`, `{course_name}`, `{date}`, `{grade}`)
- **Signature Fields**: `signature_1_name`, `signature_1_title`, `signature_1_image`, `signature_2_name`, `signature_2_title`, `signature_2_image`
- **Settings**: `orientation` (landscape/portrait, default: landscape), `page_size` (A4/Letter, default: A4), `is_active` (default: True)
- **Timestamps**: `created_at`, `updated_at`
- **Ordering**: `['name']`

### Certificate

- **Purpose**: Issued certificates linked to students and courses
- **Relationships**: `student` FK to `accounts.Student`, `course` FK to `course.Course`, `template` FK to `CertificateTemplate` (SET_NULL), `issued_by` FK to User (SET_NULL), `revoked_by` FK to User (SET_NULL)
- **Certificate Details**: `certificate_number` (unique, auto-generated as `CERT-{year}-{uuid8}`), `issue_date`, `completion_date`
- **Academic Info**: `grade`, `gpa` (decimal 4,2), `credits` (decimal 5,2)
- **File**: `pdf_file` (FileField)
- **Verification**: `hash_signature` (SHA-256, 64 chars), `blockchain_hash`, `qr_code` (ImageField), `verification_url`
- **Status**: `status` choices: pending, generated, issued, revoked (default: pending)
- **Revocation**: `is_revoked`, `revoked_at`, `revoked_by`, `revocation_reason`
- **Constraints**: `unique_together = ['student', 'course']`
- **Indexes**: `[student, -issue_date]`, `[course, -issue_date]`, `[certificate_number]`, `[status, -created_at]`
- **Methods**: `generate_certificate_number()`, `calculate_hash()`, `revoke(user, reason)`
- **Ordering**: `['-issue_date']`

### CertificateVerification

- **Purpose**: Audit trail for certificate verification attempts
- **Relationships**: `certificate` FK to Certificate, `verified_by_user` FK to User (SET_NULL, optional)
- **Fields**: `verified_at` (auto), `verification_method` (choices: qr_code, number, hash, blockchain), `ip_address`, `user_agent`, `is_valid`, `verification_notes`
- **Indexes**: `[certificate, -verified_at]`, `[-verified_at]`
- **Ordering**: `['-verified_at']`

### BatchCertificateGeneration

- **Purpose**: Track batch certificate generation jobs
- **Relationships**: `course` FK to `course.Course`, `template` FK to `CertificateTemplate` (SET_NULL), `initiated_by` FK to User (SET_NULL)
- **Criteria**: `min_grade`, `min_gpa` (decimal 4,2)
- **Progress**: `total_students`, `processed_count`, `success_count`, `failure_count`
- **Status**: `status` choices: pending, processing, completed, failed (default: pending)
- **Timing**: `started_at`, `completed_at`, `created_at`
- **Error Tracking**: `error_log` (TextField)
- **Ordering**: `['-created_at']`

## API Endpoints

### CertificateTemplate (`/api/templates/`)

| Method | Endpoint | Permission | Description |
| ------ | -------- | ---------- | ----------- |
| GET | `/api/templates/` | Anyone (read) | List templates, filter by `is_active`, search by `name`/`description` |
| POST | `/api/templates/` | Staff only | Create template |
| GET | `/api/templates/{id}/` | Anyone (read) | Retrieve template |
| PUT/PATCH | `/api/templates/{id}/` | Staff only | Update template |
| DELETE | `/api/templates/{id}/` | Staff only | Delete template |
| POST | `/api/templates/{id}/set_default/` | Staff + CanIssueCertificates | Set as default for certificate type |

### Certificate (`/api/certificates/`)

| Method | Endpoint | Permission | Description |
| ------ | -------- | ---------- | ----------- |
| GET | `/api/certificates/` | Authenticated | List certificates (students see own only) |
| POST | `/api/certificates/` | Authenticated + staff | Create certificate |
| GET | `/api/certificates/{id}/` | Authenticated + owner/staff | Retrieve certificate |
| PUT/PATCH | `/api/certificates/{id}/` | Staff only | Update certificate |
| DELETE | `/api/certificates/{id}/` | Staff only | Delete certificate |
| GET | `/api/certificates/{id}/verify/` | AllowAny | Verify certificate authenticity |
| POST | `/api/certificates/verify_by_number/` | AllowAny | Verify by certificate number (public) |
| POST | `/api/certificates/{id}/revoke/` | Staff + CanRevokeCertificates | Revoke certificate |
| POST | `/api/certificates/{id}/unrevoke/` | Staff + CanRevokeCertificates | Unrevoke certificate |
| GET | `/api/certificates/{id}/download/` | Authenticated + owner/staff | Download PDF |

### CertificateVerification (`/api/verifications/`)

| Method | Endpoint | Permission | Description |
| ------ | -------- | ---------- | ----------- |
| GET | `/api/verifications/` | Staff (CanIssueCertificates) | List verification records |
| GET | `/api/verifications/{id}/` | Staff (CanIssueCertificates) | Retrieve verification record |

### BatchCertificateGeneration (`/api/batch/`)

| Method | Endpoint | Permission | Description |
| ------ | -------- | ---------- | ----------- |
| GET | `/api/batch/` | Staff (CanIssueCertificates) | List batch jobs |
| POST | `/api/batch/` | Staff (CanIssueCertificates) | Create batch job |
| GET | `/api/batch/{id}/` | Staff (CanIssueCertificates) | Retrieve batch job |
| POST | `/api/batch/{id}/start_generation/` | Staff (CanIssueCertificates) | Start batch processing |
| GET | `/api/batch/{id}/progress/` | Staff (CanIssueCertificates) | Get progress percentage |

## File Structure

```text
certificates/
    __init__.py
    apps.py                  # CertificatesConfig
    models.py                # CertificateTemplate, Certificate, CertificateVerification, BatchCertificateGeneration
    views_frontend.py        # Template-rendered HTML views (21 views)
    views_api.py             # DRF ViewSets (4 viewsets with custom actions)
    urls.py                  # Frontend + API URL routing with api_router
    forms.py                 # CertificateTemplateForm, CertificateForm, CertificateVerificationForm, BatchCertificateGenerationForm
    serializers.py           # DRF serializers (6 serializers)
    permissions.py           # DRF permissions (5 permission classes)
    admin.py                 # Admin config with fieldsets, actions, and custom display methods
    tasks.py                 # Celery tasks (5 tasks + 1 helper function)
    README.md
    TODO.md
    ARCHITECTURE.md
    migrations/
        __init__.py
        0001_initial.py
    tests/
        __init__.py
        test_models.py       # Model creation, defaults, auto-generation, revocation, unique constraints
        test_views_frontend.py  # Access control and role-based permission tests for all frontend views
        test_views_api.py    # CRUD + custom action tests for all API viewsets
        test_forms.py        # Form validation (verification normalization, duplicate prevention, inactive template)
        test_serializers.py  # Serializer field presence, computed fields, validation
        test_permissions.py  # Permission class unit tests with mock requests
        test_admin.py        # Admin registration, list_display, actions, search_fields
        test_tasks.py        # Celery task tests (honors determination, cleanup, integrity verification)
```

## Configuration

### Rate Limiting

- Frontend views: `100/h` per user (all authenticated views)
- Public verification page: `50/h` per IP
- API verification endpoints: No rate limiting (uses `AllowAny` without `ratelimit`)

### File Upload Paths

| Upload | Path |
| ------ | ---- |
| Template files | `certificates/templates/%Y/%m/` |
| Background images | `certificates/backgrounds/` |
| Signature images | `certificates/signatures/` |
| Issued PDFs | `certificates/issued/%Y/%m/` |
| QR codes | `certificates/qr_codes/` |

### Celery Tasks

| Task Name | Schedule | Description |
| --------- | -------- | ----------- |
| `certificates.generate_batch_certificates` | On-demand | Process batch generation job, create certificates, email results |
| `certificates.send_certificate_notification` | On-demand | Email student when certificate is issued |
| `certificates.verify_certificate_integrity` | Periodic | Check all certificate SHA-256 hash signatures |
| `certificates.cleanup_expired_verifications` | Periodic | Delete verification records older than 2 years |
| `certificates.send_expiring_certificate_reminders` | Periodic | Email students about certificates expiring in 30 days |

## Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
| --- | --------------------- | ------- |
| `accounts` | Student, User, `registrar_only`, `lecturer_required`, `tenant_required` decorators | Student identity, role-based access control |
| `course` | Course | Certificate-course association |
| `result` | Result | Batch generation queries passing students |
| `django-ratelimit` | `@ratelimit` decorator | Request rate limiting |
| `django-filter` | `DjangoFilterBackend` | API queryset filtering |
| `djangorestframework` | ViewSets, serializers, permissions | REST API layer |
| `celery` | `@shared_task` | Background task processing |

### Apps That Depend On This App

None currently -- certificates is a leaf app with no reverse dependencies.

## URL Namespace

- Frontend: `frontend:certificates:<view_name>`
- API: `api:certificates:<resource-name>`

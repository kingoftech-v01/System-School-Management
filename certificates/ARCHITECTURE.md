# Certificates App -- Architecture

## Overview

The certificates app manages the full lifecycle of academic certificates: template
design, individual issuance, PDF generation, digital signing (SHA-256 hashing),
public verification, revocation/reissuance, and batch generation. It is a leaf app
with no reverse dependencies, relying on `accounts` for user/student identity,
`course` for academic context, and `result` for batch eligibility queries. It
exposes both an HTML frontend (Django template views with `@registrar_only` access
control) and a REST API (DRF ViewSets with custom permission classes).

---

## Model Relationships

### ASCII Entity-Relationship Diagram

```text
 accounts.User                          course.Program
 (get_user_model)                       +------------+
 +-------------------+                  | title      |
 | role (ROLE_CHOICES)|                 +-----+------+
 | is_staff           |                       |
 +---------+---------+                        |
           |                                  |
      1-to-1 (student FK)             FK (program)
           |                                  |
 accounts.Student                      course.Course
 +-------------------+                 +-------------------+
 | student (User)    |                 | title             |
 | level             |                 | code              |
 | program (Program) |                 | credit            |
 +--------+----------+                 | program (Program) |
          |                            +--------+----------+
          |                                     |
          |  FK (student)            FK (course) |
          |                                     |
          +------->  Certificate  <-------------+
                     +-------------------------------+
                     | certificate_number (unique)    |
                     | issue_date                     |
                     | completion_date                |
                     | grade                          |
                     | gpa                            |
                     | credits                        |
                     | pdf_file                       |
                     | hash_signature (SHA-256)       |
                     | blockchain_hash                |
                     | qr_code                        |
                     | verification_url               |
                     | status (pending/generated/     |
                     |         issued/revoked)        |
                     | is_revoked                     |
                     | revoked_at                     |
                     | revocation_reason              |
                     +------+-----+--+---+-----------+
                            |     |  |   |
              FK (template) |     |  |   | FK (issued_by -> User)
                            |     |  |   | FK (revoked_by -> User)
                            |     |  |
                            v     |  +-----> CertificateVerification
               CertificateTemplate|          +---------------------------+
               +-----------------+|          | certificate (FK)          |
               | name (unique)   ||          | verified_at               |
               | description     ||          | verification_method       |
               | template_file   ||          |   (qr_code/number/       |
               | background_image||          |    hash/blockchain)       |
               | title_text      ||          | ip_address                |
               | body_template   ||          | user_agent                |
               | signature_1_*   ||          | verified_by_user (FK User)|
               | signature_2_*   ||          | is_valid                  |
               | orientation     ||          | verification_notes        |
               | page_size       ||          +---------------------------+
               | is_active       ||
               +---------+-------+|
                         |        |
               FK (template)      |
                         |        |
                         v        |
          BatchCertificateGeneration
          +-----------------------------------+
          | course (FK -> Course)             |
          | template (FK -> CertificateTemplate)|
          | min_grade                         |
          | min_gpa                           |
          | total_students                    |
          | processed_count                   |
          | success_count                     |
          | failure_count                     |
          | status (pending/processing/       |
          |         completed/failed)         |
          | error_log                         |
          | initiated_by (FK -> User)         |
          | started_at                        |
          | completed_at                      |
          +-----------------------------------+
```

### Compact Relationship Summary

```text
accounts.Student ----1:N----> Certificate
course.Course ------1:N----> Certificate
CertificateTemplate 1:N----> Certificate
User ---------------1:N----> Certificate       (issued_by)
User ---------------1:N----> Certificate       (revoked_by)
Certificate --------1:N----> CertificateVerification
User ---------------1:N----> CertificateVerification (verified_by_user)
course.Course ------1:N----> BatchCertificateGeneration
CertificateTemplate 1:N----> BatchCertificateGeneration
User ---------------1:N----> BatchCertificateGeneration (initiated_by)
```

### Model Details

#### CertificateTemplate

- **Purpose**: Certificate design templates with layout and signature configuration.
- **Key Fields**: `name` (CharField, max_length=200, unique), `description` (TextField, blank), `template_file` (FileField, upload_to `certificates/templates/%Y/%m/`), `background_image` (ImageField, upload_to `certificates/backgrounds/`, blank), `title_text` (CharField, default "Certificate of Completion"), `body_template` (TextField, placeholders: `{student_name}`, `{course_name}`, `{date}`, `{grade}`).
- **Signature Configuration**: Two signature slots -- `signature_1_name`, `signature_1_title`, `signature_1_image` and `signature_2_name`, `signature_2_title`, `signature_2_image`. All blank-able.
- **Layout Settings**: `orientation` (landscape/portrait, default landscape), `page_size` (A4/Letter, default A4).
- **State**: `is_active` (BooleanField, default True).
- **Timestamps**: `created_at` (auto_now_add), `updated_at` (auto_now).
- **Ordering**: `['name']`.
- **Related Names**: `certificates` (Certificate FK back-reference).

#### Certificate

- **Purpose**: Issued certificates linking students to courses with digital verification data.
- **Foreign Keys**:
  - `student` -> `accounts.Student` (CASCADE), related_name `certificates`
  - `course` -> `course.Course` (CASCADE), related_name `certificates`
  - `template` -> `CertificateTemplate` (SET_NULL, nullable), related_name `certificates`
  - `issued_by` -> `User` (SET_NULL, nullable, blank), related_name `issued_certificates`
  - `revoked_by` -> `User` (SET_NULL, nullable, blank), related_name `revoked_certificates`
- **Auto-Generated Fields**:
  - `certificate_number` -- format `CERT-{year}-{uuid4.hex[:8].upper()}`, unique, auto-set in `save()`
  - `hash_signature` -- SHA-256 of `"{certificate_number}{student.id}{course.id}{issue_date}"`, auto-set in `save()` when `pdf_file` exists
- **Academic Fields**: `grade` (CharField, max_length=10), `gpa` (DecimalField 4,2), `credits` (DecimalField 5,2), `completion_date` (DateField, nullable).
- **File/Verification Fields**: `pdf_file` (FileField, upload_to `certificates/issued/%Y/%m/`), `blockchain_hash` (CharField 66), `qr_code` (ImageField, upload_to `certificates/qr_codes/`), `verification_url` (URLField).
- **Status**: choices `pending`, `generated`, `issued`, `revoked` -- default `pending`.
- **Revocation Fields**: `is_revoked` (BooleanField, default False), `revoked_at` (DateTimeField, nullable), `revocation_reason` (TextField, blank).
- **Constraints**: `unique_together = ['student', 'course']` -- one certificate per student-course pair.
- **Indexes**:

  | Fields | Purpose |
  |---|---|
  | `student, -issue_date` | Fast lookup of a student's certificates by date |
  | `course, -issue_date` | Fast lookup of certificates per course |
  | `certificate_number` | Public verification lookups |
  | `status, -created_at` | Admin filtering by status |

- **Methods**:
  - `generate_certificate_number()` -- creates `CERT-YYYY-XXXXXXXX` format
  - `calculate_hash()` -- SHA-256 of concatenated certificate data
  - `revoke(user, reason)` -- sets `is_revoked`, `status='revoked'`, timestamps, revoked_by
  - `save()` -- auto-generates `certificate_number` and `hash_signature` if missing

#### CertificateVerification

- **Purpose**: Audit log of every verification attempt (successful and failed), both public and API.
- **Foreign Keys**:
  - `certificate` -> `Certificate` (CASCADE), related_name `verifications`
  - `verified_by_user` -> `User` (SET_NULL, nullable, blank), related_name `certificate_verifications`
- **Verification Methods** (choices): `qr_code`, `number`, `hash`, `blockchain`.
- **Tracking Fields**: `ip_address` (GenericIPAddressField, nullable), `user_agent` (TextField, blank), `is_valid` (BooleanField), `verification_notes` (TextField, blank).
- **Timestamp**: `verified_at` (auto_now_add).
- **Indexes**: `(certificate, -verified_at)` and `(-verified_at)`.
- **Ordering**: `['-verified_at']`.
- **Cleanup**: Records older than 2 years deleted by `cleanup_expired_verifications` periodic task.

#### BatchCertificateGeneration

- **Purpose**: Track asynchronous batch certificate generation jobs.
- **Foreign Keys**:
  - `course` -> `course.Course` (CASCADE), related_name `batch_generations`
  - `template` -> `CertificateTemplate` (SET_NULL, nullable)
  - `initiated_by` -> `User` (SET_NULL, nullable), related_name `initiated_batch_generations`
- **Criteria Fields**: `min_grade` (CharField, max_length=10), `min_gpa` (DecimalField 4,2, nullable).
- **Progress Counters**: `total_students`, `processed_count`, `success_count`, `failure_count` -- all PositiveIntegerField, default 0.
- **Status**: choices `pending`, `processing`, `completed`, `failed` -- default `pending`.
- **Error Tracking**: `error_log` (TextField, blank).
- **Timing**: `started_at` (nullable), `completed_at` (nullable), `created_at` (auto_now_add).
- **Ordering**: `['-created_at']`.

---

## View Access Patterns per Role

The system defines ten roles in `accounts.models.ROLE_CHOICES`:

| Role | Value | Description |
|---|---|---|
| parent | `'parent'` | Parent/Guardian |
| student | `'student'` | Student |
| professor | `'professor'` | Lecturer/Professor |
| prefet | `'prefet'` | Discipline Officer |
| accountant | `'accountant'` | Accountant |
| secretary | `'secretary'` | Secretary |
| librarian | `'librarian'` | Librarian |
| registrar | `'registrar'` | Registrar |
| direction | `'direction'` | School Direction |
| admin | `'admin'` | System Administrator |

### Authorization Decorators

- **`@registrar_only`** (from `accounts.decorators`): Allows roles `registrar`, `secretary`, `direction`, `admin`. Defined as `role_required('registrar', 'secretary', 'direction', 'admin')`.
- **`@login_required`**: Standard Django authentication check.
- **`@tenant_required`**: Ensures user belongs to the current tenant for multi-tenant isolation.
- **`@ratelimit`**: Per-user (100/h) or per-IP (50/h) rate limiting via `django_ratelimit`.

### Frontend Views -- Role Access Matrix

`Y` = full access, `Own` = own records only, `--` = no access.

| View | URL | student | professor | parent | prefet | accountant | secretary | librarian | registrar | direction | admin |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `certificates_dashboard` | `/` | Own | Stats | Stats | Stats | Stats | Stats | Stats | Stats | Stats | Stats |
| `certificate_list` | `/certificates/` | Own | All | All | All | All | All | All | All | All | All |
| `certificate_detail` | `/certificates/<pk>/` | Own | All | All | All | All | All | All | All | All | All |
| `certificate_download` | `/certificates/<pk>/download/` | Own | All | All | All | All | All | All | All | All | All |
| `certificate_create` | `/certificates/create/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `certificate_edit` | `/certificates/<pk>/edit/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `certificate_revoke` | `/certificates/<pk>/revoke/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `certificate_reissue` | `/certificates/<pk>/reissue/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `template_list` | `/templates/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `template_detail` | `/templates/<pk>/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `template_create` | `/templates/create/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `template_update` | `/templates/<pk>/edit/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `template_delete` | `/templates/<pk>/delete/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `batch_generation_list` | `/batch/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `batch_generation_create` | `/batch/create/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `batch_generation_detail` | `/batch/<pk>/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `batch_generation_start` | `/batch/<pk>/start/` | -- | -- | -- | -- | -- | Y | -- | Y | Y | Y |
| `certificate_verify` | `/verify/` | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC | PUBLIC |

**Notes on scoping:**

- **Students**: `certificate_list` and `certificate_detail` check `request.user.role == 'student'`, then look up the `Student` record via `Student.objects.get(student=request.user)`, and filter/compare `certificate.student` against that.
- **Non-student authenticated users**: All non-`@registrar_only` views grant full read access to any authenticated non-student user (professor, parent, prefet, accountant, librarian). The code checks `if request.user.role == 'student':` as the only branch, so all other roles fall through to the staff/all path.
- **`certificate_verify`**: No `@login_required` -- fully public, rate-limited at 50/h per IP.

### API Views -- Permission Matrix

API views use DRF permission classes defined in `certificates/permissions.py`:

| Permission Class | Rule |
|---|---|
| `CanManageTemplates` | Safe methods (GET, HEAD, OPTIONS): anyone. Write methods: `is_authenticated` and `is_staff`. |
| `IsStudentOrStaffReadOnly` | `has_permission`: `is_authenticated`. `has_object_permission`: Staff = full access; non-staff = SAFE_METHODS only + must be object owner (`obj.student.student == request.user`). |
| `CanIssueCertificates` | `is_authenticated` and `is_staff`. |
| `CanVerifyCertificates` | Always returns `True` (public). |
| `CanRevokeCertificates` | `is_authenticated` and `is_staff`. |

| ViewSet / Action | Permission Classes | Who Can Access |
|---|---|---|
| `CertificateTemplateViewSet` (list/retrieve) | `CanManageTemplates` | Anyone (unauthenticated OK for reads) |
| `CertificateTemplateViewSet` (create/update/delete) | `CanManageTemplates` | Staff only (`is_staff=True`) |
| `CertificateTemplateViewSet.set_default` | `IsAuthenticated`, `CanIssueCertificates` | Staff only |
| `CertificateViewSet` (list/retrieve) | `IsAuthenticated`, `IsStudentOrStaffReadOnly` | Staff: all certs; Students: own only |
| `CertificateViewSet.verify` (GET) | `AllowAny` | Anyone (public) |
| `CertificateViewSet.verify_by_number` (POST) | `AllowAny` | Anyone (public) |
| `CertificateViewSet.revoke` (POST) | `IsAuthenticated`, `CanRevokeCertificates` | Staff only |
| `CertificateViewSet.unrevoke` (POST) | `IsAuthenticated`, `CanRevokeCertificates` | Staff only |
| `CertificateViewSet.download` (GET) | `IsAuthenticated`, `IsStudentOrStaffReadOnly` | Staff or certificate owner |
| `CertificateVerificationViewSet` (read-only) | `IsAuthenticated`, `CanIssueCertificates` | Staff only |
| `BatchCertificateGenerationViewSet` (full CRUD) | `IsAuthenticated`, `CanIssueCertificates` | Staff only |
| `BatchCertificateGenerationViewSet.start_generation` | `IsAuthenticated`, `CanIssueCertificates` | Staff only |
| `BatchCertificateGenerationViewSet.progress` | `IsAuthenticated`, `CanIssueCertificates` | Staff only |

**Note:** API permission classes use `is_staff` (Django's built-in admin flag), not the `role` field. This means any user with `is_staff=True` has full API access regardless of their `role` value. Frontend views use the `role` field via `@registrar_only`.

---

## Business Logic Workflows

### 1. Single Certificate Issuance (Frontend)

```text
  Registrar / Secretary / Direction / Admin
          |
          | POST /certificates/create/
          v
  +---CertificateForm.clean()---+
  | Validates:                   |
  | - student (FK Select)        |
  | - course  (FK Select)        |
  | - template (FK Select)       |
  | - completion_date, grade,    |
  |   gpa, credits               |
  | - Duplicate check:           |
  |   Certificate.objects.filter |
  |   (student=X, course=Y)     |
  |   .exists() -> raise error   |
  +----------+-----------+
             |
             v
  form.save(commit=False)
  certificate.issued_by = request.user
  certificate.status = 'issued'
  certificate.save()
  +-----------------------------------+
  | Certificate.save() triggers:      |
  | 1. generate_certificate_number()  |
  |    -> "CERT-{year}-{uuid8}"       |
  | 2. If pdf_file present:           |
  |    calculate_hash()               |
  |    -> SHA-256("{cert_number}      |
  |       {student.id}{course.id}     |
  |       {issue_date}")              |
  +-----------------------------------+
          |
          v
  Redirect -> certificate_detail(pk)
```

### 2. Certificate Revocation

```text
  Registrar / Secretary / Direction / Admin
          |
          | GET /certificates/<pk>/revoke/   (shows form)
          | POST (with reason field)
          v
  Guard: certificate.is_revoked must be False
          |
          v
  Certificate.revoke(user=request.user, reason=reason)
  +-----------------------------------+
  | Sets:                             |
  |   is_revoked   = True             |
  |   status       = 'revoked'        |
  |   revoked_at   = timezone.now()   |
  |   revoked_by   = user             |
  |   revocation_reason = reason      |
  |   .save()                         |
  +-----------------------------------+
          |
          v
  Redirect -> certificate_detail(pk)
```

### 3. Certificate Reissuance

```text
  Registrar / Secretary / Direction / Admin
          |
          | POST /certificates/<pk>/reissue/   (POST-only)
          v
  Guard: certificate.is_revoked must be True
          |
          v
  +-----------------------------------+
  | Clears revocation:                |
  |   is_revoked        = False       |
  |   revoked_at        = None        |
  |   revoked_by        = None        |
  |   revocation_reason = ''          |
  |   status            = 'issued'    |
  |   .save()                         |
  +-----------------------------------+
          |
          v
  Redirect -> certificate_detail(pk)
```

### 4. Public Certificate Verification (Frontend)

```text
  Anyone (no login required, rate-limited 50/h per IP)
          |
          | GET  /verify/     -> renders empty form
          | POST /verify/     -> submits certificate_number
          v
  CertificateVerificationForm
  +--------------------------------------+
  | clean_certificate_number():          |
  |   strip().upper()  (normalize)       |
  +----------------+---------------------+
                   |
         +---------+---------+
         |                   |
    Not Found           Found
         |                   |
    Result:             Check is_revoked
    valid=False              |
    "Certificate         +--------+--------+
     not found"          |                 |
                    Revoked=True      Revoked=False
                         |                 |
                    Result:           Result:
                    valid=False       valid=True
                    + revoked_at      "Certificate is
                    + reason           valid and
                                       authentic"
                         |                 |
                         +--------+--------+
                                  |
                                  v
                   CertificateVerification.objects.create(
                     certificate=cert,
                     verification_method='number',
                     ip_address=REMOTE_ADDR,
                     user_agent=HTTP_USER_AGENT,
                     is_valid=not cert.is_revoked,
                     verification_notes='Web verification'
                   )
```

### 5. API Hash-Based Verification

```text
  GET /api/certificates/<pk>/verify/   (AllowAny)
         |
         v
  Recalculate hash:
    SHA-256("{cert_number}{student.id}{course.id}{issue_date}")
         |
  Compare with stored hash_signature
         |
    +-----+------+
    |            |
  Match       Mismatch
    |            |
  valid=True   valid=False
  + cert info  "possible tampering"
         |
         v
  CertificateVerification.objects.create(
    certificate, verification_method='api',
    is_valid=True
  )
```

### 6. Batch Certificate Generation

```text
  Staff User (registrar_only)
          |
          | POST /batch/create/
          v
  BatchCertificateGenerationForm
  +-------------------------------------------+
  | Validates:                                 |
  | - course (FK Select)                       |
  | - template (FK Select, must be is_active)  |
  | - min_grade (optional)                     |
  | - min_gpa (optional)                       |
  +-------------------+-----------------------+
                      |
                      v
  batch.initiated_by = request.user
  batch.total_students = Student.objects.filter(
      program=batch.course.program
  ).count()
  batch.save()  (status='pending')
                      |
     +----- Manual step: view batch detail -----+
     |                                          |
     | POST /batch/<pk>/start/                  |
     v                                          |
  Guard: batch.status must be 'pending'         |
  batch.status = 'processing'                   |
  batch.started_at = now()                      |
  batch.save()                                  |
                      |                         |
                      | Celery dispatch         |
                      | (currently commented    |
                      |  out in views)          |
                      v                         |
  +-- tasks.py: generate_batch_certificates --+ |
  |                                           | |
  | Query: Result.objects.filter(             | |
  |   course=course,                          | |
  |   grade__gte=course.passing_grade         | |
  | ).select_related('student')               | |
  |                                           | |
  | FOR each passing result:                  | |
  |   IF Certificate(student, course) exists: | |
  |     skip (processed_count++)              | |
  |   ELSE:                                   | |
  |     Certificate.objects.create(           | |
  |       student, course, template,          | |
  |       issue_date=today,                   | |
  |       grade=result.grade                  | |
  |     )                                     | |
  |     processed_count++                     | |
  |     success_count++ or failure_count++    | |
  |                                           | |
  | batch.status = 'completed'                | |
  | batch.completed_at = now()                | |
  | send_mail() to batch.initiated_by        | |
  +-------------------------------------------+ |
```

### 7. Dashboard Logic

```text
  GET / (certificates dashboard)
          |
    +-----+------+
    |            |
  Student     Non-Student
    |            |
    v            v
  Student.objects.get(        Certificate.objects aggregates:
    student=request.user        count() -> total_certificates
  )                             filter(status='issued').count()
  Certificate.objects.filter(   filter(is_revoked=True).count()
    student=student             filter(status='pending').count()
  )                             order_by('-created_at')[:10]
  -> my_certificates          BatchCertificateGeneration.objects
  -> total_certificates         .filter(status__in=['pending',
                                  'processing']).count()
                              -> total, issued, revoked, pending,
                                 recent_certificates, active_batches
```

---

## Celery Background Tasks

Defined in `certificates/tasks.py`. All tasks use `@shared_task`.

| Task Name | Trigger | Description |
|---|---|---|
| `certificates.generate_batch_certificates` | `batch_generation_start` view (Celery dispatch is commented out) | Iterates eligible students via `result.Result` model, creates `Certificate` per student, updates batch counters, sends email to `initiated_by` on completion |
| `certificates.send_certificate_notification` | Manual invocation after issuance | Sends email to `certificate.student.student.email` with certificate number, issue date, and download instructions |
| `certificates.verify_certificate_integrity` | Periodic/scheduled | Iterates all non-revoked certificates, recalculates SHA-256 hash, logs mismatches to stdout |
| `certificates.cleanup_expired_verifications` | Periodic/scheduled | Deletes `CertificateVerification` records older than 730 days (2 years) |
| `certificates.send_expiring_certificate_reminders` | Periodic/scheduled | Sends email reminders for certificates expiring in 30 days (references `expiry_date` field not currently on the Certificate model) |

### Task Dependencies

```text
tasks.py imports:
  +-- certificates.models (Certificate, BatchCertificateGeneration,
  |     CertificateTemplate, CertificateVerification)
  +-- accounts.models.Student
  +-- result.models.Result
  +-- django.core.mail.send_mail
  +-- django.conf.settings (DEFAULT_FROM_EMAIL)
  +-- celery.shared_task
```

---

## Dependencies (Both Directions)

### Outbound: This App Depends On

| Dependency | Import | Where Used |
|---|---|---|
| `accounts.models.Student` | `from accounts.models import Student` | `Certificate.student` FK; student lookup in `views_frontend.py`; imported in `forms.py`, `tasks.py` |
| `accounts.models.User` | `get_user_model()` | `Certificate.issued_by`, `.revoked_by`; `CertificateVerification.verified_by_user`; `BatchCertificateGeneration.initiated_by` |
| `accounts.decorators.registrar_only` | `from accounts.decorators import registrar_only` | All template CRUD, certificate issuance, revocation, batch generation frontend views |
| `accounts.decorators.lecturer_required` | `from accounts.decorators import lecturer_required` | Imported in `views_frontend.py` but **not used** in any view |
| `accounts.decorators.tenant_required` | `from accounts.decorators import tenant_required` | All authenticated frontend views |
| `course.models.Course` | FK string reference `'course.Course'` | `Certificate.course`; `BatchCertificateGeneration.course`; imported in `forms.py` |
| `course.models.Program` | Indirect via `Student.program` and `Course.program` | `batch_generation_create` counts students by `Student.objects.filter(program=batch.course.program)` |
| `result.models.Result` | `from result.models import Result` | `tasks.py` -- batch generation queries `Result.objects.filter(course=X, grade__gte=passing_grade)` |
| `core.School` | Indirect via `@tenant_required` | Multi-tenant isolation decorator on all authenticated frontend views |
| `django_ratelimit` | `from django_ratelimit.decorators import ratelimit` | All frontend views |
| `django_filters` | `from django_filters.rest_framework import DjangoFilterBackend` | All API viewsets |
| `rest_framework` | Multiple imports | `views_api.py`, `serializers.py`, `permissions.py` |
| `celery` | `from celery import shared_task` | `tasks.py` -- 5 background tasks |
| `hashlib` (stdlib) | `import hashlib` | `models.py` -- SHA-256 hash computation |
| `uuid` (stdlib) | `import uuid` | `models.py` -- certificate number generation |

### Inbound: Apps That Depend On This App

No other app in the project imports from or references the certificates app.
It is a leaf node in the dependency graph.

### Dependency Diagram

```text
  +-----------+     +-----------+     +--------+
  | accounts  |     |  course   |     | result |
  |  .Student |     |  .Course  |     | .Result|
  |  .User    |     |  .Program |     +---+----+
  |  .decors  |     +-----+-----+         |
  +-----+-----+           |               |
        |                  |               |
        |  FK + imports    |  FK + imports |  import (tasks.py)
        |                  |               |
        +--------+---------+-------+-------+
                 |                 |
                 v                 v
          +------+------------------+------+
          |         certificates           |
          |  models.py                     |
          |  views_frontend.py             |
          |  views_api.py                  |
          |  serializers.py                |
          |  permissions.py                |
          |  tasks.py                      |
          |  forms.py                      |
          |  admin.py                      |
          +--+-------+-------+-------+-----+
             |       |       |       |
             v       v       v       v
          django  django  rest_     celery
          _rate   _filters framework
          limit
```

---

## Data Flow Diagrams

### Certificate Issuance (End to End)

```text
  Browser                    Django Frontend              Database
  ------                     ----------------             --------

  [Staff user]
       |
       |  GET /certificates/create/
       +------------------------------>  certificate_create()
       |                                 @login_required
       |                                 @registrar_only
       |                                 @tenant_required
       |                                 @ratelimit(user, 100/h)
       |                                   |
       |  <---- render certificate_form ---+
       |         (empty CertificateForm)
       |
       |  POST (student, course,
       |        template, grade, gpa,
       |        credits, completion_date)
       +------------------------------>  CertificateForm.is_valid()
       |                                   |
       |                              clean(): check
       |                              Certificate.objects.filter(
       |                                student=X, course=Y
       |                              ).exists() ----------------> SELECT
       |                                   |
       |                              form.save(commit=False)
       |                              cert.issued_by = request.user
       |                              cert.status = 'issued'
       |                              cert.save()
       |                                   |
       |                              generate_certificate_number()
       |                              -> CERT-{year}-{uuid8}
       |                                   |
       |                              calculate_hash() (if pdf_file)
       |                              -> SHA-256(...)
       |                                   |
       |                              INSERT ----------------------> certificates_certificate
       |                                   |
       |  <---- 302 redirect to detail ----+
       |
       |  GET /certificates/<pk>/
       +------------------------------>  certificate_detail()
       |                                   |
       |                              SELECT cert + joins --------> certificates_certificate
       |                              cert.verifications[:10] ----> certificates_verification
       |                                   |
       |  <---- render certificate_detail --+
```

### Public Verification Flow

```text
  External User              Django (no auth)              Database
  -------------              ----------------              --------

       |
       |  GET /verify/
       +------------------------------>  certificate_verify()
       |                                 @ratelimit(ip, 50/h)
       |                                   |
       |  <---- render verify.html ---------+
       |         (empty form)
       |
       |  POST certificate_number
       +------------------------------>  CertificateVerificationForm
       |                                   |
       |                              strip().upper() normalize
       |                                   |
       |                              SELECT WHERE cert_number=X --> certificates_certificate
       |                                   |
       |                         +----found?----+
       |                         |              |
       |                        NO             YES
       |                         |              |
       |                    valid=False    Check is_revoked
       |                    "Not found"         |
       |                         |        +-----+-----+
       |                         |       YES         NO
       |                         |        |           |
       |                         |   valid=False  valid=True
       |                         |   "Revoked"    "Authentic"
       |                         |        |           |
       |                         +--------+-----------+
       |                                   |
       |                              INSERT CertificateVerification --> certificates_verification
       |                              (certificate, method='number',
       |                               ip_address, user_agent,
       |                               is_valid, notes)
       |                                   |
       |  <---- render verify.html ---------+
       |         (with result)
```

### Batch Generation Flow

```text
  Staff Browser          Django Frontend         Celery Worker            Database
  ------------           ----------------        -------------            --------

       |
       |  POST /batch/create/
       +--------------------->  batch_generation_create()
       |                          |
       |                     Validate form
       |                     (template must be active)
       |                          |
       |                     Count students:
       |                     Student.objects.filter(
       |                       program=batch.course.program
       |                     ).count() --------------------------> SELECT COUNT
       |                          |
       |                     INSERT BatchCertificate
       |                     Generation(status='pending') -------> certificates_batch...
       |  <---- redirect          |
       |
       |  POST /batch/<pk>/start/
       +--------------------->  batch_generation_start()
       |                          |
       |                     Guard: status == 'pending'
       |                          |
       |                     UPDATE status='processing'
       |                     started_at=now() ---------> UPDATE certificates_batch...
       |                          |
       |                     [Celery dispatch]
       |                     generate_batch_certificates
       |                     .delay(batch.id)
       |  <---- redirect          |                 |
       |                          |                 v
       |                          |          SELECT batch ---------> certificates_batch...
       |                          |                 |
       |                          |          SELECT Results WHERE --> result_result
       |                          |          course=X,
       |                          |          grade >= passing
       |                          |                 |
       |                          |          FOR EACH result:
       |                          |            |
       |                          |            +-- EXISTS check ----> certificates_certificate
       |                          |            |
       |                          |            +-- INSERT cert -----> certificates_certificate
       |                          |            |
       |                          |            +-- UPDATE counters -> certificates_batch...
       |                          |                 |
       |                          |          UPDATE status=
       |                          |          'completed' -----------> certificates_batch...
       |                          |                 |
       |                          |          send_mail() to
       |                          |          initiated_by.email
       |
       |  GET /batch/<pk>/
       +--------------------->  batch_generation_detail()
       |                          |
       |                     SELECT batch + joins --------> certificates_batch...
       |                     progress_percentage =
       |                       processed / total * 100
       |  <---- render            |
```

### API Certificate Download Flow

```text
  Client App               DRF API                       Database / Storage
  ----------               -------                       ------------------

       |
       |  GET /api/certificates/<pk>/download/
       +------------------------------>  CertificateViewSet.download()
       |                                   |
       |                              Permission check:
       |                              IsAuthenticated +
       |                              IsStudentOrStaffReadOnly
       |                                   |
       |                         +--- is_staff? ---+
       |                         |                 |
       |                        YES               NO
       |                         |                 |
       |                     Full access     Check ownership:
       |                         |           cert.student.student
       |                         |           == request.user?
       |                         |                 |
       |                         |            YES     NO
       |                         |             |      |
       |                         |             |   403 Forbidden
       |                         +------+------+
       |                                |
       |                         Check pdf_file / certificate_file
       |                                |
       |                         +------+------+
       |                         |             |
       |                      Missing       Present
       |                         |             |
       |                      404 Not      FileResponse ---------> media/certificates/
       |                      Found           |                    issued/{Y}/{M}/
       |                                      |
       |  <---- PDF binary response -----------+
       |         Content-Disposition:
       |         attachment; filename=
       |         "{cert_number}.pdf"
```

---

## URL Namespace Structure

```text
certificates/
  +-- api/                                  (namespace: 'api')
  |   +-- templates/                        CertificateTemplateViewSet
  |   |   +-- <pk>/                         retrieve/update/destroy
  |   |   +-- <pk>/set_default/             POST (custom action)
  |   +-- certificates/                     CertificateViewSet
  |   |   +-- <pk>/                         retrieve/update/destroy
  |   |   +-- <pk>/verify/                  GET  (custom, AllowAny)
  |   |   +-- verify_by_number/             POST (custom, AllowAny)
  |   |   +-- <pk>/revoke/                  POST (custom)
  |   |   +-- <pk>/unrevoke/                POST (custom)
  |   |   +-- <pk>/download/                GET  (custom)
  |   +-- verifications/                    CertificateVerificationViewSet (read-only)
  |   +-- batch/                            BatchCertificateGenerationViewSet
  |       +-- <pk>/start_generation/        POST (custom)
  |       +-- <pk>/progress/                GET  (custom)
  |
  +-- (frontend)                            (namespace: 'frontend')
      +-- /                                 certificates_dashboard
      +-- templates/                        template_list
      +-- templates/create/                 template_create
      +-- templates/<pk>/                   template_detail
      +-- templates/<pk>/edit/              template_update
      +-- templates/<pk>/delete/            template_delete
      +-- certificates/                     certificate_list
      +-- certificates/create/              certificate_create
      +-- certificates/<pk>/                certificate_detail
      +-- certificates/<pk>/edit/           certificate_edit
      +-- certificates/<pk>/download/       certificate_download
      +-- certificates/<pk>/revoke/         certificate_revoke
      +-- certificates/<pk>/reissue/        certificate_reissue
      +-- verify/                           certificate_verify (PUBLIC)
      +-- batch/                            batch_generation_list
      +-- batch/create/                     batch_generation_create
      +-- batch/<pk>/                       batch_generation_detail
      +-- batch/<pk>/start/                 batch_generation_start
```

---

## Admin Configuration

Four model admins registered in `admin.py`:

| Admin Class | Model | Key Features |
|---|---|---|
| `CertificateTemplateAdmin` | CertificateTemplate | List: name, orientation, page_size, is_active. Actions: activate/deactivate templates. Fieldsets: template info, design, signatures, page settings. |
| `CertificateAdmin` | Certificate | List: cert_number, student, course, template, issue_date, is_revoked, verification status. Actions: revoke, unrevoke, regenerate hash. Custom methods: QR preview, verification count, color-coded status. Date hierarchy on `issue_date`. |
| `CertificateVerificationAdmin` | CertificateVerification | List: certificate, verified_by, method, is_valid, verified_at. Date hierarchy on `verified_at`. |
| `BatchCertificateGenerationAdmin` | BatchCertificateGeneration | List: course, template, status, progress bar, success/failed counts. Actions: mark pending, mark completed. Custom methods: HTML progress bar, color-coded success rate. |

**Note on admin field drift**: Several admin fieldsets reference fields that do not exist on the current models (`honors`, `additional_info`, `certificate_file`, `verified_by_email`, `notes`, `created_by`, `grade_threshold`, `include_honors_only`, `failed_count`). These are likely artifacts from an earlier model revision and would cause errors if accessed in the admin.

---

## Rate Limiting

| View Category | Key | Rate |
|---|---|---|
| All authenticated frontend views | `user` | 100 requests/hour |
| Public verification (`certificate_verify`) | `ip` | 50 requests/hour |

---

## Security Considerations

1. **Certificate integrity**: SHA-256 hash of `certificate_number + student.id + course.id + issue_date` stored in `hash_signature`. The `verify_certificate_integrity` periodic Celery task audits all non-revoked certificates for hash mismatches indicating potential data tampering.

2. **Unique constraint**: `unique_together = ['student', 'course']` at the database level prevents duplicate certificates. `CertificateForm.clean()` also validates this at the form level for better user feedback.

3. **Auto-generated certificate number**: Uses `uuid.uuid4().hex[:8].upper()` prefixed with `CERT-{year}-` to produce non-sequential, hard-to-guess identifiers.

4. **Verification audit trail**: Every verification attempt (frontend or API) creates a `CertificateVerification` record capturing IP address, user agent, verification method, and result.

5. **Tenant isolation**: `@tenant_required` on all authenticated frontend views prevents cross-tenant data access.

6. **Student data scoping**: Frontend views branch on `request.user.role == 'student'` and filter to the student's own certificates only. API `get_queryset()` filters by `student__student=user` for non-staff users.

7. **Public endpoint protection**: `certificate_verify` uses IP-based rate limiting (50/h) to mitigate enumeration attacks on certificate numbers.

---

## File Inventory

| File | Purpose |
|---|---|
| `models.py` | 4 models: `CertificateTemplate`, `Certificate`, `CertificateVerification`, `BatchCertificateGeneration` |
| `views_frontend.py` | 17 Django template-based views (dashboard, template CRUD, certificate CRUD, public verification, batch generation) |
| `views_api.py` | 4 DRF ViewSets with custom actions (verify, revoke, unrevoke, download, set_default, start_generation, progress) |
| `serializers.py` | 6 serializers: `CertificateTemplateSerializer`, `CertificateSerializer`, `CertificateVerificationSerializer`, `BatchCertificateGenerationSerializer`, `PublicCertificateVerificationSerializer`, `CertificateDownloadSerializer` |
| `permissions.py` | 5 DRF permission classes: `CanIssueCertificates`, `CanVerifyCertificates`, `CanRevokeCertificates`, `IsStudentOrStaffReadOnly`, `CanManageTemplates` |
| `forms.py` | 4 Django forms: `CertificateTemplateForm`, `CertificateForm`, `CertificateVerificationForm`, `BatchCertificateGenerationForm` |
| `admin.py` | 4 admin classes with custom actions, HTML progress bars, color-coded status indicators, and QR code previews |
| `tasks.py` | 5 Celery tasks: batch generation, notification, integrity verification, cleanup, expiry reminders |
| `urls.py` | URL routing split into `api_urlpatterns` (DRF router) and `frontend_urlpatterns` (path-based) |
| `apps.py` | `CertificatesConfig` -- no `ready()` method (no signals) |

---

## Technical Notes

- **No `signals.py`**: Unlike other apps, certificates has no signal handlers. Certificate number generation happens in `Certificate.save()` override. `apps.py` has no `ready()` method.
- **Certificate number format**: `CERT-{year}-{uuid4_hex[:8].upper()}` (e.g., `CERT-2024-A1B2C3D4`).
- **Hash determinism**: The hash is computed from `certificate_number + student.id + course.id + issue_date`, meaning the hash changes if any of these fields are modified after initial generation.
- **Batch generation student count mismatch**: The frontend `batch_generation_create` view counts `Student.objects.filter(program=batch.course.program)` (all students in the program), but the Celery task filters by `Result.objects.filter(course=course, grade__gte=passing_grade)` (only students who passed). These are different criteria and will produce different counts.
- **Celery task dispatch commented out**: In `batch_generation_start`, the `generate_batch_certificates.delay(batch.id)` call is commented out, meaning batch generation does not actually execute asynchronously yet.
- **`lecturer_required` import unused**: Imported in `views_frontend.py` but never applied to any view.
- **Template placeholders**: `body_template` supports `{student_name}`, `{course_name}`, `{date}`, `{grade}` but no rendering/substitution logic exists -- PDF generation is not yet implemented.
- **API vs frontend field name divergence**: The API `verify` action references `certificate.honors` (which does not exist on the current Certificate model), while the `download` action references `certificate.certificate_file` (the model uses `pdf_file`).

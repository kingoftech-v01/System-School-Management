# Admissions App

Student admission workflow management with application tracking, counseling, and payment verification.

## Description

The admissions app manages the complete student admission pipeline from application submission through counseling to final admission or rejection. It includes models for admission sessions, student applications, counseling comments, and admission payments. The app provides both public-facing views (application form, status check) and direction-level administrative views (application list, detail, counseling comments). Celery tasks handle email notifications, payment processing, counseling reminders, and archival of old applications.

## Main Features

- **Admission Sessions**: Create and manage admission periods with start/end dates and active status
- **Applications**: Multi-step application with personal, guardian, address, and academic info
- **Document Upload**: Transcript and birth certificate upload with file extension validation (pdf, jpg, jpeg, png)
- **Status Tracking**: Pipeline stages (pending, under_review, counseling, payment_pending, admitted, rejected)
- **Counseling**: Counselor assignment, comment tracking, and recommendation flagging
- **Payment Verification**: Track application fees with multiple payment methods (stripe, braintree, bank_transfer, cash)
- **Public Status Check**: Applicants can look up their application status by email
- **Email Notifications**: Automated confirmation, status update, and counseling reminder emails via Celery
- **Admin Actions**: Bulk approve, reject, and move-to-counseling actions in Django admin
- **Auto-Archival**: Scheduled task to detect stale applications from closed sessions

## User Roles

| Role | Permissions |
|------|------------|
| admin | Full access: manage sessions, review/approve/reject applications, assign counselors, verify payments, all admin actions |
| direction | Full access: manage sessions, review/approve/reject applications, assign counselors (via `@direction_only` decorator) |
| secretary | Same as direction: manage sessions, review applications, add counseling comments (via `@direction_only` decorator) |
| professor | May serve as counselor (assigned via `counselor` FK on AdmissionStudent) |
| student | No direct frontend access; public apply and status check views are unauthenticated |
| parent | No direct access |
| prefet | No direct access |
| accountant | No direct access |
| librarian | No direct access |
| registrar | No direct access (enrollment-focused; does not have `manage_admissions` permission) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| AdmissionSession | Admin panel | Frontend list, API list/detail | Admin panel | Admin panel |
| AdmissionStudent | Public form (frontend), API | Frontend list/detail (direction), API list/detail, public status check | API, Admin panel | API, Admin panel |
| CounselingComment | Frontend form (direction), Admin panel | Frontend detail (inline), Admin panel | Admin panel | Admin panel |
| AdmissionPayment | Admin panel | Frontend detail (inline), Admin panel | Admin panel (verify action) | Admin panel |

## Models

- `AdmissionSession` -- admission period with `name` (unique), `start_date`, `end_date`, `is_active`, `created_at`
- `AdmissionStudent` -- application with personal info, address, guardian info, academic info, `program` FK, `status`, `reviewed_by`/`counselor` FKs (User), document uploads (`transcript`, `birth_certificate`), payment flags, timestamps
- `CounselingComment` -- counselor feedback with `application` FK, `counselor` FK (User), `comment`, `is_recommendation`, `created_at`
- `AdmissionPayment` -- payment tracking with `application` OneToOne, `amount`, `transaction_id` (unique), `payment_method`, `verified`, `verified_by` FK (User), `verified_at`, `paid_at`

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/admissions/sessions/` | Public (AllowAny) | List active admission sessions |
| GET | `/api/v1/admissions/sessions/{id}/` | Public (AllowAny) | Retrieve a single session |
| GET | `/api/v1/admissions/applications/` | Authenticated | List all applications |
| POST | `/api/v1/admissions/applications/` | Authenticated | Create an application |
| GET | `/api/v1/admissions/applications/{id}/` | Authenticated | Retrieve application detail |
| PUT/PATCH | `/api/v1/admissions/applications/{id}/` | Authenticated | Update an application |
| DELETE | `/api/v1/admissions/applications/{id}/` | Authenticated | Delete an application |

**Note:** `AdmissionSessionViewSet` is `ReadOnlyModelViewSet` -- POST/PUT/DELETE return 405. `AdmissionStudentViewSet` is a full `ModelViewSet` with `IsAuthenticated` permission.

## Frontend URLs

| URL Pattern | View | Auth | Description |
|-------------|------|------|-------------|
| `/admissions/` | `admission_session_list` | `@login_required` | List active sessions |
| `/admissions/apply/` | `admission_apply` | Public | Application form (GET/POST) |
| `/admissions/status/` | `admission_status` | Public | Status check by email |
| `/admissions/applications/` | `admission_list` | `@direction_only` | Paginated application list with search/filter |
| `/admissions/applications/<pk>/` | `admission_detail` | `@direction_only` | Single application detail with comments and payment |
| `/admissions/comment/<student_id>/` | `counseling_comment_create` | `@direction_only` | Add counseling comment to application |

## Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `send_admission_confirmation_email` | On-demand | Email confirmation when application is submitted |
| `send_status_update_email` | On-demand | Email when application status changes |
| `process_admission_payments` | Daily at 1:00 AM | Check verified payments and auto-admit |
| `send_counseling_reminders` | Mon & Thu at 9:30 AM | Remind counselors of pending counseling applications |
| `auto_archive_old_applications` | Sunday at 3:30 AM | Log count of stale applications from closed sessions |

## Dependencies

- `course` (Program model for program selection via FK)
- `accounts` (User model for `reviewed_by`, `counselor`, `verified_by` FKs; `direction_only` decorator)
- `celery` (async tasks for email and payment processing)
- `rest_framework` (API ViewSets and serializers)

## URL Namespace

- Frontend: `frontend:admissions:<view_name>`
- API: `api:v1:admissions:<resource-name>`

## Configuration

- Celery beat schedules defined in `School_System/celery.py`
- Role permissions defined in `School_System/roles.py` (Direction, Secretary, Admin have `manage_admissions`)
- File uploads stored at `admissions/transcripts/%Y/%m/%d/` and `admissions/certificates/%Y/%m/%d/`
- Email sender hardcoded as `admissions@school.com` in tasks.py

## File Structure

```text
admissions/
  models.py              -- AdmissionSession, AdmissionStudent, CounselingComment, AdmissionPayment
  views_frontend.py      -- Template-based views (public + direction-only)
  views_api.py           -- DRF ViewSets (AdmissionSessionViewSet, AdmissionStudentViewSet)
  urls.py                -- Frontend + API URL routing with DefaultRouter
  serializers.py         -- DRF ModelSerializers (AdmissionSession, AdmissionStudent)
  forms.py               -- AdmissionApplicationForm, CounselingCommentForm, AdmissionStatusForm
  tasks.py               -- Celery tasks (email, payment processing, reminders, archival)
  admin.py               -- Admin config with inlines, fieldsets, and bulk actions
  apps.py                -- AppConfig
  tests/
    test_models.py       -- Model creation, defaults, constraints
    test_forms.py        -- Form validation (valid, invalid, missing fields)
    test_views_api.py    -- API endpoint access and permissions
    test_views_frontend.py -- Frontend view access and role restrictions
    test_tasks.py        -- Celery task unit tests
    test_admin.py        -- Admin registration, config, and actions
```

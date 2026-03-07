# Enrollment App

Multi-step student registration with document management, review workflow, account creation, and statistics.

## Description

The enrollment app handles the complete student enrollment lifecycle through two distinct registration flows: a 4-step public registration form (student info, parent info, academic info, additional info) and a 3-step parent-authenticated enrollment wizard (child info, academic info, additional info with relationship). Both flows use session-based state management. Upon approval, the app auto-creates Student and Parent user accounts with temporary passwords. The app includes document upload and verification, direction-side review and approval workflow with capacity checking, CSV export, and enrollment statistics with charts.

**Key design note**: When a registration is approved, the `_create_accounts_for_enrollment()` function in `views_frontend.py` automatically creates both a Student user account (with `accounts.Student` profile) and a Parent user account (with `accounts.Parent` profile), linking them together. The parent flow (`parent_enroll_*`) auto-populates parent fields from the logged-in parent user and skips parent account creation if the parent already exists.

## Main Features

- **Public Multi-Step Registration**: 4-step public form (student info, parent info, academic info, additional info) with rate limiting (10 POST/hour per IP)
- **Parent-Authenticated Enrollment**: 3-step wizard for logged-in parents to enroll their children, auto-populating parent info from their account
- **Document Upload**: Upload enrollment documents (PDF, JPG, PNG, DOC, DOCX; max 10MB frontend / 5MB API) with verification by direction staff
- **Registration Complete**: Confirmation page verified via cryptographic signed token (`django.core.signing.Signer`)
- **Enrollment List**: Direction-side paginated list (50 per page) with comprehensive filtering (name, email, status, type, year, filiere, date range)
- **Enrollment Detail**: Full registration details with documents and status history timeline
- **Enrollment Review**: Approve/reject registrations with notes, capacity checking against filiere limits, and auto-account creation on approval
- **Registration Edit**: Direction can edit all submitted registration fields (direction/registrar only)
- **Registration Delete**: Direction can delete registrations with GET confirmation page and POST to execute
- **Document Verification**: Verify uploaded documents with status tracking
- **Document Delete**: Direction can delete uploaded documents (POST-only, cleans up file from storage)
- **CSV Export**: Export filtered enrollment data to CSV with audit logging via `core.ActivityLog`
- **Enrollment Statistics**: Analytics with breakdowns by status, type, filiere, level, gender, and monthly trends (last 12 months)
- **Celery Tasks**: Email notifications (with retry), reminders for 7-day-old pending registrations, old rejected registration cleanup, report generation, auto-approval for complete registrations

## User Roles

The system has 10 roles. The enrollment app uses the following subset:

| Role | Frontend Permissions | Notes |
|------|----------------------|-------|
| registrar | List, detail, review, edit, delete, verify documents, delete documents, export, statistics | Primary enrollment manager role; uses `@registrar_only` decorator |
| secretary | List, detail, review, edit, delete, verify documents, delete documents, export, statistics | Included in `@registrar_only` (registrar, secretary, direction, admin) |
| direction | List, detail, review, edit, delete, verify documents, delete documents, export, statistics | Included in `@registrar_only`; also has API access via `IsDirectionUser` |
| admin | List, detail, review, edit, delete, verify documents, delete documents, export, statistics | Included in `@registrar_only`; full access; also has API access via `IsDirectionUser` |
| parent | 3-step parent enrollment wizard (enroll own children) | Uses `@parent_only` decorator; auto-populates parent fields from logged-in user |
| student | No frontend enrollment access | Can view own registration via API (filtered by `enrolled_user` or `email`) |
| professor | No enrollment access | Not applicable |
| prefet | No enrollment access | Not applicable |
| accountant | No enrollment access | Not applicable |
| librarian | No enrollment access | Not applicable |
| public (unauthenticated) | Register (4-step form), upload documents, view completion page | Rate-limited; no login required |

## CRUD Summary

| Entity | Create | Read | Update | Delete | Who |
|--------|--------|------|--------|--------|-----|
| RegistrationForm | 4-step public form / 3-step parent form / API POST | List + detail + API | Review + edit + API PATCH | `registration_delete` + API DELETE | Public (create), registrar/secretary/direction/admin (manage) |
| EnrollmentDocument | Upload form / API POST | Via detail + API | Verify (is_verified toggle) + API | `document_delete` (POST-only) + API DELETE | Public (upload), registrar/secretary/direction/admin (verify/delete) |
| EnrollmentStatusHistory | Automatic (on review/admin save) | Via detail + API (read-only) | N/A | N/A | System-created |

## Models

- **`RegistrationForm`** -- Tenant FK (`core.School`), student fields (`student_first_name`, `student_middle_name`, `student_last_name`, `date_of_birth`, `gender`, `nationality`), contact (`email`, `phone`), address (`street_address`, `city`, `province`, `country`, `postal_code`), parent fields (`parent_first_name`, `parent_middle_name`, `parent_last_name`, `parent_email`, `parent_phone`, `parent_relationship`), academic (`filiere` FK, `academic_year`, `level`, `previous_school`, `enrollment_type`), review (`status`, `reviewed_by` FK, `reviewed_at`, `review_notes`, `rejection_reason`), additional (`special_needs`, `medical_information`), links (`enrolled_user` OneToOne FK, `parent_user` FK), timestamps (`submitted_at`, `updated_at`). Properties: `student_full_name`, `parent_full_name`, `full_address`. Methods: `can_enroll()`, `get_completion_percentage()`. Indexes: `[tenant, status]`, `[academic_year, filiere]`, `[submitted_at]`.

- **`EnrollmentDocument`** -- `registration` FK (cascade), `document_type` (choices: birth_certificate, photo, transcript, transfer_letter, medical_certificate, id_card, parent_id, other), `file` (FileField, upload to `enrollment_docs/%Y/%m/%d/`, validators for pdf/jpg/jpeg/png/doc/docx), `description`, `uploaded_at`, `is_verified`, `verified_by` FK. Methods: `get_file_size()`.

- **`EnrollmentStatusHistory`** -- `registration` FK (cascade), `old_status`, `new_status`, `changed_by` FK, `notes`, `changed_at`. Read-only audit trail of all status transitions.

## URL Namespaces

- Frontend: `frontend:enrollment:<view_name>`
- API: `api:enrollment:<resource-name>` (via DRF DefaultRouter)

### Frontend Routes

| URL Pattern | View | Name | Auth |
|-------------|------|------|------|
| `register/step1/` | `register_step1` | `register_step1` | Public |
| `register/step2/` | `register_step2` | `register_step2` | Public (session) |
| `register/step3/` | `register_step3` | `register_step3` | Public (session) |
| `register/step4/` | `register_step4` | `register_step4` | Public (session) |
| `register/complete/<signed_id>/` | `register_complete` | `register_complete` | Public (signed) |
| `register/<registration_id>/upload/` | `upload_document` | `upload_document` | Public |
| `parent/enroll/step1/` | `parent_enroll_step1` | `parent_enroll_step1` | `@parent_only` |
| `parent/enroll/step2/` | `parent_enroll_step2` | `parent_enroll_step2` | `@parent_only` |
| `parent/enroll/step3/` | `parent_enroll_step3` | `parent_enroll_step3` | `@parent_only` |
| `list/` | `enrollment_list` | `enrollment_list` | `@registrar_only` |
| `detail/<registration_id>/` | `enrollment_detail` | `enrollment_detail` | `@registrar_only` |
| `review/<registration_id>/` | `enrollment_review` | `enrollment_review` | `@registrar_only` |
| `edit/<registration_id>/` | `registration_edit` | `registration_edit` | `@registrar_only` |
| `delete/<registration_id>/` | `registration_delete` | `registration_delete` | `@registrar_only` |
| `document/<document_id>/verify/` | `verify_document` | `verify_document` | `@registrar_only` |
| `document/<document_id>/delete/` | `document_delete` | `document_delete` | `@registrar_only` |
| `export/csv/` | `export_enrollments_csv` | `export_enrollments_csv` | `@registrar_only` |
| `statistics/` | `enrollment_statistics` | `enrollment_statistics` | `@registrar_only` |

### API Endpoints

| Prefix | ViewSet | Permissions | Extra Actions |
|--------|---------|-------------|---------------|
| `registrations/` | `RegistrationFormViewSet` | Create: AllowAny; List/Retrieve: IsAuthenticated; Review/Update/Delete: IsAuthenticated + IsDirectionUser | `POST /<pk>/review/`, `GET /pending/`, `GET /statistics/` |
| `documents/` | `EnrollmentDocumentViewSet` | Default: IsAuthenticated; Verify/Delete: IsAuthenticated + IsDirectionUser | `POST /<pk>/verify/` |
| `history/` | `EnrollmentStatusHistoryViewSet` (read-only) | IsAuthenticated | None |

**API Filtering**:
- Registrations: filter by `status`, `enrollment_type`, `filiere`, `academic_year`; search by `student_name`, `email`, `parent_name`; order by `created_at`, `student_name`
- Documents: filter by `registration`, `document_type`, `is_verified`; order by `uploaded_at`
- History: filter by `registration`; order by `changed_at`

## Configuration

| Setting | Purpose | Default |
|---------|---------|---------|
| `DEFAULT_FROM_EMAIL` | Sender address for enrollment notification emails | From `settings.py` |
| `CELERY_BROKER_URL` | Message broker for async email tasks | Required for email notifications |
| `MEDIA_ROOT` / `MEDIA_URL` | Storage path for uploaded enrollment documents | `enrollment_docs/%Y/%m/%d/` |

### Rate Limits

| View | Rate | Key |
|------|------|-----|
| Public registration steps (1-4) | 10 POST/hour | IP address |
| Parent enrollment steps (1-3) | 10 POST/hour | User |
| Document upload | 20 POST/hour | IP address |
| Enrollment list, detail, statistics | 50-100/hour | User |
| Review, verify, edit | 50 POST/hour | User |
| CSV export | 20/hour | User |

## Dependencies

- **`accounts`** -- User model (for `reviewed_by`, `enrolled_user`, `parent_user` FKs), `Student` and `Parent` profile models (auto-created on approval), role decorators (`@registrar_only`, `@parent_only`, `@tenant_required`), `IsDirectionUser` DRF permission class
- **`core`** -- `School` model (tenant FK), `ActivityLog` model (CSV export audit logging)
- **`filieres`** -- `Filiere` model (program FK, filtered by tenant in forms)
- **`course`** -- `Program` model (matched from filiere name during account creation)
- **`allauth`** -- `EmailAddress` model (created for student/parent accounts if allauth is installed)
- **`django-ratelimit`** -- Rate limiting on all public and authenticated views
- **`celery`** -- 5 async tasks (email notifications, reminders, cleanup, report generation, auto-approval)
- **`djangorestframework`** -- API ViewSets, serializers, permissions
- **`django-filter`** -- `DjangoFilterBackend` for API filtering

## File Structure

```
enrollment/
    __init__.py              # App default config reference
    apps.py                  # EnrollmentConfig (imports signals in ready())
    models.py                # 3 models (RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory)
    views_frontend.py        # 18 template-based views (public registration, parent enrollment, direction management)
    views_api.py             # 3 DRF ViewSets with custom actions (review, pending, statistics, verify)
    serializers.py           # 8 DRF serializers (full, list, create, review, document, upload, verify, history)
    forms.py                 # 9 Django forms (4 step forms, edit, upload, review, verify, search)
    signals.py               # 3 signal handlers (status tracking, document upload notification, status notification)
    tasks.py                 # 5 Celery tasks (email, reminders, cleanup, reports, auto-approval)
    urls.py                  # Frontend + API URL routing with DRF DefaultRouter
    admin.py                 # Admin for all 3 models with inlines, bulk actions, colored status, completion badge
    migrations/
        __init__.py
        0001_initial.py
        0002_remove_registrationform_address_and_more.py
        0003_registrationform_parent_user.py
    tests/
        __init__.py
        test_models.py       # 12 model tests (RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory)
        test_forms.py        # 8 form tests (steps 1-4, review form validation)
        test_serializers.py  # 5 serializer tests (create, review, history)
        test_views_frontend.py  # 37 frontend view tests (all 18 views with auth/permission checks)
        test_views_api.py    # 26 API tests (CRUD, review, pending, statistics, permissions)
        test_signals.py      # 11 signal tests (status tracking, document upload, notification)
        test_tasks.py        # 4 task tests (report generation, cleanup)
        test_admin.py        # 19 admin tests (registration, config, actions, queryset)
```

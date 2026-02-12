# Enrollment App Architecture

## Overview

The enrollment app manages the full lifecycle of student registration applications,
from public submission through administrative review to automatic account creation.
It supports two intake paths: a 4-step public wizard (unauthenticated) and a 3-step
parent dashboard wizard (authenticated). All administrative views are gated behind
the `registrar_only` decorator, which permits the `registrar`, `secretary`,
`direction`, and `admin` roles.

The app exposes two interfaces: 18 template-based frontend views and a REST API via
Django REST Framework (3 ViewSets with custom actions). Both share the same models
and database tables.

---

## Directory Structure

```
enrollment/
    __init__.py
    apps.py                  # EnrollmentConfig (imports signals in ready())
    models.py                # 3 models: RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
    views_frontend.py        # 18 template-based views
    views_api.py             # 3 DRF ViewSets with custom actions
    serializers.py           # 8 DRF serializers
    forms.py                 # 9 Django forms
    signals.py               # 3 signal handlers
    tasks.py                 # 5 Celery tasks
    urls.py                  # Frontend + API URL routing
    admin.py                 # Admin for all 3 models with inlines and bulk actions
    migrations/
    tests/
```

---

## Model Relationships

### Entity-Relationship Diagram

```
core.School (tenant)                 accounts.User (AUTH_USER_MODEL)
    |                                    |         |         |
    | 1:N (tenant)                       | O2O     | 1:N     | 1:N
    v                                    |         |         |
 RegistrationForm ---OneToOne-----------+   (enrolled_user)
    |            ---FK-----------------+   (reviewed_by)
    |            ---FK-----------------+   (parent_user)
    |
    |---FK---> filieres.Filiere (program selection)
    |
    | 1:N (registration)         1:N (registration)
    v                            v
EnrollmentDocument         EnrollmentStatusHistory
    |                            |
    | FK (verified_by)           | FK (changed_by)
    v                            v
accounts.User                accounts.User

--- On Approval (auto-created via _create_accounts_for_enrollment) ---

 RegistrationForm
    |
    +---> accounts.User (role='student', is_student=True)
    |         |
    |         +---> accounts.Student (profile, with course.Program FK)
    |         +---> allauth.EmailAddress (if allauth installed)
    |
    +---> accounts.User (role='parent', is_parent=True)
    |         |
    |         +---> accounts.Parent (profile, linked to Student)
    |         +---> allauth.EmailAddress (if allauth installed)
    |
    +---> course.Program (matched from filiere.name via icontains, nullable)
```

### RegistrationForm Field Reference

| Field Group          | Fields                                                                                                    |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| Tenant               | `tenant` FK -> core.School (CASCADE)                                                                      |
| Student Info         | `student_first_name`, `student_middle_name` (opt), `student_last_name`, `date_of_birth`, `gender` (M/F), `nationality` |
| Contact              | `email`, `phone`                                                                                          |
| Address              | `street_address`, `city`, `province`, `country`, `postal_code` (opt)                                      |
| Parent/Guardian      | `parent_first_name`, `parent_middle_name` (opt), `parent_last_name`, `parent_email`, `parent_phone`, `parent_relationship` (default: 'father') |
| Academic             | `filiere` FK -> filieres.Filiere (SET_NULL), `academic_year`, `level` (Bachelor/Master), `previous_school` (opt), `enrollment_type` (new/transfer/re_enrollment) |
| Review               | `status` (pending/under_review/approved/rejected/enrolled), `reviewed_by` FK -> User (SET_NULL), `reviewed_at`, `review_notes`, `rejection_reason` |
| Additional           | `special_needs`, `medical_information`                                                                    |
| Linked Accounts      | `enrolled_user` OneToOne -> User (SET_NULL), `parent_user` FK -> User (SET_NULL)                          |
| Timestamps           | `submitted_at` (auto_now_add), `updated_at` (auto_now)                                                   |

Properties: `student_full_name`, `parent_full_name`, `full_address`
Methods: `can_enroll()` (status=='approved' and no enrolled_user), `get_completion_percentage()` (15 required fields, returns 0-100)
Save override: sets `reviewed_at = timezone.now()` when status changes to 'approved' or 'rejected'

### EnrollmentDocument Field Reference

| Field            | Type/Detail                                                                                |
|------------------|--------------------------------------------------------------------------------------------|
| `registration`   | FK -> RegistrationForm (CASCADE)                                                           |
| `document_type`  | CharField choices: birth_certificate, photo, transcript, transfer_letter, medical_certificate, id_card, parent_id, other |
| `file`           | FileField, upload_to `enrollment_docs/%Y/%m/%d/`, extensions: pdf/jpg/jpeg/png/doc/docx    |
| `description`    | CharField (optional)                                                                       |
| `is_verified`    | BooleanField (default False)                                                               |
| `verified_by`    | FK -> User (SET_NULL)                                                                      |
| `uploaded_at`    | DateTimeField (auto_now_add)                                                               |

### EnrollmentStatusHistory Field Reference

| Field            | Type/Detail                                  |
|------------------|----------------------------------------------|
| `registration`   | FK -> RegistrationForm (CASCADE)             |
| `old_status`     | CharField                                    |
| `new_status`     | CharField                                    |
| `changed_by`     | FK -> User (SET_NULL)                        |
| `notes`          | TextField                                    |
| `changed_at`     | DateTimeField (auto_now_add)                 |

### Cross-App Foreign Key Summary

```
enrollment.RegistrationForm
  +-- tenant           -> core.School          (CASCADE)
  +-- filiere           -> filieres.Filiere     (SET_NULL)
  +-- reviewed_by       -> accounts.User        (SET_NULL)
  +-- enrolled_user     -> accounts.User        (SET_NULL, OneToOne)
  +-- parent_user       -> accounts.User        (SET_NULL)

enrollment.EnrollmentDocument
  +-- registration      -> RegistrationForm     (CASCADE)
  +-- verified_by       -> accounts.User        (SET_NULL)

enrollment.EnrollmentStatusHistory
  +-- registration      -> RegistrationForm     (CASCADE)
  +-- changed_by        -> accounts.User        (SET_NULL)
```

### Database Indexes (defined in Meta)

| Model              | Index Fields                     |
|--------------------|----------------------------------|
| RegistrationForm   | `(tenant, status)`               |
| RegistrationForm   | `(academic_year, filiere)`       |
| RegistrationForm   | `(submitted_at,)`                |

---

## View Access Patterns Per Role

### Frontend Views (`views_frontend.py`)

| View                      | URL Pattern                                | Auth     | Decorator Stack                                     |
|---------------------------|--------------------------------------------|----------|------------------------------------------------------|
| `register_step1`          | `register/step1/`                          | Public   | `@ratelimit(key='ip', rate='10/h', method='POST')`  |
| `register_step2`          | `register/step2/`                          | Public   | `@ratelimit(key='ip', rate='10/h', method='POST')`  |
| `register_step3`          | `register/step3/`                          | Public   | `@ratelimit(key='ip', rate='10/h', method='POST')`  |
| `register_step4`          | `register/step4/`                          | Public   | `@ratelimit(key='ip', rate='10/h', method='POST')`  |
| `register_complete`       | `register/complete/<signed_id>/`           | Public   | None (signed token verification)                     |
| `upload_document`         | `register/<id>/upload/`                    | Public   | `@ratelimit(key='ip', rate='20/h', method='POST')`  |
| `parent_enroll_step1`     | `parent/enroll/step1/`                     | Login    | `@login_required @parent_only @ratelimit(key='user', rate='10/h')` |
| `parent_enroll_step2`     | `parent/enroll/step2/`                     | Login    | `@login_required @parent_only @ratelimit(key='user', rate='10/h')` |
| `parent_enroll_step3`     | `parent/enroll/step3/`                     | Login    | `@login_required @parent_only @ratelimit(key='user', rate='10/h')` |
| `enrollment_list`         | `list/`                                    | Login    | `@login_required @registrar_only @tenant_required @ratelimit(100/h)` |
| `enrollment_detail`       | `detail/<id>/`                             | Login    | `@login_required @registrar_only @tenant_required @ratelimit(100/h)` |
| `enrollment_review`       | `review/<id>/`                             | Login    | `@login_required @registrar_only @tenant_required @ratelimit(50/h)` |
| `enrollment_statistics`   | `statistics/`                              | Login    | `@login_required @registrar_only @tenant_required @ratelimit(50/h)` |
| `registration_edit`       | `edit/<id>/`                               | Login    | `@login_required @registrar_only @tenant_required @ratelimit(50/h)` |
| `registration_delete`     | `delete/<id>/`                             | Login    | `@login_required @registrar_only @tenant_required`   |
| `verify_document`         | `document/<id>/verify/`                    | Login    | `@login_required @registrar_only @tenant_required @ratelimit(50/h)` |
| `document_delete`         | `document/<id>/delete/`                    | Login    | `@login_required @registrar_only @tenant_required`   |
| `export_enrollments_csv`  | `export/csv/`                              | Login    | `@login_required @registrar_only @tenant_required @ratelimit(20/h)` |

### API Views (`views_api.py`)

| ViewSet / Action                        | Method | Auth         | Permission Classes                                |
|-----------------------------------------|--------|--------------|---------------------------------------------------|
| `RegistrationFormViewSet.create`        | POST   | AllowAny     | Public (anyone can submit)                        |
| `RegistrationFormViewSet.list`          | GET    | Authenticated| direction/admin/secretary see all; others own only|
| `RegistrationFormViewSet.retrieve`      | GET    | Authenticated| direction/admin/secretary see all; others own only|
| `RegistrationFormViewSet.update`        | PUT    | Authenticated| IsDirectionUser (direction, admin, secretary)     |
| `RegistrationFormViewSet.partial_update`| PATCH  | Authenticated| IsDirectionUser                                   |
| `RegistrationFormViewSet.destroy`       | DELETE | Authenticated| IsDirectionUser                                   |
| `RegistrationFormViewSet.review`        | POST   | Authenticated| IsDirectionUser (custom @action)                  |
| `RegistrationFormViewSet.pending`       | GET    | Authenticated| IsDirectionUser (custom @action)                  |
| `RegistrationFormViewSet.statistics`    | GET    | Authenticated| IsDirectionUser (custom @action)                  |
| `EnrollmentDocumentViewSet.*`           | ALL    | Authenticated| General access; verify/destroy require IsDirectionUser |
| `EnrollmentDocumentViewSet.verify`      | POST   | Authenticated| IsDirectionUser                                   |
| `EnrollmentStatusHistoryViewSet.*`      | GET    | Authenticated| Read-only; scoped by role in get_queryset          |

### Role Access Summary Matrix

```
                    Submit  Submit                         Verify
Role         Public  Parent  View Own  List  Review  Edit  Delete  Export  Stats  Docs
-----------  ------  ------  --------  ----  ------  ----  ------  ------  -----  ----
Anonymous      Y       -       -        -      -      -      -       -       -      -
student        Y       -      API       -      -      -      -       -       -      -
professor      -       -       -        -      -      -      -       -       -      -
parent         Y       Y      API       -      -      -      -       -       -      -
prefet         -       -       -        -      -      -      -       -       -      -
accountant     -       -       -        -      -      -      -       -       -      -
librarian      -       -       -        -      -      -      -       -       -      -
registrar      -       -       Y        Y      Y      Y      Y       Y       Y      Y
secretary      -       -       Y        Y      Y      Y      Y       Y       Y      Y
direction      -       -       Y        Y      Y      Y      Y       Y       Y      Y
admin          -       -       Y        Y      Y      Y      Y       Y       Y      Y
superuser      *       *       *        *      *      *      *       *       *      *
```

Notes:
- `superuser` bypasses all role checks via the `role_required` decorator.
- `registrar_only` expands to `role_required('registrar', 'secretary', 'direction', 'admin')`.
- `parent_only` expands to `role_required('parent')`.
- The API `IsDirectionUser` permission checks for `secretary`, `direction`, `admin` plus
  `is_staff`/`is_superuser`. Note: it does NOT include `registrar`, so registrar users
  have full frontend access but are blocked from API write endpoints.
- Students/parents can view their own registration via the API only
  (filtered by `enrolled_user` or `email`).

---

## Business Logic Workflows

### 1. Enrollment Lifecycle (Status State Machine)

```
                       +-------------------+
                       |     (submitted)   |
                       |     pending       |
                       +--------+----------+
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
          +-----------------+     +-----------------+
          |  under_review   |     |    rejected     |
          +--------+--------+     +-----------------+
                   |                       ^
                   |                       |
          +--------v--------+              |
          |    approved     +--------------+
          +--------+--------+  (can reject
                   |            after review)
                   |
                   v
          +-----------------+
          |    enrolled     |
          +-----------------+
```

Valid transitions enforced by `RegistrationReviewSerializer.validate_status()`:
- allowed target statuses: `under_review`, `approved`, `rejected`, `enrolled`
- If target is `rejected`, `rejection_reason` is required (enforced in both serializer and form)

Key side effects per transition:
- **-> approved**: capacity check against `filiere.capacity`, then `_create_accounts_for_enrollment()`
- **-> rejected**: `rejection_reason` required
- **Any change**: `EnrollmentStatusHistory` record created, email dispatched via Celery

### 2. Public Registration Flow (4-Step Wizard)

```
  [Anonymous User]
        |
        v
  Step 1: register_step1()
  Form: RegistrationFormStep1
  Fields: student_first_name, student_middle_name, student_last_name,
          date_of_birth, gender, nationality, email, phone,
          street_address, city, province, country, postal_code
  Validation: age >= 5, email not in approved/enrolled registrations
  Action: Creates RegistrationForm row, stores ID in session['registration_id']
        |
        v
  Step 2: register_step2()
  Form: RegistrationFormStep2
  Fields: parent_first_name, parent_middle_name, parent_last_name,
          parent_email, parent_phone, parent_relationship
  Guard: session['registration_id'] must exist (redirects to step1 if missing)
  Action: Updates existing RegistrationForm
        |
        v
  Step 3: register_step3()
  Form: RegistrationFormStep3
  Fields: enrollment_type, filiere (queryset filtered by tenant),
          academic_year, level, previous_school
  Action: Updates RegistrationForm
        |
        v
  Step 4: register_step4()
  Form: RegistrationFormStep4
  Fields: special_needs, medical_information
  Action: Saves form, deletes session['registration_id'],
          dispatches send_enrollment_status_email.delay(id, 'submitted'),
          creates signed token via Signer, redirects to register_complete
        |
        v
  register_complete(signed_id)
  Guard: Signer.unsign() validates the token (redirects on BadSignature)
  Display: Confirmation page with registration details
```

### 3. Parent Dashboard Enrollment Flow (3-Step Wizard)

```
  [Authenticated Parent - @login_required @parent_only]
        |
        v
  Step 1: parent_enroll_step1()
  Form: RegistrationFormStep1 (child's personal info only)
  Auto-populated from request.user:
    parent_first_name  = user.first_name
    parent_middle_name = user.middle_name (or '')
    parent_last_name   = user.last_name
    parent_email       = user.email
    parent_phone       = user.phone (or '')
    parent_user        = request.user   <-- links parent account
  Action: Creates RegistrationForm, stores session['parent_enrollment_id']
        |
        v
  Step 2: parent_enroll_step2()
  Form: RegistrationFormStep3 (academic info -- skips parent info step)
  Guard: session['parent_enrollment_id'] + registration.parent_user == request.user
  Fields: enrollment_type, filiere, academic_year, level, previous_school
        |
        v
  Step 3: parent_enroll_step3()
  Form: RegistrationFormStep4 + parent_relationship from POST body
  Fields: special_needs, medical_information, parent_relationship
  Action: Saves, clears session, dispatches email, redirects to register_complete
```

### 4. Review and Approval Workflow

```
  [Registrar/Secretary/Direction/Admin]
        |
        v
  enrollment_list() ----- filtered by request.tenant
        |                  filters: student_name, email, status,
        |                  enrollment_type, academic_year, filiere,
        |                  date_from, date_to
        |                  pagination: 50 per page
        |                  stats: counts by status
        |
        v
  enrollment_detail(registration_id) ----- shows full info,
        |                                   documents list,
        |                                   status history
        |
        +----> enrollment_review(registration_id)
        |        |
        |        | POST: RegistrationReviewForm (status, review_notes, rejection_reason)
        |        |
        |        +-- Set reviewed_by = request.user, reviewed_at = now()
        |        +-- Save RegistrationForm
        |        +-- Create EnrollmentStatusHistory record
        |        |
        |        +-- If status changed to 'approved':
        |        |     +-- Capacity check:
        |        |     |     Count RegistrationForm where filiere=same,
        |        |     |     academic_year=same, status in ('approved','enrolled'),
        |        |     |     excluding current record.
        |        |     |     If count >= filiere.capacity: revert status, show error
        |        |     |
        |        |     +-- _create_accounts_for_enrollment(registration, tenant):
        |        |           WITHIN transaction.atomic():
        |        |           |
        |        |           +-- Create User (role='student')
        |        |           |     username: student_{first_name}[_N]
        |        |           |     must_change_password = True
        |        |           |
        |        |           +-- Match course.Program from filiere.name (icontains)
        |        |           +-- Create accounts.Student(student=user, level, program)
        |        |           +-- Set registration.enrolled_user = student_user
        |        |           +-- Create allauth.EmailAddress (verified, primary)
        |        |           |
        |        |           +-- If registration.parent_user exists:
        |        |           |     Reuse existing parent User account
        |        |           |     Update or create accounts.Parent profile
        |        |           +-- Else:
        |        |           |     Create new User (role='parent')
        |        |           |     Create accounts.Parent profile
        |        |           |
        |        |           +-- Return (student_user, parent_user)
        |        |
        |        +-- If status changed to 'rejected':
        |        |     rejection_reason required (form validation)
        |        |
        |        +-- Dispatch send_enrollment_status_email.delay(id, status)
        |        +-- Redirect to enrollment_detail
        |
        +----> registration_edit(registration_id)
        |        Full edit form (RegistrationEditForm) for all fields
        |        including status, review_notes, rejection_reason
        |
        +----> registration_delete(registration_id)
        |        GET: confirmation page
        |        POST: delete record, redirect to list
        |
        +----> verify_document(document_id)   [POST only]
        |        Form: DocumentVerificationForm (is_verified checkbox)
        |        Sets verified_by = request.user
        |
        +----> document_delete(document_id)    [POST only]
                 Deletes physical file and DB record
```

### 5. Account Creation Detail

```
_create_accounts_for_enrollment(registration, tenant)
    |
    | transaction.atomic()
    |
    +-- Extract student name from registration fields
    +-- Generate unique username: "student_{first_name.lower()}" + counter if needed
    +-- Generate temp password: 10 chars from [ascii_letters + digits + !@#$%]
    +-- User.objects.create_user(
    |       username, email, password, first_name, last_name,
    |       phone, gender, date_of_birth,
    |       is_student=True, role='student', tenant=tenant,
    |       must_change_password=True
    |   )
    +-- Program.objects.filter(title__icontains=filiere.name).first()
    +-- Student.objects.create(student=user, level=reg.level, program=program)
    +-- registration.enrolled_user = student_user
    +-- registration.save(update_fields=['enrolled_user'])
    +-- EmailAddress.get_or_create(user=student_user, email, verified=True, primary=True)
    |
    +-- If registration.parent_user is set (dashboard flow):
    |       parent_user = registration.parent_user  (reuse existing)
    |       Look for placeholder Parent (student__isnull=True), update it
    |       Or create new Parent for additional child
    |
    +-- If registration.parent_user is None (public flow):
    |       Generate unique username: "parent_{first_name.lower()}" + counter
    |       Generate temp password
    |       User.objects.create_user(
    |           is_parent=True, role='parent', tenant=tenant,
    |           must_change_password=True
    |       )
    |       EmailAddress.get_or_create(...)
    |       Parent.objects.create(user, student, first/last/phone/email, relation_ship)
    |
    +-- Return (student_user, parent_user)
```

---

## Dependencies

### Outgoing Dependencies (enrollment imports from)

```
enrollment
  |
  +-- core
  |     +-- core.models.School          (tenant FK on RegistrationForm)
  |     +-- core.models.ActivityLog     (CSV export audit logging)
  |
  +-- accounts
  |     +-- accounts.models.User        (reviewed_by, enrolled_user, parent_user FKs)
  |     +-- accounts.models.Student     (created during enrollment approval)
  |     +-- accounts.models.Parent      (created during enrollment approval)
  |     +-- accounts.decorators         (registrar_only, tenant_required,
  |     |                                role_required, parent_only)
  |     +-- accounts.permissions        (IsDirectionUser for API views)
  |
  +-- filieres
  |     +-- filieres.models.Filiere     (filiere FK, capacity check, tenant filtering in forms)
  |
  +-- course
  |     +-- course.models.Program       (Student profile creation,
  |                                      matched via filiere name icontains)
  |
  +-- allauth
  |     +-- allauth.account.models.EmailAddress
  |                                     (verified email creation, optional with ImportError catch)
  |
  +-- Third-party
        +-- django_ratelimit            (rate limiting on all views)
        +-- rest_framework              (API viewsets, serializers, permissions)
        +-- django_filters              (DjangoFilterBackend for API)
        +-- celery                      (shared_task for async emails and scheduled tasks)
```

### Incoming Dependencies (apps that import from enrollment)

No other apps in the project directly import from or depend on the enrollment app.
It is a leaf node in the dependency graph. It creates `accounts.User`,
`accounts.Student`, and `accounts.Parent` records, but no other app queries
`enrollment.*` models.

### Dependency Diagram

```
  +----------+     +----------+     +-----------+     +---------+
  |  core    |     | accounts |     | filieres  |     | course  |
  | (School, |     | (User,   |     | (Filiere) |     |(Program)|
  |  ActLog) |     |  Student,|     +-----------+     +---------+
  +----^-----+     |  Parent) |          ^                 ^
       |           +----^-----+          |                 |
       |                |                |                 |
       +------+---------+------+---------+-----------------+
              |                |
        +-----+----------------+-----+
        |       enrollment           |
        |  (RegistrationForm,        |
        |   EnrollmentDocument,      |
        |   EnrollmentStatusHistory) |
        +----------------------------+
              |           |
              v           v
        +---------+  +---------+
        | celery  |  | allauth |
        +---------+  +---------+
```

---

## Data Flow Diagrams

### 1. Public Registration Data Flow

```
  Browser (Anonymous)                    Django Server                     Database
  ===================                    =============                     ========

  POST /register/step1/ -------->  register_step1()
    form data: student_*,              +-- RegistrationFormStep1.is_valid()
    dob, gender, email,                |     clean_date_of_birth(): age >= 5
    phone, address                     |     clean_email(): no dup in approved/enrolled
                                       +-- form.save(commit=False)
                                       |     set tenant from request.tenant
                                       +-- form.save() --------------------> INSERT RegistrationForm
                                       +-- session['registration_id'] = id
  <-------- redirect step2 --------+

  POST /register/step2/ -------->  register_step2()
    form data: parent_*               +-- GET registration from session
                                       +-- RegistrationFormStep2.is_valid()
                                       +-- form.save() --------------------> UPDATE RegistrationForm
  <-------- redirect step3 --------+

  POST /register/step3/ -------->  register_step3()
    form data: filiere,                +-- RegistrationFormStep3.is_valid()
    academic_year, level               |     filiere queryset filtered by tenant
                                       +-- form.save() --------------------> UPDATE RegistrationForm
  <-------- redirect step4 --------+

  POST /register/step4/ -------->  register_step4()
    form data: special_needs,          +-- RegistrationFormStep4.is_valid()
    medical_information                +-- form.save() --------------------> UPDATE RegistrationForm
                                       +-- del session['registration_id']
                                       +-- send_enrollment_status_email
                                       |     .delay(id, 'submitted') ------> Celery queue
                                       +-- Signer.sign(id) -> signed_id
  <-- redirect register_complete ---+

  GET /register/complete/<sig> --> register_complete()
                                       +-- Signer.unsign(signed_id)
  <-------- render confirmation ----+
```

### 2. Parent Dashboard Enrollment Data Flow

```
  Browser (Authenticated Parent)         Django Server                     Database
  ==============================         =============                     ========

  POST /parent/enroll/step1/ ---->  parent_enroll_step1()
    form data: child personal           +-- @login_required @parent_only
    info (Step1 fields)                 +-- Auto-fill parent_* from request.user
                                        +-- Set parent_user = request.user
                                        +-- form.save() -------------------> INSERT RegistrationForm
                                        +-- session['parent_enrollment_id']
  <-------- redirect step2 ---------+

  POST /parent/enroll/step2/ ---->  parent_enroll_step2()
    form data: academic info            +-- Verify parent_user == request.user
                                        +-- form.save() -------------------> UPDATE RegistrationForm
  <-------- redirect step3 ---------+

  POST /parent/enroll/step3/ ---->  parent_enroll_step3()
    form data: additional info,         +-- form.save(commit=False)
    parent_relationship                 +-- reg.parent_relationship = POST value
                                        +-- reg.save() --------------------> UPDATE RegistrationForm
                                        +-- send_enrollment_status_email
                                        |     .delay(id, 'submitted') -----> Celery queue
  <-- redirect register_complete ---+
```

### 3. Review and Account Creation Data Flow

```
  Browser (Registrar/Admin)              Django Server                     Database
  =========================              =============                     ========

  GET /enrollment/list/ ---------->  enrollment_list()
                                        +-- Filter by tenant
                                        +-- EnrollmentSearchForm filters
                                        +-- Compute stats (counts by status)
                                        +-- Paginate (50 per page) -------> SELECT with filters
  <-------- render list page -------+

  POST /enrollment/review/<id>/ -->  enrollment_review()
    form data: status,                  +-- RegistrationReviewForm.is_valid()
    review_notes,                       +-- Set reviewed_by, reviewed_at
    rejection_reason                    +-- form.save() -------------------> UPDATE RegistrationForm
                                        +-- EnrollmentStatusHistory -------> INSERT history record
                                        |
                                        +-- If approved:
                                        |     +-- Capacity check ----------> SELECT COUNT(filiere,year)
                                        |     +-- If under capacity:
                                        |     |   _create_accounts_for_enrollment()
                                        |     |     +-- transaction.atomic:
                                        |     |     +-- User.create_user ---> INSERT User (student)
                                        |     |     +-- Student.create -----> INSERT Student
                                        |     |     +-- EmailAddress -------> INSERT EmailAddress
                                        |     |     +-- Parent account -----> INSERT/UPDATE User+Parent
                                        |     |     +-- registration.save --> UPDATE enrolled_user FK
                                        |     +-- If at capacity:
                                        |           Revert status ----------> UPDATE RegistrationForm
                                        |
                                        +-- send_enrollment_status_email
                                              .delay(id, status) ----------> Celery queue
  <-------- redirect to detail -----+
```

### 4. CSV Export Data Flow

```
  Browser (Registrar/Admin)              Django Server                     Database
  =========================              =============                     ========

  GET /enrollment/export/csv/ ---->  export_enrollments_csv()
    query params: same as list          +-- Filter by tenant
                                        +-- Apply EnrollmentSearchForm filters
                                        +-- Build CSV writer response:
                                        |     25 columns per row:
                                        |     First/Middle/Last Name, Email,
                                        |     Phone, Gender, DOB,
                                        |     Street/City/Province/Country/Postal,
                                        |     Parent First/Middle/Last/Email/Phone,
                                        |     Filiere, Year, Level, Type,
                                        |     Status, Submitted At,
                                        |     Reviewed By, Reviewed At
                                        |
                                        +-- ActivityLog.create() ----------> INSERT audit log
                                        |     (user, role, count, tenant, IP)
  <-------- CSV file download ------+
```

### 5. Celery Task Data Flow

```
  +--------------------+         +------------------+         +-----------------+
  | View / Admin       |         | Celery Worker    |         | SMTP Server     |
  +--------+-----------+         +--------+---------+         +--------+--------+
           |                              |                            |
           | .delay(reg_id, status)       |                            |
           +----------------------------->|                            |
                                          |                            |
           send_enrollment_status_email:  |                            |
                                          +-- Fetch RegistrationForm   |
                                          |                            |
                                          +-- Select template:         |
                                          |   submitted -> registration_received.html
                                          |   under_review -> under_review.html
                                          |   approved -> approved.html
                                          |   rejected -> rejected.html
                                          |   enrolled -> enrolled.html
                                          |                            |
                                          +-- render_to_string()       |
                                          |                            |
                                          +-- send_mail() ------------>|
                                          |   to: [email, parent_email]|
                                          |   from: DEFAULT_FROM_EMAIL |
                                          |                            |
                                          +-- On failure: retry        |
                                              max 3, countdown 60s     |

  Periodic Tasks:
  +-----------------------------------------------------------------+
  | send_enrollment_reminders()         (daily)                     |
  |   Finds pending registrations exactly 7 days old                |
  |   Emails parent_email with reminder                             |
  +-----------------------------------------------------------------+
  | cleanup_old_rejected_registrations() (weekly)                   |
  |   Finds rejected registrations > 90 days old                    |
  |   Currently only logs count (deletion commented out)            |
  +-----------------------------------------------------------------+
  | generate_enrollment_report(tenant_id, academic_year) (on-demand)|
  |   Returns dict: {total, pending, approved, rejected, enrolled}  |
  +-----------------------------------------------------------------+
  | auto_approve_complete_registrations() (periodic)                |
  |   Approves registrations where:                                 |
  |     - get_completion_percentage() == 100                        |
  |     - All 4 required doc types verified:                        |
  |       birth_certificate, photo, id_card, parent_id              |
  |   Sets status='approved', review_notes='Auto-approved...'      |
  |   Dispatches email notification                                 |
  +-----------------------------------------------------------------+
```

---

## Signal Handlers

Defined in `enrollment/signals.py`, loaded via `EnrollmentConfig.ready()` in `apps.py`:

| Signal      | Sender              | Handler                      | Behavior                                                         |
|-------------|---------------------|------------------------------|------------------------------------------------------------------|
| `pre_save`  | RegistrationForm    | `track_status_change`        | Logs status transitions via `logger.info` when old != new status |
| `post_save` | EnrollmentDocument  | `notify_document_upload`     | Logs new document uploads (only when `created=True`)             |
| `post_save` | RegistrationForm    | `send_status_notification`   | Backup notification trigger for approved/rejected/enrolled; checks for existing EnrollmentStatusHistory to avoid duplicates; currently only logs (does not send email) |

Note: The `RegistrationForm.save()` override in the model also sets `reviewed_at`
when status changes to `approved` or `rejected`.

---

## Forms Summary

| Form Class               | Purpose                         | Key Fields                                                                    |
|---------------------------|---------------------------------|-------------------------------------------------------------------------------|
| `RegistrationFormStep1`   | Student personal info (Step 1)  | student_*, dob, gender, nationality, email, phone, address fields             |
| `RegistrationFormStep2`   | Parent/guardian info (Step 2)   | parent_*, parent_relationship (select: father/mother/guardian/other)           |
| `RegistrationFormStep3`   | Academic info (Step 3)          | enrollment_type, filiere (tenant-filtered queryset), academic_year, level     |
| `RegistrationFormStep4`   | Additional info (Step 4)        | special_needs, medical_information                                            |
| `RegistrationEditForm`    | Full edit (admin/registrar)     | All RegistrationForm fields including status, review_notes, rejection_reason  |
| `DocumentUploadForm`      | Document upload                 | document_type, file (10MB max, pdf/jpg/png/doc/docx + content type check), description |
| `RegistrationReviewForm`  | Status review                   | status, review_notes, rejection_reason (required if status=='rejected')       |
| `DocumentVerificationForm`| Document verification           | is_verified (checkbox)                                                        |
| `EnrollmentSearchForm`    | List filtering (not ModelForm)  | student_name, email, status, enrollment_type, academic_year, filiere (tenant-filtered), date_from, date_to |

---

## Serializers Summary

| Serializer Class                    | Purpose                               | Read-Only Fields                                          |
|-------------------------------------|---------------------------------------|-----------------------------------------------------------|
| `RegistrationFormSerializer`        | Full detail serializer                | student_full_name, parent_full_name, full_address, filiere_name, reviewed_by_name, *_display fields |
| `RegistrationFormListSerializer`    | Lightweight list serializer           | student_full_name, filiere_name, status_display           |
| `RegistrationFormCreateSerializer`  | Public registration (POST)            | None (validates email uniqueness against enrolled status)  |
| `RegistrationReviewSerializer`      | Review action (direction only)        | None (validates status in allowed set, rejection_reason)   |
| `EnrollmentDocumentSerializer`      | Full document detail                  | registration_student_name, document_type_display, file_url, verified_by_name |
| `EnrollmentDocumentUploadSerializer`| Document upload (POST)                | None (validates file size max 5MB, allowed extensions)     |
| `DocumentVerificationSerializer`    | Document verification (direction)     | None                                                       |
| `EnrollmentStatusHistorySerializer` | Status history (read-only ViewSet)    | registration_student_name, changed_by_name                 |

---

## Admin Interface

### RegistrationFormAdmin

- **List Display**: student_full_name, colored_status (color-coded HTML span), enrollment_type, filiere, academic_year, submitted_at, completion_badge (percentage with color), reviewed_by, tenant
- **List Filter**: status, enrollment_type, level, academic_year, gender, filiere, submitted_at, tenant
- **Search**: student_first_name, student_last_name, email, phone, parent_first_name, parent_last_name, parent_email
- **Fieldsets**: Tenant Info | Student Info | Parent Info | Academic Info | Review & Status | Additional (collapsed) | Enrollment Result (collapsed) | Metadata (collapsed)
- **Inlines**: EnrollmentDocumentInline (tabular), EnrollmentStatusHistoryInline (tabular, read-only)
- **Bulk Actions**: `approve_registrations`, `reject_registrations`, `mark_under_review`
- **save_model**: Auto-sets tenant on create, tracks status changes (creates EnrollmentStatusHistory), sets reviewed_by
- **get_queryset**: Filtered by `request.tenant` for non-superusers; `select_related` on tenant, filiere, reviewed_by, enrolled_user

### EnrollmentDocumentAdmin

- **List Display**: document_type, registration, is_verified, verified_by, uploaded_at, file_size_display
- **List Filter**: document_type, is_verified, uploaded_at, registration__tenant
- **Search**: registration__student_first_name, registration__student_last_name, description
- **get_queryset**: Filtered by tenant; `select_related` on registration, verified_by

### EnrollmentStatusHistoryAdmin

- **Read-only**: No add or delete permissions (`has_add_permission` and `has_delete_permission` return False)
- **List Display**: registration, old_status, new_status, changed_by, changed_at
- **List Filter**: old_status, new_status, changed_at, registration__tenant
- **get_queryset**: Filtered by tenant; `select_related` on registration, changed_by

---

## Rate Limiting

| View / Endpoint               | Key    | Rate    | Method |
|-------------------------------|--------|---------|--------|
| `register_step1` through `4`  | `ip`   | 10/h    | POST   |
| `upload_document`             | `ip`   | 20/h    | POST   |
| `parent_enroll_step1` thru `3`| `user` | 10/h    | POST   |
| `enrollment_list`             | `user` | 100/h   | ALL    |
| `enrollment_detail`           | `user` | 100/h   | ALL    |
| `enrollment_review`           | `user` | 50/h    | POST   |
| `verify_document`             | `user` | 50/h    | POST   |
| `export_enrollments_csv`      | `user` | 20/h    | ALL    |
| `enrollment_statistics`       | `user` | 50/h    | ALL    |
| `registration_edit`           | `user` | 50/h    | POST   |

---

## URL Namespace Structure

```
enrollment/
  +-- api/
  |     +-- registrations/              (RegistrationFormViewSet, basename='registration')
  |     |     +-- <pk>/review/          POST (custom action)
  |     |     +-- pending/              GET  (custom action)
  |     |     +-- statistics/           GET  (custom action)
  |     +-- documents/                  (EnrollmentDocumentViewSet, basename='document')
  |     |     +-- <pk>/verify/          POST (custom action)
  |     +-- history/                    (EnrollmentStatusHistoryViewSet, basename='history')
  |
  +-- (frontend)
        +-- register/step1/
        +-- register/step2/
        +-- register/step3/
        +-- register/step4/
        +-- register/complete/<signed_id>/
        +-- register/<id>/upload/
        +-- parent/enroll/step1/
        +-- parent/enroll/step2/
        +-- parent/enroll/step3/
        +-- list/
        +-- detail/<id>/
        +-- review/<id>/
        +-- edit/<id>/
        +-- delete/<id>/
        +-- document/<id>/verify/
        +-- document/<id>/delete/
        +-- export/csv/
        +-- statistics/
```

Frontend namespace: `frontend:enrollment:<view_name>`
API namespace: uses DefaultRouter under `api/` path

---

## Key Design Decisions

1. **Two registration paths**: Public (4-step) vs Parent dashboard (3-step). The parent
   flow skips the parent info step because it auto-populates from `request.user` and
   sets the `parent_user` FK to avoid creating a duplicate parent account on approval.

2. **Automatic account creation on approval**: When a registrar approves an enrollment,
   `_create_accounts_for_enrollment()` atomically creates User + Student + Parent
   accounts with temporary passwords (`must_change_password=True`). The parent account
   is reused if `parent_user` was set during submission (dashboard flow).

3. **Capacity enforcement**: Before approving, the system checks `filiere.capacity`
   against the count of already approved/enrolled registrations for the same
   filiere and academic year. This check exists only in the frontend review view.

4. **Signed tokens for completion page**: The `register_complete` view uses
   `django.core.signing.Signer` to prevent enumeration of registration IDs.

5. **Tenant isolation**: All admin/registrar views filter by `request.tenant`.
   The admin `get_queryset` methods apply tenant filtering for non-superusers.
   Public registration sets tenant from `request.tenant` (determined by domain).

6. **Audit trail**: Every status change creates an `EnrollmentStatusHistory` record
   (from views, admin save_model, and API review action). CSV exports are logged
   to `core.ActivityLog` with user, role, record count, tenant, and IP address.

7. **Parent account reuse**: If a parent already has an account (dashboard flow with
   `parent_user` set), the system reuses it. It looks for a placeholder `Parent`
   profile (where `student` is null) and updates it, or creates a new `Parent`
   profile for an additional child.

8. **View separation**: Frontend views (`views_frontend.py`) use Django decorators
   and template rendering. API views (`views_api.py`) use DRF ViewSets with
   serializer-based validation. Both operate on the same models.

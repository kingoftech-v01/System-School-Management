# Admissions App -- Architecture

## Overview

The `admissions` app manages the full student admission lifecycle: public application
submission, staff review and counseling, payment tracking, and final admission
decisions.  It exposes both server-rendered HTML views (frontend) and a DRF-based
REST API.  Background work (email notifications, payment reconciliation, archiving)
is handled by Celery tasks on a beat schedule.

---

## 1. Model Relationships

### 1a. ASCII Relationship Diagram

```text
+---------------------+            +------------------------+
|  AdmissionSession   |            |    course.Program      |
|---------------------|            |------------------------|
| id  (PK)            |            | id  (PK)              |
| name (unique)       |            | title                  |
| start_date          |            | summary                |
| end_date            |            +------------------------+
| is_active           |                    |
| created_at          |                    | FK (program)
+---------------------+                   | on_delete=SET_NULL
        |                                  | null=True, blank=True
        | FK (session)                     |
        | on_delete=CASCADE                |
        | related_name='applications'      |
        v                                  |
+------------------------------------------+--------------------------+
|                   AdmissionStudent                                  |
|---------------------------------------------------------------------|
| id  (PK)                                                            |
|                                                                     |
| -- Personal Info --                                                 |
| first_name, middle_name, last_name                                  |
| email, phone, date_of_birth, gender (M/F/O), nationality           |
|                                                                     |
| -- Address --                                                       |
| street_address, city, province, country, postal_code                |
|                                                                     |
| -- Guardian Info --                                                 |
| guardian_first_name, guardian_middle_name, guardian_last_name        |
| guardian_phone, guardian_email                                       |
|                                                                     |
| -- Academic Info --                                                 |
| program  -------> course.Program (FK, SET_NULL)                     |
| previous_school, previous_grade, exam_scores (JSONField)            |
|                                                                     |
| -- Status --                                                        |
| status  (pending | under_review | counseling |                      |
|          payment_pending | admitted | rejected)                     |
| reviewed_by  -------> accounts.User (FK, SET_NULL)                  |
| counselor    -------> accounts.User (FK, SET_NULL)                  |
|                                                                     |
| -- Payment & Admission --                                           |
| application_fee_paid (bool), admitted (bool)                        |
| admission_date (DateField), rejection_reason (TextField)            |
|                                                                     |
| -- Documents --                                                     |
| transcript   (FileField: pdf/jpg/jpeg/png)                          |
| birth_certificate (FileField: pdf/jpg/jpeg/png)                     |
|                                                                     |
| -- Timestamps --                                                    |
| created_at (auto_now_add), updated_at (auto_now)                    |
+---------------------------------------------------------------------+
        |                             |
        | 1:N (counseling_comments)   | 1:1 (payment)
        | on_delete=CASCADE           | on_delete=CASCADE
        v                             v
+--------------------------+   +---------------------------+
|   CounselingComment      |   |    AdmissionPayment       |
|--------------------------|   |---------------------------|
| id  (PK)                 |   | id  (PK)                  |
| application (FK) --------+   | application (OneToOne) ---+
| counselor -> User (FK,   |   | amount (Decimal 10,2)     |
|   CASCADE)               |   | transaction_id (unique)   |
| comment (TextField)      |   | payment_method            |
| is_recommendation (bool) |   |   (stripe | braintree     |
| created_at (auto)        |   |    | bank_transfer | cash) |
+--------------------------+   | verified (bool)           |
        |                      | verified_by -> User (FK,  |
        v                      |   SET_NULL)               |
   accounts.User               | verified_at (DateTime)    |
   (counselor FK,              | paid_at (auto_now_add)    |
    CASCADE)                   +---------------------------+
                                       |
                                       v
                                  accounts.User
                                  (verified_by FK,
                                   SET_NULL)
```

### 1b. FK Reference Table

| Source Model      | Field       | Target Model     | Relation | on_delete | related_name                  |
|-------------------|-------------|------------------|----------|-----------|-------------------------------|
| AdmissionStudent  | session     | AdmissionSession | FK       | CASCADE   | `applications`                |
| AdmissionStudent  | program     | course.Program   | FK       | SET_NULL  | (default)                     |
| AdmissionStudent  | reviewed_by | accounts.User    | FK       | SET_NULL  | `reviewed_applications`       |
| AdmissionStudent  | counselor   | accounts.User    | FK       | SET_NULL  | `counseled_applications`      |
| CounselingComment | application | AdmissionStudent | FK       | CASCADE   | `counseling_comments`         |
| CounselingComment | counselor   | accounts.User    | FK       | CASCADE   | (default)                     |
| AdmissionPayment  | application | AdmissionStudent | 1:1      | CASCADE   | `payment`                     |
| AdmissionPayment  | verified_by | accounts.User    | FK       | SET_NULL  | `verified_admission_payments` |

### 1c. Database Indexes (AdmissionStudent)

| Fields                | Purpose                                  |
|-----------------------|------------------------------------------|
| (status, -created_at) | Fast status filtering with date ordering |
| (session, status)     | Per-session status dashboards            |
| (email,)              | Public status-check lookup by email      |

### 1d. Model Details

**AdmissionSession** -- Defines an admission period during which applications
can be submitted.  Only sessions with `is_active=True` appear in the public
form dropdown and the API listing.  Ordered by `-start_date`.

**AdmissionStudent** -- Central model.  Stores the complete application: personal
data, guardian info, academic background, workflow status, and document uploads.
`get_full_name()` is a regular method (not a `@property`).  `guardian_full_name`
and `full_address` are `@property` accessors.  `exam_scores` is an unvalidated
`JSONField(default=dict)`.  Ordered by `-created_at`.

**CounselingComment** -- Append-only feedback record tied to an application.
The `is_recommendation` boolean flag distinguishes formal recommendations from
general notes.  Ordered by `-created_at`.

**AdmissionPayment** -- One-to-one with `AdmissionStudent`.  Tracks fee amount,
transaction ID, method, and verification state.  Verification happens via Django
admin (not frontend views).  Ordered by `-paid_at`.

---

## 2. View Access Patterns per Role

### 2a. Frontend Views (views_frontend.py)

Access control uses the `@direction_only` decorator from `accounts.decorators`,
which resolves to `@role_required('secretary', 'direction', 'admin')`.
Superusers bypass all role checks.

| URL Pattern                             | View Function               | Auth              | Allowed Roles               |
|-----------------------------------------|-----------------------------|-------------------|-----------------------------|
| `/admissions/apply/`                    | `admission_apply`           | **Public**        | Anyone (no login)           |
| `/admissions/status/`                   | `admission_status`          | **Public**        | Anyone (email-based lookup) |
| `/admissions/`                          | `admission_session_list`    | `@login_required` | Any authenticated user      |
| `/admissions/applications/`             | `admission_list`            | `@direction_only` | secretary, direction, admin |
| `/admissions/applications/<int:pk>/`    | `admission_detail`          | `@direction_only` | secretary, direction, admin |
| `/admissions/comment/<int:student_id>/` | `counseling_comment_create` | `@direction_only` | secretary, direction, admin |

### 2b. REST API Views (views_api.py)

| Endpoint                           | ViewSet                 | Permission        | HTTP Methods               |
|------------------------------------|-------------------------|-------------------|----------------------------|
| `/api/v1/admissions/sessions/`     | AdmissionSessionViewSet | `AllowAny`        | GET (list, retrieve)       |
| `/api/v1/admissions/applications/` | AdmissionStudentViewSet | `IsAuthenticated` | GET, POST, PUT, PATCH, DEL |

### 2c. Full Role Access Matrix

```text
Endpoint      | Anon | student | professor | parent | prefet | accountant | librarian | registrar | secretary | direction | admin
--------------+------+---------+-----------+--------+--------+------------+-----------+-----------+-----------+-----------+------
Apply         |  Y   |    Y    |     Y     |   Y    |   Y    |     Y      |     Y     |     Y     |     Y     |     Y     |   Y
Status        |  Y   |    Y    |     Y     |   Y    |   Y    |     Y      |     Y     |     Y     |     Y     |     Y     |   Y
Session List  |  -   |    Y    |     Y     |   Y    |   Y    |     Y      |     Y     |     Y     |     Y     |     Y     |   Y
App List      |  -   |    -    |     -     |   -    |   -    |     -      |     -     |     -     |     Y     |     Y     |   Y
App Detail    |  -   |    -    |     -     |   -    |   -    |     -      |     -     |     -     |     Y     |     Y     |   Y
Add Comment   |  -   |    -    |     -     |   -    |   -    |     -      |     -     |     -     |     Y     |     Y     |   Y
API Sessions  |  Y   |    Y    |     Y     |   Y    |   Y    |     Y      |     Y     |     Y     |     Y     |     Y     |   Y
API Apps      |  -   |    Y    |     Y     |   Y    |   Y    |     Y      |     Y     |     Y     |     Y     |     Y     |   Y

Key: Y = access granted, - = access denied
     Superusers bypass all checks regardless of role.
```

**Important caveat**: The API `AdmissionStudentViewSet` has no role-based
filtering -- any authenticated user (including students and parents) can
list/create/update/delete all applications via the API.  Only the frontend
enforces the direction-only restriction.

### 2d. Django Admin Access

All four models are registered in admin.  Access is controlled by Django's
standard `is_staff` / permission framework.  Bulk actions:

| Admin Class            | Model             | Bulk Actions                                                        |
|------------------------|-------------------|---------------------------------------------------------------------|
| AdmissionSessionAdmin  | AdmissionSession  | (none)                                                              |
| AdmissionStudentAdmin  | AdmissionStudent  | `approve_applications`, `reject_applications`, `move_to_counseling` |
| CounselingCommentAdmin | CounselingComment | (none)                                                              |
| AdmissionPaymentAdmin  | AdmissionPayment  | `verify_payments` (sets verified, verified_by, verified_at)         |

Inlines on `AdmissionStudentAdmin`:

- `CounselingCommentInline` (TabularInline, extra=1)
- `AdmissionPaymentInline` (TabularInline, extra=0)

---

## 3. Business Logic Workflows

### 3a. Admission Lifecycle State Machine

```text
                +----------+
                |  pending  |  <-- initial (public form submit)
                +-----+----+
                      |
           (staff begins review)
                      |
                      v
             +--------+---------+
             |   under_review   |
             +--------+---------+
                      |
         +------------+------------+
         |                         |
         v                         v
   +-----+------+          +------+-----+
   | counseling  |          |  rejected  |  <-- terminal
   +-----+------+          +------------+
         |
    (counselor adds CounselingComment,
     optionally with is_recommendation=True)
         |
         v
   +-----+-----------+
   | payment_pending  |
   +-----+-----------+
         |
    (AdmissionPayment created & verified)
         |
         v
    +----+-----+
    | admitted  |  <-- terminal (happy path)
    +----------+
```

Status values (`AdmissionStudent.STATUS_CHOICES`):

1. `pending` -- default on creation
2. `under_review` -- staff has started reviewing
3. `counseling` -- assigned to a counselor for interview/assessment
4. `payment_pending` -- approved pending fee payment
5. `admitted` -- fully admitted (sets `admitted=True`, `admission_date`)
6. `rejected` -- denied (populates `rejection_reason`)

### 3b. Public Application Submission Flow

```text
Applicant                        Server
   |                                |
   |  GET /admissions/apply/        |
   |------------------------------->|
   |                                |  AdmissionApplicationForm (empty)
   |                                |  session dropdown: AdmissionSession
   |  <---- render apply.html ------|    .objects.filter(is_active=True)
   |                                |
   |  POST /admissions/apply/       |
   |  (form data)                   |
   |------------------------------->|
   |                                |  form.is_valid()
   |                                |    -> form.save()
   |                                |    -> AdmissionStudent created
   |                                |       status = 'pending'
   |                                |
   |  <---- redirect + success -----|  -> /admissions/status/
```

Fields collected by `AdmissionApplicationForm`:

- Session: `session`
- Personal: `first_name`, `middle_name`, `last_name`, `email`, `phone`,
  `gender`, `date_of_birth`, `nationality`
- Address: `street_address`, `city`, `province`, `country`, `postal_code`
- Guardian: `guardian_first_name`, `guardian_middle_name`, `guardian_last_name`,
  `guardian_phone`, `guardian_email`

Fields **excluded** from the public form (managed by staff via admin/API):
`program`, `previous_school`, `previous_grade`, `exam_scores`, `transcript`,
`birth_certificate`, `status`, `reviewed_by`, `counselor`, `application_fee_paid`,
`admitted`, `admission_date`, `rejection_reason`.

### 3c. Public Status Check Flow

```text
Applicant                        Server
   |                                |
   |  GET /admissions/status/       |
   |------------------------------->|  AdmissionStatusForm (email field)
   |  <---- render status.html -----|
   |                                |
   |  POST (email=xxx@yyy.com)      |
   |------------------------------->|  AdmissionStudent.objects.filter(email=...)
   |                                |    .select_related('session')
   |                                |    .order_by('-created_at')
   |  <---- results or "not found"--|
```

### 3d. Staff Review Workflow

```text
Direction/Secretary/Admin            Server
   |                                    |
   |  GET /admissions/applications/     |
   |----------------------------------->|
   |                                    |  select_related(session, program,
   |                                    |    reviewed_by, counselor)
   |                                    |  filter by ?status= and ?search=
   |                                    |  search: first_name, last_name,
   |                                    |    email (icontains via Q objects)
   |  <-- admission_list.html ---------|  Paginator(qs, 20)
   |      (paginated, 20/page)         |
   |                                    |
   |  GET /admissions/applications/42/  |
   |----------------------------------->|
   |                                    |  get_object_or_404(AdmissionStudent, pk=42)
   |                                    |  + counseling_comments (reverse FK)
   |                                    |  + payment (try/except DoesNotExist)
   |  <-- admission_detail.html -------|
   |                                    |
   |  POST /admissions/comment/42/      |
   |  (comment text, is_recommendation) |
   |----------------------------------->|
   |                                    |  CounselingCommentForm.is_valid()
   |                                    |  comment.application = application
   |                                    |  comment.counselor = request.user
   |                                    |  comment.save()
   |  <-- redirect to detail -----------|
```

### 3e. Payment Verification and Auto-Admission

Payment verification happens exclusively through Django admin.  There is no
frontend view for creating or verifying payments.

1. Staff creates an `AdmissionPayment` via the admin inline on
   `AdmissionStudentAdmin` (fields: amount, transaction_id, payment_method).
2. Admin uses the **"Verify selected payments"** bulk action:
   - Sets `verified = True`
   - Sets `verified_by = request.user`
   - Sets `verified_at = timezone.now()`
3. The `process_admission_payments` Celery task runs daily at 01:00 and scans
   for `status='payment_pending'` with `application_fee_paid=False`:

   ```text
   If application.payment exists AND application.payment.verified:
       application.application_fee_paid = True
       application.status = 'admitted'
       application.admitted = True
       application.admission_date = today
       application.save()
       send_status_update_email.delay(application.id)
   ```

### 3f. Celery Task Schedule

| Task                                | Schedule                | Action                                     |
|-------------------------------------|-------------------------|--------------------------------------------|
| `send_admission_confirmation_email` | On-demand (not on beat) | Email applicant after submission           |
| `send_status_update_email`          | On-demand (not on beat) | Email applicant on status change           |
| `process_admission_payments`        | Daily at 01:00          | Auto-admit after verified payment          |
| `send_counseling_reminders`         | Mon and Thu at 09:30    | Email counselors their pending app list    |
| `auto_archive_old_applications`     | Sunday at 03:30         | Log count of archivable apps (no mutation) |

---

## 4. Dependencies (Both Directions)

### 4a. Outbound -- admissions depends on

```text
admissions
  |
  +---> accounts.models.User         FK: reviewed_by, counselor (AdmissionStudent)
  |                                  FK: counselor (CounselingComment)
  |                                  FK: verified_by (AdmissionPayment)
  |
  +---> accounts.decorators           direction_only -> role_required(
  |                                     'secretary', 'direction', 'admin')
  |
  +---> course.models.Program         FK: AdmissionStudent.program
  |
  +---> celery                        @shared_task for 5 background tasks
  |
  +---> django.core.mail              send_mail() in 3 tasks
  |
  +---> rest_framework                ViewSets, ModelSerializer, permissions
  |
  +---> django.core.validators        FileExtensionValidator (transcript,
                                       birth_certificate)
```

### 4b. Inbound -- other code depends on admissions

```text
admissions
  ^
  |
  +---- School_System/urls.py
  |       Includes admissions.urls (frontend_urlpatterns and api_urlpatterns)
  |       Frontend: path('admissions/', ..., 'admissions')
  |       API:      path('admissions/', ..., 'admissions')
  |
  +---- School_System/celery.py
  |       Beat schedule references 3 tasks:
  |         admissions.tasks.process_admission_payments
  |         admissions.tasks.send_counseling_reminders
  |         admissions.tasks.auto_archive_old_applications
  |
  +---- tests/helpers.py
  |       create_admission_session() factory
  |       create_admission_student() factory
  |
  +---- tests/test_views_phase2.py
  |       Integration tests importing AdmissionSession
  |
  +---- tests/test_tasks_deep.py
  |       Task unit tests (mocked send_mail)
  |
  +---- tests/test_tasks_api_misc_cov.py
  +---- tests/test_forms_tasks_misc_deep.py
  +---- tests/test_admin_tasks_serializers.py
  +---- tests/test_admin_registration.py
  +---- tests/test_model_methods_deep.py
  |
  +---- admissions/tests/*
          App-level test modules (test_models, test_forms, test_admin,
          test_views_api, test_views_frontend, test_tasks)
```

### 4c. Dependency Diagram

```text
+--------------------+          +--------------------+
|  accounts          |          |  course            |
|  - User model      |          |  - Program model   |
|  - direction_only  |          +----------+---------+
+---------+----------+                     |
          |  FK x4 + decorator             |  FK x1
          |                                |
+---------+--------------------------------+---------+
|                  admissions                        |
|                                                    |
|  models:   AdmissionSession                        |
|            AdmissionStudent  (central)             |
|            CounselingComment                       |
|            AdmissionPayment                        |
|                                                    |
|  views:    views_frontend.py (6 views)             |
|            views_api.py (2 viewsets)               |
|                                                    |
|  tasks:    tasks.py (5 Celery tasks)               |
|                                                    |
|  forms:    forms.py (3 forms)                      |
|                                                    |
|  admin:    admin.py (4 ModelAdmin + 2 inlines)     |
+----------------------------------------------------+
          |           |             |
          v           v             v
       celery    rest_framework   django.core.mail
```

**No other Django app has a foreign key pointing into admissions models.**
The `enrollment` app is a logically separate post-admission workflow with
no hard database dependency on admissions.

---

## 5. Data Flow Diagrams

### 5a. End-to-End Admission Data Flow

```text
                         PUBLIC INTERNET
                               |
                +--------------+--------------+
                |                             |
         [Apply Form]                 [Status Check]
         POST /apply/                 POST /status/
                |                             |
                v                             v
       AdmissionStudent              filter(email=...)
       .objects.create()             .select_related('session')
       status='pending'                       |
                |                             |
                +---------- DATABASE ---------+
                               |
                 +-------------+-------------+
                 |                           |
          [Staff Frontend]             [REST API]
          @direction_only              @IsAuthenticated
                 |                           |
         +-------+-------+          +-------+-------+
         |               |          |               |
    [List View]    [Detail View]  [List]       [Detail]
    search/filter  + comments     GET/POST     GET/PUT/
    paginate(20)   + payment                   PATCH/DELETE
         |               |
         |        [Add Comment]
         |        CounselingComment
         |               |
         +-------+-------+
                 |
         [Django Admin]
         - Status transitions (bulk actions)
         - Payment creation (inline)
         - Payment verification (bulk action)
                 |
                 v
         +-------+--------+
         |  Celery Beat    |
         +--+---------+---+
            |         |
   01:00 daily   Mon/Thu 09:30    Sun 03:30
   process_      send_            auto_archive_
   admission_    counseling_      old_
   payments      reminders        applications
            |
            v
   status -> 'admitted'
   send_status_update_email.delay()
            |
            v
      [SMTP / Email]
      To: applicant email
      From: admissions@school.com
```

### 5b. Request Routing

```text
Browser/API Client
      |
      v
School_System/urls.py
      |
      +---> Frontend: path('', include(frontend_urlpatterns, 'frontend'))
      |       |
      |       +---> path('admissions/', include(..., 'admissions'))
      |               |
      |               +--- ''                   -> admission_session_list  [@login_required]
      |               +--- 'apply/'             -> admission_apply         [Public]
      |               +--- 'status/'            -> admission_status        [Public]
      |               +--- 'applications/'      -> admission_list          [@direction_only]
      |               +--- 'applications/<pk>/' -> admission_detail        [@direction_only]
      |               +--- 'comment/<id>/'      -> counseling_comment_create [@direction_only]
      |
      +---> API: path('api/v1/', include(api_v1_urlpatterns, 'api'))
              |
              +---> path('admissions/', include(..., 'admissions'))
                      |
                      +--- 'sessions/'          -> AdmissionSessionViewSet [AllowAny, read-only]
                      +--- 'sessions/<pk>/'     -> AdmissionSessionViewSet [AllowAny, read-only]
                      +--- 'applications/'      -> AdmissionStudentViewSet [IsAuthenticated]
                      +--- 'applications/<pk>/' -> AdmissionStudentViewSet [IsAuthenticated]
```

URL namespace resolution:

- Frontend: `frontend:admissions:<view_name>`  (e.g., `frontend:admissions:apply`)
- API: `api:admissions:<basename>-list` / `api:admissions:<basename>-detail`

### 5c. Celery Task Data Flow

```text
Celery Beat Scheduler
      |
      +---> process_admission_payments (daily 01:00)
      |       |
      |       +---> Query: status='payment_pending' AND
      |       |       application_fee_paid=False
      |       |       .select_related('program', 'session')
      |       |
      |       +---> For each application:
      |               |
      |               +---> If application.payment.verified == True:
      |                       application_fee_paid = True
      |                       status = 'admitted'
      |                       admitted = True
      |                       admission_date = today
      |                       application.save()
      |                       send_status_update_email.delay(id)
      |
      +---> send_counseling_reminders (Mon and Thu 09:30)
      |       |
      |       +---> Query: status='counseling' AND
      |       |       counselor__isnull=False
      |       |       .select_related('counselor', 'session', 'program')
      |       |
      |       +---> Group applications by counselor
      |       +---> For each counselor with apps:
      |               send_mail(to=counselor.email, app_list)
      |
      +---> auto_archive_old_applications (Sunday 03:30)
              |
              +---> Query: AdmissionSession where
              |       is_active=False AND end_date < today
              |
              +---> Count: AdmissionStudent where
              |       session__in=closed AND status in (pending, under_review)
              |
              +---> logger.info(count)  [NO MUTATION - placeholder]
```

---

## 6. Forms

| Form Class                 | Base        | Fields                                                                                                                                                                                                                                             | Usage                |
|----------------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| `AdmissionApplicationForm` | `ModelForm` | session, first_name, middle_name, last_name, email, phone, gender, date_of_birth, nationality, street_address, city, province, country, postal_code, guardian_first_name, guardian_middle_name, guardian_last_name, guardian_phone, guardian_email | Public apply page    |
| `CounselingCommentForm`    | `ModelForm` | comment, is_recommendation                                                                                                                                                                                                                         | Staff comment form   |
| `AdmissionStatusForm`      | `Form`      | email                                                                                                                                                                                                                                              | Public status lookup |

All form widgets use Bootstrap 5 classes (`form-control`, `form-select`,
`form-check-input`).

---

## 7. Serializers

| Serializer                   | Model            | Fields    | Notes                     |
|------------------------------|------------------|-----------|---------------------------|
| `AdmissionSessionSerializer` | AdmissionSession | `__all__` | Used by read-only viewset |
| `AdmissionStudentSerializer` | AdmissionStudent | `__all__` | Used by full CRUD viewset |

Both use `fields = '__all__'` which exposes all model fields to API consumers.

---

## 8. Templates

All templates live in `templates/admissions/` and extend
`w3crm/elements/layouts/admin.html`.

| Template                | View                        | Purpose                                      |
|-------------------------|-----------------------------|----------------------------------------------|
| `apply.html`            | `admission_apply`           | Public application form                      |
| `status.html`           | `admission_status`          | Public email lookup + results                |
| `session_list.html`     | `admission_session_list`    | Active session listing                       |
| `admission_list.html`   | `admission_list`            | Staff paginated application list             |
| `admission_detail.html` | `admission_detail`          | Full application detail + comments + payment |
| `counseling_form.html`  | `counseling_comment_create` | Staff counseling comment entry form          |

---

## 9. File Upload Configuration

| Field               | Upload Path                         | Allowed Extensions  |
|---------------------|-------------------------------------|---------------------|
| `transcript`        | `admissions/transcripts/%Y/%m/%d/`  | pdf, jpg, jpeg, png |
| `birth_certificate` | `admissions/certificates/%Y/%m/%d/` | pdf, jpg, jpeg, png |

Validation uses `FileExtensionValidator` from `django.core.validators`.

---

## 10. Technical Notes and Known Gaps

1. **No signals.py** -- The app has no Django signals file.  State transitions
   happen through admin bulk actions and Celery tasks, not signal-driven
   side effects.

2. **Email tasks are never auto-triggered** -- `send_admission_confirmation_email`
   and `send_status_update_email` are defined but never wired to form submission
   or status changes.  They must be called explicitly.

3. **Admin fieldsets reference wrong field names** -- `AdmissionStudentAdmin`
   fieldsets reference `address` and `guardian_name` which do not exist on
   the model.  Correct names are `street_address`/`city`/`province`/`country`/
   `postal_code` and `guardian_first_name`/`guardian_middle_name`/
   `guardian_last_name`.

4. **API lacks role-based scoping** -- `AdmissionStudentViewSet` uses
   `IsAuthenticated` without any role check.  Any authenticated user can
   perform full CRUD on all applications.

5. **Admin bulk approve does not set all fields** -- `approve_applications`
   only sets `status='admitted'` but does not set `admitted=True` or
   `admission_date`.

6. **Archive task is a no-op** -- `auto_archive_old_applications` only logs
   a count; the model lacks an `archived` field.

7. **Cascade delete risk on CounselingComment.counselor** -- Uses
   `on_delete=CASCADE`, so deleting a User deletes all their counseling
   comments.  Compare with `AdmissionStudent.counselor` which uses
   `SET_NULL`.

8. **get_full_name asymmetry** -- On `AdmissionStudent` it is a regular
   method (`get_full_name()`).  On the `User` model it is a `@property`
   (`user.get_full_name`).  Templates and tasks must use the correct call
   convention.

9. **No connection to enrollment** -- Conversion from admitted
   `AdmissionStudent` to `accounts.Student` + enrollment `RegistrationForm`
   is a manual process handled outside this app.

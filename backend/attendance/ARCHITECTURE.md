# Attendance App - Architecture

## Overview

The attendance app is a self-contained Django application for tracking classroom attendance. It maintains its own Student, Group, and Subject models separate from the rest of the system, and bridges to the `accounts` app only through the `User` model (for teacher foreign keys and role-based decorators) and email-based matching (for the student attendance report view).

The app exposes two interfaces: a set of template-based frontend views (19 views) and a REST API via Django REST Framework (5 ViewSets). Both share the same models and database tables.

## Directory Structure

```
attendance/
    __init__.py
    admin.py                 # Admin registration for all 7 models
    apps.py                  # Django app config
    forms.py                 # 5 ModelForms (Attendance, AttendanceReport, Student, Group, Subject)
    models.py                # 6 models + 1 TextChoices enum (217 lines)
    pagination.py            # CustomPagination (10 items/page)
    permissions.py           # IsTeacher DRF permission class
    serializers.py           # 6 DRF serializers
    tasks.py                 # 3 Celery task stubs (none implemented)
    urls.py                  # Frontend + API URL routing
    views_api.py             # 5 DRF ViewSets
    views_frontend.py        # 19 template-based views
    migrations/
        __init__.py
        0001_initial.py
    tests/
        __init__.py
        test_admin.py
        test_forms.py
        test_models.py
        test_permissions.py
        test_serializers.py
        test_tasks.py
        test_views_api.py
        test_views_frontend.py
```

## Data Model

### Entity Relationship Diagram (Text)

```
accounts.User (external)
    |
    | 1:N (teacher)
    v
Subject ----M2M----> Group
    |                   |
    | 1:N               | 1:N
    v                   v
Attendance          Student
    |                   |
    |       +-----------+
    |       |
    v       v
AttendanceReport (unique_together: attendance + student)
    |
    | aggregated into
    v
DailyAttendanceStat (unique_together: subject + group + date)
```

### Model Details

**Group**
- Represents a class or grade level (e.g., "L3 Informatique").
- Fields: `name` (CharField, max 50).
- Ordered alphabetically by `name`.
- Referenced by: `Student.group` (FK), `Subject.group` (M2M), `DailyAttendanceStat.group` (FK).

**Student**
- An attendance-specific student record. This is NOT the same as `accounts.Student`.
- Fields: `first_name`, `last_name`, `email` (unique), `group` (FK to Group).
- Ordered by `last_name`, then `first_name`.
- Key methods:
  - `get_attendance_percentage(subject=None)` -- Returns percentage of sessions marked present or late (0-100).
  - `has_low_attendance(threshold=75, subject=None)` -- Boolean check against a configurable threshold.
  - `get_attendances` (property) -- Returns all related `AttendanceReport` objects.
  - `get_absents_and_lates` (property) -- Returns reports with absent or late status.
  - `get_subjects` (property) -- Returns all subjects for the student's group.
  - `load_students_from_csv()`, `load_students_from_json()` -- Bulk import methods (both have bugs; see TODO.md).

**Subject**
- A taught subject, linked to a teacher (User) and one or more groups.
- Fields: `name`, `teacher` (FK to User), `group` (M2M to Group), `slug`.
- The `teacher` FK is the primary ownership mechanism: frontend views scope queries with `subject__teacher=request.user`.

**Satus** (TextChoices enum -- NOTE: typo in name)
- Values: `PRESENT` ("present"), `ABSENT` ("absent"), `LATE` ("late").
- Used as choices for `AttendanceReport.status` with default `ABSENT`.

**Attendance**
- Represents a single attendance session (one subject, one date).
- Fields: `subject` (FK to Subject), `date`, `created_at`, `updated_at`.
- Ordered by `-date` (most recent first).
- One Attendance session contains many AttendanceReports (one per student).

**AttendanceReport**
- An individual student's attendance record within a session.
- Fields: `attendance` (FK), `student` (FK), `status` (Satus choices, default "absent"), `created_at`, `updated_at`.
- Constraints: `unique_together = [attendance, student]` prevents duplicate entries.
- Indexes: `[attendance, status]` for per-session status queries; `[student, -created_at]` for per-student history.
- The `mark_attendance` view uses `update_or_create` so re-marking is idempotent.

**DailyAttendanceStat**
- Pre-aggregated daily statistics for faster reporting.
- Fields: `subject` (FK), `group` (FK), `date`, `total_students`, `present_count`, `absent_count`, `late_count`, `attendance_percentage` (Decimal 5,2).
- Constraints: `unique_together = [subject, group, date]`.
- Key methods:
  - `calculate_stats()` -- Queries AttendanceReports and updates all count fields and percentage.
  - `generate_for_date(date=None)` (classmethod) -- Generates or updates stats for all subject-group combinations on a given date.

## Request Flow

### Frontend (Template Views)

```
Browser Request
    |
    v
Django URL Router (urls.py: frontend_urlpatterns)
    |
    v
Decorators (applied in order):
    1. @login_required
    2. @role_required('professor','prefet','secretary','direction','admin')
       OR @prefet_allowed OR @lecturer_required
    3. @tenant_required
    4. @ratelimit(key='user', rate='50-100/h')
    |
    v
View Function (views_frontend.py)
    |
    v
Model Query (models.py) --> Database
    |
    v
Template Rendering --> HTML Response
```

### API (DRF ViewSets)

```
API Request (JSON)
    |
    v
DRF Router (urls.py: api_router / DefaultRouter)
    |
    v
Permission Check:
    - StudentViewSet: no extra permissions (any authenticated user)
    - GroupViewSet: no extra permissions (any authenticated user)
    - SubjectViewSet: IsAdminUser
    - AttendanceViewSet: IsAuthenticated
    - AttendanceReportViewSet: IsAuthenticatedOrReadOnly
    |
    v
ViewSet Method (views_api.py)
    |
    v
Serializer Validation (serializers.py)
    |
    v
Model Operations (models.py) --> Database
    |
    v
Serialized JSON Response (with CustomPagination if paginated)
```

## Authentication and Authorization

### Decorator Stack

The frontend views use a layered decorator pattern from the `accounts` app:

| Decorator | Purpose | Used By |
|-----------|---------|---------|
| `@login_required` | Ensures user is authenticated | All views |
| `@role_required(roles...)` | Restricts to listed roles | Dashboard, take/mark/edit/delete attendance |
| `@prefet_allowed` | Allows prefet + all higher roles | Student/Group/Subject CRUD |
| `@lecturer_required` | Allows lecturer/professor role | `attendance_detail` |
| `@tenant_required` | Ensures valid tenant context (multi-tenancy) | All views |
| `@ratelimit` | Rate limiting via django-ratelimit | Most views (50-100/h) |

### Role Access Matrix (Frontend)

| View Category | professor | prefet | secretary | direction | admin | student |
|---------------|-----------|--------|-----------|-----------|-------|---------|
| Dashboard | Yes | Yes | Yes | Yes | Yes | No |
| Take/Mark Attendance | Yes | Yes | Yes | Yes | Yes | No |
| Session Detail | Yes | Yes | No (bug) | No (bug) | No (bug) | No |
| Session Edit/Delete | Yes | Yes | Yes | Yes | Yes | No |
| Student/Group/Subject CRUD | No | Yes | Yes | Yes | Yes | No |
| Student Report | No | Yes | Yes | Yes | Yes | Own only |

Note: `attendance_detail` uses `@lecturer_required` instead of `@role_required`, which blocks secretary, direction, and admin users who can create sessions. This is a known bug tracked in TODO.md.

### Permission Model (API)

| ViewSet | Permission Class | HTTP Methods |
|---------|-----------------|--------------|
| `StudentViewSet` | None (default) | GET only |
| `GroupViewSet` | None (default) | GET only |
| `SubjectViewSet` | `IsAdminUser` | GET only |
| `AttendanceViewSet` | `IsAuthenticated` | GET, POST |
| `AttendanceReportViewSet` | `IsAuthenticatedOrReadOnly` | GET, POST, PUT, PATCH |

The `IsTeacher` custom permission class in `permissions.py` is defined but not used by any ViewSet currently. It checks `is_lecturer`, `is_staff`, or `is_superuser` for `has_permission`, and has a bug in `has_object_permission` (compares user to the object itself instead of checking the teacher relationship).

## Attendance Workflow

### Taking Attendance (Frontend)

1. **Create Session**: Teacher visits `/attendance/take/`, selects subject and date, submits form.
   - Creates an `Attendance` record (subject + date).
   - Redirects to mark attendance page.

2. **Mark Students**: Teacher visits `/attendance/<pk>/mark/`.
   - Displays all students from groups linked to the session's subject.
   - Teacher sets each student's status (present/absent/late) via radio buttons or select.
   - On submit, creates or updates `AttendanceReport` for each student using `update_or_create`.
   - Redirects to session detail page.

3. **Review**: Teacher views `/attendance/<pk>/` to see summary counts and per-student breakdown.

4. **Edit/Delete**: Teacher can edit the session's subject/date at `/attendance/<pk>/edit/` or delete it at `/attendance/<pk>/delete/` (with GET confirmation page, POST to execute).

### Taking Attendance (API)

1. **Create Session**: `POST /api/attendances/` with `{subject: <id>, date: "YYYY-MM-DD"}`.
   - Serializer validates: subject exists, no duplicate session, user is the teacher.
   - `perform_create` sets `subject_id` from request data.

2. **Mark Student**: `POST /api/reports/` with `{attendance: <id>, student: <id>, status: "present"}`.
   - Serializer validates: attendance exists, student exists, no duplicate report, user is teacher, student belongs to a subject group.

3. **Update Status**: `PUT/PATCH /api/reports/<id>/` with `{status: "late"}`.
   - Only updates the `status` field.

4. **Query**: `GET /api/attendances/<pk>/reports/?group=<id>` for per-session reports; `GET /api/students/<pk>/attendances/?status=present` for per-student reports.

## Pagination

### Frontend
- `student_list`: 50 items per page via `django.core.paginator.Paginator`.
- `student_attendance_report`: 50 items per page.
- Other list views (groups, subjects): No pagination.

### API
- `CustomPagination` (pagination.py): 10 items per page, configurable via `?page_size=N` query parameter.
- Response format: `{links: {next, previous}, total, page, page_size, results: [...]}`.
- Note: `CustomPagination` is defined but not explicitly set on any ViewSet in the current code. If `DEFAULT_PAGINATION_CLASS` is set globally in settings, it applies.

## Celery Tasks (Stubs)

Three tasks are defined in `tasks.py` but none are implemented (all are `pass`):

| Task | Intended Schedule | Purpose |
|------|-------------------|---------|
| `send_attendance_reminders` | Daily at 6 PM | Email professors who haven't marked attendance |
| `generate_daily_attendance_stats` | Daily at 12:05 AM | Call `DailyAttendanceStat.generate_for_date()` |
| `send_low_attendance_alerts` | Every Friday at 10 AM | Alert students/parents with low attendance |

**Critical bug**: All three tasks fail to import because `tasks.py` imports `AttendanceRecord` (line 10), which does not exist. The correct model name is `AttendanceReport`.

## Key Design Decisions

### Separate Student Model
The attendance app defines its own `Student` model rather than using `accounts.Student`. This means:
- Students exist independently in the attendance system (their own name, email, group).
- The `student_attendance_report` view matches between the two models by comparing email addresses.
- There is no foreign key relationship between the two Student models.
- This creates a risk of data desynchronization (a student's name updated in accounts will not reflect in attendance).

### Pre-aggregated Statistics
The `DailyAttendanceStat` model denormalizes attendance counts for faster reporting. The `calculate_stats()` method re-queries `AttendanceReport` and updates all fields. This avoids expensive aggregation queries at read time but requires explicit regeneration when reports change.

### Session-based Marking
Attendance is organized as sessions (`Attendance` model) containing individual reports (`AttendanceReport`). This two-level structure allows:
- One session per subject per date (enforced at API level via serializer, not at the database level).
- Bulk marking of all students in a single form submission.
- `update_or_create` for idempotent re-marking.

### View File Separation
Views are split into `views_frontend.py` (template-based) and `views_api.py` (DRF ViewSets). Both operate on the same models but with different serialization, permissions, and response formats.

## Known Issues

See `TODO.md` for the full list. The most critical issues are:

1. **`tasks.py` import error** -- All Celery tasks fail to load due to importing `AttendanceRecord` instead of `AttendanceReport`.
2. **`Satus` typo** -- The enum name is misspelled throughout the codebase.
3. **`IsTeacher.has_object_permission` bug** -- Compares user to the model instance instead of the teacher field.
4. **`StudentSerializer.create()` bug** -- Uses `group['name']` instead of `group['id']` for group lookup.
5. **`StudentViewSet.attendances` variable shadowing** -- Local `status` variable shadows the DRF `status` module, causing `AttributeError` when no status filter is provided.
6. **`attendance_detail` uses wrong decorator** -- `@lecturer_required` blocks secretary, direction, and admin users from viewing session details they can create.
7. **API permission gaps** -- `StudentViewSet` and `GroupViewSet` have no permission classes; `AttendanceReportViewSet` allows unauthenticated reads.

# Attendance App

Classroom attendance tracking with session management, student marking, reporting, and analytics.

## Description

The attendance app manages classroom attendance using its own Student, Group, and Subject models (separate from the `accounts` app). Teachers create attendance sessions for a subject and date, then bulk-mark individual students as present, absent, or late. The app includes a dashboard with today's summary statistics, detailed per-session reports, per-student attendance history with percentage calculations, and pre-aggregated daily statistics via `DailyAttendanceStat`.

**Important**: The `attendance.Student` model is a standalone record distinct from `accounts.Student`. Matching between the two is done by email address (see `student_attendance_report` view). This is a known design issue tracked in TODO.md.

## Main Features

- **Attendance Dashboard**: Overview of today's sessions and recent attendance, with present/absent/late counts for the logged-in teacher
- **Take Attendance**: Create an attendance session by selecting a subject and date (POST rate-limited to 50/hour)
- **Mark Attendance**: Bulk mark students as present/absent/late for a session using `update_or_create` (supports re-marking)
- **Attendance Detail**: View session summary with per-status counts and student-level breakdown
- **Edit/Delete Sessions**: Edit session subject/date or delete erroneous sessions with confirmation
- **Student Reports**: Per-student attendance report with overall percentage, subject filtering, and pagination (50 per page)
- **Low Attendance Detection**: `Student.has_low_attendance(threshold=75)` flags students below a configurable threshold
- **Student/Group/Subject CRUD**: Full create, read, update, delete for attendance-local Student, Group, and Subject models
- **Daily Statistics**: `DailyAttendanceStat` model with `calculate_stats()` and `generate_for_date()` for pre-aggregated reporting
- **REST API**: DRF ViewSets for students, groups, subjects, attendance sessions, and reports with custom pagination (10/page)

## User Roles

The system has 10 roles. The attendance app uses the following subset:

| Role | Frontend Permissions | Notes |
|------|----------------------|-------|
| professor | Create sessions, mark attendance, view dashboard, view session detail | Scoped to own subjects (`subject__teacher=request.user`) |
| prefet | All professor permissions + full CRUD on students, groups, subjects | Uses `@prefet_allowed` decorator |
| secretary | Create sessions, mark attendance, view dashboard | Same as professor for attendance |
| direction | Create sessions, mark attendance, view dashboard | Same as professor for attendance |
| admin | Create sessions, mark attendance, view dashboard | Full access via `@role_required` |
| student | View own attendance report only | Matched by email to `attendance.Student`; redirected if trying to view another student's report |
| parent | No access | Redirected with "Access denied" |
| accountant | No attendance-specific access | Not applicable |
| librarian | No attendance-specific access | Not applicable |
| registrar | No attendance-specific access | Not applicable |

## CRUD Summary

| Entity | Create | Read | Update | Delete | Who |
|--------|--------|------|--------|--------|-----|
| Attendance (session) | POST via `take_attendance` | Dashboard + detail | `attendance_edit` | `attendance_delete` (with confirmation) | professor, prefet, secretary, direction, admin |
| AttendanceReport | Bulk via `mark_attendance` | Detail + student report | Re-mark via `mark_attendance` | Cascade on session delete | professor, prefet, secretary, direction, admin |
| Student | `student_create` | `student_list` (search + group filter) | `student_edit` | `student_delete` (with confirmation) | prefet (and roles above) |
| Group | `group_create` | `group_list` (with student count) | `group_edit` | `group_delete` (with confirmation) | prefet (and roles above) |
| Subject | `subject_create` | `subject_list` (with group count) | `subject_edit` | `subject_delete` (with confirmation) | prefet (and roles above) |
| DailyAttendanceStat | `generate_for_date()` classmethod | Via admin | Auto-calculated | Cascade on subject/group delete | Programmatic / admin |

## Models

- **`Group`** -- Student group/class. Fields: `name` (CharField, max 50). Ordered by `name`.
- **`Student`** -- Attendance-specific student record (NOT `accounts.Student`). Fields: `first_name`, `last_name`, `email` (unique), `group` FK. Has `get_attendance_percentage(subject=None)`, `has_low_attendance(threshold=75)`, CSV/JSON import methods.
- **`Subject`** -- Subject taught to groups. Fields: `name`, `teacher` FK (User), `group` M2M (Group), `slug`. Teacher relation scopes session ownership.
- **`Satus`** -- TextChoices enum (NOTE: typo, should be `Status`). Values: `PRESENT`, `ABSENT`, `LATE`.
- **`Attendance`** -- A single attendance session for a subject on a date. Fields: `subject` FK, `date`, `created_at`, `updated_at`. Ordered by `-date`.
- **`AttendanceReport`** -- Individual student status within a session. Fields: `attendance` FK, `student` FK, `status` (Satus choices, default `absent`), `created_at`, `updated_at`. Unique together: `[attendance, student]`. Indexed on `[attendance, status]` and `[student, -created_at]`.
- **`DailyAttendanceStat`** -- Pre-aggregated daily statistics. Fields: `subject` FK, `group` FK, `date`, `total_students`, `present_count`, `absent_count`, `late_count`, `attendance_percentage` (Decimal 5,2). Unique together: `[subject, group, date]`.

## URL Namespaces

- Frontend: `frontend:attendance:<view_name>`
- API: `api:v1:attendance:<resource-name>`

### Frontend Routes

| URL Pattern | View | Name |
|-------------|------|------|
| `attendance/` | `attendance_dashboard` | `dashboard` |
| `attendance/take/` | `take_attendance` | `take_attendance` |
| `attendance/<pk>/mark/` | `mark_attendance` | `mark_attendance` |
| `attendance/<pk>/` | `attendance_detail` | `attendance_detail` |
| `attendance/<pk>/edit/` | `attendance_edit` | `attendance_edit` |
| `attendance/<pk>/delete/` | `attendance_delete` | `attendance_delete` |
| `attendance/student/<student_id>/report/` | `student_attendance_report` | `student_report` |
| `attendance/students/` | `student_list` | `student_list` |
| `attendance/students/create/` | `student_create` | `student_create` |
| `attendance/students/<pk>/edit/` | `student_edit` | `student_edit` |
| `attendance/students/<pk>/delete/` | `student_delete` | `student_delete` |
| `attendance/groups/` | `group_list` | `group_list` |
| `attendance/groups/create/` | `group_create` | `group_create` |
| `attendance/groups/<pk>/edit/` | `group_edit` | `group_edit` |
| `attendance/groups/<pk>/delete/` | `group_delete` | `group_delete` |
| `attendance/subjects/` | `subject_list` | `subject_list` |
| `attendance/subjects/create/` | `subject_create` | `subject_create` |
| `attendance/subjects/<pk>/edit/` | `subject_edit` | `subject_edit` |
| `attendance/subjects/<pk>/delete/` | `subject_delete` | `subject_delete` |

### API Endpoints

| Prefix | ViewSet | Extra Actions |
|--------|---------|---------------|
| `students/` | `StudentViewSet` (read-only) | `GET /<pk>/attendances/?status=` |
| `groups/` | `GroupViewSet` (read-only) | `GET /<pk>/students/`, `GET /<pk>/subjects/` |
| `subjects/` | `SubjectViewSet` (read-only, IsAdminUser) | None |
| `attendances/` | `AttendanceViewSet` (read + create) | `GET /<pk>/reports/?group=`, `GET /date/?day=YYYY-MM-DD` |
| `reports/` | `AttendanceReportViewSet` (CRUD, IsAuthenticatedOrReadOnly) | None |

## Dependencies

- **`accounts`** -- User model (for `Subject.teacher` FK), role decorators (`@lecturer_required`, `@prefet_allowed`, `@role_required`, `@tenant_required`), `accounts.Student` model (for email matching in reports)
- **`django-ratelimit`** -- Rate limiting on all write views and dashboard (50-100 requests/hour)
- **`djangorestframework`** -- API ViewSets, serializers, permissions, pagination
- **`celery`** -- Three stub tasks in `tasks.py` (none implemented yet)

## Files

| File | Purpose |
|------|---------|
| `models.py` | 7 model/enum definitions (Group, Student, Satus, Subject, Attendance, AttendanceReport, DailyAttendanceStat) |
| `views_frontend.py` | 19 template-based views (dashboard, CRUD, reports) |
| `views_api.py` | 5 DRF ViewSets with custom actions |
| `serializers.py` | 6 DRF serializers (Group, Subject, Student, Attendance, AttendanceReport, AttendanceReportView) |
| `forms.py` | 5 Django ModelForms (Attendance, AttendanceReport, Student, Group, Subject) |
| `permissions.py` | `IsTeacher` DRF permission class |
| `pagination.py` | `CustomPagination` (10 items/page with page_size query param) |
| `tasks.py` | 3 Celery task stubs (reminders, stats generation, low attendance alerts) |
| `urls.py` | Frontend and API URL routing with DRF DefaultRouter |
| `admin.py` | Admin registration for all models; `SubjectAdmin` with inline M2M, filters, search |

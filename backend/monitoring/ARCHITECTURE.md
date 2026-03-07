# Monitoring App - Architecture Document

## Overview

The `monitoring` app is a **read-only analytics dashboard** that aggregates data from
multiple apps across the system. It has **no models of its own** -- it queries other
apps' models at runtime via conditional imports and presents cross-domain statistics
to school administrators.

**App label:** `monitoring`
**Verbose name:** Monitoring & Analytics
**Registered in:** `School_System/settings/base.py` INSTALLED_APPS
**URL mount point:** `/monitoring/` (frontend) and `/api/v1/monitoring/` (API)

---

## File Inventory

| File | Purpose |
|---|---|
| `views_frontend.py` | Template-rendered dashboard, detail pages, CSV export |
| `views_api.py` | DRF API endpoints returning JSON statistics |
| `urls.py` | URL routing for both frontend and API namespaces |
| `forms.py` | `DashboardFilterForm` (date range), `ExportFormatForm` (format selector) |
| `serializers.py` | Output-only DRF serializers (no model backing) |
| `apps.py` | Django AppConfig |
| `__init__.py` | Empty module init |

**Files that do NOT exist** (the app intentionally omits them):

- `models.py` -- no database tables
- `admin.py` -- nothing to register
- `signals.py` -- no signal handlers
- `tasks.py` -- no Celery tasks
- `permissions.py` -- reuses `accounts.permissions.IsDirectionUser`

---

## Model Relationships

The monitoring app owns zero models. It reads from six apps via conditional imports.
If an app is not installed, the corresponding section is silently skipped.

```
+-------------------------------------------------------------------+
|                      monitoring (no models)                        |
|                                                                   |
|  Reads from:                                                      |
|                                                                   |
|  accounts.User ─────────────────────────────────────────────────  |
|    Fields queried: tenant, role, gender, date_joined              |
|    Aggregations:   COUNT by role ('student','professor','parent') |
|                    COUNT by gender (GROUP BY gender)              |
|                                                                   |
|  enrollment.RegistrationForm ───────────────────────────────────  |
|    Fields queried: tenant, status, level, created_at              |
|    Aggregations:   COUNT by status                                |
|                    COUNT by (status, level)                        |
|                                                                   |
|  library.Book ──────────────────────────────────────────────────  |
|    Fields queried: tenant, category                               |
|    Aggregations:   COUNT total, COUNT by category                 |
|                                                                   |
|  library.BorrowRecord ──────────────────────────────────────────  |
|    Fields queried: tenant, status, borrowed_at                    |
|    Aggregations:   COUNT by status ('borrowed','overdue',         |
|                    'returned','lost')                              |
|                                                                   |
|  discipline.DisciplinaryAction ─────────────────────────────────  |
|    Fields queried: tenant, is_resolved, created_at                |
|    Aggregations:   COUNT total, COUNT where is_resolved=False     |
|                                                                   |
|  attendance.Attendance ─────────────────────────────────────────  |
|    Fields queried: tenant, status, date                           |
|    Aggregations:   COUNT total, COUNT by status                   |
|                    ('present','absent','late')                     |
|                                                                   |
|  grading.RubricGrade ───────────────────────────────────────────  |
|    Fields queried: graded_at, percentage                          |
|    Aggregations:   COUNT total, AVG(percentage)                   |
+-------------------------------------------------------------------+
```

### Cross-App Entity Relationship Diagram

```
core.School (tenant)
    |
    +--< accounts.User >---------+--- role: student|professor|parent|...
    |       |  .tenant FK         |    .gender: M|F
    |       |  .date_joined       |
    |       |                     |
    |       +--- queried by monitoring for user counts & gender distribution
    |
    +--< enrollment.RegistrationForm
    |       |  .tenant FK
    |       |  .status: pending|under_review|approved|rejected|enrolled
    |       |  .level: Bachelor|Master
    |       |  .created_at
    |       |
    |       +--- queried by monitoring for enrollment stats
    |
    +--< library.Book
    |       |  .tenant FK
    |       |  .category FK -> BookCategory (TreeForeignKey)
    |       |
    |       +--- queried by monitoring for book totals & category breakdown
    |
    +--< library.BorrowRecord
    |       |  .tenant FK
    |       |  .status: borrowed|returned|overdue|lost
    |       |  .borrowed_at
    |       |
    |       +--- queried by monitoring for borrow statistics
    |
    +--< discipline.DisciplinaryAction
    |       |  .tenant FK
    |       |  .is_resolved: bool
    |       |  .created_at
    |       |
    |       +--- queried by monitoring for discipline totals
    |
    +--< attendance.Attendance
    |       |  .tenant (queried with tenant= filter)
    |       |  .status (via AttendanceReport)
    |       |  .date
    |       |
    |       +--- queried by monitoring for attendance breakdown
    |
    +--- grading.RubricGrade
            |  .percentage: Decimal
            |  .graded_at: DateTime
            |
            +--- queried by monitoring for grade averages
```

---

## URL Structure

### Frontend URLs (namespace: `frontend:monitoring`)

| URL Pattern | View Function | Name |
|---|---|---|
| `/monitoring/` | `monitoring_dashboard` | `dashboard` |
| `/monitoring/enrollment-stats/` | `enrollment_statistics` | `enrollment_stats` |
| `/monitoring/library-stats/` | `library_statistics` | `library_stats` |
| `/monitoring/export/csv/` | `export_dashboard_csv` | `export_csv` |

### API URLs (namespace: `api:monitoring`)

| URL Pattern | View Class | Name | Method |
|---|---|---|---|
| `/api/v1/monitoring/dashboard/` | `DashboardStatsAPIView` | `dashboard-stats` | GET |
| `/api/v1/monitoring/enrollment/` | `EnrollmentStatsAPIView` | `enrollment-stats` | GET |
| `/api/v1/monitoring/library/` | `LibraryStatsAPIView` | `library-stats` | GET |
| `/api/v1/monitoring/export/` | `ExportDashboardAPIView` | `export-dashboard` | GET |

---

## View Access Patterns Per Role

### Access Control Mechanism

- **Frontend views** use the `@direction_only` decorator from `accounts.decorators`.
  `direction_only` is a shortcut for `@role_required('secretary', 'direction', 'admin')`.
  Superusers (`is_superuser=True`) always bypass the check.

- **API views** use `permission_classes = [IsAuthenticated, IsDirectionUser]` from
  `accounts.permissions`. `IsDirectionUser.has_permission()` grants access when:
  - `user.is_staff is True`, OR
  - `user.is_superuser is True`, OR
  - `user.role in ('secretary', 'direction', 'admin')`

- **Tenant isolation** is enforced via the `@tenant_required` decorator on frontend views
  and via `request.tenant` filtering in API views.

### Role Access Matrix

```
Role         | Frontend Dashboard | API Endpoints | CSV Export | Notes
-------------|--------------------|----|-----------|------|------
admin        |        YES         | YES |    YES   | is_superuser bypass
direction    |        YES         | YES |    YES   | Primary intended user
secretary    |        YES         | YES |    YES   | Included in direction_only
student      |        NO          | NO  |    NO    | Redirected to /dashboard/
professor    |        NO          | NO  |    NO    | Redirected to /dashboard/
parent       |        NO          | NO  |    NO    | Redirected to /dashboard/
prefet       |        NO          | NO  |    NO    | Not in allowed roles
accountant   |        NO          | NO  |    NO    | Not in allowed roles
librarian    |        NO          | NO  |    NO    | Not in allowed roles
registrar    |        NO          | NO  |    NO    | Not in allowed roles
```

**Summary:** Only three roles have access -- `admin`, `direction`, and `secretary`.
All other roles (student, professor, parent, prefet, accountant, librarian, registrar)
are denied. Superusers always have access regardless of their `role` field value.

---

## Business Logic Workflows

### 1. Dashboard Rendering (Frontend)

```
Browser GET /monitoring/
    |
    v
@login_required --> redirect to login if anonymous
    |
@direction_only --> redirect to /dashboard/ if role not in
    |                (secretary, direction, admin)
@tenant_required --> 403 if user.tenant != request.tenant
    |
@ratelimit(100/h) --> 429 if exceeded
    |
    v
monitoring_dashboard(request)
    |
    +---> Parse DashboardFilterForm from GET params
    |     Extract date_from, date_to (optional)
    |
    +---> Query accounts.User (filtered by tenant + role)
    |     Apply date_joined range if date filters set
    |     -> total_students, total_professors, total_parents
    |
    +---> Query enrollment.RegistrationForm (tenant-scoped)
    |     Apply created_at range if date filters set
    |     -> enrollment_stats: GROUP BY status
    |
    +---> Query accounts.User (students only)
    |     -> gender_stats: GROUP BY gender
    |
    +---> try: import library.models
    |     Query Book (total count), BorrowRecord (by status)
    |     Apply borrowed_at range if date filters set
    |     -> library_stats dict
    |     except ImportError: skip
    |
    +---> try: import discipline.models
    |     Query DisciplinaryAction (total, unresolved)
    |     Apply created_at range if date filters set
    |     -> discipline_stats dict
    |     except ImportError: skip
    |
    +---> try: import attendance.models
    |     Query Attendance (total, present, absent, late)
    |     Apply date range if date filters set
    |     -> attendance_stats dict
    |     except (ImportError, Exception): skip
    |
    +---> try: import grading.models
    |     Query RubricGrade aggregate (COUNT, AVG percentage)
    |     Apply graded_at range if date filters set
    |     -> grade_stats dict
    |     except (ImportError, Exception): skip
    |
    v
render('monitoring/dashboard.html', context)
```

### 2. CSV Export (Frontend)

```
Browser GET /monitoring/export/csv/
    |
    v
[same auth chain: login_required -> direction_only -> tenant_required]
    |
    v
export_dashboard_csv(request)
    |
    +---> Create HttpResponse(content_type='text/csv')
    |     Set Content-Disposition: attachment; filename="dashboard_export.csv"
    |
    +---> Write header row: ['Category', 'Metric', 'Value']
    |
    +---> Write Users section:
    |       ['Users', 'Total Students', count]
    |       ['Users', 'Total Professors', count]
    |       ['Users', 'Total Parents', count]
    |
    +---> Write Enrollment section:
    |       ['Enrollment', 'Status: <status>', count] per status
    |       ['Enrollment', 'Total Enrollments', total]
    |
    +---> Write Gender Distribution section:
    |       ['Gender Distribution', '<gender>', count] per gender
    |
    +---> Write Library section (if importable):
    |       ['Library', 'Total Books', count]
    |       ['Library', 'Currently Borrowed', count]
    |       ['Library', 'Overdue', count]
    |       ['Library', 'Returned', count]
    |       ['Library', 'Lost', count]
    |
    +---> Write Discipline section (if importable):
    |       ['Discipline', 'Total Actions', count]
    |       ['Discipline', 'Resolved', count]
    |       ['Discipline', 'Unresolved', count]
    |
    +---> Write Attendance section (if importable):
    |       ['Attendance', 'Total Records', count]
    |       ['Attendance', 'Present', count]
    |       ['Attendance', 'Absent', count]
    |       ['Attendance', 'Late', count]
    |
    +---> Write Grades section (if importable):
    |       ['Grades', 'Total Grade Entries', count]
    |       ['Grades', 'Average Percentage', avg]
    |
    v
Return CSV HttpResponse
```

### 3. API Dashboard Stats

```
GET /api/v1/monitoring/dashboard/
    |
    v
[IsAuthenticated + IsDirectionUser] permission check
    |
@ratelimit(100/h)
    |
    v
DashboardStatsAPIView.get(request)
    |
    +---> users: {students: N, professors: N, parents: N}
    +---> gender_distribution: [{gender: 'M', count: N}, ...]
    +---> enrollment: [{status: '...', count: N}, ...]
    +---> library: {total_books: N, borrowed: N, overdue: N} | null
    +---> discipline: {total: N, unresolved: N} | null
    |
    v
Response(stats) --> 200 OK JSON
```

### 4. Detailed Enrollment Stats (API)

```
GET /api/v1/monitoring/enrollment/
    |
    v
EnrollmentStatsAPIView.get(request)
    |
    +---> Query RegistrationForm.objects
    |       .filter(tenant=request.tenant)
    |       .values('status', 'level')
    |       .annotate(count=Count('id'))
    |
    v
Response({'stats': [...]}) --> 200 OK
  or
Response({'error': 'Enrollment app not installed'}) --> 503
```

### 5. Detailed Library Stats (API)

```
GET /api/v1/monitoring/library/
    |
    v
LibraryStatsAPIView.get(request)
    |
    +---> books_by_category: Book GROUP BY category
    +---> borrow_status: BorrowRecord GROUP BY status
    |
    v
Response({books_by_category: [...], borrow_status: [...]}) --> 200 OK
  or
Response({'error': 'Library app not installed'}) --> 503
```

---

## Data Flow Diagrams

### Frontend Data Flow

```
                  +------------------+
                  |     Browser      |
                  +--------+---------+
                           |
                    GET /monitoring/
                    + optional ?date_from=&date_to=
                           |
                           v
              +---------------------------+
              |   Django URL Router       |
              |   monitoring:frontend:*   |
              +------------+--------------+
                           |
                           v
              +---------------------------+
              |   views_frontend.py       |
              |   (direction_only guard)  |
              +------+----+----+----+-----+
                     |    |    |    |
         +-----------+    |    |    +------------+
         |                |    |                 |
         v                v    v                 v
+----------------+ +------+----+-----+ +-----------------+
| accounts.User  | | enrollment.     | | library.Book    |
|   .role        | | RegistrationForm| | library.Borrow  |
|   .gender      | |   .status       | |   Record        |
|   .tenant      | |   .level        | |   .status       |
|   .date_joined | |   .created_at   | |   .borrowed_at  |
+----------------+ +-----------------+ +-----------------+
         |                                       |
         |    +------------------+               |
         |    | discipline.      |               |
         |    | DisciplinaryAction|              |
         |    |   .is_resolved   |               |
         |    |   .created_at    |               |
         |    +------------------+               |
         |                                       |
         |    +------------------+    +----------+--------+
         |    | attendance.      |    | grading.          |
         |    | Attendance       |    | RubricGrade       |
         |    |   .status        |    |   .percentage     |
         |    |   .date          |    |   .graded_at      |
         |    +------------------+    +-------------------+
                     |
                     v
              +---------------------------+
              |  Template Engine          |
              |  monitoring/dashboard.html|
              +---------------------------+
                     |
                     v
              +---------------------------+
              |  HTML Response            |
              +---------------------------+
```

### API Data Flow

```
                  +------------------+
                  |   API Client     |
                  +--------+---------+
                           |
              GET /api/v1/monitoring/*
              Authorization: Token <...>
                           |
                           v
              +---------------------------+
              |  DRF Authentication       |
              |  IsAuthenticated          |
              |  IsDirectionUser          |
              +------------+--------------+
                           |
                           v
              +---------------------------+
              |  views_api.py             |
              |  (APIView subclasses)     |
              +------+----+----+----------+
                     |    |    |
         +-----------+    |    +--------+
         v                v             v
+----------------+ +------------+ +------------+
| accounts.User  | | enrollment | | library    |
| (always)       | | (try/catch)| | (try/catch)|
+----------------+ +------------+ +------------+
                     |
         +-----------+
         v
+----------------+
| discipline     |
| (try/catch)    |
+----------------+
                     |
                     v
              +---------------------------+
              |  DRF Response()           |
              |  JSON serialization       |
              +---------------------------+
                     |
                     v
              +---------------------------+
              |  JSON Response            |
              +---------------------------+
```

### Export Data Flow

```
              GET /monitoring/export/csv/
                        |
                        v
              +--------------------+
              | Auth + Decorators  |
              +--------+-----------+
                       |
                       v
              +--------------------+
              | export_dashboard_  |
              | csv(request)       |
              +--------+-----------+
                       |
          +------+-----+------+-------+------+------+
          |      |            |       |      |      |
          v      v            v       v      v      v
        User  Enrollment  Library  Disc.  Attend. Grading
       counts   stats      stats   stats  stats   stats
          |      |            |       |      |      |
          +------+-----+------+-------+------+------+
                       |
                       v
              +--------------------+
              | csv.writer()       |
              | Category/Metric/   |
              | Value rows         |
              +--------+-----------+
                       |
                       v
              +--------------------+
              | HttpResponse       |
              | Content-Type:      |
              |  text/csv          |
              | Content-Disposition|
              |  attachment;       |
              |  filename=         |
              |  dashboard_export  |
              |  .csv              |
              +--------------------+
```

---

## Dependencies

### Apps That Monitoring Depends On (imports from)

| Dependency App | Import | Required? | Failure Mode |
|---|---|---|---|
| `accounts` | `User` model, `IsDirectionUser` permission, `direction_only` / `tenant_required` decorators | **Required** | App will crash at import time |
| `enrollment` | `RegistrationForm` model | **Required** in frontend views (top-level import); conditional in API views | Frontend: crash. API: graceful skip. |
| `library` | `Book`, `BorrowRecord` models | Optional | `try/except ImportError` -- section omitted |
| `discipline` | `DisciplinaryAction` model | Optional | `try/except ImportError` -- section omitted |
| `attendance` | `Attendance` model | Optional | `try/except (ImportError, Exception)` -- section omitted |
| `grading` | `RubricGrade` model | Optional | `try/except (ImportError, Exception)` -- section omitted |
| `core` | `School` model (via `request.tenant`) | **Required** (implicit) | Tenant filtering fails |
| `django_ratelimit` | `@ratelimit` decorator | **Required** | Import error at module load |
| `rest_framework` | DRF `APIView`, `Response`, serializers | **Required** | Import error at module load |

### Apps That Depend On Monitoring (reverse dependencies)

| Dependent | Nature |
|---|---|
| *None* | No other app imports from `monitoring`. It is a leaf node. |

### Dependency Direction Diagram

```
                 REQUIRED                    OPTIONAL (try/except)
                 --------                    ---------------------

accounts ------+
  .models.User |
  .permissions |----> monitoring <---- library.Book
  .decorators  |         ^             library.BorrowRecord
               |         |
enrollment ----+         +------------ discipline.DisciplinaryAction
  .models.             |
  RegistrationForm     +------------ attendance.Attendance
               |         |
core ----------+         +------------ grading.RubricGrade
  .School (tenant)
               |
django_ratelimit
rest_framework
```

---

## Serializers (Output-Only)

All serializers in `serializers.py` are `serializers.Serializer` (not
`ModelSerializer`), since monitoring has no models. They define the
JSON contract for the API responses.

```
DashboardStatsSerializer
  +-- users: UserStatsSerializer
  |     +-- students: IntegerField
  |     +-- professors: IntegerField
  |     +-- parents: IntegerField
  |
  +-- gender_distribution: GenderDistributionSerializer (many=True)
  |     +-- gender: CharField
  |     +-- count: IntegerField
  |
  +-- enrollment: EnrollmentStatsSerializer (many=True)
  |     +-- status: CharField
  |     +-- level: CharField (optional)
  |     +-- count: IntegerField
  |
  +-- library: LibraryStatsSerializer (optional, nullable)
  |     +-- total_books: IntegerField
  |     +-- borrowed: IntegerField
  |     +-- overdue: IntegerField
  |
  +-- discipline: DisciplineStatsSerializer (optional, nullable)
        +-- total: IntegerField
        +-- unresolved: IntegerField


DetailedLibraryStatsSerializer
  +-- books_by_category: BooksByCategorySerializer (many=True)
  |     +-- category: CharField
  |     +-- count: IntegerField
  |
  +-- borrow_status: BorrowStatusSerializer (many=True)
        +-- status: CharField
        +-- count: IntegerField
```

Note: The API views build raw dicts and pass them to `Response()` directly.
The serializers exist to document the contract but are not currently invoked
in the views for validation.

---

## Forms

### DashboardFilterForm

Used in `monitoring_dashboard` to parse GET parameters for date range filtering.

| Field | Type | Required | Widget |
|---|---|---|---|
| `date_from` | DateField | No | `<input type="date" class="form-control">` |
| `date_to` | DateField | No | `<input type="date" class="form-control">` |

**Validation:** `date_from` must be before `date_to` when both are provided.

### ExportFormatForm

Defines export format options (currently only CSV export is wired in the frontend).

| Field | Type | Choices |
|---|---|---|
| `format` | ChoiceField | csv, xlsx, json, pdf |
| `include_charts` | BooleanField | True (default) |

---

## Templates

| Template | Used By | Purpose |
|---|---|---|
| `monitoring/dashboard.html` | `monitoring_dashboard` | Main analytics dashboard |
| `monitoring/enrollment_stats.html` | `enrollment_statistics` | Enrollment detail page |
| `monitoring/library_stats.html` | `library_statistics` | Library detail page |
| `monitoring/not_available.html` | `library_statistics` | Fallback when library app missing |

---

## Rate Limiting

| Endpoint | Rate Limit | Key |
|---|---|---|
| `monitoring_dashboard` (frontend) | 100 requests/hour | `user` |
| `DashboardStatsAPIView` | 100 requests/hour | `user` |
| `EnrollmentStatsAPIView` | 100 requests/hour | `user` |
| `LibraryStatsAPIView` | 100 requests/hour | `user` |
| `ExportDashboardAPIView` | 50 requests/hour | `user` |

The export endpoint has a stricter limit (50/h vs 100/h) because it is more
resource-intensive, querying all six data sources and writing CSV output.

---

## Tenant Isolation

All queries are scoped to `request.tenant`:

- Frontend views: `@tenant_required` decorator ensures `user.tenant == request.tenant`
- API views: all ORM queries include `.filter(tenant=request.tenant)` or `.filter(tenant=tenant)`
- The `Attendance` and `RubricGrade` queries in `monitoring_dashboard` are notable
  exceptions -- the attendance query uses `tenant=request.tenant` but the `RubricGrade`
  query does **not** filter by tenant (it calls `RubricGrade.objects.aggregate(...)` on
  the full table). Similarly, the CSV export's grade section omits tenant filtering.

---

## Design Decisions and Notes

1. **No models by design.** The monitoring app is purely an aggregation layer.
   It never writes data, only reads. This keeps the dependency graph one-directional.

2. **Conditional imports with try/except.** Library, discipline, attendance, and
   grading apps are imported inside function bodies so the monitoring app remains
   functional even when those apps are not installed. The enrollment import in
   `views_frontend.py` is a top-level import and will fail if enrollment is missing.

3. **Enrollment is a hard dependency in the frontend.** `views_frontend.py` has
   `from enrollment.models import RegistrationForm` at module level, meaning the
   enrollment app must be installed for the frontend views to load. The API views
   use a conditional import for enrollment, making them more resilient.

4. **Serializers are documentation, not validation.** The API views build plain
   dicts and return them via `Response()` without passing through the serializers.
   The serializers serve as a formal contract specification.

5. **No write operations.** There are no POST, PUT, PATCH, or DELETE endpoints.
   All views and API endpoints are GET-only (read-only).

6. **Date range filtering** is only available on the main dashboard frontend view.
   The API endpoints do not currently accept date range parameters.

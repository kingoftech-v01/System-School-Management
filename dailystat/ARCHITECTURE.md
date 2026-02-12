# Daily Stat - Architecture

## Overview

The dailystat app is a read-only analytics layer that aggregates daily absence data from the attendance system. It does not create or modify attendance records directly. Instead, a Celery background task (`send_daily_stats`) processes raw `AttendanceReport` records and produces `DailyAttendanceStat` summaries. These summaries are then exposed through frontend HTML views (direction-only), export endpoints (lecturer-accessible), and a REST API.

## Component Diagram

```text
+---------------------+       +---------------------+       +----------------------+
|   attendance app    |       |    dailystat app     |       |     Frontend         |
|                     |       |                      |       |    (Templates)       |
|  AttendanceReport   |------>|  tasks.py            |       |                      |
|  Student            |       |  send_daily_stats()  |       |  dashboard.html      |
|  Subject            |       |        |             |       |  today_stats.html    |
|  Satus (enum)       |       |        v             |       |  date_stats.html     |
|                     |       |  DailyAttendanceStat |------>|  trends.html         |
+---------------------+       |  (models.py)         |       +----------------------+
                              |        |             |
                              |        v             |
                              |  views_frontend.py   |
                              |  views_api.py        |
                              |  serializers.py      |
                              |  filters.py          |
                              +----------------------+
```

## Data Flow

### 1. Data Generation (Celery Task)

The `send_daily_stats` task in `tasks.py` is the sole mechanism for creating `DailyAttendanceStat` records in production.

```text
Celery Beat (scheduler)
    |
    v
send_daily_stats()
    |
    +--> Query AttendanceReport where date = today AND status = ABSENT
    |
    +--> For each absent report:
    |       |
    |       +--> If DailyAttendanceStat exists for (student, day):
    |       |       Add the subject to existing record
    |       |
    |       +--> Else:
    |               Create new DailyAttendanceStat(student, day)
    |               Add the subject
    |
    v
DailyAttendanceStat records ready for querying
```

Key points:
- The task runs once per day (configured in Celery Beat, defined in `School_System/celery.py`).
- Each `DailyAttendanceStat` row represents one student's absences for one day.
- The `subjects` M2M field accumulates all subjects the student was absent from on that day.
- The model also has a legacy `run_report_and_save()` method with hardcoded dates; this is unused and should be removed.

### 2. Data Reading (Frontend Views)

All four primary frontend views follow the same pattern:

```text
HTTP GET request
    |
    v
@login_required --> @direction_only --> @tenant_required --> @ratelimit(100/h)
    |
    v
Query DailyAttendanceStat with filters (date, subject, date range)
    |
    v
Paginate results (50 per page for today_stats and date_stats)
    |
    v
Render HTML template with context
```

View routing summary:

```text
/dailystat/                --> daily_stats_dashboard  (today's summary, max 20 rows)
/dailystat/today/          --> today_stats            (paginated, 50/page)
/dailystat/date/           --> date_stats             (date picker + subject filter)
/dailystat/trends/         --> attendance_trends      (date range, top-10 absentees)
/dailystat/export/csv/     --> export_csv             (lecturer access, CSV download)
/dailystat/export/pdf/     --> export_pdf             (lecturer access, PDF download)
```

### 3. Data Reading (REST API)

The API exposes a single read-only viewset:

```text
GET /dailystat/api/stats/        --> List today's stats (with filters)
GET /dailystat/api/stats/{id}/   --> Retrieve single stat

    |
    v
DailyAttendanceStatViewSet
    |
    +--> Queryset: filter(day=today), ordered by student last name
    +--> Serializer: DailyAttendanceStatSerializer (nested student + subjects)
    +--> Filter backend: DjangoFilterBackend
    +--> Filter class: DailyAttendanceStatFilter
            |
            +--> ?student=<name>    (first/last name icontains)
            +--> ?subjects=<slug>   (exact slug match)
            +--> ?group=<name>      (student group name exact match)
```

HTTP methods allowed: `GET`, `HEAD`, `OPTIONS` only (enforced via `http_method_names`).

## Model Schema

```text
DailyAttendanceStat
+------------+---------------------------+-------------------------------------------+
| Field      | Type                      | Notes                                     |
+------------+---------------------------+-------------------------------------------+
| id         | BigAutoField (PK)         | Auto-generated                            |
| student    | FK -> attendance.Student  | CASCADE delete, related_name='daily_stats'|
| subjects   | M2M -> attendance.Subject | Subjects the student was absent from      |
| day        | DateField                 | Date of the absence record                |
+------------+---------------------------+-------------------------------------------+

Meta:
  - ordering: ['-day']
  - verbose_name: 'Daily Attendance Stat'
```

## Cross-App Dependencies

```text
dailystat
    |
    +--> attendance.models.Student          (FK in DailyAttendanceStat)
    +--> attendance.models.Subject          (M2M in DailyAttendanceStat)
    +--> attendance.models.AttendanceReport (queried in tasks.py)
    +--> attendance.models.Satus            (enum used in tasks.py to filter ABSENT)
    |
    +--> accounts.decorators.direction_only   (frontend view access control)
    +--> accounts.decorators.lecturer_required (export view access control)
    +--> accounts.decorators.tenant_required   (multi-tenant scoping)
    |
    +--> School_System.celery.app             (Celery task registration)
```

Third-party dependencies:

| Package | Usage |
| --- | --- |
| `djangorestframework` | ViewSet, Serializer, DefaultRouter |
| `django-filter` | DjangoFilterBackend, FilterSet |
| `django-ratelimit` | `@ratelimit` decorator on frontend views |
| `reportlab` | PDF generation in `export_pdf` view |
| `celery` | Background task for daily stat generation |

## Access Control Architecture

The app uses a decorator-based access control pattern applied at the view level:

```text
Frontend views (dashboard, today, date, trends):
    @login_required
    @direction_only        <-- Only users with role='direction' pass
    @tenant_required       <-- Multi-tenant scoping
    @ratelimit(100/h)      <-- Rate limiting per user

Export views (CSV, PDF):
    @login_required
    @lecturer_required     <-- Direction and professor roles pass

API viewset:
    No explicit permission class (inherits DRF defaults)
    http_method_names = ['get', 'head', 'options']  <-- Read-only enforcement
```

There is no object-level permission logic. All queries are unscoped within the tenant -- any direction user sees all students' stats for the current tenant.

## Forms

### DailyStatFilterForm

Used by `date_stats` and `attendance_trends` views for date selection.

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `date` | DateField | No | Single date lookup (date_stats view) |
| `start_date` | DateField | No | Range start (trends view) |
| `end_date` | DateField | No | Range end (trends view) |

Validation rules:
- `start_date` must be before `end_date`
- Date range cannot exceed 90 days

## Serialization (API)

`DailyAttendanceStatSerializer` outputs nested representations:

- `student` field: serialized as `{id, first_name, last_name}` via `SerializerMethodField`
- `subjects` field: serialized as list of `{id, name}` via `SerializerMethodField`; subject names are cleaned by stripping parenthetical suffixes (e.g., "Mathematics (L3)" becomes "Mathematics")

## Template Layout

Templates are stored in the project-level `templates/dailystat/` directory (not inside the app):

| Template | View | Description |
| --- | --- | --- |
| `dashboard.html` | `daily_stats_dashboard` | Summary dashboard with today's absent count |
| `today_stats.html` | `today_stats` | Paginated list of today's absentees |
| `date_stats.html` | `date_stats` | Date picker form with results table |
| `trends.html` | `attendance_trends` | Date range form with daily counts and frequent absentees |

## Error Handling

Current error handling approach:

- **Frontend views** (`daily_stats_dashboard`, `today_stats`): Use bare `except:` clauses to fall back to the most recent day if today's query fails. This silently swallows all exceptions.
- **API viewset** (`get_queryset`): Same bare `except:` pattern; falls back to the last available day. Additionally, calling `.first().day` without a null check will raise `AttributeError` if no records exist at all.
- **Date stats view**: Uses specific `except (Subject.DoesNotExist, ValueError)` for subject filter -- this is the correct pattern.

Recommended improvement: Replace all bare `except:` clauses with `except DailyAttendanceStat.DoesNotExist:` or `except Exception:` with logging.

## Test Architecture

Tests are organized in `dailystat/tests/` with one module per component:

```text
dailystat/tests/
    __init__.py
    test_models.py           <-- Model creation, fields, ordering, str representation
    test_views_frontend.py   <-- All 6 frontend views (access, rendering, pagination)
    test_views_api.py        <-- API list/retrieve, filtering
    test_forms.py            <-- Form validation (date ranges, 90-day limit)
    test_serializers.py      <-- Serializer output format
    test_tasks.py            <-- Celery task creates correct records
    test_filters.py          <-- FilterSet query parameter behavior
    test_admin.py            <-- Admin site registration
```

All tests share a common setup pattern: create `Student`, `Subject`, and `AttendanceReport` fixtures from the attendance app, then run the component under test against `DailyAttendanceStat` records.

# Daily Stat App

Pre-aggregated daily attendance statistics and absence trend reporting.

## Description

The dailystat app provides a read-only statistics layer on top of the attendance data. It displays daily absent student counts, allows date-based lookups, and shows attendance trends over configurable date ranges including frequent absentee identification. Frontend views are restricted to the direction role. Export views (CSV/PDF) are available to lecturers. The app also exposes a read-only REST API for programmatic access with filtering support.

## Main Features

- **Dashboard**: Today's absent students with summary counts (capped at 20 entries)
- **Today's Stats**: Detailed view of today's absentees with pagination (50 per page)
- **Date Stats**: Look up absentees for any specific date using a date picker, with optional subject filter
- **Attendance Trends**: Trend display over a configurable date range (default 7 days, max 90 days) with top-10 frequent absentee list
- **CSV Export**: Download daily stats as CSV grouped by date and subject (lecturer access)
- **PDF Export**: Download daily stats as PDF via reportlab (lecturer access)
- **REST API**: Read-only API endpoint with student, subject (by slug), and group filters
- **Celery Task**: Background task to generate DailyAttendanceStat records from today's absent AttendanceReports

## User Roles

| Role | Frontend Views | Export Views | API Access |
|------|---------------|--------------|------------|
| student | No access | No access | No access |
| professor | No access | CSV, PDF export | No access |
| direction | Full access (dashboard, today, date, trends) | CSV, PDF export | Full read access |
| parent | No access | No access | No access |
| admin | No access | No access | No access |
| prefet | No access | No access | No access |
| accountant | No access | No access | No access |
| secretary | No access | No access | No access |
| librarian | No access | No access | No access |
| registrar | No access | No access | No access |

Note: Frontend views use `@direction_only`. Export views use `@lecturer_required` (which includes direction and professor roles). The API viewset has no explicit permission class beyond DRF defaults.

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| DailyAttendanceStat | Via Celery task only | Yes (dashboard, today, date, trends, API) | N/A | N/A |

## Models

### DailyAttendanceStat

Defined in `dailystat/models.py` (not imported from attendance -- this app owns the model).

| Field | Type | Description |
|-------|------|-------------|
| `student` | ForeignKey(Student) | The absent student (CASCADE, related_name='daily_stats') |
| `subjects` | ManyToManyField(Subject) | Subjects the student was absent from |
| `day` | DateField | The date of the absence record |

- Ordering: `-day` (most recent first)
- Contains a legacy method `run_report_and_save()` with hardcoded date values (superseded by the Celery task)

## Frontend URL Endpoints

All frontend views are under the namespace `frontend:dailystat:<view_name>`.

| URL Pattern | View | Name | Access | Description |
|-------------|------|------|--------|-------------|
| `/` | `daily_stats_dashboard` | `dashboard` | direction | Main dashboard with today's stats |
| `/today/` | `today_stats` | `today_stats` | direction | Paginated today's absentees |
| `/date/` | `date_stats` | `date_stats` | direction | Date picker lookup with subject filter |
| `/trends/` | `attendance_trends` | `trends` | direction | Trend analysis over date range |
| `/export/csv/` | `export_csv` | `export_csv` | lecturer | CSV download |
| `/export/pdf/` | `export_pdf` | `export_pdf` | lecturer | PDF download |

## API Endpoints

All API endpoints are under the namespace `api:v1:dailystat:<resource-name>`. The API uses Django REST Framework with a `DefaultRouter`.

| Method | URL Pattern | Description |
|--------|-------------|-------------|
| GET | `/api/stats/` | List today's DailyAttendanceStat records |
| GET | `/api/stats/{id}/` | Retrieve a single DailyAttendanceStat record |

### API Query Parameters (Filters)

| Parameter | Type | Description |
|-----------|------|-------------|
| `student` | string | Filter by student first or last name (case-insensitive contains) |
| `subjects` | string | Filter by subject slug (exact match) |
| `group` | string | Filter by student group name (exact match) |

### API Response Format

```json
{
    "id": 1,
    "student": {
        "id": 42,
        "first_name": "John",
        "last_name": "Doe"
    },
    "subjects": [
        {
            "id": 5,
            "name": "Mathematics"
        }
    ],
    "day": "2025-01-15"
}
```

## File Structure

```
dailystat/
    __init__.py
    apps.py                  # DailystatConfig
    models.py                # DailyAttendanceStat model
    views_frontend.py        # 6 frontend views (4 dashboard + 2 export)
    views_api.py             # DailyAttendanceStatViewSet (read-only)
    urls.py                  # Frontend and API URL routing
    forms.py                 # DailyStatFilterForm (date/date-range picker)
    filters.py               # DailyAttendanceStatFilter (DRF filter)
    serializers.py           # DailyAttendanceStatSerializer
    tasks.py                 # Celery task: send_daily_stats()
    admin.py                 # DailyAttendanceStatAdmin
    tests/
        __init__.py
        test_models.py       # Model tests
        test_views_frontend.py  # Frontend view tests
        test_views_api.py    # API view tests
        test_forms.py        # Form validation tests
        test_serializers.py  # Serializer tests
        test_tasks.py        # Celery task tests
        test_filters.py      # API filter tests
        test_admin.py        # Admin registration tests
templates/
    dailystat/
        dashboard.html       # Dashboard template
        today_stats.html     # Today's stats template
        date_stats.html      # Date lookup template
        trends.html          # Trends template
```

## Dependencies

| Dependency | Usage |
|-----------|-------|
| `attendance` | DailyAttendanceStat references Student, Subject; tasks.py uses AttendanceReport, Satus |
| `accounts` | Role-based decorators (`direction_only`, `lecturer_required`, `tenant_required`) |
| `django-ratelimit` | Rate limiting on all frontend views (100 requests/hour per user) |
| `django-filter` | DRF filter backend for API viewset |
| `djangorestframework` | REST API viewset, serializers, routers |
| `reportlab` | PDF generation in export_pdf view |
| `celery` | Background task for generating daily stats (`School_System.celery`) |

## URL Namespace

- Frontend: `frontend:dailystat:<view_name>`
- API: `api:v1:dailystat:<resource-name>`

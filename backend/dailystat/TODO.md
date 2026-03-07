# Daily Stat - TODO

## Backend

- [ ] Add subject-level filtering on date stats view -- currently shows all subjects
- [ ] Implement present count calculation in export views -- CSV and PDF both output '-' as placeholder for present count (`views_frontend.py:259`)
- [ ] Replace bare `except:` clauses with specific exception types (`views_frontend.py:57-58`, `views_frontend.py:98-99`, `views_api.py:25`)
- [ ] Fix duplicate import in `models.py:3` -- `from attendance.models import Satus, Subject` imported twice; keep only one import line
- [ ] Fix duplicate import in `tasks.py:3-4` -- `Subject` imported twice from attendance.models
- [ ] Add permission class to `DailyAttendanceStatViewSet` -- currently has no explicit DRF permission restriction
- [ ] Remove legacy `run_report_and_save()` method from `DailyAttendanceStat` model -- contains hardcoded date (Nov 18, 2022) and uses `self.objects` incorrectly; replaced by Celery task
- [ ] Add caching to API viewset -- `cache_page` decorator is commented out in `views_api.py:18-20`

## Frontend

- [ ] Add chart visualization on trends page -- currently text/table only, no graphs
- [ ] Add clickable student names on absent student lists linking to attendance reports
- [ ] Add subject filter dropdown on today_stats page -- date_stats already supports subject filtering

## Sidebar

- [ ] Add "Daily Stats" entry to sidebar under ANALYTICS section with sub-links: Dashboard, Trends

## Security

- [ ] No critical security issues found
- [ ] Rate limiting is in place on all frontend views (100/hour per user)

## Unnecessary Files

- [ ] None identified

## Documentation

- [x] README.md written with full API endpoints, file structure, and role table
- [x] ARCHITECTURE.md written with data flow and component diagrams
- [ ] Add inline docstrings to `filters.py` filter methods
- [ ] Add inline docstrings to `serializers.py` custom methods

## Testing

Test suite location: `dailystat/tests/`

Existing test modules:

- [x] `test_models.py` -- DailyAttendanceStat model tests
- [x] `test_views_frontend.py` -- Frontend view tests (dashboard, today, date, trends, exports)
- [x] `test_views_api.py` -- API viewset tests
- [x] `test_forms.py` -- DailyStatFilterForm validation tests
- [x] `test_serializers.py` -- DailyAttendanceStatSerializer tests
- [x] `test_tasks.py` -- Celery task `send_daily_stats()` tests
- [x] `test_filters.py` -- DailyAttendanceStatFilter tests
- [x] `test_admin.py` -- Admin registration tests

Missing or additional test coverage needed:

- [ ] Add test for `export_csv` with empty data (no stats)
- [ ] Add test for `export_pdf` with empty data (no stats)
- [ ] Add test for `date_stats` subject filter with invalid subject ID
- [ ] Add test for `attendance_trends` with date range exceeding 90-day limit
- [ ] Add test for API viewset when no DailyAttendanceStat records exist (bare except may hide errors)
- [ ] Add role-based access tests ensuring non-direction roles get 403/redirect on frontend views
- [ ] Add role-based access tests ensuring non-lecturer roles get 403/redirect on export views

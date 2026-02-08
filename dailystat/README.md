# Daily Stat App

Pre-aggregated daily attendance statistics and absence trend reporting.

## Description

The dailystat app provides a read-only statistics layer on top of the attendance data. It displays daily absent student counts, allows date-based lookups, and shows attendance trends over configurable date ranges including frequent absentee identification. All views are restricted to direction role only.

## Main Features

- **Dashboard**: Today's absent students with summary counts
- **Today's Stats**: Detailed view of today's absentees with pagination
- **Date Stats**: Look up absentees for any specific date using a date picker
- **Attendance Trends**: Trend display over a date range with frequent absentee list

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full access to all views |
| other roles | No access |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| DailyAttendanceStat | N/A (read-only) | Yes (dashboard, today, date, trends) | N/A | N/A |

## Models

- `DailyAttendanceStat` -- pre-aggregated daily statistics (model defined in attendance app)

## Dependencies

- `attendance` (DailyAttendanceStat model)
- `accounts` (role decorators)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:dailystat:<view_name>`
- API: `api:v1:dailystat:<resource-name>`

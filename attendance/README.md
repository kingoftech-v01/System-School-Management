# Attendance App

Classroom attendance tracking with session management, student marking, and reporting.

## Description

The attendance app manages classroom attendance with its own Student, Group, and Subject models (separate from the accounts app). Lecturers create attendance sessions for a subject and date, then mark individual students as present, absent, or late. The app includes a dashboard, detailed reports, and pre-aggregated daily statistics via the DailyAttendanceStat model.

## Main Features

- **Attendance Dashboard**: Overview of today's and recent attendance sessions for the lecturer
- **Take Attendance**: Create attendance session by selecting subject and date
- **Mark Attendance**: Bulk mark students (present/absent/late) for an attendance session
- **Attendance Detail**: View session summary with counts per status
- **Student Reports**: Per-student attendance report with percentage and subject filtering
- **Student/Group/Subject Lists**: Browse students, groups, and subjects (read-only lists)

## User Roles

| Role | Permissions |
|------|------------|
| direction | View student list, group list, subject list |
| professor/lecturer | Create sessions, mark attendance, view dashboard |
| student | View own attendance report (via student report) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Attendance (session) | Yes | Yes (dashboard + detail) | No | No |
| AttendanceReport | Yes (via mark) | Yes | Yes (re-mark) | No |
| Student | No | Yes (list) | No | No |
| Group | No | Yes (list) | No | No |
| Subject | No | Yes (list) | No | No |

## Models

- `Group` -- student group/class
- `Student` -- attendance-specific student record
- `Subject` -- subject taught to groups, teacher FK
- `Attendance` -- session for a subject and date
- `AttendanceReport` -- individual student status (present/absent/late)
- `DailyAttendanceStat` -- pre-aggregated daily statistics

## Dependencies

- `accounts` (User model for subject teachers, role decorators)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:attendance:<view_name>`
- API: `api:v1:attendance:<resource-name>`

# Monitoring App

Direction-only analytics dashboard aggregating system-wide statistics from students, enrollment, library, and discipline with CSV export.

## Description

The monitoring app provides a central dashboard for direction to view system-wide statistics. It aggregates data from multiple apps (accounts, enrollment, library, discipline) using conditional imports. The app includes enrollment statistics, library statistics, and CSV export of dashboard metrics.

## Main Features

- **Main Dashboard**: Student/professor/parent counts, enrollment stats by status, gender distribution
- **Enrollment Statistics**: Status and level breakdown of enrollment data
- **Library Statistics**: Books by category, borrow status breakdown
- **CSV Export**: Export dashboard metrics to CSV
- **Cross-App Data**: Conditional imports from library, discipline apps

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full access to all monitoring views and exports |
| all others | No access |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Dashboard Data | N/A | Yes (read-only) | N/A | N/A |

## Models

- No models of its own (reads from other apps)

## Dependencies

- `accounts` (User model)
- `enrollment` (RegistrationForm model)
- `library` (Book, BorrowRecord -- optional, conditional import)
- `discipline` (DisciplinaryAction -- optional, conditional import)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:monitoring:<view_name>`

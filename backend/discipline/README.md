# Discipline App

Student disciplinary action tracking with severity levels and resolution management.

## Description

The discipline app tracks student disciplinary incidents with details including incident type, description, action taken, severity level, and resolution status. Each action is linked to a tenant (school), the student involved, and the reporting staff member. The app currently has 3 frontend views providing create, list, and detail operations.

## Main Features

- **Action List**: View all disciplinary actions for the school, ordered by incident date
- **Create Action**: Record new disciplinary incident with severity and action taken
- **Action Detail**: View full details of a disciplinary record

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full access: list, create, detail |
| other roles | No frontend access |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| DisciplinaryAction | Yes | Yes (list + detail) | No | No |

## Models

- `DisciplinaryAction` -- tenant FK, student FK, reported_by FK, incident_type, description, action_taken, severity (minor/moderate/serious/critical), incident_date, resolution_date, is_resolved

## Dependencies

- `accounts` (User model for student and reporter, role decorators)
- `core` (School model for tenant)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:discipline:<view_name>`
- API: `api:v1:discipline:<resource-name>`

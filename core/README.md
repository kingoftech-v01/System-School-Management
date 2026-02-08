# Core App

Central app providing tenant models, role-based dashboards, news/events, and academic session/semester management.

## Description

The core app is the backbone of the School Management System. It provides the School (tenant) model with conditional multi-tenancy support (TenantMixin in production, plain Model in development), role-based unified dashboards that route to student/parent/professor/direction/admin views, news and events management, and academic session and semester configuration.

## Main Features

- **Unified Dashboard**: Single entry point that routes to role-specific dashboards (student, parent, professor, direction, admin)
- **News & Events**: Full CRUD for news posts and event announcements
- **Session Management**: Full CRUD for academic sessions with current-session toggle
- **Semester Management**: Full CRUD for semesters linked to sessions with current-semester toggle
- **Activity Log**: System-wide activity logging
- **School/Tenant Model**: Multi-tenant school configuration with subscription management

## User Roles

| Role | Permissions |
|------|------------|
| admin | Admin dashboard, full session/semester CRUD, activity logs |
| direction | Direction dashboard with school-wide statistics |
| professor | Professor dashboard, session/semester CRUD, news CRUD |
| student | Student dashboard (read-only) |
| parent | Parent dashboard (read-only) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| NewsAndEvents | Yes | Yes (list) | Yes | Yes |
| Session | Yes | Yes (list) | Yes | Yes |
| Semester | Yes | Yes (list) | Yes | Yes |

## Models

- `School` (TenantMixin/Model) -- name, slug, email, phone, logo, subscription_type, max_students, max_staff
- `Domain` (DomainMixin/Model) -- domain routing for tenants
- `NewsAndEvents` -- title, summary, posted_as (News/Event), updated_date
- `Session` -- session name, is_current_session flag
- `Semester` -- semester name, session FK, is_current_semester flag
- `ActivityLog` -- system-wide activity tracking

## Dependencies

- `accounts` (User, Student, Parent models, role decorators)
- `result` (TakenCourse for student dashboard)
- `course` (Course for professor dashboard)
- `payments` (Invoice for direction dashboard)

## URL Namespace

- Frontend: `frontend:core:<view_name>`
- API: `api:v1:core:<resource-name>`

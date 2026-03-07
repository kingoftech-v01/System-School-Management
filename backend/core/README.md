# Core App

Central app providing tenant models, role-based dashboards, news/events, and academic session/semester management.

## Description

The core app is the backbone of the School Management System. It provides the School (tenant) model with conditional multi-tenancy support (TenantMixin in production, plain Model in development), role-based unified dashboards that route to specialized views for each of the 10 user roles, news and events management with i18n support, academic session and semester configuration, and system-wide activity logging.

## Main Features

- **Unified Dashboard**: Single entry point (`unified_dashboard`) routing to role-specific dashboards for all 10 roles
- **News & Events**: Full CRUD for news posts and event announcements with translation support (modeltranslation)
- **Session Management**: Full CRUD for academic sessions with current-session toggle
- **Semester Management**: Full CRUD for semesters linked to sessions with current-semester toggle
- **Activity Log**: System-wide activity logging for audit trails
- **School/Tenant Model**: Multi-tenant school configuration with subscription management and validation
- **Beta Data Generator**: Management command `generate_beta_data` for populating test data
- **Template Tags**: Custom tags (`custom_tags.py`) and HTML sanitization (`sanitize.py`)

## User Roles

| Role | Permissions |
|------|------------|
| admin | Admin dashboard, full session/semester CRUD, activity logs, admin panel |
| direction | Direction dashboard with school-wide statistics, session/semester CRUD, news CRUD |
| professor | Professor dashboard with teaching info, news CRUD |
| student | Student dashboard with grades, attendance, courses (read-only) |
| parent | Parent dashboard with child's academic info (read-only) |
| prefet | Discipline officer dashboard with incident tracking |
| accountant | Financial dashboard with payment/invoice statistics |
| secretary | Academic management dashboard |
| librarian | Library management dashboard with book/borrow stats |
| registrar | Enrollment and certificate management dashboard |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| NewsAndEvents | Yes | Yes (list + detail) | Yes | Yes |
| Session | Yes | Yes (list) | Yes | Yes |
| Semester | Yes | Yes (list) | Yes | Yes |
| ActivityLog | No | Yes (API only) | No | No |

## Models

- `School` (TenantMixin/Model) -- name, slug, email, phone, logo, subscription_type, max_students, max_staff, subscription dates
- `Domain` (DomainMixin/Model) -- domain routing for tenants
- `NewsAndEvents` -- title, summary, posted_as (News/Event), updated_date, upload_time; custom manager with search
- `Session` -- session name, is_current_session flag, next_session_begins date
- `Semester` -- semester name (First/Second/Third), session FK, is_current_semester flag
- `ActivityLog` -- message text, created_at timestamp

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | /api/v1/core/sessions/ | List/create sessions |
| GET/PUT/DELETE | /api/v1/core/sessions/{id}/ | Session detail/update/delete |
| POST | /api/v1/core/sessions/{id}/set_current/ | Set session as current |
| GET | /api/v1/core/sessions/current/ | Get current session |
| GET/POST | /api/v1/core/semesters/ | List/create semesters |
| GET/PUT/DELETE | /api/v1/core/semesters/{id}/ | Semester detail/update/delete |
| GET/POST | /api/v1/core/news/ | List/create news & events |
| GET/PUT/DELETE | /api/v1/core/news/{id}/ | News detail/update/delete |
| GET | /api/v1/core/activity-logs/ | List activity logs (read-only) |

## Dependencies

- `accounts` (User, Student, Parent models, role decorators)
- `result` (TakenCourse for student dashboard)
- `course` (Course, CourseAllocation for professor dashboard)
- `payments` (Invoice for direction dashboard)
- `modeltranslation` (i18n for NewsAndEvents)

## Configuration

- `USE_TENANTS`: Auto-detected from `INSTALLED_APPS` -- controls whether School uses TenantMixin or plain Model
- `EMAIL_FROM_ADDRESS`: Used by `utils.py` for sending emails
- `FIRST`, `SECOND`, `THIRD`: Semester choice constants exported for use by other apps

## URL Namespace

- Frontend: `frontend:core:<view_name>`
- API: `api:v1:core:<resource-name>`
- Public: `core_public:landing`

## File Structure

```
core/
  models.py              -- School, Domain, NewsAndEvents, Session, Semester, ActivityLog
  views.py               -- Legacy views (home, dashboard, news/session/semester CRUD)
  views_frontend.py      -- Extended views with all 10 role dashboards, news search
  views_api.py           -- DRF ViewSets for Session, Semester, News, ActivityLog
  urls.py                -- Frontend + API URL routing
  urls_public.py         -- Public landing page URL
  serializers.py         -- DRF serializers for all models
  forms.py               -- NewsAndEventsForm, SessionForm, SemesterForm
  admin.py               -- Admin config with conditional TenantAdminMixin
  utils.py               -- send_email, send_html_email, slug generators
  translation.py         -- modeltranslation config for NewsAndEvents
  templatetags/
    custom_tags.py       -- Custom template tags
    sanitize.py          -- HTML sanitization filters
  management/commands/
    generate_beta_data.py -- Beta data population command
  tests/                 -- Comprehensive test suite (models, views, API, forms, tags)
```

# Core - Architecture

## Overview

The core app is the foundational layer of the entire School Management System. It provides the tenant model (School), academic configuration (Session, Semester), content management (NewsAndEvents), and system-wide audit logging (ActivityLog). Nearly every other app depends on core for tenant context and academic period references. The app uses conditional imports to support both multi-tenant production (django-tenants with PostgreSQL) and single-tenant development (SQLite).

## Models & Relationships

### Entity-Relationship Summary

```
School ──1:N──> Domain
Session ──1:N──> Semester
NewsAndEvents (standalone)
ActivityLog (standalone)
```

### Model Details

#### School
- **Purpose**: Represents an individual school/tenant in the multi-tenant system
- **Key Fields**: name, slug, email, phone, address, logo, subscription_type, subscription_start/end, max_students, max_staff, is_active
- **Relationships**: 1:N to Domain (via DomainMixin or FK)
- **Business Rules**:
  - Conditional implementation: TenantMixin (production) vs plain Model (development)
  - `auto_create_schema = True` in production (auto-creates PostgreSQL schema)
  - `auto_drop_schema = False` (safety: never auto-delete schemas)
  - `is_subscription_valid()` checks is_active AND subscription_end >= today

#### Domain
- **Purpose**: Routes HTTP requests to the correct tenant
- **Key Fields**: domain (unique), is_primary
- **Relationships**: FK to School

#### NewsAndEvents
- **Purpose**: School news posts and event announcements
- **Key Fields**: title, summary, posted_as (News/Event), updated_date, upload_time
- **Managers**: `NewsAndEventsManager` with custom QuerySet supporting `search(query)` via Q lookups on title/summary/posted_as
- **Business Rules**: Translatable fields (title, summary) via modeltranslation

#### Session
- **Purpose**: Academic year/session (e.g., "2024/2025")
- **Key Fields**: session (unique CharField), is_current_session (boolean), next_session_begins (date)
- **Business Rules**: Only one session should have `is_current_session=True` at a time (enforced via API action)

#### Semester
- **Purpose**: Academic semester within a session
- **Key Fields**: semester (First/Second/Third choice), is_current_semester (boolean), next_semester_begins (date)
- **Relationships**: FK to Session (nullable)

#### ActivityLog
- **Purpose**: System-wide audit trail for significant actions
- **Key Fields**: message (TextField), created_at (auto DateTimeField)

## View Logic Flow

### Frontend Views (`views_frontend.py`)

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| `home_view` | GET | No | all | News/events list (landing page) |
| `unified_dashboard` | GET | Yes | all | Routes to role-specific dashboard |
| `render_student_dashboard` | GET | Yes | student | Personal grades, attendance, courses |
| `render_parent_dashboard` | GET | Yes | parent | Child's academic info |
| `render_professor_dashboard` | GET | Yes | professor | Teaching courses, student counts |
| `render_direction_dashboard` | GET | Yes | direction | School-wide stats, quick links |
| `render_secretary_dashboard` | GET | Yes | secretary | Academic management focus |
| `render_prefet_dashboard` | GET | Yes | prefet | Discipline incidents dashboard |
| `render_accountant_dashboard` | GET | Yes | accountant | Financial stats dashboard |
| `render_librarian_dashboard` | GET | Yes | librarian | Book/borrow statistics |
| `render_registrar_dashboard` | GET | Yes | registrar | Enrollment/certificate stats |
| `post_add` | GET/POST | Yes | any* | Create news/event (*needs restriction) |
| `edit_post` | GET/POST | Yes | any | Edit news/event |
| `delete_post` | GET | Yes | any | Delete news/event |
| `post_detail` | GET | Yes | all | Single news/event detail |
| `news_search` | GET | Yes | all | Search news with pagination |
| Session/Semester CRUD | GET/POST | Yes | direction+ | Full CRUD for academic config |

### API Views (`views_api.py`)

| ViewSet | Methods | Auth | Roles | Description |
|---------|---------|------|-------|-------------|
| `SessionViewSet` | list, create, retrieve, update, destroy | Yes | all | Session CRUD + `current`, `set_current` actions |
| `SemesterViewSet` | list, create, retrieve, update, destroy | Yes | all | Semester CRUD + custom actions |
| `NewsAndEventsViewSet` | list, create, retrieve, update, destroy | Yes | all | News/events CRUD with type filtering |
| `ActivityLogViewSet` | list, retrieve | Yes | admin | Read-only activity logs |

### Key Patterns

- `unified_dashboard` uses a role-to-renderer mapping dict for clean routing
- Dashboard renderers query data from multiple apps (accounts, course, result, payments)
- Conditional multi-tenancy: `USE_TENANTS = 'django_tenants' in settings.INSTALLED_APPS`
- Admin config conditionally uses `TenantAdminMixin` based on `USE_TENANTS`

## Business Logic

### Core Workflows

#### Dashboard Routing
1. User hits `/` or dashboard URL
2. `unified_dashboard` determines user role via `request.user.role`
3. Dispatches to role-specific renderer function
4. Renderer queries data from this app + dependent apps
5. Returns rendered template with context

#### Session/Semester Management
1. Direction user creates session (e.g., "2024/2025")
2. Creates semesters linked to session
3. Marks one session and one semester as "current"
4. `set_current` API action toggles the flag (should unset others)

#### News/Events Lifecycle
1. Authorized user creates post via form (posted_as: News or Event)
2. Post appears on home page list (reverse chronological)
3. Translatable via modeltranslation (title, summary)

### Validation Rules

- Session name must be unique
- Semester choices limited to First/Second/Third
- School subscription validated via `is_subscription_valid()` comparing end date to today

## Inter-App Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
|-----|----------------------|---------|
| `accounts` | User, Student, Parent, decorators | Dashboard data, role checks |
| `result` | TakenCourse | Student dashboard grade display |
| `course` | Course, CourseAllocation | Professor dashboard course listing |
| `payments` | Invoice | Direction dashboard financial stats |

### Apps That Depend On This App

| App | What They Use | Purpose |
|-----|--------------|---------|
| `accounts` | School (tenant) | User.tenant FK |
| `course` | Semester, ActivityLog | Course registration filtering, audit |
| `scheduling` | School, Session, Semester | Timetable tenant/period context |
| `filieres` | School | Filiere.tenant FK |
| `enrollment` | School | Enrollment tenant context |
| `discipline` | School | Incident tenant context |
| `library` | School | Library tenant context |
| `events` | School | Event tenant context |
| `notes` | School, Session, Semester | Note context |
| `attendance` | (indirect) | Academic period references |
| `anomaly_detection` | (indirect) | Tenant context |

### Dependency Diagram

```
                    ┌──────────────┐
    accounts ──────>│              │<────── scheduling
    result ────────>│     CORE     │<────── filieres
    course ────────>│              │<────── enrollment
    payments ──────>│  School      │<────── discipline
                    │  Session     │<────── library
                    │  Semester    │<────── events
                    │  ActivityLog │<────── notes
                    └──────────────┘
```

## Data Flow

### Request/Response Flow

```
User Request
    │
    ▼
urls.py / urls_public.py (route matching)
    │
    ├── Frontend: views_frontend.py
    │   ├── forms.py (validation)
    │   └── models.py (data access)
    │
    └── API: views_api.py
        ├── serializers.py (validation + serialization)
        └── models.py (data access)
    │
    ▼
Template / JSON Response
```

### Key Data Paths

- **Dashboard**: Request -> `unified_dashboard` -> role dispatch -> multi-app queries -> rendered template
- **News CRUD**: Request -> form validation -> `NewsAndEvents.objects.create/update` -> redirect
- **Session Toggle**: API POST -> `set_current` action -> update boolean flag -> JSON response

## Technical Notes

- Conditional imports for django-tenants (`USE_TENANTS` flag) -- School model definition changes at module load time
- `NewsAndEventsManager` provides custom QuerySet with chainable `search()` method
- Translation support via `translation.py` registering `title` and `summary` fields with `empty_values = None`
- Custom template tags in `templatetags/custom_tags.py` and `sanitize.py` for safe HTML rendering
- `utils.py` provides shared email and slug generation utilities used across multiple apps
- Management command `generate_beta_data` creates sample data for development/testing

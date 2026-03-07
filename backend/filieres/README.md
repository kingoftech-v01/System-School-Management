# Filieres App

Academic program (filiere) management with subject assignments, admission requirements, and enrollment tracking per tenant.

## Description

The filieres app manages academic tracks/programs with their associated subjects and admission requirements. It provides full CRUD for filieres with search and filtering, subject management with coefficients (add, edit, remove), requirement management (add, edit, remove), and enrollment counts annotated on list views. Safety checks prevent deletion of filieres with enrolled students.

## Main Features

- **Filiere CRUD**: Full create, list, detail, edit, delete with search and filter
- **Subject Management**: Add, edit, and remove subjects per filiere with coefficient, year, semester, credits, hours_per_week
- **Requirement Management**: Add, edit, and remove admission requirements per filiere
- **Enrollment Tracking**: Enrollment count annotations on list view via `RegistrationForm` relation
- **Safety Checks**: Prevents deletion of filieres with enrolled students (both frontend and API)
- **Capacity Tracking**: `is_full()` checks enrollment against capacity limit
- **Coordinator Assignment**: Assign a professor or direction user as program coordinator
- **REST API**: Full CRUD API with DRF ViewSets, filtering, search, and ordering

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full CRUD for filieres, subjects, requirements (frontend + API) |
| admin | Full access via API (superuser) |
| professor | View filiere list and detail; may be assigned as coordinator |
| student | View filiere list and detail |
| parent | View filiere list and detail (read-only) |
| prefet | View filiere list and detail |
| accountant | View filiere list and detail |
| secretary | View filiere list and detail |
| librarian | View filiere list and detail |
| registrar | View filiere list and detail |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Filiere | Yes (direction) | Yes (list + detail) | Yes (direction) | Yes (direction, safety check) |
| FiliereSubject | Yes (direction) | Yes (via detail) | Yes (direction) | Yes (direction) |
| FiliereRequirement | Yes (direction) | Yes (via detail) | Yes (direction) | Yes (direction) |

## Models

- `Filiere` -- tenant FK, name, code, level (Bachelor/Master), duration_years, capacity, is_active, coordinator FK (User), description; unique_together: [tenant, code]
- `FiliereSubject` -- filiere FK, subject FK (Course), coefficient (Decimal), is_mandatory, year, semester, credits, hours_per_week; unique_together: [filiere, subject, year, semester]
- `FiliereRequirement` -- filiere FK, requirement_type (academic/language/exam/document/other), description, is_mandatory, order

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/filieres/` | List filieres (search, filter by level/is_active) |
| POST | `/api/filieres/` | Create filiere (direction only) |
| GET | `/api/filieres/{id}/` | Filiere detail with subjects |
| PUT/PATCH | `/api/filieres/{id}/` | Update filiere (direction only) |
| DELETE | `/api/filieres/{id}/` | Delete filiere (direction only, safety check) |
| GET | `/api/filieres/{id}/subjects/` | List subjects for filiere |
| GET | `/api/filieres/{id}/requirements/` | List requirements for filiere |
| GET | `/api/filieres/active/` | List active filieres only |
| GET/POST | `/api/subjects/` | List/create filiere subjects |
| GET/PUT/DELETE | `/api/subjects/{id}/` | Subject detail/update/delete |
| GET/POST | `/api/requirements/` | List/create requirements |
| GET/PUT/DELETE | `/api/requirements/{id}/` | Requirement detail/update/delete |

## Dependencies

- `core` (School model for tenant)
- `course` (Course model for subject linkage)
- `enrollment` (RegistrationForm for enrolled count annotation)
- `accounts` (User model for coordinator; `direction_only`, `tenant_required` decorators; `IsDirectionUser` permission)
- `django-ratelimit` (rate limiting on all views)
- `django-filter` (API filtering)
- `djangorestframework` (API views)

## Configuration

No app-specific settings. Rate limits are hardcoded in view decorators (100/h for read, 50/h for write).

## URL Namespace

- Frontend: `frontend:filieres:<view_name>`
- API: `api:v1:filieres:<resource-name>`

## File Structure

```
filieres/
  __init__.py
  admin.py
  apps.py
  forms.py            # FiliereForm, FiliereSubjectForm, FiliereRequirementForm, FiliereSearchForm
  models.py           # Filiere, FiliereSubject, FiliereRequirement
  serializers.py      # DRF serializers (list, create, detail variants)
  signals.py          # Activity logging signals
  urls.py             # Frontend + API URL routing with DRF router
  views_api.py        # FiliereViewSet, FiliereSubjectViewSet, FiliereRequirementViewSet
  views_frontend.py   # 10 frontend views (CRUD + subject/requirement management)
  README.md
  TODO.md
```

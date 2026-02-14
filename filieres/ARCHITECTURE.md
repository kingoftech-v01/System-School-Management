# Filieres - Architecture

## Overview

The filieres app manages academic programs (tracks/departments) and their curricula. It serves as the bridge between courses and student enrollment, defining which courses belong to which program, with coefficients, credit hours, and admission requirements. It is a mid-level dependency: depends on `core` and `course`, and is depended on by `enrollment` and `admissions`.

## Models & Relationships

### Entity-Relationship Summary

```
School (core) ──1:N──> Filiere
User (accounts) ──1:N──> Filiere (coordinator)
Filiere ──1:N──> FiliereSubject
Filiere ──1:N──> FiliereRequirement
Course (course) ──1:N──> FiliereSubject (subject FK)
Filiere <──1:N── RegistrationForm (enrollment, reverse: registrations)
```

### Model Details

#### Filiere
- **Purpose**: Represents an academic program/track (e.g., Computer Science, Business Administration)
- **Key Fields**: name, code, level (Bachelor/Master), duration_years, capacity, is_active, description
- **Relationships**: tenant FK -> School, coordinator FK -> User (limit_choices_to professor/direction)
- **Business Rules**:
  - Code must be unique per tenant (unique_together: [tenant, code])
  - `is_full()` checks enrollment count against capacity
  - `get_enrolled_students_count()` queries RegistrationForm (lazy import from enrollment app)
  - Deletion blocked if enrolled students exist (both frontend and API)
- **Indexes**: [tenant, is_active], [code]

#### FiliereSubject
- **Purpose**: Links a Course to a Filiere with academic metadata
- **Key Fields**: coefficient (Decimal 0.1-10), is_mandatory, year, semester (1-4), credits, hours_per_week
- **Relationships**: filiere FK -> Filiere, subject FK -> Course
- **Business Rules**:
  - Unique together: [filiere, subject, year, semester] (same course can appear in different years/semesters)
  - `get_total_hours()` returns hours_per_week * 15 (semester weeks)
- **Indexes**: [filiere, year, semester], [is_mandatory]

#### FiliereRequirement
- **Purpose**: Admission prerequisites for a filiere
- **Key Fields**: requirement_type (academic/language/exam/document/other), description, is_mandatory, order
- **Relationships**: filiere FK -> Filiere
- **Business Rules**: Ordered by [order, requirement_type]

## View Logic Flow

### Frontend Views

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| filiere_list | GET | login + tenant | all authenticated | List with search, filter, pagination (20/page) |
| filiere_detail | GET | login + tenant | all authenticated | Detail with subjects grouped by year/semester |
| filiere_create | GET/POST | login + direction + tenant | direction | Create form with tenant-filtered coordinator |
| filiere_edit | GET/POST | login + direction + tenant | direction | Edit form |
| filiere_delete | GET/POST | login + direction + tenant | direction | Delete with enrollment safety check |
| add_subject | GET/POST | login + direction + tenant | direction | Add subject to filiere |
| edit_subject | GET/POST | login + direction + tenant | direction | Edit subject coefficient/year/semester/credits |
| remove_subject | GET/POST | login + direction + tenant | direction | Remove subject with confirmation page |
| add_requirement | GET/POST | login + direction + tenant | direction | Add requirement to filiere |
| edit_requirement | GET/POST | login + direction + tenant | direction | Edit requirement |
| remove_requirement | POST | login + direction + tenant | direction | Remove requirement (POST-only, redirect on GET) |

### API Views

| ViewSet | Methods | Auth | Roles | Description |
|---------|---------|------|-------|-------------|
| FiliereViewSet | CRUD + subjects/requirements/active | IsAuthenticated; write: IsDirectionUser | all read; direction write | Full CRUD with custom actions |
| FiliereSubjectViewSet | CRUD | IsAuthenticated; write: IsDirectionUser | all read; direction write | Subject management |
| FiliereRequirementViewSet | CRUD | IsAuthenticated; write: IsDirectionUser | all read; direction write | Requirement management |

### Key Patterns

- **Decorator chain**: `@login_required` -> `@direction_only` -> `@tenant_required` -> `@ratelimit`
- **Tenant filtering**: All querysets filter by `request.tenant` (frontend) or `self.request.tenant` (API)
- **Form tenant injection**: Forms receive `tenant=request.tenant` to filter coordinator/subject choices
- **Annotated querysets**: List views annotate `subject_count` and `enrolled_count` via Count/Q

## Business Logic

### Core Workflows

#### 1. Create Filiere
1. Direction user submits FiliereForm
2. Form validates code uniqueness within tenant
3. Filiere saved with `tenant = request.tenant`
4. Redirect to filiere detail

#### 2. Manage Curriculum (Subjects)
1. Direction user navigates to filiere detail
2. Clicks "Add Subject" -> FiliereSubjectForm with tenant-filtered courses
3. Subject saved with filiere FK
4. Edit/remove subjects via separate views with filiere_pk + subject_pk routing

#### 3. Delete Filiere (Safety Check)
1. Direction user clicks delete
2. System checks `get_enrolled_students_count() > 0`
3. If enrolled: error message, redirect to detail
4. If no enrollments: show confirmation page -> POST deletes

#### 4. Filiere Detail Aggregation
1. View prefetches `subjects__subject` and `requirements`
2. Subjects grouped by (year, semester) tuple in dict
3. Counts: total_credits, mandatory_count, elective_count
4. All passed to template context

### Validation Rules

- Filiere code: uppercase, unique per tenant
- Subject coefficient: Decimal 0.1 to 10.0
- Duration: 1 to 10 years
- Credits: 1 to 20 per subject
- Hours per week: 1 to 40
- Capacity: optional (null = unlimited)

## Inter-App Dependencies

### Depends On

| App | Models Used | Purpose |
|-----|------------|---------|
| core | School | Tenant FK on Filiere |
| course | Course | Subject FK on FiliereSubject |
| accounts | User | Coordinator FK; decorators (direction_only, tenant_required); IsDirectionUser permission |

### Depended On By

| App | What They Use | Purpose |
|-----|--------------|---------|
| enrollment | Filiere | RegistrationForm.filiere FK for enrollment tracking |
| admissions | Filiere | Application.filiere FK for admission targeting |
| scheduling | Filiere | Schedule entries may reference filiere for student group |
| analytics | Filiere | Program-level analytics and reporting |

### Dependency Diagram

```
core.School ─────────────┐
                         v
accounts.User ──> [filieres] <── course.Course
                    │
         ┌──────────┴──────────┐
         v                     v
  enrollment.RegistrationForm  admissions.Application
```

## Data Flow

### Frontend Request Flow

```
Request -> URL (frontend_urlpatterns)
       -> @login_required -> @direction_only -> @tenant_required -> @ratelimit
       -> View function
       -> Form (tenant-filtered querysets)
       -> Model.save()
       -> messages.success/error
       -> redirect to detail/list
```

### API Request Flow

```
Request -> DRF Router -> ViewSet
       -> get_permissions() (IsAuthenticated + IsDirectionUser for writes)
       -> get_queryset() (tenant-filtered, annotated)
       -> get_serializer_class() (action-based: list/create/detail)
       -> perform_create() (sets tenant)
       -> destroy() override (enrollment safety check)
       -> Response (JSON)
```

## Technical Notes

- **Lazy import in model**: `get_enrolled_students_count()` uses local import of `enrollment.models.RegistrationForm` to avoid circular imports
- **Bare except in model**: `get_enrolled_students_count()` has `except:` that silently returns 0 on any error (should catch specific exceptions)
- **Rate limiting**: All views use `django-ratelimit` with `key='user'`; read: 100/h, write: 50/h with `method='POST'`
- **Dual view architecture**: Frontend views in `views_frontend.py`, API views in `views_api.py`, both registered in `urls.py`
- **API serializer variants**: FiliereListSerializer (summary), FiliereSerializer (detail), FiliereCreateSerializer (write) selected by action

# Grading App

Rubric-based grading system with criteria management, grade entry using formsets, student gradebook, peer reviews, and grade curve application.

## Description

The grading app provides a comprehensive rubric-based assessment system. Lecturers create rubrics with weighted criteria, enter grades using multi-criteria formsets, and view student gradebooks. The app also supports peer reviews with status tracking and grade curves managed by direction. All views are role-aware with appropriate permission checks, rate-limited to 100 requests/hour per user, and tenant-scoped.

## Main Features

- **Rubric CRUD**: Full create, list, detail, edit, delete with course association
- **Criteria Management**: Add, edit, delete, and reorder criteria within rubrics with achievement-level descriptions (excellent, good, satisfactory, needs improvement)
- **Grade Entry**: Enter grades using rubric + criterion formsets for multi-criteria weighted scoring with automatic total calculation
- **Student Gradebook**: Aggregate statistics (count, average percentage) with per-student views
- **Peer Reviews**: Anonymous peer assessment with status tracking (pending, in_progress, completed, expired) and deadline enforcement
- **Grade Curves**: Direction-only grade curve management supporting linear, square root, bell curve, and custom adjustments with before/after statistics
- **Dashboard**: Role-aware (student sees recent grades + pending reviews, lecturer sees grading activity + active rubrics, direction sees system-wide stats)
- **Celery Tasks**: Background processing for grade notifications, peer review assignment, reminders, curve application, and low-score alerts
- **Rich Admin**: Full Django admin with inline criteria, color-coded grade displays, batch actions (activate, deactivate, duplicate, recalculate)

## User Roles

| Role | Rubrics | Grade Entry | Gradebook | Peer Reviews | Grade Curves | Dashboard |
|------|---------|-------------|-----------|--------------|--------------|-----------|
| student | -- | -- | View own grades | Submit reviews, view received | -- | Recent grades, pending reviews |
| professor | CRUD own rubrics + criteria | Create, edit, delete own grades | View any student | View all reviews | -- | Recent activity, active rubrics |
| direction | View all rubrics | View all grades | View any student | View all reviews | Full CRUD | System-wide stats |
| admin | View all rubrics | View all grades | View any student | View all reviews | -- | System-wide stats |
| secretary | View all rubrics | View all grades | -- | -- | -- | System-wide stats |
| parent | -- | -- | -- | -- | -- | -- |
| prefet | -- | -- | -- | -- | -- | -- |
| accountant | -- | -- | -- | -- | -- | -- |
| librarian | -- | -- | -- | -- | -- | -- |
| registrar | -- | -- | -- | -- | -- | -- |

Notes:
- "professor" and "lecturer" are treated as the same role in views (checked via `@lecturer_required` decorator).
- Direction users bypass ownership checks on rubrics and grade entries.
- The `@direction_only` decorator restricts all grade curve views to direction role exclusively.
- Roles not listed with specific permissions (parent, prefet, accountant, librarian, registrar) have no access to grading features and will be denied by the `@lecturer_required` decorator on most views.

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| GradingRubric | Yes (lecturer+) | Yes (list + detail) | Yes (owner or direction) | Yes (owner or direction) |
| RubricCriterion | Yes (via rubric) | Yes (via rubric detail) | Yes (owner or direction) | Yes (owner or direction) |
| RubricGrade | Yes (lecturer+) | Yes (list + detail) | Yes (owner or direction) | Yes (owner or direction) |
| CriterionGrade | Yes (via grade entry) | Yes (via grade detail) | Yes (via grade edit) | Yes (cascade with grade) |
| PeerReview | Assigned via Celery task | Yes (list, filtered by role) | Yes (submit by reviewer) | No |
| GradeCurve | Yes (direction only) | Yes (list + detail) | Yes (direction only) | Yes (direction only) |

## Models

- `GradingRubric` -- name, description, course FK (Course), max_score, passing_score, allow_partial_credit, is_active, created_by FK (User), created_at, updated_at
- `RubricCriterion` -- rubric FK (GradingRubric), name, description, max_points, weight (0-100), order, excellent/good/satisfactory/needs_improvement descriptions
- `RubricGrade` -- rubric FK, student FK (Student), assignment_name, assignment_type (essay/project/presentation/lab/other), total_score, percentage, letter_grade, graded_by FK (User), overall_feedback, graded_at
- `CriterionGrade` -- rubric_grade FK (RubricGrade), criterion FK (RubricCriterion), score, feedback; unique_together on (rubric_grade, criterion)
- `PeerReview` -- course FK (Course), assignment_name, rubric FK (optional), reviewee FK (Student), reviewer FK (Student), score, feedback, is_anonymous, status (pending/in_progress/completed/expired), deadline, submitted_at; unique_together on (assignment_name, reviewee, reviewer)
- `GradeCurve` -- course FK (Course), assignment_name, curve_type (linear/sqrt/bell/custom), adjustment_factor, add_points, mean/median/std_dev before and after, applied_by FK (User), is_active, applied_at

## API Endpoints

All API endpoints require authentication (`IsAuthenticated`). The base path is the grading app's API namespace.

### Rubrics (`/api/rubrics/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/rubrics/` | List rubrics (filterable by course, is_active; searchable by title, description) | Authenticated |
| POST | `/api/rubrics/` | Create rubric with nested criteria | Staff or Teacher |
| GET | `/api/rubrics/{id}/` | Retrieve rubric with all criteria | Authenticated |
| PUT/PATCH | `/api/rubrics/{id}/` | Update rubric | Creator or Staff |
| DELETE | `/api/rubrics/{id}/` | Delete rubric | Creator or Staff |
| POST | `/api/rubrics/{id}/duplicate/` | Duplicate rubric with all criteria (starts as inactive) | Staff or Teacher |
| GET | `/api/rubrics/{id}/statistics/` | Get grade distribution and averages for this rubric | Authenticated |

### Criteria (`/api/criteria/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/criteria/` | List criteria (filterable by rubric) | Authenticated |
| POST | `/api/criteria/` | Create criterion | Staff or Teacher |
| PUT/PATCH | `/api/criteria/{id}/` | Update criterion | Staff or Teacher |
| DELETE | `/api/criteria/{id}/` | Delete criterion | Staff or Teacher |
| POST | `/api/criteria/reorder/` | Reorder criteria (body: `{"criteria_order": [{"id": 1, "order": 0}, ...]}`) | Staff or Teacher |

### Grades (`/api/grades/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/grades/` | List grades (students see own; staff/teachers see all; filterable by rubric, student, graded_by) | Authenticated |
| POST | `/api/grades/` | Create grade with nested criterion grades; auto-calculates total | Staff or Teacher |
| GET | `/api/grades/{id}/` | Retrieve grade with criterion breakdown | Owner or Staff |
| POST | `/api/grades/{id}/finalize/` | Mark grade as finalized (no more edits) | Staff or Teacher |
| GET | `/api/grades/{id}/breakdown/` | Get detailed criterion-by-criterion breakdown | Owner or Staff |

### Criterion Grades (`/api/criterion-grades/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/criterion-grades/` | List criterion grades (read-only; filterable by rubric_grade, criterion) | Authenticated |
| GET | `/api/criterion-grades/{id}/` | Retrieve criterion grade detail | Authenticated |

### Peer Reviews (`/api/peer-reviews/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/peer-reviews/` | List reviews (students see own sent/received; staff see all; filterable by status, reviewer, reviewee) | Authenticated |
| POST | `/api/peer-reviews/{id}/submit/` | Submit a pending review with score and feedback | Reviewer only |
| GET | `/api/peer-reviews/my_reviews/` | List reviews assigned to current user | Authenticated |
| GET | `/api/peer-reviews/received_reviews/` | List submitted reviews received by current user | Authenticated |

### Grade Curves (`/api/curves/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/curves/` | List curves (filterable by course, curve_type) | Staff or Teacher |
| POST | `/api/curves/` | Create and apply a grade curve | Staff or Teacher |
| GET | `/api/curves/{id}/` | Retrieve curve with before/after statistics | Staff or Teacher |
| POST | `/api/curves/{id}/preview/` | Preview curve effect without applying | Staff or Teacher |

## File Structure

```
grading/
    __init__.py
    apps.py
    models.py              # 6 models: GradingRubric, RubricCriterion, RubricGrade,
                           #            CriterionGrade, PeerReview, GradeCurve
    views_frontend.py      # 20 frontend views (HTML template-based)
    views_api.py           # 6 DRF ViewSets with custom actions
    urls.py                # Frontend + API URL routing with DRF router
    serializers.py         # 9 serializers (CRUD + nested create + submit)
    forms.py               # 6 forms + 1 formset (CriterionGradeFormSet)
    permissions.py         # 6 DRF permission classes
    tasks.py               # 6 Celery tasks (notifications, assignment, reminders, curves, stats)
    admin.py               # 6 ModelAdmin classes with inlines, actions, fieldsets
    README.md
    TODO.md
    ARCHITECTURE.md
```

## Configuration

### Required Dependencies

These must be in `INSTALLED_APPS` or available in the Python environment:

| Package | Purpose |
|---------|---------|
| `djangorestframework` | API ViewSets and serializers |
| `django-filter` | `DjangoFilterBackend` for API queryset filtering |
| `django-ratelimit` | `@ratelimit` decorator on all frontend views |
| `celery` | Background tasks (grade notifications, peer review assignment) |

### Required Apps

The grading app depends on these Django apps being installed:

- `accounts` -- provides `User` model (with `role` field, `is_teacher` property), `Student` model, and decorators (`@login_required`, `@lecturer_required`, `@direction_only`, `@tenant_required`)
- `course` -- provides `Course` model (FK target for rubrics, peer reviews, grade curves) and `CourseAllocation` model (used in forms to filter courses by lecturer)
- `core` -- provides `School` model (tenant)

### Settings

- `DEFAULT_FROM_EMAIL` -- used by Celery tasks for grade notifications and reminders
- Celery broker must be configured for background tasks to run
- Rate limit: all frontend views are limited to 100 requests/hour per user (delete views limited to 50/hour)

## URL Namespace

- Frontend: `frontend:grading:<view_name>`
- API: `api:v1:grading:<resource-name>`

## Known Issues

- `tasks.py` references `is_finalized` field on `RubricGrade` model, but this field is not defined in `models.py`
- `tasks.py` references `assignment.models.Assignment` and `result.models.Result` which may not exist or have different interfaces
- `views_api.py` references `assignment` field on `GradingRubric` queryset (`select_related('assignment')`) but the model only has a `course` FK
- PeerReview status choices in `models.py` use `expired` but `views_api.py` submit action sets status to `submitted` (not in model choices)

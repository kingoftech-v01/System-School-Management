# Grading App - Architecture

This document describes the internal architecture of the `grading` Django app, including its data model, view layer, business logic, inter-app dependencies, and data flow.

## Data Model

### Entity-Relationship Diagram (Text)

```text
+------------------+          +-------------------+
|  GradingRubric   |          |  RubricCriterion  |
|------------------|          |-------------------|
| id               |  1----*  | id                |
| name             |          | rubric FK --------+
| description      |          | name              |
| course FK -------+--+       | description       |
| max_score        |  |       | weight (0-100)    |
| passing_score    |  |       | max_points        |
| allow_partial    |  |       | order             |
| is_active        |  |       | excellent_desc    |
| created_by FK    |  |       | good_desc         |
| created_at       |  |       | satisfactory_desc |
| updated_at       |  |       | needs_improv_desc |
+------------------+  |       +-------------------+
       |               |                |
       | 1             |                |
       |               |                |
       | *             |                | 1
+------------------+   |       +-------------------+
|   RubricGrade    |   |       |  CriterionGrade   |
|------------------|   |       |-------------------|
| id               |   |  *    | id                |
| rubric FK -------+   |       | rubric_grade FK --+
| student FK ------+---+--+    | criterion FK -----+
| assignment_name  |   |  |    | score             |
| assignment_type  |   |  |    | feedback          |
| total_score      |   |  |    +-------------------+
| percentage       |   |  |    unique(rubric_grade,
| letter_grade     |   |  |           criterion)
| graded_by FK     |   |  |
| overall_feedback |   |  |
| graded_at        |   |  |
+------------------+   |  |
                       |  |
+------------------+   |  |
|   PeerReview     |   |  |
|------------------|   |  |
| id               |   |  |
| course FK -------+---+  |
| assignment_name  |      |
| rubric FK (opt)  |      |
| reviewee FK -----+------+
| reviewer FK -----+------+
| score            |      |
| feedback         |      |
| is_anonymous     |      |
| status           |      |
| deadline         |      |
| submitted_at     |      |
| created_at       |      |
+------------------+      |
unique(assignment_name,   |
       reviewee, reviewer)|
                          |
+------------------+      |
|   GradeCurve     |      |
|------------------|      |
| id               |      |
| course FK -------+------+
| assignment_name  |
| curve_type       |
| adjustment_factor|
| add_points       |
| mean_before      |
| median_before    |
| std_dev_before   |
| mean_after       |
| median_after     |
| std_dev_after    |
| applied_by FK    |
| is_active        |
| applied_at       |
+------------------+
```

### Model Details

#### GradingRubric

The central entity. A rubric defines a grading template for a specific course. It contains scoring configuration (max_score, passing_score), partial credit settings, and an active/inactive flag. Rubrics are always scoped to a `Course` via FK and tracked by their creator.

**Key relationships:**

- `course` -> `course.Course` (CASCADE) -- the course this rubric applies to
- `created_by` -> `User` (SET_NULL) -- the lecturer/admin who created it
- `criteria` (reverse) -- all `RubricCriterion` rows belonging to this rubric
- `grades` (reverse) -- all `RubricGrade` rows using this rubric

**Indexes:** Composite index on `(course, is_active)` for filtered listing queries.

#### RubricCriterion

Individual grading dimensions within a rubric. Each criterion has a weight (percentage, 0-100) and max_points, plus text descriptions for four achievement levels. Criteria are ordered by the `order` field for consistent display.

**Key relationships:**

- `rubric` -> `GradingRubric` (CASCADE) -- deleting a rubric deletes all its criteria

**Ordering:** `(rubric, order)` -- criteria display in their defined order within each rubric.

#### RubricGrade

An applied grade for one student on one assignment, using a specific rubric. The `total_score` and `percentage` fields are computed by `calculate_grade()` from the sum of weighted criterion grades. The `assignment_type` field categorizes the work (essay, project, presentation, lab, other).

**Key relationships:**

- `rubric` -> `GradingRubric` (CASCADE)
- `student` -> `accounts.Student` (CASCADE) -- the student being graded
- `graded_by` -> `User` (SET_NULL) -- the lecturer who entered the grade
- `criterion_grades` (reverse) -- individual criterion scores for this grade

**Indexes:** Composite indexes on `(student, -graded_at)` and `(rubric, -graded_at)` for gradebook and rubric statistics queries.

#### CriterionGrade

The score for a single criterion within a rubric grade. Each rubric grade has one CriterionGrade per criterion in its rubric. The `unique_together` constraint on `(rubric_grade, criterion)` ensures no duplicate scores.

**Key relationships:**

- `rubric_grade` -> `RubricGrade` (CASCADE)
- `criterion` -> `RubricCriterion` (CASCADE)

#### PeerReview

A peer assessment assignment where one student (reviewer) evaluates another student's (reviewee) work. Reviews can be anonymous and have a deadline. The status tracks the review lifecycle: pending -> in_progress -> completed (or expired).

**Key relationships:**

- `course` -> `course.Course` (CASCADE)
- `rubric` -> `GradingRubric` (SET_NULL, optional) -- an optional rubric to guide the review
- `reviewer` -> `accounts.Student` (CASCADE)
- `reviewee` -> `accounts.Student` (CASCADE)

**Constraints:** `unique_together` on `(assignment_name, reviewee, reviewer)` prevents duplicate review assignments.

**Indexes:** Composite indexes on `(reviewee, -created_at)` and `(reviewer, status)` for student review queries.

#### GradeCurve

A grade adjustment applied to all grades for a course assignment. Supports four curve types: linear (multiply + add), square root, bell curve, and custom. Captures before/after statistics (mean, median, std_dev) for audit.

**Key relationships:**

- `course` -> `course.Course` (CASCADE)
- `applied_by` -> `User` (SET_NULL) -- the direction user who applied it

## View Layer Architecture

### Frontend Views (views_frontend.py)

All frontend views follow a consistent pattern:

1. **Decorator stack:** `@login_required` -> `@role_required` -> `@tenant_required` -> `@ratelimit(key='user', rate='100/h')`
2. **Permission check:** Role-based filtering via queryset scoping (not just decorator-level checks)
3. **Template rendering:** Each view returns a rendered HTML template with context data

The views are organized into six groups:

#### Rubric Management (5 views)

`rubric_list`, `rubric_create`, `rubric_detail`, `rubric_update`, `rubric_delete`

- Protected by `@lecturer_required` (allows lecturer, professor, direction, admin, secretary roles)
- Direction users see all rubrics; lecturers see only their own
- Ownership checks: direction can modify any rubric; lecturers can only modify their own

#### Criteria Management (3 views)

`criterion_create`, `criterion_update`, `criterion_delete`

- Protected by `@lecturer_required`
- Scoped to the parent rubric's ownership (same rules as rubric management)
- After mutation, redirects back to the parent rubric detail page

#### Grade Entry (4 views)

`grade_entry_list`, `grade_entry_create`, `grade_entry_edit`, `grade_entry_delete`

- `grade_entry_create` uses `RubricGradeForm` + `CriterionGradeFormSet` (dynamic formset based on rubric criteria)
- `grade_entry_detail` has special role-based queryset filtering: students see own grades, lecturers see grades they assigned, direction/admin/secretary see all, other roles see nothing
- `grade_entry_edit` deletes existing criterion grades and re-creates them (full replacement strategy)
- `grade_entry_delete` uses a lower rate limit (50/hour) for POST requests

#### Student Gradebook (1 view)

`student_gradebook`

- Students automatically see their own gradebook (looks up `Student` from `request.user`)
- Lecturers and direction can pass a `student_id` URL parameter to view any student
- Calculates aggregate statistics: total grade count and average percentage

#### Peer Reviews (2 views)

`peer_review_list`, `peer_review_submit`

- No `@lecturer_required` -- open to all authenticated users
- Students see a split view: pending reviews they need to complete + completed reviews they received
- Non-students see a paginated list of all reviews with status and course filters
- Submit view enforces reviewer ownership for students and checks review status is pending/in_progress

#### Grade Curves (5 views)

`grade_curve_list`, `grade_curve_create`, `grade_curve_detail`, `grade_curve_edit`, `grade_curve_delete`

- Protected by `@direction_only` -- exclusively available to direction users
- `grade_curve_delete` uses a lower rate limit (50/hour) for POST requests

#### Dashboard (1 view)

`grading_dashboard`

- Three branches based on `request.user.role`:
  - **student:** Recent 5 grades + count of pending peer reviews
  - **lecturer:** Recent 10 grading activities + count of active rubrics
  - **direction/other:** System-wide counts (total rubrics, grades, pending reviews, active curves)

### API Views (views_api.py)

Six DRF ViewSets registered with a `DefaultRouter`:

| ViewSet | Basename | Queryset Optimization | Custom Actions |
| --- | --- | --- | --- |
| `GradingRubricViewSet` | `rubric` | `select_related` + `prefetch_related('criteria')` | `duplicate`, `statistics` |
| `RubricCriterionViewSet` | `criterion` | `select_related('rubric')` | `reorder` |
| `RubricGradeViewSet` | `grade` | `select_related` + `prefetch_related('criterion_grades')` | `finalize`, `breakdown` |
| `CriterionGradeViewSet` | `criterion-grade` | `select_related('rubric_grade', 'criterion')` | None (read-only) |
| `PeerReviewViewSet` | `peer-review` | `select_related('assignment', 'reviewer', 'reviewee')` | `submit`, `my_reviews`, `received_reviews` |
| `GradeCurveViewSet` | `curve` | `select_related('course', 'applied_by')` | `preview` |

**Queryset scoping in API views:**

- `RubricGradeViewSet.get_queryset()`: Staff/teachers see all grades; students see only their own
- `PeerReviewViewSet.get_queryset()`: Staff/teachers see all reviews; students see reviews they wrote or received

### Permission Classes (permissions.py)

| Class | Read Access | Write Access |
| --- | --- | --- |
| `CanCreateRubrics` | Any authenticated user | Staff or teacher only |
| `CanGradeSubmissions` | Staff or teacher only | Staff or teacher only |
| `CanApplyCurves` | Staff or teacher only | Staff or teacher only |
| `IsReviewerOrReadOnly` | Anyone (object-level) | Reviewer only (object-level) |
| `CanViewGrades` | Any authenticated user | Staff/teacher see all; students see own (object-level) |
| `CanManageRubric` | Anyone (object-level) | Creator or staff only (object-level) |

## Business Logic

### Grade Calculation (RubricGrade.calculate_grade)

The `calculate_grade()` method on `RubricGrade` computes the total score from individual criterion grades:

```text
For each CriterionGrade in this RubricGrade:
    weighted_score = (criterion_grade.score / criterion.max_points) * criterion.weight
    total += weighted_score

rubric_grade.total_score = total
rubric_grade.percentage = (total / rubric.max_score) * 100
```

This is called automatically after grade creation (both in frontend `grade_entry_create` and API `RubricGradeCreateSerializer.create()`). The admin also provides a "Recalculate selected grades" batch action.

### Letter Grade Assignment

Letter grades are derived from percentage in the serializer (not stored on creation in the model, though the field exists):

| Percentage | Grade |
| --- | --- |
| >= 90% | A |
| >= 80% | B |
| >= 70% | C |
| >= 60% | D |
| < 60% | F |

### Peer Review Lifecycle

```text
[Created] --> pending --> in_progress --> completed
                  |                          ^
                  |                          |
                  +--> expired          (submitted_at set)
```

- Reviews are created by the `assign_peer_reviews` Celery task or manually
- Students submit reviews via `peer_review_submit` (frontend) or `PeerReviewViewSet.submit` (API)
- Submission sets `status='completed'` and records `submitted_at` timestamp
- The `send_peer_review_reminders` Celery task sends emails for reviews pending > 7 days

### Grade Curve Application

The `apply_grade_curve` Celery task processes curves based on `curve_type`:

- **flat_boost:** `grade = min(grade + adjustment_value, 100)`
- **percentage_boost:** `grade = min(grade * (1 + adjustment_value / 100), 100)`
- **square_root:** `grade = min(sqrt(grade) * 10, 100)`
- **set_mean:** Not yet implemented

Note: The task modifies `result.models.Result` records, not `RubricGrade` records.

### Rubric Duplication

Both the API (`GradingRubricViewSet.duplicate`) and admin (`duplicate_rubric` action) support duplicating a rubric with all its criteria. The copy:

- Gets a " (Copy)" suffix on its name
- Starts as inactive (`is_active=False`)
- Has no assignment association (API) / inherits course (admin)
- All criteria are duplicated with the same configuration

## Celery Tasks (tasks.py)

| Task Name | Trigger | Description |
| --- | --- | --- |
| `grading.send_grade_notifications` | After grade finalization | Emails student with score and feedback |
| `grading.assign_peer_reviews` | Manual (assignment_id param) | Randomly assigns N peer reviews per student from submissions |
| `grading.send_peer_review_reminders` | Periodic (scheduled) | Emails reminders for reviews pending > 7 days |
| `grading.apply_grade_curve` | After curve creation | Applies curve algorithm to Result records for the course |
| `grading.calculate_rubric_statistics` | Periodic (scheduled) | Caches average score/percentage per rubric (1-hour TTL) |
| `grading.notify_low_scores` | Periodic (scheduled) | Emails students and advisors when recent grades fall below threshold (default 60%) |

## Inter-App Dependencies

### Inbound Dependencies (apps that grading imports from)

```text
grading
  |
  +-- accounts
  |     +-- User model (created_by, graded_by, applied_by FKs)
  |     +-- Student model (student, reviewer, reviewee FKs)
  |     +-- Decorators: @login_required, @lecturer_required,
  |     |               @direction_only, @tenant_required
  |     +-- CourseAllocation (used in forms.py for lecturer course filtering)
  |
  +-- course
  |     +-- Course model (FK target for rubrics, peer reviews, grade curves)
  |     +-- CourseAllocation model (used in RubricGradeForm to filter students)
  |
  +-- core
  |     +-- School model (tenant, via @tenant_required decorator)
  |
  +-- result (in tasks.py only)
  |     +-- Result model (target of grade curve application)
  |
  +-- assignment (in tasks.py only)
        +-- Assignment model (source of submissions for peer review assignment)
        +-- Submission model (to find students who submitted work)
```

### Outbound Dependencies (apps that import from grading)

The grading app does not export models or utilities that other apps are known to depend on. It is a leaf node in the dependency graph.

### Third-Party Dependencies

| Package | Usage |
| --- | --- |
| `djangorestframework` | ViewSets, serializers, permissions, filters, routers |
| `django-filter` | `DjangoFilterBackend` for API queryset filtering |
| `django-ratelimit` | `@ratelimit` decorator on all frontend views |
| `celery` | `@shared_task` for background processing |

## Data Flow

### Flow 1: Lecturer Creates a Rubric and Grades a Student

```text
1. Lecturer visits /grading/rubrics/create/
   -> rubric_create view
   -> GradingRubricForm (filtered courses based on lecturer's allocations)
   -> POST saves GradingRubric with created_by=request.user

2. Lecturer adds criteria via /grading/rubrics/{id}/criteria/create/
   -> criterion_create view
   -> RubricCriterionForm
   -> POST saves RubricCriterion with rubric FK

3. Lecturer enters grade via /grading/grades/create/{rubric_pk}/{student_id}/
   -> grade_entry_create view
   -> RubricGradeForm + CriterionGradeFormSet (one form per criterion)
   -> POST saves RubricGrade + CriterionGrade rows
   -> Calls grade.calculate_grade() to compute total_score and percentage
   -> Redirect to grade_entry_detail
```

### Flow 2: Peer Review Assignment and Submission

```text
1. Celery task assign_peer_reviews(assignment_id) is triggered
   -> Finds all submissions for the assignment
   -> Randomly assigns N reviewers per student (avoiding self-review)
   -> Creates PeerReview records with status='pending'

2. Student visits /grading/peer-reviews/
   -> peer_review_list view (student branch)
   -> Shows pending reviews (to complete) and received reviews (completed)

3. Student submits review via /grading/peer-reviews/{pk}/submit/
   -> peer_review_submit view
   -> PeerReviewForm (score + feedback)
   -> POST sets status='completed', submitted_at=now()
```

### Flow 3: Direction Applies a Grade Curve

```text
1. Direction visits /grading/curves/create/
   -> grade_curve_create view (protected by @direction_only)
   -> GradeCurveForm (course, assignment_name, curve_type, adjustment_factor, add_points)
   -> POST saves GradeCurve with applied_by=request.user

2. (Optional) Celery task apply_grade_curve(curve_id) is triggered
   -> Reads GradeCurve configuration
   -> Queries result.models.Result for the course
   -> Applies curve algorithm to each result
   -> Saves adjusted grades (capped at 100)
```

### Flow 4: API Grade Creation with Nested Criterion Grades

```text
1. POST /api/grades/
   -> RubricGradeViewSet.create()
   -> RubricGradeCreateSerializer validates input
   -> Creates RubricGrade record (graded_by=request.user)
   -> Creates CriterionGrade records from nested data
   -> Calls rubric_grade.calculate_grade()
   -> Returns serialized grade with computed totals

2. POST /api/grades/{id}/finalize/
   -> RubricGradeViewSet.finalize()
   -> Sets is_finalized=True on the grade
   -> (Triggers send_grade_notifications task if configured)
```

## Admin Interface

The admin interface provides rich management for all six models:

| Model | Admin Features |
| --- | --- |
| `GradingRubric` | Inline criteria, date hierarchy, activate/deactivate/duplicate batch actions, criteria count display |
| `RubricCriterion` | Collapsible achievement level descriptions, rubric course filter |
| `RubricGrade` | Inline criterion grades, color-coded grade display (A=green to F=red), recalculate batch action, criterion breakdown display |
| `CriterionGrade` | Color-coded percentage display, max points display |
| `PeerReview` | Date hierarchy on deadline, mark pending/completed batch actions |
| `GradeCurve` | Collapsible before/after statistics, student count display, mean improvement display (color-coded) |

## Security Considerations

- **IDOR Prevention:** Frontend views use queryset-level filtering before `get_object_or_404()` to ensure users cannot access resources outside their role scope
- **Rate Limiting:** All frontend views are rate-limited to 100 requests/hour per user (delete operations limited to 50/hour)
- **Tenant Isolation:** The `@tenant_required` decorator ensures all views operate within the correct tenant context
- **Ownership Enforcement:** Rubric and grade mutation views check `created_by`/`graded_by` against the current user (direction users bypass this)
- **Anonymous Reviews:** PeerReview `is_anonymous` flag controls whether reviewer identity is disclosed to the reviewee (enforced in serializer `get_reviewer_name`)

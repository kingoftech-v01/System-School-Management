# Discipline App - Architecture

## Overview

The discipline app manages student disciplinary incidents with a full lifecycle
from reporting through resolution and parent acknowledgment. It provides both
HTML frontend views (for staff) and a REST API (DRF ViewSet). All data is
tenant-scoped via a `tenant` FK to `core.School`.

---

## Model: `DisciplinaryAction`

Single model in `discipline/models.py`. No signals, no tasks, no Celery
integration.

### Fields

| Field                   | Type             | Constraints                        | Purpose                              |
|-------------------------|------------------|------------------------------------|--------------------------------------|
| `tenant`                | FK `core.School` | `on_delete=CASCADE`                | Tenant isolation                     |
| `student`               | FK `User`        | `on_delete=CASCADE`, rel=`disciplinary_actions` | Student the action is about |
| `reported_by`           | FK `User`        | `on_delete=CASCADE`, rel=`reports_filed` | Staff member who filed the report |
| `incident_type`         | CharField(100)   |                                    | Free-text incident category          |
| `description`           | TextField        |                                    | Full incident description            |
| `action_taken`          | TextField        |                                    | What was done in response            |
| `severity`              | CharField(20)    | choices: minor/moderate/serious/critical | Severity classification        |
| `incident_date`         | DateField        |                                    | When the incident occurred           |
| `resolution_date`       | DateField        | null, blank                        | When the incident was resolved       |
| `is_resolved`           | BooleanField     | default=False                      | Resolution status flag               |
| `created_at`            | DateTimeField    | auto_now_add                       | Record creation timestamp            |
| `updated_at`            | DateTimeField    | auto_now                           | Last modification timestamp          |
| `updated_by`            | FK `User`        | `on_delete=SET_NULL`, null, rel=`discipline_updates` | Audit: who last updated |
| `parent_acknowledged`   | BooleanField     | default=False                      | Whether parent has acknowledged      |
| `parent_acknowledged_at`| DateTimeField    | null, blank                        | When parent acknowledged             |
| `parent_response`       | TextField        | blank                              | Optional parent written response     |

### Meta

- `ordering`: `['-incident_date']` (newest incidents first)
- Custom permission: `view_all_disciplinary_actions`

### Entity-Relationship Diagram

```
+-------------------+         +-------------------------------+         +-------------------+
|   core.School     |         |     DisciplinaryAction        |         |  accounts.User    |
|   (Tenant)        |         |                               |         |  (AUTH_USER_MODEL)|
+-------------------+         +-------------------------------+         +-------------------+
| id           PK   |<---+   | id                PK          |   +---->| id           PK   |
| name              |    |   | tenant_id          FK ---------+---+    | username          |
| slug              |    +---| student_id         FK ---------|---+    | first_name        |
| ...               |        | reported_by_id     FK ---------|---+    | last_name         |
+-------------------+        | updated_by_id      FK (null) --|---+    | role              |
                             | incident_type      CharField   |        | tenant_id    FK   |
                             | description        TextField   |        | is_student   bool |
                             | action_taken       TextField   |        | is_parent    bool |
                             | severity           CharField   |        | is_lecturer  bool |
                             | incident_date      DateField   |        | ...               |
                             | resolution_date    DateField?  |        +-------------------+
                             | is_resolved        BooleanField|                |
                             | parent_acknowledged BooleanField|               |
                             | parent_acknowledged_at DateTime?|        +------+-------+
                             | parent_response    TextField   |        | accounts.Parent   |
                             | created_at         DateTime    |        +-------------------+
                             | updated_at         DateTime    |        | id           PK   |
                             +-------------------------------+        | user_id      FK   |
                                                                      | student_id   FK   |
                                                                      | relation_ship     |
                                                                      +-------------------+
                                                                             |
                                                                      +------+-------+
                                                                      | accounts.Student  |
                                                                      +-------------------+
                                                                      | id           PK   |
                                                                      | student_id   FK   |
                                                                      |   (OneToOne User) |
                                                                      | program_id   FK   |
                                                                      | level             |
                                                                      +-------------------+
```

**Key FK relationships on `DisciplinaryAction`:**

- `tenant` --> `core.School` (CASCADE) -- tenant isolation
- `student` --> `accounts.User` (CASCADE) -- the student involved
- `reported_by` --> `accounts.User` (CASCADE) -- staff who reported
- `updated_by` --> `accounts.User` (SET_NULL, nullable) -- audit trail

**Parent access path (indirect):**

Parents do not have a direct FK on `DisciplinaryAction`. Access is resolved
through the `accounts.Parent` model:

```
Parent.user  -->  accounts.User
Parent.student  -->  accounts.Student.student  -->  accounts.User
DisciplinaryAction.student  -->  accounts.User

Query: DisciplinaryAction.objects.filter(student=student.student)
       where `student` is the Parent's linked Student object
```

In the API ViewSet, parent access uses `queryset.filter(student__parent=user)`,
which relies on a reverse relation through the Parent model.

---

## URL Routing

Defined in `discipline/urls.py`. Exports two pattern lists consumed by the
project-level `School_System/urls.py`.

### Frontend URLs (HTML views)

Namespace: `frontend:discipline:<name>`

| URL Pattern             | Name              | View Function                   | HTTP Methods |
|-------------------------|-------------------|---------------------------------|--------------|
| `/discipline/`          | `action_list`     | `disciplinary_action_list`      | GET          |
| `/discipline/create/`   | `action_create`   | `disciplinary_action_create`    | GET, POST    |
| `/discipline/<pk>/`     | `action_detail`   | `disciplinary_action_detail`    | GET          |
| `/discipline/<pk>/edit/`| `action_edit`     | `disciplinary_action_edit`      | GET, POST    |
| `/discipline/<pk>/delete/` | `action_delete`| `disciplinary_action_delete`    | GET, POST    |
| `/discipline/<pk>/resolve/`| `action_resolve`| `disciplinary_action_resolve`  | POST         |

### API URLs (DRF)

Namespace: `api:discipline:<name>`

Registered via `DefaultRouter` on `DisciplinaryActionViewSet` with basename `action`.

| URL Pattern                                   | Name               | HTTP Methods       |
|-----------------------------------------------|--------------------|--------------------|
| `/api/v1/discipline/actions/`                 | `action-list`      | GET, POST          |
| `/api/v1/discipline/actions/<pk>/`            | `action-detail`    | GET, PUT, PATCH, DELETE |
| `/api/v1/discipline/actions/<pk>/resolve/`    | `action-resolve`   | POST               |
| `/api/v1/discipline/actions/student_history/` | `action-student-history` | GET          |
| `/api/v1/discipline/actions/stats/`           | `action-stats`     | GET                |

### Parent URLs (in `accounts/urls.py`)

These live outside the discipline app but operate on `DisciplinaryAction`:

| URL Pattern                                         | Name                            | View                              |
|-----------------------------------------------------|---------------------------------|-----------------------------------|
| `/accounts/parent/discipline/`                      | `parent_disciplinary_records`   | `views_parent.parent_disciplinary_records` |
| `/accounts/parent/discipline/<action_id>/acknowledge/` | `parent_acknowledge_discipline` | `views_parent.parent_acknowledge_discipline` |

---

## View Access Patterns Per Role

### Frontend Views (`views_frontend.py`)

All frontend views are decorated with:
1. `@login_required` -- must be authenticated
2. `@prefet_allowed` -- expands to `@role_required('secretary', 'direction', 'admin', 'prefet')`
3. `@tenant_required` -- enforces tenant isolation

| Role          | List | Create | Detail | Edit | Delete | Resolve |
|---------------|------|--------|--------|------|--------|---------|
| **admin**     | Yes  | Yes    | Yes    | Yes  | Yes    | Yes     |
| **direction** | Yes  | Yes    | Yes    | Yes  | Yes    | Yes     |
| **prefet**    | Yes  | Yes    | Yes    | Yes  | Yes    | Yes     |
| **secretary** | Yes  | Yes    | Yes    | Yes  | Yes    | Yes     |
| **professor** | No   | No     | No     | No   | No     | No      |
| **student**   | No   | No     | No     | No   | No     | No      |
| **parent**    | No   | No     | No     | No   | No     | No      |
| **accountant**| No   | No     | No     | No   | No     | No      |
| **librarian** | No   | No     | No     | No   | No     | No      |
| **registrar** | No   | No     | No     | No   | No     | No      |
| **superuser** | Yes  | Yes    | Yes    | Yes  | Yes    | Yes     |

Superusers bypass all role checks via the `role_required` decorator.

### API ViewSet (`views_api.py`)

Permission class: `permissions.IsAuthenticated` (any authenticated user can
reach the ViewSet, but `get_queryset()` filters results by role).

**Queryset scoping in `get_queryset()`:**

| Role / Condition                              | Records Visible                     |
|-----------------------------------------------|-------------------------------------|
| `user.is_staff` or `user.is_direction`        | All tenant records                  |
| `user.role == 'prefet'`                       | All tenant records                  |
| `user.is_student`                             | Own records only (`student=user`)   |
| `user.is_parent`                              | Children's records (`student__parent=user`) |
| All other roles                               | Empty queryset (`queryset.none()`)  |

**Resolve action permission (API):**

Only `is_staff`, `is_direction`, or `role == 'prefet'` can call the `resolve`
endpoint. Others receive HTTP 403.

### Parent Portal Views (`accounts/views_parent.py`)

Decorated with `@parent_only` which resolves to `@role_required('parent')`.

| Role          | View Records | Acknowledge |
|---------------|-------------|-------------|
| **parent**    | Yes         | Yes         |
| All others    | No          | No          |

Parents access records through their `Parent.student` link, not directly.
The view filters by `student=student.student` (the `User` object).

### Django Admin (`admin.py`)

Available to any user with `is_staff=True` who can access `/admin/`.
The `get_queryset` method filters by `request.tenant` for non-superusers.
`save_model` auto-sets `reported_by` on creation and `updated_by` on edit.

### Consolidated Access Matrix (All Interfaces)

```
                  Frontend  API       API       API       Parent    Admin
Role              CRUD      List/Get  Write     Resolve   Portal    Panel
---------------------------------------------------------------------------
admin             Full      All       Yes       Yes       --        Full
direction         Full      All       Yes       Yes       --        Full*
prefet            Full      All       Yes       Yes       --        --
secretary         Full      None**    No**      No**      --        --
professor         --        None**    No**      No**      --        --
student           --        Own only  No        No        --        --
parent            --        Children  No        No        Full      --
accountant        --        None**    No**      No**      --        --
librarian         --        None**    No**      No**      --        --
registrar         --        None**    No**      No**      --        --
superuser         Full      All       Yes       Yes       --        Full
---------------------------------------------------------------------------
* if is_staff=True    ** API queryset returns empty for these roles
```

Note: The secretary role has frontend access (via `@prefet_allowed`) but the
API `get_queryset()` does not explicitly grant secretary access -- it falls
through to `queryset.none()`. This is a divergence between frontend and API
access.

---

## Business Logic Workflows

### Incident Lifecycle

```
                                  +------------------+
                                  |  Incident Occurs |
                                  +--------+---------+
                                           |
                                           v
                              +------------+------------+
                              | Staff Creates Record    |
                              | (prefet/direction/admin  |
                              |  /secretary)            |
                              |                         |
                              | Sets: student,          |
                              |   incident_type,        |
                              |   description,          |
                              |   action_taken,         |
                              |   severity,             |
                              |   incident_date         |
                              | Auto: reported_by =     |
                              |   request.user          |
                              |   tenant = request.tenant|
                              |   is_resolved = False   |
                              +------------+------------+
                                           |
                          +----------------+----------------+
                          |                                 |
                          v                                 v
                +---------+---------+           +-----------+-----------+
                | Parent Notified   |           | Record Editable       |
                | (sees on portal)  |           | by staff              |
                +---------+---------+           | (edit view / API PUT) |
                          |                     | Sets: updated_by      |
                          v                     +-----------+-----------+
                +---------+---------+                       |
                | Parent Acknowledges|                      |
                | Sets:             |                       v
                |  parent_acknowledged|          +-----------+-----------+
                |    = True         |           | Staff Resolves        |
                |  parent_acknowledged|         | POST to resolve       |
                |    _at = now()    |           | endpoint              |
                |  parent_response  |           |                       |
                |    = text         |           | Sets:                 |
                +-------------------+           |  is_resolved = True   |
                                                |  resolution_date =   |
                                                |    now().date()       |
                                                |  updated_by =        |
                                                |    request.user       |
                                                +-----------+-----------+
                                                            |
                                                            v
                                                +-----------+-----------+
                                                | Record Deletable      |
                                                | (by staff via         |
                                                |  frontend or API)     |
                                                +-----------------------+
```

### Create Flow (Frontend)

```
GET  /discipline/create/
  --> DisciplinaryActionForm (empty)
  --> renders discipline/action_form.html

POST /discipline/create/
  --> DisciplinaryActionForm(request.POST)
  --> form.is_valid()?
      YES --> action = form.save(commit=False)
              action.tenant = request.tenant
              action.reported_by = request.user
              action.save()
              --> redirect to action_list
      NO  --> re-render form with errors
```

### Create Flow (API)

```
POST /api/v1/discipline/actions/
  Body: { student, incident_type, description, action_taken,
          severity, incident_date, [resolution_date], [is_resolved] }

  --> DisciplinaryActionCreateSerializer validates:
      - incident_date not in future
      - resolution_date >= incident_date (if given)
      - if is_resolved=True, resolution_date required
  --> perform_create() sets tenant + reported_by
  --> 201 Created
```

### Resolve Flow (Frontend)

```
POST /discipline/<pk>/resolve/
  --> get_object_or_404(pk, tenant)
  --> action.is_resolved = True
  --> action.resolution_date = timezone.now().date()
  --> action.updated_by = request.user
  --> action.save()
  --> redirect to action_detail
```

### Resolve Flow (API)

```
POST /api/v1/discipline/actions/<pk>/resolve/
  Body (optional): { "resolution_date": "YYYY-MM-DD" }

  --> Permission check: must be staff/direction/prefet
  --> Sets is_resolved=True, resolution_date, updated_by
  --> save(update_fields=[...])
  --> 200 OK with serialized record
```

### Parent Acknowledgment Flow

```
GET  /accounts/parent/discipline/<action_id>/acknowledge/
  --> Verifies parent owns the student
  --> Checks action not already acknowledged
  --> Renders DisciplineAcknowledgmentForm

POST /accounts/parent/discipline/<action_id>/acknowledge/
  --> DisciplineAcknowledgmentForm(request.POST)
  --> Sets: parent_acknowledged = True
            parent_acknowledged_at = timezone.now()
            parent_response = form.cleaned_data['response']
  --> save(update_fields=[...])
  --> redirect to parent_disciplinary_records
```

---

## Serializers

Defined in `discipline/serializers.py`.

### Hierarchy

```
UserMinimalSerializer          (nested, read-only)
  |-- fields: id, username, email, full_name (via get_full_name property)
  |
DisciplinaryActionSerializer   (detail / update)
  |-- student:     UserMinimalSerializer (read-only)
  |-- reported_by: UserMinimalSerializer (read-only)
  |-- updated_by:  UserMinimalSerializer (read-only)
  |-- severity_display: from get_severity_display
  |-- read_only: id, tenant, reported_by, updated_by, created_at, updated_at
  |
DisciplinaryActionListSerializer  (lightweight list)
  |-- student_name:     source='student.get_full_name'
  |-- reported_by_name: source='reported_by.get_full_name'
  |-- severity_display: from get_severity_display
  |-- All fields read-only
  |
DisciplinaryActionCreateSerializer  (create)
  |-- fields: student, incident_type, description, action_taken,
  |           severity, incident_date, resolution_date, is_resolved
  |-- Validations:
  |     - incident_date <= today
  |     - resolution_date >= incident_date
  |     - is_resolved=True requires resolution_date
```

### Serializer Selection in ViewSet

```
ViewSet Action   -->  Serializer Class
----------------------------------------------
list             -->  DisciplinaryActionListSerializer
create           -->  DisciplinaryActionCreateSerializer
retrieve         -->  DisciplinaryActionSerializer
update           -->  DisciplinaryActionSerializer
partial_update   -->  DisciplinaryActionSerializer
destroy          -->  (no serializer needed)
```

---

## Forms

Defined in `discipline/forms.py`.

### `DisciplinaryActionForm`

ModelForm for `DisciplinaryAction` used by frontend create/edit views.

| Field            | Widget                         |
|------------------|--------------------------------|
| `student`        | Select (form-control)          |
| `incident_type`  | TextInput (form-control)       |
| `description`    | Textarea (4 rows)              |
| `action_taken`   | Textarea (4 rows)              |
| `severity`       | Select (form-control)          |
| `incident_date`  | DateInput (type=date)          |
| `resolution_date`| DateInput (type=date)          |
| `is_resolved`    | CheckboxInput (form-check-input)|

Excluded from form: `tenant`, `reported_by`, `updated_by`, `parent_acknowledged`,
`parent_acknowledged_at`, `parent_response` -- these are set programmatically.

### `DisciplineAcknowledgmentForm` (in `accounts/forms.py`)

Plain Form (not ModelForm) used by parent acknowledge view.

| Field      | Widget                   | Required |
|------------|--------------------------|----------|
| `response` | Textarea (4 rows)        | No       |

---

## Django Admin Configuration

Registered in `discipline/admin.py` as `DisciplinaryActionAdmin`.

| Setting          | Value                                                                 |
|------------------|-----------------------------------------------------------------------|
| `list_display`   | student, incident_type, severity, incident_date, is_resolved, tenant  |
| `list_filter`    | severity, is_resolved, incident_date, tenant                         |
| `search_fields`  | student__username, student__first_name, student__last_name, incident_type, description |
| `readonly_fields`| created_at, updated_at, reported_by, updated_by                       |

**Fieldsets:**

1. "Basic Information" -- tenant, student, reported_by, incident_type, severity
2. "Details" -- description, action_taken, incident_date, resolution_date, is_resolved
3. "Audit Trail" (collapsed) -- created_at, updated_at, updated_by

**Custom behavior:**

- `get_queryset`: Filters by `request.tenant` for non-superusers
- `save_model`: On create sets `reported_by = request.user`; on edit sets `updated_by = request.user`

---

## Templates

Located in `templates/discipline/`.

| Template                       | Used By                         | Purpose                     |
|--------------------------------|---------------------------------|-----------------------------|
| `action_list.html`             | `disciplinary_action_list`      | Paginated list with filters |
| `action_form.html`             | `disciplinary_action_create`, `disciplinary_action_edit` | Create/edit form |
| `action_detail.html`           | `disciplinary_action_detail`    | Single record detail view   |
| `action_confirm_delete.html`   | `disciplinary_action_delete`    | Deletion confirmation       |

Parent-facing templates live in `templates/parent/`:

| Template                       | Used By                              | Purpose                     |
|--------------------------------|--------------------------------------|-----------------------------|
| `discipline.html`              | `parent_disciplinary_records`        | List child's records        |
| `discipline_acknowledge.html`  | `parent_acknowledge_discipline`      | Acknowledgment form         |
| `dashboard.html`               | `parent_dashboard`                   | Shows `unacked_discipline` count |

---

## Dependencies

### Discipline App Depends On (Imports From)

```
discipline/
  |
  +--> core.School            (models.py: tenant FK)
  +--> settings.AUTH_USER_MODEL (models.py: student, reported_by, updated_by FKs)
  +--> accounts.decorators     (views_frontend.py: prefet_allowed, tenant_required)
  +--> django_ratelimit        (views_frontend.py: @ratelimit)
  +--> rest_framework          (views_api.py, serializers.py: DRF ViewSet, serializers)
  +--> django_filters          (views_api.py: DjangoFilterBackend)
```

### Other Apps That Depend On Discipline (Import From)

```
discipline/
  ^
  |
  +-- accounts/views_parent.py     imports DisciplinaryAction for parent portal
  |     - parent_dashboard: counts unacknowledged actions
  |     - parent_disciplinary_records: lists child's actions
  |     - parent_acknowledge_discipline: parent acknowledges action
  |
  +-- monitoring/views_frontend.py  imports DisciplinaryAction (conditional)
  |     - monitoring_dashboard: shows total + unresolved counts
  |     - monitoring_export_csv: exports discipline stats
  |
  +-- monitoring/views_api.py       imports DisciplinaryAction (conditional)
  |     - DashboardStatsAPI: includes discipline total/unresolved in stats
  |
  +-- monitoring/serializers.py     DisciplineStatsSerializer (output-only)
  |
  +-- core/management/commands/generate_beta_data.py  creates seed data
  |
  +-- School_System/urls.py         includes discipline URL patterns
  |
  +-- School_System/roles.py        Direction + Secretary roles declare
  |     view_disciplinary_records + create_disciplinary_actions permissions
  |
  +-- accounts/permissions.py       IsPrefetOrDirectionUser permission class
```

### Dependency Diagram

```
+------------------+      +-------------------+      +------------------+
|  accounts app    |----->|  discipline app   |<-----|  monitoring app  |
|                  |      |                   |      |  (conditional)   |
| - decorators     |      | - models          |      | - views_frontend |
| - models (User)  |      | - views_frontend  |      | - views_api      |
| - views_parent   |<-----| - views_api       |      | - serializers    |
| - forms          |      | - serializers     |      +------------------+
| - permissions    |      | - forms           |
+------------------+      | - admin           |      +------------------+
                          | - urls            |      |  core app        |
                          +-------------------+      | - School model   |
                                |                    +------------------+
                                |                           ^
                                +---------------------------+
                                       tenant FK

+------------------+
| django_ratelimit |----> used by views_frontend.py
+------------------+

+------------------+
| rest_framework   |----> used by views_api.py, serializers.py
+------------------+

+------------------+
| django_filters   |----> used by views_api.py (DjangoFilterBackend)
+------------------+
```

---

## Data Flow Diagrams

### Frontend CRUD Data Flow

```
Browser                  Django Views              Database
-------                  ------------              --------

GET /discipline/
  |----[HTTP]----------> disciplinary_action_list
                           |--filter(tenant)------> DisciplinaryAction
                           |  + severity/search/     SELECT ... WHERE
                           |    resolved filters       tenant_id = ?
                           |<--QuerySet------------- [rows]
  |<---[HTML]----------- render action_list.html


POST /discipline/create/
  |----[form data]-----> disciplinary_action_create
                           |--DisciplinaryActionForm
                           |    .is_valid()
                           |--form.save(commit=False)
                           |  action.tenant = request.tenant
                           |  action.reported_by = request.user
                           |--action.save()--------> INSERT INTO
                           |                         disciplinary...
  |<---[302]------------- redirect -> action_list


POST /discipline/<pk>/resolve/
  |----[POST]----------> disciplinary_action_resolve
                           |--get_object_or_404()---> SELECT ... WHERE
                           |                           pk=? AND tenant=?
                           |--set is_resolved=True
                           |--action.save()--------> UPDATE ...
                           |                         SET is_resolved=True
  |<---[302]------------- redirect -> action_detail
```

### API Data Flow

```
Client                   DRF ViewSet               Database
------                   -----------               --------

GET /api/v1/discipline/actions/?severity=critical
  |----[HTTP+JWT]------> DisciplinaryActionViewSet
                           .list()
                           |--get_queryset()
                           |   filter by tenant
                           |   filter by role (all/own/children)
                           |--DjangoFilterBackend
                           |   .severity=critical
                           |--SearchFilter, OrderingFilter
                           |--paginate_queryset()--> SELECT ... WHERE
                           |                         tenant_id=? AND
                           |                         severity='critical'
                           |<--QuerySet------------- [rows]
                           |--DisciplinaryActionListSerializer
  |<---[JSON]------------ { count, next, prev, results: [...] }


POST /api/v1/discipline/actions/
  |----[JSON+JWT]------> DisciplinaryActionViewSet
                           .create()
                           |--DisciplinaryActionCreateSerializer
                           |    .is_valid()
                           |    validate_incident_date()
                           |    validate_resolution_date()
                           |    cross-field validate()
                           |--perform_create()
                           |  serializer.save(
                           |    tenant=request.tenant,
                           |    reported_by=request.user
                           |  )--------------------> INSERT INTO ...
  |<---[201 JSON]-------- { id, student, ... }


POST /api/v1/discipline/actions/<pk>/resolve/
  |----[JSON+JWT]------> DisciplinaryActionViewSet
                           .resolve()
                           |--Permission check
                           |   (staff/direction/prefet)
                           |--get_object()---------> SELECT ... WHERE pk=?
                           |--set is_resolved=True
                           |--save(update_fields)---> UPDATE ... SET
                           |                          is_resolved=True
  |<---[200 JSON]-------- { id, is_resolved: true, ... }
```

### Parent Portal Data Flow

```
Parent Browser           Parent Views              Database
--------------           ------------              --------

GET /accounts/parent/discipline/
  |----[HTTP]----------> parent_disciplinary_records
                           |--get_active_child()
                           |   session['active_child_id']
                           |   --> Parent.objects
                           |       .filter(user=request.user)
                           |<--parent, student
                           |
                           |--DisciplinaryAction
                           |   .objects.filter(
                           |     student=student.student
                           |   )--------------------> SELECT ... WHERE
                           |                           student_id = ?
                           |<--QuerySet------------- [rows]
  |<---[HTML]----------- render parent/discipline.html


POST /accounts/parent/discipline/<id>/acknowledge/
  |----[form data]-----> parent_acknowledge_discipline
                           |--get_active_child()
                           |--get_object_or_404(
                           |    pk=action_id,
                           |    student=student.student
                           |  )--------------------> SELECT ... WHERE
                           |                          pk=? AND student_id=?
                           |--DisciplineAcknowledgmentForm
                           |    .is_valid()
                           |--action.parent_acknowledged = True
                           |  action.parent_acknowledged_at = now()
                           |  action.parent_response = ...
                           |--action.save(
                           |    update_fields=[...]
                           |  )--------------------> UPDATE ... SET
                           |                         parent_acknowledged=1
  |<---[302]------------- redirect -> parent_disciplinary_records
```

### Monitoring Dashboard Data Flow

```
Staff Browser            Monitoring Views           Database
-------------            ----------------           --------

GET /monitoring/
  |----[HTTP]----------> monitoring_dashboard
                           |
                           |  (conditional import)
                           |--from discipline.models
                           |   import DisciplinaryAction
                           |
                           |--DisciplinaryAction.objects
                           |   .filter(tenant=request.tenant)
                           |   .count()
                           |   .filter(is_resolved=False)
                           |   .count()  -----------> SELECT COUNT(*)
                           |                          FROM discipline_...
                           |                          WHERE tenant_id=?
                           |<--stats: {total, unresolved}
                           |
  |<---[HTML]----------- render monitoring/dashboard.html
                         (includes discipline_stats)
```

---

## Rate Limiting

| View                         | Rate          | Method | Key    |
|------------------------------|---------------|--------|--------|
| `disciplinary_action_list`   | 100/hour      | ALL    | user   |
| `disciplinary_action_create` | 50/hour       | POST   | user   |
| `disciplinary_action_edit`   | 50/hour       | POST   | user   |

The `detail`, `delete`, and `resolve` frontend views have no rate limiting
beyond the general middleware.

API views rely on DRF's throttling configuration (not app-specific).

---

## Migrations

| Migration | Description |
|-----------|-------------|
| `0001_initial.py` | Creates `DisciplinaryAction` table with all core fields |
| `0002_disciplinaryaction_parent_acknowledged_and_more.py` | Adds `parent_acknowledged`, `parent_acknowledged_at`, `parent_response` |

---

## Files Summary

```
discipline/
  __init__.py
  apps.py               DisciplineConfig (name='discipline')
  models.py             DisciplinaryAction model
  forms.py              DisciplinaryActionForm (ModelForm)
  views_frontend.py     6 function-based views (list, create, detail, edit, delete, resolve)
  views_api.py          DisciplinaryActionViewSet (ModelViewSet with 3 custom actions)
  serializers.py        4 serializers (UserMinimal, Detail, List, Create)
  urls.py               frontend_urlpatterns + api_urlpatterns + api_router
  admin.py              DisciplinaryActionAdmin (ModelAdmin)
  migrations/
    __init__.py
    0001_initial.py
    0002_..._parent_acknowledged_and_more.py
  tests/
    test_models.py
    test_forms.py
    test_admin.py
    test_serializers.py
    test_views_frontend.py
    test_views_api.py
```

**Not present:** `signals.py`, `tasks.py` -- the discipline app has no signals
and no asynchronous/Celery task processing.

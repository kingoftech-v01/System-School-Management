# Notes App - Architecture

## Overview

The notes app implements a professor-to-student grading system with a multi-stage approval workflow, complete audit history, async email notifications, and a dual interface (server-rendered templates + REST API). All data is tenant-scoped via a ForeignKey to the `core.School` model.

## High-Level Data Flow

```
Professor creates note (draft)
        |
        v
Professor submits for approval (status -> pending)
        |
        v
Direction reviews pending queue
        |
    +---+---+-------------------+
    |       |                   |
    v       v                   v
Approved  Rejected   Revision Requested
    |       |                   |
    v       v                   v
  Celery  Celery             Celery
  task     task               task
    |       |                   |
    v       v                   v
  Email   Email              Email
  to prof  to prof            to prof
  + student
```

## Approval Workflow State Machine

```
              submit_for_approval()
    DRAFT --------------------------> PENDING
      ^                                 |
      |                    +------------+------------+
      |                    |            |            |
      |                    v            v            v
      |               APPROVED     REJECTED   REVISION_REQUESTED
      |                                             |
      +---------------------------------------------+
              (professor edits and re-submits)
```

### Status Transitions

| From | To | Actor | Method |
| --- | --- | --- | --- |
| draft | pending | Professor | `submit_for_approval()` |
| pending | approved | Direction | `approve(user, notes)` |
| pending | rejected | Direction | `reject(user, notes)` |
| pending | revision_requested | Direction | `request_revision(user, notes)` |
| revision_requested | draft | Professor | (manual edit, then re-submit) |

### Edit/Delete Restrictions by Status

| Status | Professor Can Edit | Professor Can Delete | Direction Can Edit |
| --- | --- | --- | --- |
| draft | Yes | Yes (hard delete) | Yes |
| pending | Yes | Yes (hard delete) | Yes |
| approved | No | No | Yes |
| rejected | Yes | Yes (hard delete) | Yes |
| revision_requested | Yes | Yes (hard delete) | Yes |

## Component Architecture

### 1. Models Layer (`models.py`)

Three models form the core data layer:

**ProfessorNote** is the central entity. Key design decisions:
- `weighted_score` is auto-calculated in `save()` as `(score / max_score) * 100 * coefficient`
- `delete()` is overridden: approved notes are soft-deleted (is_deleted=True), draft/pending notes are hard-deleted
- `can_edit()` and `can_delete()` encode business rules for role-based access at the model level
- `submit_for_approval()`, `approve()`, `reject()`, `request_revision()` are convenience methods that encapsulate status transitions
- Four database indexes optimize common query patterns: (tenant, student, status), (filiere, subject), (session, semester), (created_at)
- Two custom permissions (`approve_note`, `view_all_notes`) are defined for use with Django's permission framework

**NoteHistory** provides an immutable audit trail. Each record captures an action type, the user who made the change, and JSON snapshots of old/new values. History records are created both by signals (auto-tracking) and by views (explicit creation).

**NoteComment** enables communication between professors and direction during the approval process. Comments are append-only with no edit or delete capability.

### 2. Signals Layer (`signals.py`)

Two signal handlers are registered in `apps.py` via the `ready()` method:

**`track_note_changes` (pre_save)**: Fires before every ProfessorNote save. If the instance already exists in the database (has a pk), it fetches the old version and compares `score` and `status`. If either changed, it creates a NoteHistory record with old/new values. The `changed_by` user is obtained from a `_changed_by` attribute that callers can optionally set on the instance.

**`log_note_creation` (post_save)**: Fires after every ProfessorNote save. If `created=True`, it logs an INFO message with the professor's username, student's username, and subject.

Note: There is intentional duplication between signal-created history records and view-created history records. The signals serve as a safety net to capture changes made outside of views (e.g., management commands, admin, shell).

### 3. Views Layer

The app has two parallel view layers that share the same models and business logic:

#### Frontend Views (`views_frontend.py`)

Ten server-rendered views using Django templates. All views use decorator-based access control:

- `@login_required` -- requires authentication
- `@professor_only` / `@direction_only` -- role-based access (from `accounts.decorators`)
- `@tenant_required` -- ensures `request.tenant` is set (multi-tenant middleware)
- `@ratelimit` -- rate limiting (from `django-ratelimit`)

The `note_create` view auto-populates `filiere`, `session`, and `semester` fields if not provided by the form. It queries `FiliereSubject` to find the filiere for the selected subject/course, and uses the current session/semester from `core.models`.

The `note_approve` view handles all three approval actions (approve, reject, request revision) via a single form (`NoteApprovalForm`) where direction selects the target status.

The `note_comment_create` view has custom permission logic: it allows the note's owner (professor) or direction/admin staff to comment, but rejects other users.

#### API Views (`views_api.py`)

Two DRF ViewSets provide a REST API:

**ProfessorNoteViewSet (ModelViewSet)**: Full CRUD with four custom actions:
- `pending` (list action, GET) -- direction-only, lists pending notes
- `approve` (detail action, POST) -- direction-only, changes status
- `history` (detail action, GET) -- returns note's audit trail

The ViewSet uses dynamic serializer selection via `get_serializer_class()`:
- List: `ProfessorNoteListSerializer` (lightweight, fewer fields)
- Create: `ProfessorNoteCreateSerializer` (input validation)
- Approve: `NoteApprovalSerializer` (status + approval_notes only)
- Default: `ProfessorNoteSerializer` (full detail)

Queryset filtering is role-aware: professors see only their own notes, direction sees all tenant notes.

**NoteHistoryViewSet (ReadOnlyModelViewSet)**: List and retrieve only. Filtered by tenant via `note__tenant`.

Both ViewSets use `DjangoFilterBackend` for field-based filtering, `SearchFilter` for text search, and `OrderingFilter` for sort control.

### 4. Serializers Layer (`serializers.py`)

Five serializers handle data transformation between models and JSON:

- `ProfessorNoteSerializer` -- full detail with computed display fields (professor_name, student_name, subject_name, status_display, note_type_display)
- `ProfessorNoteListSerializer` -- lightweight subset for list endpoints (no comment, no professor_name)
- `ProfessorNoteCreateSerializer` -- input-only with custom validation (score 0-20, coefficient > 0)
- `NoteApprovalSerializer` -- restricted to status + approval_notes with validation (only approved/rejected/revision_requested allowed)
- `NoteHistorySerializer` -- read-only with computed `note_title` and `changed_by_name`

### 5. Forms Layer (`forms.py`)

Three Django ModelForms for the template-based frontend:

- `ProfessorNoteForm` -- fields: student, subject, note_type, score, max_score, coefficient (readonly widget), comment, private_note
- `NoteApprovalForm` -- fields: status (limited to approve/reject/revision), approval_notes
- `NoteCommentForm` -- fields: comment

All forms use Bootstrap `form-control` CSS classes via widget attrs.

### 6. Tasks Layer (`tasks.py`)

One Celery shared task:

**`notify_note_status_change(note_id, status)`**: Sends email notifications when a note's status changes. Always notifies the professor. Additionally notifies the student when the status is `approved`. Uses `fail_silently=True` to prevent email failures from breaking the workflow. Handles nonexistent notes gracefully via try/except.

This task is called from both `views_frontend.note_approve` and `views_api.ProfessorNoteViewSet.approve` using `.delay()` for async execution.

### 7. Admin Layer (`admin.py`)

Three admin classes registered with `@admin.register`:

- `ProfessorNoteAdmin` -- full admin with fieldsets (Basic Information, Score Details, Status & Approval, Private Notes, Audit Trail), NoteHistoryInline, tenant-filtered queryset for non-superusers
- `NoteHistoryAdmin` -- read-only (no add/delete permissions), all fields readonly
- `NoteCommentAdmin` -- basic list/filter configuration

### 8. URL Routing (`urls.py`)

URLs are split into two namespaced groups:

- **Frontend** (`frontend_urlpatterns`): Nine path-based URLs mapped to `views_frontend` functions
- **API** (`api_urlpatterns`): DRF router-generated URLs for two ViewSets

Both are combined into a single `urlpatterns` list with prefix-based separation (`/api/` vs `/`).

## Cross-Cutting Concerns

### Multi-Tenancy

Every query filters by `tenant=request.tenant`. The `tenant` field is a ForeignKey to `core.School`. The `@tenant_required` decorator and tenant middleware ensure `request.tenant` is always available in views.

### Rate Limiting

All views are rate-limited via `django-ratelimit`:
- GET endpoints: 100 requests/hour per user
- POST endpoints (create/edit): 50 requests/hour per user
- DELETE endpoint: 20 requests/hour per user

### Audit Trail

Changes are tracked at two levels:
1. **Signal-level** (automatic): The `track_note_changes` pre_save signal captures score and status changes on every save, regardless of how the save was triggered
2. **View-level** (explicit): Views create NoteHistory records with richer context (change_summary, specific action types like 'created', 'deleted', 'status_changed')

### Soft Delete

Approved notes are never physically deleted. The `delete()` override on ProfessorNote sets `is_deleted=True` and `deleted_at` for approved notes. Non-approved notes are hard-deleted. All list queries exclude `is_deleted=True` records.

## Dependency Graph

```
notes
  +---> accounts
  |       +---> User model (professor, student, direction)
  |       +---> Decorators (professor_only, direction_only, tenant_required)
  |       +---> Permissions (IsProfessorUser, IsDirectionUser)
  |
  +---> core
  |       +---> School model (tenant FK)
  |       +---> Session model (academic session FK)
  |       +---> Semester model (semester FK)
  |
  +---> course
  |       +---> Course model (subject FK)
  |
  +---> filieres
  |       +---> Filiere model (filiere FK)
  |       +---> FiliereSubject model (auto-populate filiere from subject)
  |
  +---> celery (async task execution)
  +---> django-ratelimit (rate limiting)
  +---> djangorestframework (API layer)
  +---> django-filter (DRF filtering)
```

## Known Issues and Technical Debt

1. **`get_full_name` property/method mismatch**: The User model defines `get_full_name` as a `@property`, but `tasks.py` calls it as `get_full_name()` (with parentheses). This works in production because Django's User model has both, but it creates confusion in tests.

2. **Duplicate history creation**: Both signals and views create NoteHistory records. For updates triggered through views, this can result in duplicate history entries (one from the signal, one from the view). The signal serves as a safety net for non-view changes.

3. **No NoteComment API ViewSet**: NoteComment has a frontend view (`note_comment_create`) but no DRF ViewSet. API consumers cannot create or list comments.

4. **No pagination on pending notes view**: The `notes_pending_approval` frontend view returns all pending notes without pagination. This could be slow for tenants with many pending notes.

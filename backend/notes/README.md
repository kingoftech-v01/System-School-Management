# Notes App

Professor note management with an approval workflow, audit history, and status change notifications.

## Description

The notes app manages professor-submitted notes (grades/scores) with a full approval workflow. Notes start as draft or pending, and direction staff can approve, reject, or request revisions. The app includes a complete audit trail via NoteHistory, soft delete support, and Celery-based notifications when note status changes. Edit and delete operations are blocked for approved notes. NoteComment enables communication between professors and direction during the approval process.

## Main Features

- **Note CRUD**: Full create, list, detail, edit, delete with soft delete support
- **Approval Workflow**: Draft -> Pending -> Approved/Rejected/Revision Requested
- **Edit/Delete Restrictions**: Cannot modify approved notes (direction/secretary override for edits)
- **Audit Trail**: NoteHistory tracks creates, updates, deletes, status changes with old/new JSON values
- **Pending Queue**: Direction-only view of notes pending approval
- **All Notes View**: Direction-only view of all notes with status, student, and professor filters
- **Comments**: NoteComment for professor/direction communication during approval
- **Notifications**: Celery task notifies professors on status change; students on approval
- **Weighted Scores**: Auto-calculated as `(score / max_score) * 100 * coefficient`
- **Rate Limiting**: All views protected with `django-ratelimit`
- **REST API**: Full DRF API with filtering, search, ordering, and pagination

## User Roles

| Role | Permissions |
|------|------------|
| professor | CRUD own notes; edit/delete blocked for approved notes; add comments on own notes |
| direction | View all notes; view pending queue; approve/reject/request revision; add comments |
| secretary | Can edit approved notes (model-level `can_edit` check); same as direction for edits |
| admin | Full access via API and Django admin; bypasses all permission checks (superuser) |
| student | No access to notes views; receives email notification when a note is approved |
| parent | No direct access to notes views |
| prefet | No direct access to notes views |
| accountant | No direct access to notes views |
| librarian | No direct access to notes views |
| registrar | No direct access to notes views |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| ProfessorNote | Professor (frontend + API) | List + Detail (professor: own; direction: all) | Professor (if not approved); direction/secretary (even approved) | Soft delete (if not approved) |
| NoteHistory | Automatic (signals + views) | Via note detail + API | N/A (immutable) | N/A (immutable) |
| NoteComment | Professor (own notes) + direction (any note) | Via note detail | N/A | N/A |

## Models

### ProfessorNote
Professor notes for students with filiere coefficient and approval workflow. Cannot be deleted after approval (soft delete with audit trail).

| Field | Type | Description |
|-------|------|-------------|
| tenant | FK (School) | Multi-tenant relationship |
| student | FK (User) | Student receiving the note |
| professor | FK (User) | Professor who created the note |
| filiere | FK (Filiere) | Filiere/program (auto-populated from subject if not set) |
| subject | FK (Course) | Subject/course for the note |
| session | FK (Session) | Academic session (auto-populated to current) |
| semester | FK (Semester) | Semester (auto-populated to current) |
| note_type | CharField | participation, homework, quiz, midterm, final, project, presentation, behavior, attendance, other |
| score | Decimal(5,2) | Score out of max_score (validators: 0-100) |
| max_score | Decimal(5,2) | Maximum possible score (default: 100) |
| coefficient | Decimal(3,2) | Weight from filiere configuration (0.1-10) |
| weighted_score | Decimal(6,2) | Auto-calculated: (score/max_score)*100*coefficient |
| comment | TextField | Professor's comment (visible to student) |
| private_note | TextField | Internal note (not visible to student) |
| status | CharField | draft, pending, approved, rejected, revision_requested |
| submitted_for_approval | Boolean | Whether note has been submitted |
| approved_by | FK (User) | Who approved/rejected the note |
| approved_at | DateTime | When the note was approved/rejected |
| approval_notes | TextField | Reviewer feedback |
| is_deleted | Boolean | Soft delete flag |
| deleted_at | DateTime | When soft-deleted |
| deleted_by | FK (User) | Who soft-deleted |
| last_modified_by | FK (User) | Last user to modify |
| created_at | DateTime | Auto-set on creation |
| updated_at | DateTime | Auto-set on save |

**DB Indexes**: (tenant, student, status), (filiere, subject), (session, semester), (created_at)

**Custom Permissions**: `approve_note`, `view_all_notes`

### NoteHistory
Immutable audit trail for all changes to professor notes.

| Field | Type | Description |
|-------|------|-------------|
| note | FK (ProfessorNote) | The note being tracked |
| action | CharField | created, updated, submitted, approved, rejected, revision_requested, soft_deleted |
| changed_by | FK (User) | Who made the change |
| changed_at | DateTime | Auto-set timestamp |
| old_values | JSONField | Previous field values |
| new_values | JSONField | New field values |
| change_summary | TextField | Human-readable summary |

### NoteComment
Comments/feedback on professor notes for communication during the approval workflow.

| Field | Type | Description |
|-------|------|-------------|
| note | FK (ProfessorNote) | The note being commented on |
| author | FK (User) | Comment author |
| comment | TextField | Comment content |
| created_at | DateTime | Auto-set timestamp |

## Frontend Endpoints

| URL Pattern | View | Method | Role | Description |
|-------------|------|--------|------|-------------|
| `/` | note_list | GET | professor | List professor's own notes (paginated, filterable by status/student) |
| `/all/` | note_list_all | GET | direction | List ALL notes with status/student/professor filters |
| `/create/` | note_create | GET/POST | professor | Create a new note |
| `/<pk>/` | note_detail | GET | professor | View note details with history |
| `/<pk>/edit/` | note_edit | GET/POST | professor | Edit a note (blocked for approved) |
| `/<pk>/delete/` | note_delete | GET/POST | professor | Soft delete confirmation + action (blocked for approved) |
| `/<pk>/comment/` | note_comment_create | GET/POST | professor/direction | Add a comment to a note |
| `/pending/` | notes_pending_approval | GET | direction | View notes awaiting approval |
| `/<pk>/approve/` | note_approve | GET/POST | direction | Approve, reject, or request revision |

**Namespace**: `frontend:notes:<view_name>`

## API Endpoints

### ProfessorNoteViewSet (basename: `note`)

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/api/notes/` | GET | Authenticated | List notes (professor: own only; direction: all) |
| `/api/notes/` | POST | Authenticated | Create a note |
| `/api/notes/{pk}/` | GET | Authenticated | Retrieve note detail |
| `/api/notes/{pk}/` | PUT/PATCH | Authenticated | Update note (blocked for approved) |
| `/api/notes/{pk}/` | DELETE | Authenticated | Soft delete note (blocked for approved) |
| `/api/notes/pending/` | GET | Direction | List notes pending approval |
| `/api/notes/{pk}/approve/` | POST | Direction | Approve/reject/request revision |
| `/api/notes/{pk}/history/` | GET | Authenticated | Get note history |

**Filtering**: `status`, `student`, `subject`, `is_deleted`
**Search**: `comment`
**Ordering**: `created_at`, `score`

### NoteHistoryViewSet (basename: `history`, read-only)

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/api/history/` | GET | Authenticated | List all history records |
| `/api/history/{pk}/` | GET | Authenticated | Retrieve a history record |

**Filtering**: `note`, `action`, `changed_by`
**Ordering**: `changed_at`

**API Namespace**: `api:notes:<resource-name>`

## Serializers

| Serializer | Purpose | Fields |
|------------|---------|--------|
| ProfessorNoteSerializer | Full detail (retrieve/update) | All fields + professor_name, student_name, subject_name, approved_by_name, status_display, note_type_display |
| ProfessorNoteListSerializer | Lightweight list | id, student_name, subject_name, score, coefficient, note_type, status, status_display, created_at |
| ProfessorNoteCreateSerializer | Create only | student, subject, score, coefficient, note_type, comment, status |
| NoteApprovalSerializer | Approve/reject | status, approval_notes |
| NoteHistorySerializer | History read-only | All fields + changed_by_name, note_title |

## Forms

| Form | Fields | Usage |
|------|--------|-------|
| ProfessorNoteForm | student, subject, note_type, score, max_score, coefficient, comment, private_note | Create/edit notes (frontend) |
| NoteApprovalForm | status (approve/reject/revision), approval_notes | Approve/reject notes (frontend) |
| NoteCommentForm | comment | Add comments to notes (frontend) |

## File Structure

```
notes/
  __init__.py
  apps.py              # NotesConfig with signal import in ready()
  models.py            # ProfessorNote, NoteHistory, NoteComment
  views_frontend.py    # 10 frontend views (note_list, note_list_all, note_create, note_detail, note_edit, note_delete, note_comment_create, notes_pending_approval, note_approve)
  views_api.py         # ProfessorNoteViewSet, NoteHistoryViewSet
  urls.py              # Frontend + API URL routing with DRF router
  serializers.py       # 5 DRF serializers
  forms.py             # ProfessorNoteForm, NoteApprovalForm, NoteCommentForm
  signals.py           # pre_save (track changes), post_save (log creation)
  tasks.py             # notify_note_status_change Celery task
  admin.py             # ProfessorNoteAdmin (with NoteHistoryInline), NoteHistoryAdmin, NoteCommentAdmin
  README.md
  TODO.md
  ARCHITECTURE.md
  migrations/
    __init__.py
    0001_initial.py
  tests/
    __init__.py
    test_models.py         # ProfessorNote, NoteHistory, NoteComment model tests
    test_views_frontend.py # All 10 frontend views + role-based access tests
    test_views_api.py      # ProfessorNoteViewSet + NoteHistoryViewSet tests
    test_signals.py        # pre_save/post_save signal tests
    test_tasks.py          # Celery task notification tests
    test_forms.py          # ProfessorNoteForm, NoteApprovalForm, NoteCommentForm tests
    test_serializers.py    # All 5 serializer tests
    test_admin.py          # Admin registration, config, and permission tests
```

## Dependencies

- `accounts` -- User model (professor, student, direction), decorators (`professor_only`, `direction_only`, `tenant_required`), permissions (`IsProfessorUser`, `IsDirectionUser`)
- `core` -- School model (tenant), Session and Semester models
- `course` -- Course model (subject FK)
- `filieres` -- Filiere and FiliereSubject models (filiere FK, auto-population)
- `celery` -- Async status change notifications
- `django-ratelimit` -- Rate limiting on all views
- `djangorestframework` -- API ViewSets, serializers, permissions
- `django-filter` -- DRF filtering backend

## URL Namespace

- Frontend: `frontend:notes:<view_name>`
- API: `api:notes:<resource-name>`

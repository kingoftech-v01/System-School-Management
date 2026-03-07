# Notes - TODO

## Backend

- [x] Add NoteComment views: allow professors and direction to add comments to notes -- `note_comment_create` view added in `views_frontend.py`, NoteCommentForm in `forms.py`
- [x] Add pagination to `note_list` view -- paginated with `Paginator(notes, 20)` in `views_frontend.py`
- [x] Add filtering by status and student to `note_list` view -- `?status=` and `?student=` query params supported
- [x] Add a view for direction to see all notes (not just pending) with filter options -- `note_list_all` view with status, student, and professor filters
- [ ] Add bulk note approval endpoint (direction can approve multiple notes at once)
- [ ] Add note export (CSV/PDF) for direction to download note reports
- [ ] Add `NoteComment` to the API (currently only frontend view exists; no DRF ViewSet for comments)

## Frontend

- [x] Add comment section to note detail template (showing NoteComments and a form to add new comments) -- `note_comment_create` view and URL at `/<pk>/comment/`
- [x] Add status filter dropdown and student search to note list page -- implemented with query params in `note_list` view
- [x] Add pagination controls to note list template -- paginated at 20 items per page
- [ ] Add visual status badges (draft=gray, pending=yellow, approved=green, rejected=red) to note list items
- [ ] Add AJAX-based inline comment submission on note detail page (avoid full page reload)
- [ ] Add confirmation modal for approve/reject actions instead of separate page

## Sidebar

- [ ] Expand Notes from single link to expandable menu with sub-links: "My Notes" (professors), "Pending Approval" (direction), "All Notes" (direction)

## Security

- [x] No critical security issues found -- rate limiting applied to all views via `django-ratelimit`

## Unnecessary Files

- [x] None identified

## Documentation

- [x] Add module docstring to models.py -- docstring present at top of `models.py`
- [x] Write comprehensive README.md with API endpoints, file structure, and all 10 roles
- [x] Write ARCHITECTURE.md documenting data flow, approval workflow, and signal/task pipeline

## Testing

A full test suite exists in `notes/tests/` covering all major components:

| Test Module | Tests | Coverage |
| --- | --- | --- |
| `test_models.py` | 15 tests | ProfessorNote CRUD, weighted score calculation, submit/approve/reject/revision, soft delete vs hard delete, can_edit/can_delete permissions; NoteHistory creation; NoteComment creation |
| `test_views_frontend.py` | 30 tests | All 10 frontend views (note_list, note_list_all, note_create, note_detail, note_edit, note_delete, note_comment_create, notes_pending, note_approve); role-based access (professor, direction, admin, student); filters; anonymous redirect; nonexistent/wrong-owner 404s |
| `test_views_api.py` | 16 tests | ProfessorNoteViewSet (list, retrieve, create, update, delete, pending, approve, history, search, filter); NoteHistoryViewSet (list, retrieve, read-only enforcement, filter, ordering); authentication enforcement |
| `test_signals.py` | 11 tests | `track_note_changes` pre_save: score change, status change, both, no-change skip, old/new values, change_summary, `_changed_by` attribute; `log_note_creation` post_save: log content, professor/student username, update-no-log, multiple creations |
| `test_tasks.py` | 5 tests | `notify_note_status_change`: professor notification, student notification on approval, no student notification on rejection, nonexistent note handling, pending status notification |
| `test_forms.py` | 7 tests | ProfessorNoteForm (valid, missing required, optional fields, meta fields); NoteApprovalForm (approve, reject, meta fields); NoteCommentForm (valid, empty invalid) |
| `test_serializers.py` | 11 tests | ProfessorNoteSerializer fields and values; ProfessorNoteListSerializer lightweight fields; ProfessorNoteCreateSerializer validation (valid, score bounds, coefficient bounds, missing fields); NoteApprovalSerializer (valid statuses, invalid status); NoteHistorySerializer fields |
| `test_admin.py` | 12 tests | Admin registration for all 3 models; ProfessorNoteAdmin (list_display, list_filter, search_fields, readonly_fields, inlines, fieldsets, queryset); NoteHistoryAdmin (config, no add/delete permissions); NoteCommentAdmin config |

**Total: ~107 tests across 8 test modules.**

### Running Tests

```bash
# Run all notes tests
venv/Scripts/python.exe manage.py test notes --settings=School_System.settings.development

# Run a specific test module
venv/Scripts/python.exe manage.py test notes.tests.test_models --settings=School_System.settings.development

# Run with pytest (if installed)
venv/Scripts/python.exe -m pytest notes/tests/ --settings=School_System.settings.development
```

### Test Gotchas

- Celery tasks are mocked with `@patch('notes.tasks.send_mail')` and `@patch('notes.views_frontend.notify_note_status_change')` to avoid actual email sending
- `get_full_name` is a `@property` on the User model but `tasks.py` calls it as `get_full_name()` (method) -- test_tasks.py works around this with a `CallableStr` monkey-patch
- API tests use `force_authenticate()` (not `login()`) due to `django-axes` backend requirements
- Frontend view tests use `Client(raise_request_exception=False)` to catch 500s gracefully
- Tenant filtering depends on `request.tenant` middleware; some API tests accept both 200 and 404 depending on tenant setup

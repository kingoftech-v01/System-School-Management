# Notes App

Professor note management with an approval workflow, audit history, and status change notifications.

## Description

The notes app manages professor-submitted notes (grades/scores) with a full approval workflow. Notes start as draft or pending, and direction staff can approve, reject, or request revisions. The app includes a complete audit trail via NoteHistory, soft delete support, and Celery-based notifications when note status changes. Edit and delete operations are blocked for approved notes.

## Main Features

- **Note CRUD**: Full create, list, detail, edit, delete with soft delete support
- **Approval Workflow**: Draft -> Pending -> Approved/Rejected/Revision Requested
- **Edit/Delete Restrictions**: Cannot modify approved notes
- **Audit Trail**: NoteHistory tracks creates, updates, deletes, status changes with old/new values
- **Pending Queue**: Direction-only view of notes pending approval
- **Notifications**: Celery task notifies professors when note status changes
- **Weighted Scores**: Support for coefficient-based weighted score calculation

## User Roles

| Role | Permissions |
|------|------------|
| direction | View pending notes, approve/reject/request revision |
| professor | CRUD own notes (edit/delete blocked for approved notes) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| ProfessorNote | Yes | Yes (list + detail) | Yes (if not approved) | Yes (soft delete, if not approved) |
| NoteHistory | Automatic | Yes (via detail) | N/A | N/A |
| NoteComment | No views | No views | N/A | N/A |

## Models

- `ProfessorNote` -- tenant FK, professor FK, student FK, subject FK, score, coefficient, weighted_score, status, is_deleted, approved_by FK
- `NoteHistory` -- note FK, action, changed_by FK, old_values JSON, new_values JSON, change_summary
- `NoteComment` -- note FK, author FK, content, created_at

## Dependencies

- `accounts` (User model for professor, student)
- `core` (School model for tenant)
- `celery` (status change notifications)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:notes:<view_name>`
- API: `api:v1:notes:<resource-name>`

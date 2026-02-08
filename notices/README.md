# Notices App

School-wide notice and announcement system with priority levels, rich text content, file attachments, group targeting, and acknowledgment tracking.

## Description

The notices app manages school-wide announcements and notices. Direction users can create notices with priority levels, rich text content, file attachments, and target specific notification groups. The app includes search, priority filtering, and pagination. An acknowledgment/response endpoint exists but does not yet persist data.

## Main Features

- **Notice CRUD**: Full create, list, detail, edit, delete (direction only for write operations)
- **Search & Filter**: Search by title/content, filter by priority
- **Pagination**: 20 notices per page
- **Rich Text**: CKEditor-based content editing
- **File Attachments**: Upload documents via NoticeDocument model
- **Group Targeting**: Target specific NotifyGroups
- **Acknowledgment**: Response endpoint (placeholder -- does not persist yet)

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full CRUD for notices |
| all authenticated | View notices, acknowledge notices |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Notice | Yes | Yes (list + detail) | Yes | Yes (with confirmation) |
| NoticeDocument | Via notice | Via notice detail | N/A | N/A |
| NoticeResponse | Placeholder | N/A | N/A | N/A |

## Models

- `NotifyGroup` -- name, members M2M
- `Notice` -- tenant FK, title, content (RichText), priority (low/normal/high/urgent), expires_at, uploaded_by FK, target groups M2M
- `NoticeDocument` -- notice FK, file, uploaded_at
- `NoticeResponse` -- notice FK, user FK, acknowledged, response_text, responded_at

## Dependencies

- `core` (School model for tenant)
- `django-ckeditor` (rich text)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:notices:<view_name>`
- API: `api:v1:notices:<resource-name>`

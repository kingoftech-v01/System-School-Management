# Notices App Architecture

## Overview

The notices app provides a school-wide announcement system with targeted delivery
via notification groups, file attachments, read/acknowledgment tracking, and
automated lifecycle management through Celery tasks. It operates within the
multi-tenant architecture, scoping all frontend queries to `request.tenant`.

---

## Model Relationships

```
+------------------+          +-------------------+
|   accounts.User  |          |    NotifyGroup     |
|  (AUTH_USER)     |          |-------------------|
|                  |<---M2M-->| id                |
|                  |  users   | name (unique)     |
+--------+---------+          | description       |
         |                    | users (M2M->User) |
         |                    | created_at        |
         |                    +--------+----------+
         |                             |
         | uploaded_by (FK,            | notify_groups
         |   SET_NULL)                 | (M2M)
         |                             |
         v                             v
+--------+-----------------------------+---------+
|                  Notice                        |
|------------------------------------------------|
| id                                             |
| title           CharField(200)                 |
| content         RichTextField (ckeditor)       |
| uploaded_by     FK -> User (SET_NULL, null)    |
| priority        CharField [low|normal|high|    |
|                            urgent]             |
| notify_groups   M2M -> NotifyGroup             |
| expires_at      DateField (null, blank)        |
| is_active       BooleanField (default=True)    |
| created_at      DateTimeField (auto_now_add)   |
| updated_at      DateTimeField (auto_now)       |
+-----+-------------------+---------------------+
      |                   |
      | notice (FK,       | notice (FK,
      | CASCADE)          | CASCADE)
      v                   v
+-----+----------+  +----+--------------+
| NoticeDocument  |  |  NoticeResponse   |
|-----------------|  |------------------|
| id              |  | id               |
| notice (FK)     |  | notice (FK)      |
| file (FileField)|  | user (FK->User)  |
| filename        |  | read_at (auto)   |
| file_size       |  | acknowledged     |
| uploaded_at     |  | acknowledged_at  |
+-----------------+  +------------------+

Constraints:
  NoticeResponse: unique_together = ['notice', 'user']
  Notice.Meta.permissions: [('can_send_urgent_notice', 'Can send urgent notices')]

Indexes:
  Notice: (is_active, -created_at), (priority, -created_at), (expires_at)
  NoticeResponse: (notice, user), (acknowledged)
```

### Foreign Key Summary

| Source           | Target         | Field          | on_delete  | Nullable |
|------------------|----------------|----------------|------------|----------|
| Notice           | User           | uploaded_by    | SET_NULL   | Yes      |
| Notice           | NotifyGroup    | notify_groups  | M2M        | -        |
| NotifyGroup      | User           | users          | M2M        | -        |
| NoticeDocument   | Notice         | notice         | CASCADE    | No       |
| NoticeResponse   | Notice         | notice         | CASCADE    | No       |
| NoticeResponse   | User           | user           | CASCADE    | No       |

### Reverse Accessors

| From Model   | Related Name        | Description                       |
|--------------|---------------------|-----------------------------------|
| User         | `notices`           | Notices uploaded by this user      |
| User         | `notify_groups`     | NotifyGroups this user belongs to  |
| User         | `notice_responses`  | NoticeResponses by this user       |
| Notice       | `documents`         | Attached NoticeDocument records    |
| Notice       | `responses`         | NoticeResponse acknowledgments     |
| NotifyGroup  | `notices`           | Notices targeting this group       |

---

## View Access Patterns Per Role

### Frontend Views (views_frontend.py)

All frontend views require `@login_required`. Tenant isolation is enforced by
`@tenant_required` on every view. Write operations also require `@direction_only`,
which permits **secretary**, **direction**, and **admin** roles (plus superusers).

| View             | URL Pattern            | HTTP   | Decorator Stack                                 | Roles Allowed                             |
|------------------|------------------------|--------|--------------------------------------------------|-------------------------------------------|
| notice_list      | `/notices/`            | GET    | login_required, tenant_required, ratelimit       | ALL authenticated users                   |
| notice_detail    | `/notices/<pk>/`       | GET    | login_required, tenant_required                  | ALL authenticated users                   |
| notice_create    | `/notices/create/`     | GET/POST | login_required, direction_only, tenant_required, ratelimit | secretary, direction, admin     |
| notice_update    | `/notices/<pk>/edit/`  | GET/POST | login_required, direction_only, tenant_required, ratelimit | secretary, direction, admin     |
| notice_delete    | `/notices/<pk>/delete/`| GET/POST | login_required, direction_only, tenant_required  | secretary, direction, admin               |
| notice_respond   | `/notices/<pk>/respond/`| POST  | login_required, tenant_required, ratelimit       | ALL authenticated users                   |

### API Views (views_api.py)

The `NoticeViewSet` is a standard DRF `ModelViewSet` with `IsAuthenticated`
permission. It does NOT apply tenant filtering or role-based restrictions
beyond authentication.

| Action   | Method   | URL                          | Serializer Used        |
|----------|----------|------------------------------|------------------------|
| list     | GET      | `/api/v1/notices/notices/`   | NoticeListSerializer   |
| create   | POST     | `/api/v1/notices/notices/`   | NoticeCreateSerializer |
| retrieve | GET      | `/api/v1/notices/notices/<pk>/` | NoticeSerializer     |
| update   | PUT      | `/api/v1/notices/notices/<pk>/` | NoticeSerializer     |
| partial  | PATCH    | `/api/v1/notices/notices/<pk>/` | NoticeSerializer     |
| destroy  | DELETE   | `/api/v1/notices/notices/<pk>/` | NoticeSerializer     |
| active   | GET      | `/api/v1/notices/notices/active/` | NoticeListSerializer |

**Filters**: `priority`, `is_active` (DjangoFilterBackend)
**Search**: `title`, `content` (SearchFilter)
**Ordering**: `created_at`, `priority` (default: `-created_at`)

### Role-Permission Matrix (from roles.py)

| Role        | view_notices | acknowledge_notices | create_notices | edit_all_notices | delete_notices | view_acknowledgments |
|-------------|:------------:|:-------------------:|:--------------:|:----------------:|:--------------:|:--------------------:|
| student     |      Y       |          Y          |       -        |        -         |       -        |          -           |
| parent      |      Y       |          Y          |       -        |        -         |       -        |          -           |
| professor   |      Y       |          -          |       Y        |        -         |       -        |          -           |
| prefet      |      -       |          -          |       -        |        -         |       -        |          -           |
| accountant  |      -       |          -          |       -        |        -         |       -        |          -           |
| librarian   |      -       |          -          |       -        |        -         |       -        |          -           |
| registrar   |      -       |          -          |       -        |        -         |       -        |          -           |
| secretary   |      *       |          *          |       Y        |        Y         |       Y        |          Y           |
| direction   |      *       |          *          |       Y        |        Y         |       Y        |          Y           |
| admin       |      *       |          *          |       Y        |        Y         |       Y        |          Y           |

`*` = Secretary/Direction/Admin inherit all Direction permissions, which include
full notice management. They can also view and acknowledge since list/detail
are open to all authenticated users.

`-` = No explicit permission defined in roles.py. However, the frontend views
for listing and detail only check `@login_required` + `@tenant_required`, so
**all authenticated users** (including prefet, accountant, librarian, registrar)
can still view and acknowledge notices through the frontend.

### Detail View Special Behavior

The `notice_detail` view conditionally exposes acknowledgment tracking data
based on role:

```
user_role = getattr(request.user, 'role', '')
is_direction = user_role in ('direction', 'admin') or request.user.is_superuser
```

- **direction/admin/superuser**: See the full list of users who acknowledged
  the notice, with timestamps (`acknowledged_users` queryset).
- **All other roles**: See only aggregate counts (`acknowledged_count`,
  `acknowledgment_percentage`) and their own acknowledgment status.

---

## Business Logic Workflows

### 1. Notice Creation Workflow

```
Direction/Secretary/Admin
         |
         v
  +------+------+
  | notice_create|  (POST with form + files)
  +------+------+
         |
         v
  NoticeForm.is_valid()
    - clean_title(): min 5 chars
    - clean_expires_at(): must be in the future
         |
         v
  Notice.save(commit=False)
    - Set notice.tenant = request.tenant
    - Set notice.uploaded_by = request.user
  Notice.save()
  form.save_m2m()   <-- saves notify_groups M2M
         |
         v
  For each file in request.FILES.getlist('attachments'):
    NoticeDocument.objects.create(
        notice=notice,
        file=f,
        filename=f.name,
        file_size=f.size,
    )
         |
         v
  Redirect to notice_detail
```

**Note**: The `send_notice_notifications` Celery task exists but is NOT
automatically triggered by creation in the views. It must be invoked
manually or wired via a signal (no signals.py exists currently).

### 2. Notice Update Workflow

```
Direction/Secretary/Admin
         |
         v
  +------+------+
  | notice_update|  (POST with form + files)
  +------+------+
         |
         v
  NoticeForm(instance=notice).is_valid()
         |
         +--- New attachments: NoticeDocument.objects.create(...)
         |
         +--- Removals: request.POST.getlist('remove_attachments')
         |    NoticeDocument.objects.filter(id__in=remove_ids, notice=notice).delete()
         |
         v
  Redirect to notice_detail
```

### 3. Acknowledgment Workflow

```
Any Authenticated User
         |
         v
  +------+--------+
  | notice_respond |  (POST only)
  +------+--------+
         |
         v
  NoticeResponse.objects.get_or_create(
      notice=notice,
      user=request.user,
      defaults={'acknowledged': True, 'acknowledged_at': now()}
  )
         |
         +--- If already exists but not acknowledged:
         |      response_obj.acknowledged = True
         |      response_obj.acknowledged_at = now()
         |      response_obj.save()
         |
         v
  Redirect back to notice_detail
```

### 4. Expiration Check (Frontend)

The `notice_list` view hides expired notices by default:

```python
if not show_expired:
    notices = notices.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=today)
    )
```

Users can toggle `?show_expired=true` to see past notices.

The `Notice.is_expired()` model method provides instance-level checking:
```python
def is_expired(self):
    if self.expires_at:
        return timezone.now().date() > self.expires_at
    return False
```

---

## Celery Tasks (Background Jobs)

All tasks are defined in `notices/tasks.py` and scheduled in
`School_System/celery.py`.

### send_notice_notifications(notice_id)

- **Trigger**: Manual invocation (not auto-triggered by views or signals)
- **Purpose**: Email all users in the notice's notify_groups
- **Flow**:
  1. Load `Notice` by ID
  2. Collect all users across all `notify_groups`
  3. For each user: create a `NoticeResponse` record (unacknowledged) and
     send an email with subject `"New Notice: {title}"`
- **From address**: `notices@school.com` (hardcoded)

### check_notice_acknowledgments

- **Schedule**: Daily at 14:00 (2 PM)
- **Purpose**: Send reminder emails for unacknowledged notices
- **Flow**:
  1. Query `NoticeResponse` where `acknowledged=False` and `notice.is_active=True`
  2. Send reminder email to each user with a valid email address
- **From address**: `notices@school.com` (hardcoded)

### archive_expired_notices

- **Schedule**: Daily at 02:00 (2 AM)
- **Purpose**: Deactivate notices past their expiry date
- **Flow**:
  1. Query `Notice` where `is_active=True` and `expires_at < now()`
  2. Bulk update `is_active=False`

```
Celery Beat Schedule:
  +----------------------------------+------------------+
  | Task                             | Schedule         |
  +----------------------------------+------------------+
  | check_notice_acknowledgments     | Daily at 14:00   |
  | archive_expired_notices          | Daily at 02:00   |
  +----------------------------------+------------------+
```

---

## Dependencies

### Inbound (Who depends on notices)

| Consumer                          | What it uses                      | How                               |
|-----------------------------------|-----------------------------------|------------------------------------|
| `core.views_frontend`             | `Notice` model                    | Fetches 5 most recent notices for secretary dashboard widget |
| `School_System/celery.py`         | `notices.tasks.*`                 | Schedules periodic tasks           |
| `School_System/roles.py`          | Permission names                  | Defines `view_notices`, `create_notices`, etc. for each role |
| `School_System/urls.py`           | `notices.urls`                    | Includes frontend and API URL patterns under `/notices/` and `/api/v1/notices/` |
| `School_System/settings/base.py`  | App name                          | `'notices'` in `INSTALLED_APPS`    |
| `tests/helpers.py`                | `Notice` model                    | `create_notice()` factory method   |
| Various test modules              | Models, tasks, admin, serializers | Unit and integration tests         |

### Outbound (What notices depends on)

| Dependency                    | Usage                                               |
|-------------------------------|------------------------------------------------------|
| `django.contrib.auth` (User) | FK/M2M relations in Notice, NotifyGroup, NoticeResponse |
| `accounts.decorators`         | `direction_only`, `tenant_required` for view protection |
| `ckeditor.fields.RichTextField` | Rich text editing for `Notice.content`             |
| `rest_framework`              | API ViewSet, serializers, filters, permissions       |
| `django_filters`              | `DjangoFilterBackend` for API filtering              |
| `django_ratelimit`            | Rate limiting on frontend views                      |
| `celery`                      | `@shared_task` for async notification and archival   |
| `django.core.mail`            | Email sending in Celery tasks                        |

---

## Data Flow Diagrams

### Notice Lifecycle

```
                          +-----------+
                          |  Created  |
                          | is_active |
                          | = True    |
                          +-----+-----+
                                |
                +---------------+---------------+
                |                               |
                v                               v
   +------------+----------+       +------------+-----------+
   | Manual deactivation   |       | expires_at passes      |
   | (admin toggle or      |       | (archive_expired_      |
   |  admin action)        |       |  notices task, 2 AM)   |
   +------------+----------+       +------------+-----------+
                |                               |
                v                               v
          +-----+-------------------------------+-----+
          |            is_active = False               |
          |         (Archived / Deactivated)           |
          +-------------------------------------------+
```

### Notice Delivery and Acknowledgment Flow

```
  Direction/Secretary/Admin
         |
         | creates Notice (frontend form)
         v
  +------+------+
  |   Notice     |---> NotifyGroup(s) ---> User(s) in groups
  +------+------+
         |
         |  (manually trigger send_notice_notifications task)
         v
  +------+--------------+
  | Celery Task:         |
  | send_notice_         |
  | notifications        |
  +------+--------------+
         |
         +--- For each user in notify_groups:
         |      |
         |      +---> Create NoticeResponse (read_at=now, acknowledged=False)
         |      +---> Send email notification
         |
         v
  Users see notice in notice_list
         |
         | User clicks "Acknowledge" (POST to notice_respond)
         v
  +------+--------+
  | NoticeResponse |
  | acknowledged   |
  | = True         |
  | acknowledged_  |
  | at = now()     |
  +------+--------+
         |
         |  (Daily at 2 PM: check_notice_acknowledgments)
         v
  +------+-------------------+
  | Unacknowledged users     |
  | receive reminder emails  |
  +------+-------------------+
         |
         |  (Direction/Admin view notice_detail)
         v
  +------+-------------------+
  | Acknowledgment stats:    |
  | - total_responses        |
  | - acknowledged_count     |
  | - % acknowledged         |
  | - list of ack'd users    |
  |   (direction/admin only) |
  +--------------------------+
```

### Request Flow Through URL Routing

```
Browser Request
      |
      +--- /notices/             ---> frontend:notices:notice_list
      +--- /notices/create/      ---> frontend:notices:notice_create
      +--- /notices/<pk>/        ---> frontend:notices:notice_detail
      +--- /notices/<pk>/edit/   ---> frontend:notices:notice_update
      +--- /notices/<pk>/delete/ ---> frontend:notices:notice_delete
      +--- /notices/<pk>/respond/---> frontend:notices:notice_respond
      |
      +--- /api/v1/notices/notices/          ---> api:notices:notice-list
      +--- /api/v1/notices/notices/<pk>/     ---> api:notices:notice-detail
      +--- /api/v1/notices/notices/active/   ---> api:notices:notice-active

Full namespace resolution:
  Frontend: frontend:notices:<view_name>
  API:      api:notices:<action_name>
```

---

## Templates

| Template                              | Used By         | Purpose                                |
|---------------------------------------|-----------------|----------------------------------------|
| `notices/notice_list.html`            | notice_list     | Paginated list with search and filters |
| `notices/notice_detail.html`          | notice_detail   | Full notice view with acknowledgment   |
| `notices/notice_form.html`            | notice_create, notice_update | Create/edit form with attachments |
| `notices/notice_confirm_delete.html`  | notice_delete   | Deletion confirmation page             |

All templates are located under `templates/notices/` in the project root.

---

## Admin Configuration

The `admin.py` registers all four models with customized admin classes:

| Model          | Admin Class          | Key Features                                           |
|----------------|----------------------|--------------------------------------------------------|
| Notice         | NoticeAdmin          | Inline documents, fieldsets, filter_horizontal for notify_groups, bulk actions (activate/deactivate/mark urgent), read/unread counts |
| NoticeDocument | NoticeDocumentAdmin  | List by filename/notice/size, search by filename       |
| NotifyGroup    | NotifyGroupAdmin     | filter_horizontal for users, member count display      |
| NoticeResponse | NoticeResponseAdmin  | Filter by acknowledged status, bulk mark-as-acknowledged action |

### Admin Bulk Actions

| Action              | Effect                                |
|---------------------|---------------------------------------|
| activate_notices    | Set `is_active=True` on selection     |
| deactivate_notices  | Set `is_active=False` on selection    |
| mark_as_urgent      | Set `priority='urgent'` on selection  |
| mark_as_acknowledged| Set `acknowledged=True` + timestamp   |

---

## Forms

### NoticeForm

- **Model**: Notice
- **Fields**: `title`, `content`, `priority`, `notify_groups`, `expires_at`, `is_active`
- **Validations**:
  - `clean_title()`: Minimum 5 characters
  - `clean_expires_at()`: Must be a future date (if provided)
- **Widget classes**: Bootstrap 5 (`form-control`, `form-select`, `form-check-input`)

### NotifyGroupForm

- **Model**: NotifyGroup
- **Fields**: `name`, `description`, `users`
- **Note**: Not used in any current view; available for admin or future frontend use

---

## Serializers

| Serializer             | Purpose                       | Fields                                                                 |
|------------------------|-------------------------------|------------------------------------------------------------------------|
| UserMinimalSerializer  | Nested user display           | `id`, `username`, `email`, `full_name` (via `get_full_name` property)  |
| NoticeSerializer       | Detail/update serialization   | All fields; `uploaded_by` nested as UserMinimalSerializer (read-only)  |
| NoticeListSerializer   | List serialization (compact)  | `id`, `title`, `uploaded_by_name`, `priority`, `priority_display`, `is_active`, `created_at` |
| NoticeCreateSerializer | Creation serialization        | `title`, `content`, `priority`, `notify_groups`, `expires_at`, `is_active` |

---

## Known Gaps and Observations

1. **No signals.py**: The `send_notice_notifications` task is not automatically
   triggered on notice creation. There is no `post_save` signal wired up.

2. **API tenant isolation**: The API ViewSet's `get_queryset()` returns
   `Notice.objects.all()` without tenant filtering, unlike the frontend views
   which filter by `request.tenant`. This could expose cross-tenant data.

3. **API write permissions**: The API ViewSet uses only `IsAuthenticated`,
   meaning any authenticated user (including students) can create, update, and
   delete notices via the API, bypassing the `direction_only` restriction
   enforced on frontend views.

4. **Prefet, Accountant, Librarian, Registrar**: These roles have no explicit
   notice permissions in `roles.py`, but they can still view and acknowledge
   notices through the frontend (which only checks authentication and tenant).

5. **No tenant field on Notice model**: The `Notice` model does not have a
   `tenant` FK field, yet `views_frontend.py` filters by `tenant=request.tenant`
   and sets `notice.tenant = request.tenant`. This suggests the tenant field is
   either added dynamically by multi-tenant middleware or exists in a migration
   not reflected in the current `models.py` source.

6. **Hardcoded email from-address**: Tasks use `notices@school.com` instead of
   the `EMAIL_FROM_ADDRESS` setting defined in `base.py`.

# Events App - Architecture

## Overview

The `events` app manages school-wide calendar events (exams, holidays, meetings,
activities, ceremonies, deadlines). Events are tenant-scoped and audience-filtered
so that students, parents, and staff each see only the events targeted at them.
Direction and admin roles have full CRUD control; all other roles have read-only
access. A Celery background task sends email reminders the day before each event.

---

## Model Relationships

```
+-------------------------------+
|           Event               |
+-------------------------------+
| id             (BigAuto PK)   |
| title          (CharField)    |
| description    (TextField)    |
| event_type     (CharField)    |   choices: exam, holiday, meeting,
|                               |            activity, ceremony, deadline
| start_date     (DateTimeField)|
| end_date       (DateTimeField)|
| location       (CharField)    |   blank=True
| target_audience(CharField)    |   choices: all, students, parents, staff
| send_reminder  (BooleanField) |   default=True
| reminder_sent  (BooleanField) |   default=False
| created_at     (DateTimeField)|   auto_now_add
+-------------------------------+
        |                 |
        | FK (CASCADE)    | FK (SET_NULL, null=True)
        v                 v
+-------------+    +------------------+
| core.School |    | accounts.User    |
| (tenant)    |    | (created_by)     |
+-------------+    +------------------+
```

### Field-Level Detail

| Field             | Type            | Constraints / Notes                                 |
|-------------------|-----------------|------------------------------------------------------|
| `tenant`          | FK -> `core.School` | `on_delete=CASCADE` -- event deleted when school is removed |
| `title`           | `CharField(200)`    | Required                                           |
| `description`     | `TextField`         | Required                                           |
| `event_type`      | `CharField(50)`     | One of: `exam`, `holiday`, `meeting`, `activity`, `ceremony`, `deadline` |
| `start_date`      | `DateTimeField`     | Used for ordering (`Meta.ordering = ['start_date']`) |
| `end_date`        | `DateTimeField`     | Validated >= `start_date` in `EventCreateSerializer` |
| `location`        | `CharField(200)`    | Optional (`blank=True`)                            |
| `target_audience` | `CharField(20)`     | One of: `all`, `students`, `parents`, `staff`       |
| `send_reminder`   | `BooleanField`      | Default `True` -- controls whether the Celery task sends email |
| `reminder_sent`   | `BooleanField`      | Default `False` -- flipped to `True` after task runs |
| `created_by`      | FK -> `User`        | `on_delete=SET_NULL, null=True` -- preserved if creator deleted |
| `created_at`      | `DateTimeField`     | `auto_now_add=True`                                |

---

## View Access Patterns per Role

### Frontend Views (`views_frontend.py`)

The `@direction_only` decorator permits **secretary**, **direction**, and **admin**.
The `@tenant_required` decorator enforces cross-tenant isolation.

| View            | URL Pattern             | student | professor | parent | direction | secretary | admin | prefet | accountant | librarian | registrar |
|-----------------|-------------------------|---------|-----------|--------|-----------|-----------|-------|--------|------------|-----------|-----------|
| `event_list`    | `/events/`              | R*      | R*        | R*     | R         | R         | R     | R      | R          | R         | R         |
| `event_detail`  | `/events/<pk>/`         | R       | R         | R      | R         | R         | R     | R      | R          | R         | R         |
| `event_create`  | `/events/create/`       | --      | --        | --     | CW        | CW        | CW    | --     | --         | --        | --        |
| `event_edit`    | `/events/<pk>/edit/`    | --      | --        | --     | UW        | UW        | UW    | --     | --         | --        | --        |
| `event_delete`  | `/events/<pk>/delete/`  | --      | --        | --     | D         | D         | D     | --     | --         | --        | --        |

Legend: **R** = Read, **R*** = Read (filtered by `target_audience`), **CW** = Create+Write,
**UW** = Update+Write, **D** = Delete, **--** = Access denied (redirect).

**Audience filtering in `event_list`:**
- `student` sees events where `target_audience IN ('all', 'students')`
- `parent` sees events where `target_audience IN ('all', 'parents')`
- `professor` sees events where `target_audience IN ('all', 'staff')`
- `direction`, `secretary`, `admin` (and all other roles) see **all** events unfiltered

### API Views (`views_api.py` -- `EventViewSet`)

All endpoints require `IsAuthenticated`. Queryset filtering mirrors frontend logic.

| Endpoint                                | Method | student | professor | parent | direction | secretary | admin |
|-----------------------------------------|--------|---------|-----------|--------|-----------|-----------|-------|
| `/api/v1/events/events/`               | GET    | R*      | R*        | R*     | R         | R         | R     |
| `/api/v1/events/events/`               | POST   | C       | C         | C      | C         | C         | C     |
| `/api/v1/events/events/{pk}/`          | GET    | R*      | R*        | R*     | R         | R         | R     |
| `/api/v1/events/events/{pk}/`          | PUT    | U       | U         | U      | U         | U         | U     |
| `/api/v1/events/events/{pk}/`          | PATCH  | U       | U         | U      | U         | U         | U     |
| `/api/v1/events/events/{pk}/`          | DELETE | D       | D         | D      | D         | D         | D     |
| `/api/v1/events/events/upcoming/`      | GET    | R*      | R*        | R*     | R         | R         | R     |
| `/api/v1/events/events/calendar/`      | GET    | R*      | R*        | R*     | R         | R         | R     |
| `/api/v1/events/events/stats/`         | GET    | R*      | R*        | R*     | R         | R         | R     |

**Note:** The API ViewSet only enforces `IsAuthenticated`. Write operations (POST,
PUT, PATCH, DELETE) are allowed for any authenticated user. The frontend layer
applies stricter role-based guards via the `@direction_only` decorator. If the API
needs to restrict writes, additional DRF permissions should be added.

### Parent-Specific Views (`accounts/views_parent.py`)

| View                 | URL                          | Access       | Audience Filter                                |
|----------------------|------------------------------|--------------|------------------------------------------------|
| `parent_events`      | Parent events list page      | `parent_only`| `target_audience IN ('all', 'parents')` + future only (`end_date >= now`) |
| `parent_event_detail`| Parent event detail page     | `parent_only`| Single event by PK (no audience check)          |

### Dashboard Widgets (read-only)

Several dashboards query `Event` to display upcoming events:

| Dashboard                          | File                            | Events Shown                                              |
|------------------------------------|---------------------------------|-----------------------------------------------------------|
| Student dashboard                  | `accounts/views.py:482`         | Next 5 where `target_audience IN ('all', 'students')`, `start_date >= now` |
| Student dashboard (frontend)       | `accounts/views_frontend.py:547`| Same as above                                             |
| Direction/Admin dashboard          | `accounts/views.py:719`         | Next 5, all audiences, `start_date >= now`                |
| Direction dashboard (frontend)     | `accounts/views_frontend.py:784`| Same as above                                             |
| Core home page                     | `core/views_frontend.py:231`    | Next 5, no audience filter, `start_date >= now`           |
| Scheduling calendar (FullCalendar) | `scheduling/views_api.py:366`   | Date-range query, audience-filtered by role, color-coded by `event_type` |

---

## Business Logic Workflows

### 1. Event Creation (Frontend)

```
User (direction/secretary/admin)
  |
  v
GET  /events/create/
  |  --> renders EventForm (empty)
  v
POST /events/create/
  |  --> EventForm validates fields
  |  --> event.tenant = get_current_tenant(request)
  |  --> event.created_by = request.user
  |  --> event.save()
  |  --> messages.success()
  v
Redirect --> /events/  (event_list)
```

### 2. Event Creation (API)

```
POST /api/v1/events/events/
  |
  v
EventCreateSerializer.validate()
  |  --> checks end_date >= start_date
  v
EventViewSet.perform_create()
  |  --> serializer.save(tenant=request.tenant, created_by=request.user)
  v
201 Created (JSON response)
```

### 3. Event Reminder Workflow (Celery)

```
Celery Beat (daily at 08:00)
  |
  v
events.tasks.send_event_reminders()
  |
  v
Query: Event.objects.filter(
    send_reminder=True,
    reminder_sent=False,
    start_date__date = tomorrow
)
  |
  v
For each event:
  |
  +-- target_audience == 'all'
  |     --> recipients = all users in tenant
  |
  +-- target_audience == 'students'
  |     --> recipients = users where role='student' in tenant
  |
  +-- target_audience == 'parents'
  |     --> recipients = users where role='parent' in tenant
  |
  +-- target_audience == 'staff'
  |     --> recipients = users where role in ('professor', 'direction') in tenant
  |
  v
send_mail(
    subject = "[{tenant.name}] Upcoming Event: {event.title}",
    message = title + date + location + description,
    from_email = settings.DEFAULT_FROM_EMAIL,
    recipient_list = recipients,
    fail_silently = True
)
  |
  v
event.reminder_sent = True
event.save()
```

**Important:** The task marks `reminder_sent = True` unconditionally, even when
`recipients` is empty. This prevents re-processing the event on subsequent runs.

### 4. Audience Filtering Logic

```
                    +-----------------------+
                    |   incoming request    |
                    +-----------------------+
                              |
                    +---------v----------+
                    | user.role check    |
                    +--------------------+
                     /     |       |     \
                    /      |       |      \
                   v       v       v       v
             student   parent  professor  other
                |        |        |         |
                v        v        v         v
           [all,     [all,    [all,      no filter
           students] parents] staff]     (see all)
```

### 5. Scheduling Integration

The scheduling app's `CalendarViewSet._get_school_events()` method queries
`Event` objects for a date range and converts them into FullCalendar-compatible
JSON objects. Events are color-coded by `event_type`:

| event_type | Color     |
|------------|-----------|
| `exam`     | `#dc3545` (red)    |
| `holiday`  | `#6c757d` (gray)   |
| `meeting`  | `#6f42c1` (purple) |
| `activity` | `#28a745` (green)  |
| `ceremony` | `#28a745` (green)  |
| `deadline` | `#fd7e14` (orange) |

Direction, admin, and secretary roles see all events on the calendar. Other roles
see only events matching their audience mapping.

---

## Dependencies

### Incoming Dependencies (other apps that depend on `events`)

```
accounts/views.py             --> imports Event for student dashboard widget
accounts/views_frontend.py    --> imports Event for student + direction dashboard widgets
accounts/views_parent.py      --> imports Event for parent events list + detail
core/views_frontend.py        --> imports Event for home page upcoming events widget
core/management/commands/     --> imports Event for generate_beta_data command
    generate_beta_data.py
scheduling/views_api.py       --> imports Event for FullCalendar integration
School_System/celery.py       --> references events.tasks.send_event_reminders in beat schedule
School_System/settings/base.py--> routes events.tasks.* to 'events' Celery queue
```

### Outgoing Dependencies (apps that `events` depends on)

```
events/models.py
  --> core.School           (FK tenant)
  --> settings.AUTH_USER_MODEL (FK created_by)

events/views_frontend.py
  --> accounts.decorators   (direction_only, tenant_required)
  --> core.models.School    (get_current_tenant helper)
  --> django_ratelimit      (rate limiting)

events/views_api.py
  --> django_filters        (DjangoFilterBackend)
  --> rest_framework        (ViewSets, permissions, filters)

events/tasks.py
  --> celery                (shared_task)
  --> accounts.models.User  (query recipients by role + tenant)
  --> django.core.mail      (send_mail)

events/serializers.py
  --> rest_framework        (ModelSerializer)
  --> django.contrib.auth   (get_user_model)

events/forms.py
  --> django.forms          (ModelForm)

events/admin.py
  --> django.contrib.admin  (ModelAdmin)
```

### Dependency Diagram

```
                          +------------+
                          |   celery   |
                          +-----+------+
                                |
                                v
+-----------+           +-------+--------+           +------------------+
|  accounts |<----------| events (this)  |---------->| core.School      |
| .models   | tasks.py  |                | models.py | (tenant FK)      |
| User      | queries   | models.py      |           +------------------+
+-----------+ by role   | views_frontend |
      ^                 | views_api      |
      |                 | serializers    |
      |                 | forms          |
      |                 | tasks          |
      |                 | admin          |
      |                 +-------+--------+
      |                         ^
      |                         |
      +---- accounts/views*.py--+  (dashboard widgets import Event)
      +---- core/views_frontend.py (home page widget imports Event)
      +---- scheduling/views_api.py (FullCalendar imports Event)
```

---

## Data Flow Diagrams

### Frontend Request Flow

```
Browser
  |
  v
Django URL Router
  |
  +--> /events/          --> frontend_urlpatterns
  |    |
  |    +--> ''               --> event_list (views_frontend)
  |    +--> 'create/'        --> event_create
  |    +--> '<pk>/'          --> event_detail
  |    +--> '<pk>/edit/'     --> event_edit
  |    +--> '<pk>/delete/'   --> event_delete
  |
  v
Decorator Stack:
  @login_required       -- must be authenticated
  @direction_only       -- must be secretary/direction/admin (create/edit/delete only)
  @tenant_required      -- must belong to current tenant
  @ratelimit            -- 100/h GET, 50/h POST
  |
  v
View Function
  |
  +--> get_current_tenant(request)  -- resolves School from request or dev fallback
  +--> Event.objects.filter(tenant=tenant)  -- scoped queryset
  +--> Audience filtering by request.user.role
  +--> EventForm for create/edit
  |
  v
Template Rendering
  |
  +--> events/event_list.html
  +--> events/event_form.html           (create + edit share this template)
  +--> events/event_detail.html
  +--> events/event_confirm_delete.html
  |
  v
HTTP Response --> Browser
```

### API Request Flow

```
HTTP Client (JS, mobile, etc.)
  |
  v
Django URL Router
  |
  +--> /api/v1/events/events/           --> EventViewSet (DRF Router)
  |    |
  |    +--> GET    list
  |    +--> POST   create
  |    +--> GET    retrieve  (/{pk}/)
  |    +--> PUT    update    (/{pk}/)
  |    +--> PATCH  partial_update (/{pk}/)
  |    +--> DELETE destroy   (/{pk}/)
  |    +--> GET    upcoming  (/upcoming/)
  |    +--> GET    calendar  (/calendar/?month=YYYY-MM)
  |    +--> GET    stats     (/stats/)
  |
  v
DRF Permission Check: IsAuthenticated
  |
  v
EventViewSet
  |
  +--> get_queryset()
  |      --> filter by tenant (request.tenant)
  |      --> filter by target_audience based on user role flags:
  |           is_student  -> ['all', 'students']
  |           is_parent   -> ['all', 'parents']
  |           is_lecturer/is_professor -> ['all', 'staff']
  |           else        -> all events
  |      --> select_related('created_by')
  |
  +--> get_serializer_class()
  |      --> list   : EventListSerializer   (lightweight, 10 fields)
  |      --> create : EventCreateSerializer (write fields, validates dates)
  |      --> default: EventSerializer       (full detail, nested user)
  |
  +--> Filter backends:
  |      --> DjangoFilterBackend  (event_type, target_audience, start_date, end_date)
  |      --> SearchFilter         (title, description, location)
  |      --> OrderingFilter       (start_date, end_date, created_at)
  |
  v
JSON Response --> HTTP Client
```

### Celery Task Flow

```
Celery Beat (crontab: daily 08:00)
  |
  v
events.tasks.send_event_reminders
  |  (routed to 'events' queue)
  |
  v
Query events starting tomorrow
where send_reminder=True AND reminder_sent=False
  |
  v
For each event:
  |
  +--> Resolve recipients from accounts.User
  |    based on event.target_audience + event.tenant
  |
  +--> django.core.mail.send_mail()
  |    (fail_silently=True)
  |
  +--> event.reminder_sent = True
  |    event.save()
  |
  v
Return count of processed events
```

---

## URL Namespace Structure

```
Root URL conf (School_System/urls.py)
  |
  +--> frontend_urlpatterns
  |    |
  |    +--> path('events/', include(events.urls, 'events'))
  |         |
  |         +--> frontend_urlpatterns  (namespace: frontend:events:*)
  |              |
  |              +--> event_list           ''
  |              +--> event_create         'create/'
  |              +--> event_detail         '<int:pk>/'
  |              +--> event_edit           '<int:pk>/edit/'
  |              +--> event_delete         '<int:pk>/delete/'
  |
  +--> api_v1_urlpatterns
       |
       +--> path('events/', include(events.urls.api_urlpatterns, 'events'))
            |
            +--> DRF Router  (namespace: api:events:*)
                 |
                 +--> event-list         'events/'
                 +--> event-detail       'events/{pk}/'
                 +--> event-upcoming     'events/upcoming/'
                 +--> event-calendar     'events/calendar/'
                 +--> event-stats        'events/stats/'
```

---

## Serializer Summary

| Serializer              | Used For          | Fields                                                                                                   |
|-------------------------|-------------------|----------------------------------------------------------------------------------------------------------|
| `EventSerializer`       | Detail / Update   | All model fields + `event_type_display`, `target_audience_display`, nested `created_by` (UserMinimalSerializer) |
| `EventListSerializer`   | List / Upcoming / Calendar | `id`, `title`, `event_type`, `event_type_display`, `start_date`, `end_date`, `location`, `target_audience`, `target_audience_display`, `created_by_name` |
| `EventCreateSerializer` | Create            | `title`, `description`, `event_type`, `start_date`, `end_date`, `location`, `target_audience`, `send_reminder` -- validates `end_date >= start_date` |
| `UserMinimalSerializer` | Nested in detail  | `id`, `username`, `email`, `full_name` (via `get_full_name` property)                                     |

---

## Admin Configuration

`EventAdmin` registered at `events/admin.py`:

- **list_display:** `title`, `event_type`, `start_date`, `end_date`, `target_audience`, `tenant`
- **list_filter:** `event_type`, `target_audience`, `tenant`, `start_date`
- **search_fields:** `title`, `description`
- **readonly_fields:** `created_at`, `reminder_sent`
- **Tenant scoping:** Non-superusers see only events for their `request.tenant`

---

## Rate Limiting

| View            | Method | Rate       |
|-----------------|--------|------------|
| `event_list`    | ALL    | 100/hour per user |
| `event_create`  | POST   | 50/hour per user  |
| `event_edit`    | POST   | 50/hour per user  |

API endpoints rely on DRF throttling configured at the project level rather than
per-view rate limits.

---

## Template Files

| Template                              | Used By          | Purpose                          |
|---------------------------------------|------------------|----------------------------------|
| `templates/events/event_list.html`    | `event_list`     | Paginated event list with filters |
| `templates/events/event_form.html`    | `event_create`, `event_edit` | Shared create/edit form  |
| `templates/events/event_detail.html`  | `event_detail`   | Single event view                |
| `templates/events/event_confirm_delete.html` | `event_delete` | Deletion confirmation page  |
| `templates/parent/events.html`        | `parent_events`  | Parent-specific events list      |
| `templates/parent/event_detail.html`  | `parent_event_detail` | Parent-specific event detail |

# Scheduling App

Full-featured scheduling and timetable management system with automatic generation, conflict detection, substitution workflows, and multi-role calendar views.

## Description

The scheduling app manages the complete lifecycle of school timetables: configuring rooms and time slots, creating schedule entries manually or via an auto-generation engine, handling day-to-day exceptions (cancellations, room changes, substitutions, reschedules), and delivering in-app and email notifications to affected users. It provides both a FullCalendar-based web UI and a REST API. The auto-generation engine uses a greedy placement algorithm with MRV heuristic, soft-constraint scoring, and local search optimization.

## Main Features

- **Room Management**: Full CRUD for physical and virtual rooms with capacity, equipment (JSON), building/floor, and 7 room types
- **Time Slot Configuration**: Configurable weekly grid with day-of-week, start/end times, slot types (class/break/lunch), and display ordering
- **Schedule Entry Management**: Manual creation and editing of recurring weekly or bi-weekly class assignments with date-range scoping
- **Auto-Generation Engine**: Multi-phase timetable generator (data collection, MRV constraint scoring, greedy placement, local search optimization, validation)
- **Conflict Detection**: Real-time detection of professor overlaps, room overlaps, student group overlaps, and room capacity mismatches
- **Schedule Exceptions**: One-off modifications (cancellation, room change, substitution, reschedule, extra session) with approval workflow
- **Substitution Requests**: Professor-initiated workflow with suggested/assigned substitute, direction review, and automatic exception creation on approval
- **FullCalendar Integration**: Interactive calendar view with role-based filtering, drag-and-drop editing (direction/admin), and school event overlay
- **Notifications**: In-app notifications with email delivery (Celery) for schedule changes, created via signals on exceptions and substitution status changes
- **Reports**: Room utilization statistics and PDF timetable export (via xhtml2pdf)
- **Timetable Wizard**: 3-step guided workflow for auto-generation (scope selection, constraint configuration, preview/validation)
- **Template Tags**: `todays_schedule` inclusion tag for dashboard widgets
- **i18n Support**: Translatable Room and TimeSlot names via modeltranslation

## User Roles

| Role | Calendar View | My Schedule | Room Mgmt | Time Slot Config | Schedule Editor | Entry CRUD | Wizard / Generation | Conflicts | Reports / Export | Substitution Mgmt | Exception Mgmt | Notifications | Professor Actions | Parent Schedule |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| student | Read (own filiere) | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |
| professor | Read (own classes) | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | Cancel / Substitute | -- |
| direction | Read (all + filters) | Read | Full CRUD | Full CRUD | Full | Full CRUD | Full | View / Resolve | Full | Review / Approve | Full CRUD | Read | -- | -- |
| parent | Read (child's filiere) | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | Read |
| admin | Read (all + filters) | Read | Full CRUD | Full CRUD | Full | Full CRUD | Full | View / Resolve | Full | Review / Approve | Full CRUD | Read | -- | -- |
| prefet | -- | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |
| accountant | -- | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |
| secretary | Read (all + filters) | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |
| librarian | -- | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |
| registrar | -- | Read | -- | -- | -- | -- | -- | -- | -- | -- | -- | Read | -- | -- |

**Notes**:
- `direction_only` decorator gates management views (rooms, time slots, editor, wizard, conflicts, reports, substitution management, exceptions)
- `professor_only` decorator gates professor-specific views (cancel class, request substitution, view own substitution requests)
- `parent_only` decorator gates the parent child schedule view
- `schedule_calendar` and `my_schedule` are available to all authenticated users with `tenant_required`
- Secretary role gets filter dropdowns in the calendar view alongside direction and admin
- Calendar API feed (`calendar_feed`) filters data by role: students see their filiere, professors see their classes, parents see children's filieres, direction/admin/secretary see everything

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Room | Yes (direction) | Yes (list + detail) | Yes (direction) | Yes (direction) |
| TimeSlot | Yes (direction) | Yes (grouped by day) | Yes (direction) | Yes (direction) |
| ScheduleEntry | Yes (direction) | Yes (calendar + editor) | Yes (direction) | Yes (direction) |
| ScheduleException | Yes (direction + professor*) | Yes (list) | No | No |
| SubstitutionRequest | Yes (professor) | Yes (list, filtered) | Yes (status via review) | No |
| ScheduleNotification | No (auto-created) | Yes (list) | Yes (mark read) | No |
| TimetableGeneration | Yes (via wizard) | Yes (results page) | No | Yes (rollback) |
| ProfessorAvailability | No (admin only) | No (engine internal) | No | No |

*Professors create cancellation exceptions directly via `mark_cancellation`; direction creates all exception types.

## Models

- `Room` -- name, code (unique per tenant), building, floor, capacity (min 1), room_type (classroom/lab/amphitheatre/computer_room/meeting/gym/online), equipment (JSONField list), is_active, tenant FK
- `TimeSlot` -- name, start_time, end_time, day_of_week (0-6), slot_type (class/break/lunch), order, is_active, tenant FK; unique on (tenant, day_of_week, start_time); property `duration_minutes`
- `ProfessorAvailability` -- professor FK (User), time_slot FK, preference (unavailable/avoid/neutral/preferred); unique on (professor, time_slot)
- `ScheduleEntry` -- course FK, professor FK (limit_choices_to role=professor), room FK (nullable), time_slot FK, filiere FK (nullable), group_name, session FK, semester FK, effective_from, effective_until, recurrence (weekly/biweekly_odd/biweekly_even), status (active/cancelled/substituted/rescheduled), color (hex), is_locked, generation FK (nullable), created_by FK, tenant FK; method `is_active_on(date)` checks status + date range + weekday + recurrence parity
- `ScheduleException` -- schedule_entry FK, exception_type (cancellation/room_change/substitution/reschedule/extra_session), date, new_room FK (nullable), substitute_professor FK (nullable), new_start_time, new_end_time, reason, is_approved, approved_by FK, notify_students, notification_sent, created_by FK, tenant FK; unique on (schedule_entry, date, exception_type)
- `SubstitutionRequest` -- schedule_entry FK, date, requesting_professor FK, suggested_substitute FK (nullable), assigned_substitute FK (nullable), reason, status (pending/approved/rejected/fulfilled), reviewed_by FK, reviewed_at, tenant FK
- `ScheduleNotification` -- recipient FK (User), notification_type (cancellation/room_change/substitution/reschedule/new_event/reminder), title, message, related_entry FK (nullable), related_exception FK (nullable), is_read, read_at, email_sent, tenant FK
- `TimetableGeneration` -- session FK, semester FK, status (pending/running/completed/failed/rolled_back), config (JSONField dict), entries_created, conflicts_found, conflict_details (JSONField list), is_published, started_at, completed_at, created_by FK, tenant FK

## API Endpoints

### Rooms (`/api/v1/scheduling/rooms/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rooms/` | List all rooms (compact serializer) |
| POST | `/rooms/` | Create a room |
| GET | `/rooms/{id}/` | Room detail (full serializer) |
| PUT/PATCH | `/rooms/{id}/` | Update a room |
| DELETE | `/rooms/{id}/` | Delete a room |
| GET | `/rooms/available/?date=&start_time=&end_time=` | Find available rooms at a given date/time |
| GET | `/rooms/{id}/utilization/?start_date=&end_date=` | Room utilization statistics for a period |

### Time Slots (`/api/v1/scheduling/timeslots/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/timeslots/` | List all time slots |
| POST | `/timeslots/` | Create a time slot |
| GET/PUT/DELETE | `/timeslots/{id}/` | Time slot detail/update/delete |
| GET | `/timeslots/grid/` | Weekly time slot grid grouped by day |

### Schedule Entries (`/api/v1/scheduling/entries/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/entries/` | List all entries (with related data) |
| POST | `/entries/` | Create an entry |
| GET/PUT/DELETE | `/entries/{id}/` | Entry detail/update/delete |
| GET | `/entries/calendar_feed/?start=&end=` | FullCalendar event source (role-filtered, with exceptions and school events overlay) |
| GET | `/entries/my_schedule/?date=` | Personal schedule for authenticated user |
| GET | `/entries/conflicts/?day_of_week=&start_time=&end_time=&professor_id=&room_id=&filiere_id=` | Check for scheduling conflicts |
| POST | `/entries/move/` | Drag-and-drop time slot move (entry_id, time_slot_id) |
| POST | `/entries/bulk_create/` | Create multiple entries at once (from auto-generation) |

### Schedule Exceptions (`/api/v1/scheduling/exceptions/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/exceptions/` | List all exceptions |
| POST | `/exceptions/` | Create an exception |
| GET/PUT/DELETE | `/exceptions/{id}/` | Exception detail/update/delete |
| GET | `/exceptions/pending/` | List unapproved exceptions |
| POST | `/exceptions/{id}/approve/` | Approve an exception |

### Substitution Requests (`/api/v1/scheduling/substitutions/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/substitutions/` | List all substitution requests |
| POST | `/substitutions/` | Create a substitution request |
| GET/PUT/DELETE | `/substitutions/{id}/` | Request detail/update/delete |
| POST | `/substitutions/{id}/approve/` | Approve (with optional substitute_id) |
| POST | `/substitutions/{id}/reject/` | Reject a request |
| GET | `/substitutions/available_professors/?date=&timeslot_id=` | Find available professors for substitution |

### Notifications (`/api/v1/scheduling/notifications/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | List user's notifications |
| GET | `/notifications/{id}/` | Notification detail |
| POST | `/notifications/{id}/mark_read/` | Mark single notification as read |
| POST | `/notifications/mark_all_read/` | Mark all notifications as read |
| GET | `/notifications/unread_count/` | Get unread notification count for badge display |

### Timetable Generations (`/api/v1/scheduling/generations/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/generations/` | List all generation runs |
| POST | `/generations/` | Create a generation record |
| GET/PUT/DELETE | `/generations/{id}/` | Generation detail/update/delete |
| POST | `/generations/{id}/run/` | Trigger generation (Celery async or synchronous fallback) |
| POST | `/generations/{id}/rollback/` | Rollback: delete all entries from this generation |

## Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
|-----|----------------------|---------|
| `core` | School, Session, Semester | Tenant context, academic period for entries and generation |
| `accounts` | User, Student, Parent, decorators (`direction_only`, `professor_only`, `parent_only`, `tenant_required`, `role_required`) | Professor/student identity, role-based view access, notification recipients |
| `course` | Course, CourseAllocation | Course data for schedule entries; allocation data for generation engine |
| `filieres` | Filiere, FiliereSubject | Student group context for entries; curriculum data for generation |
| `events` | Event | School events overlay in calendar feed |

### External Dependencies

| Package | Purpose |
|---------|---------|
| `django-rest-framework` | REST API viewsets and serializers |
| `django-filter` | FilterSet classes for room, entry, notification filtering |
| `django-crispy-forms` | Form layouts for all frontend forms |
| `django-ratelimit` | Rate limiting on POST endpoints (50/h general, 5/h for generation) |
| `celery` | Async timetable generation and email notification tasks |
| `modeltranslation` | i18n for Room.name and TimeSlot.name |
| `xhtml2pdf` | PDF timetable export (optional, falls back to HTML) |

## Configuration

- **Celery**: Required for async timetable generation and email notification tasks; synchronous fallback exists for generation
- **EMAIL_FROM_ADDRESS**: Used by `tasks.py` for sending notification and reminder emails (defaults to `noreply@school.local`)
- **Rate Limits**: Most POST views limited to 50/hour per user; timetable generation limited to 5/hour
- **Time Limits**: Celery generation task has a 120-second time limit (`time_limit=120`)

## URL Namespaces

- Frontend: `frontend:scheduling:<view_name>`
- API: `api:v1:scheduling:<resource-name>`

## File Structure

```text
scheduling/
  models.py              -- Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
                            ScheduleException, SubstitutionRequest, ScheduleNotification,
                            TimetableGeneration + choice tuples
  views_frontend.py      -- 30+ frontend views: calendar, professor, parent, room CRUD,
                            time slot config, editor, entry CRUD, wizard (4 steps),
                            conflicts, reports, substitutions, exceptions, notifications
  views_api.py           -- 7 DRF ViewSets: Room, TimeSlot, ScheduleEntry, ScheduleException,
                            SubstitutionRequest, ScheduleNotification, TimetableGeneration
  urls.py                -- Frontend + API URL routing with DRF router
  serializers.py         -- 10 serializers including list/create variants and CalendarEvent
  forms.py               -- 6 forms: Room, TimeSlot, ScheduleEntry, ScheduleException,
                            SubstitutionRequest, Cancellation (all with crispy layouts)
  filters.py             -- django-filter FilterSets for Room, TimeSlot, ScheduleEntry,
                            SubstitutionRequest, ScheduleNotification
  signals.py             -- post_save on ScheduleException and SubstitutionRequest for notifications
  services.py            -- Notification creation logic: exception notifications, substitution
                            notifications, recipient resolution
  tasks.py               -- 3 Celery tasks: generate_timetable_task, send_schedule_change_notifications,
                            send_daily_schedule_reminder
  admin.py               -- 8 ModelAdmin classes with tenant-scoped querysets
  apps.py                -- SchedulingConfig with signal registration
  translation.py         -- modeltranslation for Room.name and TimeSlot.name
  templatetags/
    scheduling_tags.py   -- todays_schedule inclusion tag for dashboard widgets
  engine/
    __init__.py
    types.py             -- Dataclasses: SchedulingUnit, SlotAssignment, ConflictInfo
    collector.py         -- ScheduleDataCollector: gathers courses, rooms, slots, availability
    scorer.py            -- SoftScorer: preference, morning, consistency, gap, distribution scoring
    generator.py         -- TimetableGenerator: main 6-phase generation pipeline
    local_search.py      -- LocalSearchOptimizer: hill-climbing slot-swap optimization
    validator.py         -- detect_conflicts(): professor, room, student overlap + capacity checks
  tests/                 -- Test suite
```

# Scheduling - Architecture

## Overview

The scheduling app is the timetable backbone of the School Management System. It manages rooms, time slots, recurring schedule entries, one-off exceptions, substitution workflows, and an automated timetable generation engine. The app spans three distinct layers: a Django template frontend with FullCalendar integration, a DRF REST API, and a background task layer (Celery) for async generation and email notifications. All data is tenant-scoped via FK to `core.School`.

## Models & Relationships

### Entity-Relationship Diagram

```
core.School (tenant)
  |
  |--1:N--> Room
  |           |
  |--1:N--> TimeSlot -------+
  |           |              |
  |--1:N--> ScheduleEntry --+------+
  |           |  |  |  |           |
  |           |  |  |  +--N:1--> course.Course
  |           |  |  +-----N:1--> accounts.User (professor)
  |           |  +---------N:1--> filieres.Filiere
  |           |
  |           +--1:N--> ScheduleException
  |           |           |
  |           |           +--N:1--> Room (new_room, nullable)
  |           |           +--N:1--> User (substitute_professor, nullable)
  |           |           +--N:1--> User (approved_by, nullable)
  |           |           +--N:1--> User (created_by, nullable)
  |           |
  |           +--1:N--> SubstitutionRequest
  |           |           |
  |           |           +--N:1--> User (requesting_professor)
  |           |           +--N:1--> User (suggested_substitute, nullable)
  |           |           +--N:1--> User (assigned_substitute, nullable)
  |           |           +--N:1--> User (reviewed_by, nullable)
  |           |
  |           +--1:N--> ScheduleNotification
  |                       |
  |                       +--N:1--> User (recipient)
  |                       +--N:1--> ScheduleEntry (related_entry, nullable)
  |                       +--N:1--> ScheduleException (related_exception, nullable)
  |
  +--1:N--> TimetableGeneration
  |           |
  |           +--N:1--> core.Session
  |           +--N:1--> core.Semester
  |           +--N:1--> User (created_by, nullable)
  |           +--1:N--> ScheduleEntry (generation FK)
  |
  +--ProfessorAvailability
              |
              +--N:1--> User (professor)
              +--N:1--> TimeSlot
```

### ScheduleEntry Foreign Key Map

```
ScheduleEntry
  +-- tenant -----------> core.School (CASCADE)
  +-- course -----------> course.Course (CASCADE)
  +-- professor --------> accounts.User (CASCADE, limit_choices_to={role: professor})
  +-- room -------------> Room (SET_NULL, nullable)
  +-- time_slot --------> TimeSlot (CASCADE)
  +-- filiere ----------> filieres.Filiere (CASCADE, nullable)
  +-- session ----------> core.Session (CASCADE, nullable)
  +-- semester ---------> core.Semester (CASCADE, nullable)
  +-- generation -------> TimetableGeneration (SET_NULL, nullable)
  +-- created_by -------> accounts.User (SET_NULL, nullable)
```

### ScheduleException Foreign Key Map

```
ScheduleException
  +-- tenant -----------> core.School (CASCADE)
  +-- schedule_entry ---> ScheduleEntry (CASCADE)
  +-- new_room ---------> Room (SET_NULL, nullable)
  +-- substitute_professor -> accounts.User (SET_NULL, nullable)
  +-- approved_by ------> accounts.User (SET_NULL, nullable)
  +-- created_by -------> accounts.User (SET_NULL, nullable)
```

### Database Indexes

```
ScheduleEntry:
  - (tenant, professor)
  - (tenant, room)
  - (tenant, filiere, semester)
  - (effective_from, effective_until)

ScheduleNotification:
  - (recipient, is_read)
  - (tenant, -created_at)
```

### Unique Constraints

```
Room:           (tenant, code)
TimeSlot:       (tenant, day_of_week, start_time)
ProfessorAvail: (professor, time_slot)
ScheduleExcept: (schedule_entry, date, exception_type)
```

## View Access Patterns

### Frontend Views by Decorator

```
@login_required + @tenant_required (all authenticated users):
  schedule_calendar          -- FullCalendar page (filters vary by role)
  my_schedule                -- Today's personal schedule
  notification_list          -- User's schedule notifications
  notification_mark_read     -- Mark single notification read
  notification_mark_all_read -- Mark all notifications read

@login_required + @professor_only + @tenant_required:
  professor_schedule         -- Professor's teaching schedule
  mark_cancellation          -- Cancel a class (+ @ratelimit 50/h)
  request_substitution       -- Request a substitute (+ @ratelimit 50/h)
  my_substitution_requests   -- List own substitution requests

@login_required + @parent_only + @tenant_required:
  parent_child_schedule      -- View child's timetable

@login_required + @direction_only + @tenant_required:
  room_list, room_create (+ratelimit), room_detail, room_edit (+ratelimit), room_delete
  timeslot_config, timeslot_create (+ratelimit), timeslot_edit (+ratelimit), timeslot_delete
  schedule_editor
  schedule_entry_create (+ratelimit), schedule_entry_edit (+ratelimit), schedule_entry_delete
  timetable_wizard_step1, step2, step3, generate (+ratelimit 5/h), results
  conflict_list, conflict_resolve
  room_utilization_report, export_timetable_pdf
  substitution_list, substitution_review (+ratelimit)
  exception_list, exception_create (+ratelimit)
```

### API ViewSet Permissions (Current State)

```
All ViewSets: IsAuthenticated only (no role check)
  RoomViewSet              -- ModelViewSet (full CRUD + available, utilization)
  TimeSlotViewSet          -- ModelViewSet (full CRUD + grid)
  ScheduleEntryViewSet     -- ModelViewSet (full CRUD + calendar_feed, my_schedule,
                              conflicts, move, bulk_create)
  ScheduleExceptionViewSet -- ModelViewSet (full CRUD + pending, approve)
  SubstitutionRequestViewSet -- ModelViewSet (full CRUD + approve, reject, available_professors)
  ScheduleNotificationViewSet -- ReadOnlyModelViewSet (+ mark_read, mark_all_read, unread_count)
  TimetableGenerationViewSet -- ModelViewSet (full CRUD + run, rollback)
```

### Calendar Feed Role-Based Filtering

```
calendar_feed endpoint (ScheduleEntryViewSet):
  student    --> entries.filter(filiere=student.program)
  professor  --> entries.filter(professor=user)
  parent     --> entries.filter(filiere__in=children's programs)
  direction  --> entries (no filter, all entries)
  admin      --> entries (no filter, all entries)
  secretary  --> entries (no filter, all entries)
  other      --> entries.none()
```

## Business Logic Workflows

### 1. Manual Schedule Entry Creation

```
Direction User
    |
    v
schedule_entry_create (frontend) or POST /entries/ (API)
    |
    v
ScheduleEntryForm validates:
  - effective_until >= effective_from
  - Room/TimeSlot filtered by tenant (frontend only)
    |
    v
ScheduleEntry.objects.create()
  - tenant = current tenant
  - created_by = request.user
  - status = 'active' (default)
    |
    v
Entry appears in calendar_feed for matching roles
```

### 2. Timetable Auto-Generation (Wizard)

```
Step 1: Scope Selection
  Direction selects session, semester, filieres, date range
  --> Stored in request.session['wizard_config']
    |
    v
Step 2: Constraint Configuration
  Direction sets max_classes_per_day, max_consecutive_hours,
  respect_lunch_break, prefer_morning
  --> Merged into wizard_config
    |
    v
Step 3: Preview & Validation
  System calculates:
  - Subject count (FiliereSubject for selected filieres/semester)
  - Room count
  - Time slot count
  - Unallocated courses (courses without CourseAllocation)
  Shows warnings if prerequisites missing
    |
    v
Step 4: Generate
  TimetableGeneration record created
    |
    +-- Celery available? --> generate_timetable_task.delay(gen.id)
    |                           (async, status='running')
    |
    +-- Celery unavailable? --> TimetableGenerator(gen).generate()
                                 (synchronous, blocking)
    |
    v
TimetableGenerator.generate() pipeline:
  Phase 1: ScheduleDataCollector collects:
    - SchedulingUnits (from FiliereSubject + CourseAllocation)
    - Rooms (active, current tenant)
    - TimeSlots (active, class type, current tenant)
    - ProfessorAvailability preferences
    - Locked entries (is_locked=True)

  Phase 2: Constraint scoring (MRV heuristic):
    - Fewer valid rooms -> higher score
    - Less professor availability -> higher score
    - More slots needed -> higher score
    - Lab requirement -> +5 score
    Sort units descending by constraint_score

  Phase 3: Initialize occupation matrices from locked entries:
    - prof_occupied[prof_id] = set of time_slot_ids
    - room_occupied[room_id] = set of time_slot_ids
    - group_occupied[filiere_id] = set of time_slot_ids

  Phase 4: Greedy placement (for each unit, for each slot needed):
    For each time slot (preferring different days):
      Check hard constraints:
        - Professor not already occupied
        - Student group not already occupied
      Find smallest sufficient room not occupied
      Score via SoftScorer:
        - Professor preference (+20 preferred, +10 neutral, -15 avoid)
        - Morning preference for heavy courses (+10)
        - Room consistency (+15 same room, +5 first assignment)
        - Minimize student gaps (-5 per gap)
        - Even week distribution (-3 per deviation)
        - Professor workload distribution (-2 per deviation)
      Select best-scoring (slot, room) pair
      Create ScheduleEntry, update occupation matrices

  Phase 5: Local search optimization (max 500 iterations):
    Hill-climbing on non-locked entries:
      Try moving each entry to alternative slots
      Accept if: hard constraints met AND soft score improves
      Stop when no improvements found

  Phase 6: Validation:
    detect_conflicts() checks:
      - Professor double-booking (same time slot)
      - Room double-booking (same time slot)
      - Student group overlap (same filiere, same slot, same/no group)
      - Room capacity vs expected students
    Log unscheduled units as conflicts
    |
    v
generation.status = 'completed'
generation.entries_created = count
generation.conflicts_found = count
    |
    v
Redirect to results page
```

### 3. Class Cancellation (Professor)

```
Professor
    |
    v
mark_cancellation(entry_id) -- verifies professor owns the entry
    |
    v
CancellationForm: date, reason, notify_students
    |
    v
ScheduleException.objects.create(
  exception_type='cancellation',
  is_approved=True,       <-- auto-approved (no direction review)
  approved_by=professor,  <-- professor self-approves
  notify_students=form.notify_students,
)
    |
    v
Signal: post_save on ScheduleException
    |
    v
services.create_exception_notifications(exception):
  - Gets recipients: professor + students in filiere
  - Creates ScheduleNotification for each recipient
    |
    v
Celery task: send_schedule_change_notifications (periodic):
  - Finds notifications with email_sent=False
  - Sends email to each recipient
  - Marks email_sent=True
```

### 4. Substitution Request Workflow

```
Professor                     Direction
    |                             |
    v                             |
request_substitution(entry_id)    |
    |                             |
    v                             |
SubstitutionRequestForm:          |
  date, suggested_substitute,     |
  reason                          |
    |                             |
    v                             |
SubstitutionRequest created       |
(status='pending')                |
    |                             |
    v                             |
Signal: post_save (created=True)  |
    |                             |
    v                             |
services.notify_substitution_created():
  - Notify direction/admin/secretary users
  - Notify suggested_substitute (if any)
                                  |
                                  v
                    substitution_review(pk):
                      - Shows available professors
                        (not teaching at that time slot)
                      - Direction selects action:
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
              action='approve'           action='reject'
                    |                           |
                    v                           v
              sub.status='approved'     sub.status='rejected'
              sub.assigned_substitute   sub.reviewed_by=user
              = selected or suggested   sub.reviewed_at=now
                    |                           |
                    v                           |
              ScheduleException                 |
              created automatically:            |
                exception_type='substitution'   |
                substitute_professor=assigned   |
                is_approved=True                |
                notify_students=True            |
                    |                           |
                    v                           v
              Signal: post_save          Signal: post_save
              on SubstitutionRequest     on SubstitutionRequest
                    |                           |
                    v                           v
              services.notify_          services.notify_
              substitution_updated():   substitution_updated():
                - Notify requesting       - Notify requesting
                  professor                 professor
                - Notify assigned           (rejection message)
                  substitute
```

### 5. Calendar Feed Data Flow

```
FullCalendar (browser)
    |
    v
GET /api/v1/scheduling/entries/calendar_feed/
    ?start=2025-01-01&end=2025-01-31
    &filiere_id=X&professor_id=Y  (optional filters)
    |
    v
ScheduleEntryViewSet.calendar_feed():
    |
    +-- Filter entries by date range (effective_from/until overlap)
    +-- Apply role-based filtering (student->filiere, professor->self, etc.)
    +-- Apply optional filter params (filiere_id, professor_id, room_id)
    |
    +-- Load ScheduleExceptions for date range
    |   Build map: (entry_id, date) -> exception
    |
    +-- _expand_entries(): for each entry, for each day in range:
    |     if day matches weekday AND is_active_on(date):
    |       Look up exception for (entry.id, date)
    |       _build_event(): create FullCalendar event dict
    |         - Apply exception overrides (color, room, professor, time)
    |         - Set editable=True for direction/admin/secretary
    |
    +-- Optionally overlay school events from events.Event
    |
    v
JSON array of FullCalendar event objects:
  [{id, title, start, end, color, textColor, editable, extendedProps}, ...]
```

### 6. Notification Lifecycle

```
Trigger Event
    |
    +-- ScheduleException created --> Signal: notify_schedule_exception
    |     services.create_exception_notifications():
    |       Recipients = professor + students in filiere
    |       Bulk create ScheduleNotification records
    |
    +-- SubstitutionRequest created --> Signal: notify_substitution_status
    |     services.notify_substitution_created():
    |       Recipients = direction/admin/secretary + suggested_substitute
    |       Bulk create ScheduleNotification records
    |
    +-- SubstitutionRequest status changed --> Signal: notify_substitution_status
          services.notify_substitution_updated():
            Notify requesting_professor
            If approved: notify assigned_substitute
    |
    v
ScheduleNotification records (email_sent=False)
    |
    +-- In-app: notification_list / API /notifications/
    |   User reads list, marks read via notification_mark_read
    |
    +-- Email: send_schedule_change_notifications (Celery periodic task)
    |   Processes batch of 50 unsent notifications
    |   Sends email via django send_mail
    |   Marks email_sent=True
    |
    +-- Daily: send_daily_schedule_reminder (Celery periodic task)
        Groups tomorrow's entries by professor
        Sends schedule summary email to each professor
```

## Inter-App Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
|-----|----------------------|---------|
| `core` | School, Session, Semester | Tenant FK on all models; session/semester for entries and generation |
| `accounts` | User (AUTH_USER_MODEL), Student, Parent, decorators (`direction_only`, `professor_only`, `parent_only`, `tenant_required`, `role_required`) | Professor/student identity; role decorators for view access; parent-child relationship for schedule filtering; notification recipients |
| `course` | Course, CourseAllocation | Course FK on ScheduleEntry; allocation data for auto-generation (professor-course mapping) |
| `filieres` | Filiere, FiliereSubject | Filiere FK on ScheduleEntry; curriculum data for auto-generation (subjects per filiere/semester) |
| `events` | Event | School events overlay in calendar feed (optional, guarded by try/except ImportError) |

### Apps That Depend On This App

| App | What They Use | Purpose |
|-----|--------------|---------|
| (None currently) | -- | Scheduling is a leaf app; no other apps import from it |

**Note**: The `todays_schedule` template tag is used in dashboard templates (core app templates), creating a template-level dependency from core templates to the scheduling app.

### Dependency Diagram

```
                 ┌─────────────────────────────────────┐
                 |           SCHEDULING                 |
                 |                                      |
  accounts ─────>|  Room, TimeSlot, ProfessorAvail      |
  (User,Student, |  ScheduleEntry, ScheduleException    |
   Parent,       |  SubstitutionRequest                 |
   decorators)   |  ScheduleNotification                |
                 |  TimetableGeneration                 |
  core ─────────>|                                      |
  (School,       |  engine/                             |
   Session,      |    generator, collector, scorer,     |
   Semester)     |    local_search, validator, types     |
                 |                                      |
  course ───────>|  services (notifications)            |
  (Course,       |  signals (post_save triggers)        |
   CourseAlloc)  |  tasks (Celery async)                |
                 |                                      |
  filieres ─────>|  templatetags/scheduling_tags.py     |
  (Filiere,      |                                      |
   FiliereSubj)  └─────────────────────────────────────┘
                                |
  events ──────> (optional: calendar event overlay)
```

### Internal Module Dependencies

```
views_frontend.py
  +-- models.py (all models)
  +-- forms.py (all forms)
  +-- engine/validator.py (detect_conflicts)
  +-- engine/generator.py (TimetableGenerator, sync fallback)
  +-- tasks.py (generate_timetable_task, async path)

views_api.py
  +-- models.py (all models)
  +-- serializers.py (all serializers)
  +-- engine/generator.py (TimetableGenerator, sync fallback)
  +-- tasks.py (generate_timetable_task, async path)

signals.py
  +-- models.py (ScheduleException, SubstitutionRequest)
  +-- services.py (notification creation functions)

services.py
  +-- models.py (ScheduleNotification)
  +-- accounts.models (Student, for recipient lookup)

tasks.py
  +-- models.py (TimetableGeneration, ScheduleNotification, ScheduleEntry)
  +-- engine/generator.py (TimetableGenerator)

engine/generator.py
  +-- engine/collector.py (ScheduleDataCollector)
  +-- engine/scorer.py (SoftScorer)
  +-- engine/validator.py (detect_conflicts)
  +-- engine/local_search.py (LocalSearchOptimizer)
  +-- models.py (ScheduleEntry)

engine/collector.py
  +-- engine/types.py (SchedulingUnit)
  +-- models.py (Room, TimeSlot, ProfessorAvailability, ScheduleEntry)
  +-- filieres.models (FiliereSubject)
  +-- course.models (CourseAllocation)
  +-- accounts.models (Student)

engine/validator.py
  +-- engine/types.py (ConflictInfo)
  +-- models.py (ScheduleEntry)

engine/scorer.py
  (no external dependencies, pure scoring logic)

engine/local_search.py
  (no external dependencies, pure optimization logic)

templatetags/scheduling_tags.py
  +-- models.py (ScheduleEntry)
  +-- core.models (School)
  +-- accounts.models (Parent)
```

## Data Flow

### Request/Response Flow

```
User Request
    |
    v
urls.py (route matching)
    |
    ├── Frontend: views_frontend.py
    |   ├── forms.py (validation + crispy layout)
    |   ├── models.py (data access)
    |   ├── engine/ (generation, conflict detection)
    |   └── tasks.py (async generation)
    |
    └── API: views_api.py
        ├── serializers.py (validation + serialization)
        ├── models.py (data access)
        ├── engine/ (generation, conflict detection)
        └── tasks.py (async generation)
    |
    v
Template / JSON Response
```

### Signal-Driven Notification Flow

```
Model Save (ScheduleException or SubstitutionRequest)
    |
    v
signals.py (post_save receiver)
    |
    v
services.py (create_exception_notifications / notify_substitution_*)
    |
    v
ScheduleNotification bulk_create
    |
    ├── In-app: views read ScheduleNotification
    └── Email: tasks.send_schedule_change_notifications (Celery periodic)
```

### Generation Engine Data Flow

```
TimetableGeneration (config JSON)
    |
    v
ScheduleDataCollector
    |
    ├── FiliereSubject ──> SchedulingUnit[]
    |   + CourseAllocation    (course, professor, filiere, hours, lab requirement)
    |
    ├── Room[] (active rooms)
    ├── TimeSlot[] (active class slots)
    ├── ProfessorAvailability{} (prof_id, slot_id -> preference)
    └── ScheduleEntry[] (locked entries)
    |
    v
constraint scoring (MRV)
    |
    v
greedy placement + SoftScorer
    |
    v
LocalSearchOptimizer (hill climbing)
    |
    v
detect_conflicts (validation)
    |
    v
ScheduleEntry[] created in database
TimetableGeneration updated with results
```

## Technical Notes

- **Tenant isolation**: All models have a `tenant` FK to `core.School`. Frontend views use `get_current_tenant(request)` which falls back to creating a default school in dev mode. API views use `get_tenant(request)` which returns `None` when no tenant context exists (less safe -- queryset returns all data).
- **Recurrence handling**: `ScheduleEntry.is_active_on(date)` checks weekday match and ISO week parity for bi-weekly entries. The `calendar_feed` expands recurring entries by iterating day-by-day over the requested date range (O(entries * days)).
- **Exception overlay**: The calendar feed pre-loads all `ScheduleException` records for the date range into a dict keyed by `(entry_id, date)`, then applies overrides (color, room, professor, time) during event expansion.
- **Generation fallback**: Both frontend wizard and API viewset try Celery first (`task.delay()`), catch any exception, and fall back to synchronous `TimetableGenerator.generate()`. The Celery task has `max_retries=0` and `time_limit=120`.
- **Scoring weights**: SoftScorer uses fixed weights: professor preference (20), morning placement (10), room consistency (15), student gap minimization (25 effective), week distribution (15 effective), professor workload (10 effective). These are not configurable.
- **Translation**: Room.name and TimeSlot.name are registered with `modeltranslation` for i18n.
- **Occupation matrices**: The generator uses three `defaultdict(set)` structures (`prof_occupied`, `room_occupied`, `group_occupied`) mapping entity IDs to sets of time_slot IDs. These are initialized from locked entries and updated during placement.
- **Local search**: The optimizer uses a simplified improvement heuristic (prefer earlier slots and different days) rather than the full SoftScorer, which means optimization quality is limited.

# Alumni App -- Architecture

## Overview

The alumni app tracks graduates after they leave the school. It manages alumni
profiles, career data, events, donations, and achievements. Six Celery tasks
handle automated emails (newsletters, event reminders, donation receipts,
profile-update nudges).

---

## Model Relationships

```
 accounts.User                 course.Program
      |                              |
      | OneToOne (user.student)      | FK (student.program)
      v                              v
 accounts.Student ------------------>+
      |
      | OneToOne  (student -> alumni_record)
      v
 +------------------+
 |     Alumni       |
 +------------------+
 | student (O2O)    |  --> accounts.Student
 | graduation_year  |
 | graduation_date  |
 | current_occupation|
 | current_employer |
 | industry         |
 | job_title        |
 | personal_email   |
 | phone            |
 | linkedin_url     |
 | city, country    |
 | is_active        |
 | willing_to_mentor|
 | newsletter_subscribed |
 | notes            |
 | created_at       |
 | updated_at       |
 +--------+---------+
          |
          | FK (alumni)                M2M (attendees)
          |                            |
          v                            v
 +------------------+        +--------------------+
 | AlumniDonation   |        |   AlumniEvent      |
 +------------------+        +--------------------+
 | alumni (FK) -----+------> | title              |
 | amount           |        | description        |
 | currency         |        | event_type         |
 | purpose          |        | event_date         |
 | purpose_details  |        | end_date           |
 | transaction_id   |        | location           |
 | payment_method   |        | venue_details      |
 | is_anonymous     |        | max_attendees      |
 | tax_receipt_sent |        | registration_deadline|
 | tax_receipt_number|       | registration_fee   |
 | thank_you_sent   |        | attendees (M2M) ---+--> Alumni
 | thank_you_sent_at|        | organizer (FK) ----+--> accounts.User
 | notes            |        | is_active          |
 | donated_at       |        | created_at         |
 +------------------+        | updated_at         |
                              +--------------------+
          |
          | FK (alumni)
          v
 +------------------------+
 |   AlumniAchievement    |
 +------------------------+
 | alumni (FK) -----------+--> Alumni
 | achievement_type       |
 | title                  |
 | description            |
 | achievement_date       |
 | image                  |
 | url                    |
 | is_featured            |
 | is_published           |
 | created_at             |
 +------------------------+
```

### FK / Reverse-Name Quick Reference

| From               | To                | Relation    | Field / Related Name            |
|--------------------|--------------------|-------------|----------------------------------|
| Alumni             | accounts.Student   | OneToOne    | `student` / `alumni_record`      |
| AlumniDonation     | Alumni             | FK          | `alumni` / `donations`           |
| AlumniAchievement  | Alumni             | FK          | `alumni` / `achievements`        |
| AlumniEvent        | Alumni (attendees) | M2M         | `attendees` / `events_attended`  |
| AlumniEvent        | accounts.User      | FK          | `organizer` / `organized_alumni_events` |

### Chain to reach a User from any alumni model

```
AlumniDonation.alumni.student.student   --> accounts.User
AlumniAchievement.alumni.student.student --> accounts.User
Alumni.student.student                   --> accounts.User
```

The double `.student.student` happens because `Alumni.student` points to
`accounts.Student`, and `Student.student` is the OneToOneField back to
`accounts.User`.

---

## Enum / Choice Fields

### AlumniEvent.event_type
| Value          | Display          |
|---------------|------------------|
| `reunion`      | Reunion          |
| `networking`   | Networking       |
| `workshop`     | Workshop         |
| `social`       | Social Gathering |
| `fundraiser`   | Fundraiser       |
| `career_fair`  | Career Fair      |
| `other`        | Other            |

### AlumniDonation.purpose
| Value            | Display          |
|-----------------|------------------|
| `general`        | General Fund     |
| `scholarship`    | Scholarship Fund |
| `infrastructure` | Infrastructure   |
| `research`       | Research         |
| `sports`         | Sports           |
| `library`        | Library          |
| `other`          | Other            |

### AlumniDonation.payment_method
| Value            | Display        |
|-----------------|----------------|
| `stripe`         | Stripe         |
| `braintree`      | Braintree      |
| `bank_transfer`  | Bank Transfer  |
| `check`          | Check          |
| `cash`           | Cash           |

### AlumniAchievement.achievement_type
| Value               | Display            |
|--------------------|--------------------|
| `award`             | Award/Recognition  |
| `publication`       | Publication        |
| `promotion`         | Career Promotion   |
| `entrepreneurship`  | Started Business   |
| `community_service` | Community Service  |
| `other`             | Other              |

---

## Database Indexes

| Model              | Indexed Fields                        |
|-------------------|---------------------------------------|
| Alumni             | `graduation_year`                     |
| Alumni             | `is_active`                           |
| AlumniAchievement  | `-achievement_date`                   |
| AlumniAchievement  | `is_featured`, `-achievement_date`    |
| AlumniDonation     | `-donated_at`                         |
| AlumniDonation     | `purpose`, `-donated_at`              |
| AlumniEvent        | `-event_date`                         |
| AlumniEvent        | `event_type`, `-event_date`           |

---

## URL Structure

The app is mounted at two levels in `School_System/urls.py`:

- **Frontend**: `/alumni/` (namespace `alumni`)
- **API v1**: `/api/v1/alumni/` (namespace `alumni`)

### Frontend URL Map (`frontend_urlpatterns`)

| Path                     | View                       | Name            | Access              |
|-------------------------|----------------------------|-----------------|---------------------|
| `/alumni/`              | `alumni_directory`          | `directory`     | Any authenticated   |
| `/alumni/profile/<pk>/` | `alumni_profile`            | `profile`       | Any authenticated   |
| `/alumni/create/`       | `alumni_create`             | `alumni_create` | `@direction_only`   |
| `/alumni/edit/<pk>/`    | `alumni_edit`               | `alumni_edit`   | `@direction_only`   |
| `/alumni/events/`       | `alumni_event_list`         | `events`        | Any authenticated   |
| `/alumni/events/<pk>/`  | `alumni_event_detail`       | `event_detail`  | Any authenticated   |
| `/alumni/achievements/` | `achievement_list`          | `achievements`  | Any authenticated   |
| `/alumni/donate/`       | `donation_create`           | `donate`        | Any authenticated*  |

\* `donation_create` requires the logged-in user to have an `alumni_record`
attached to their Student profile. Non-alumni are redirected with an error
message.

### REST API Endpoints (DRF Router)

| Prefix              | ViewSet              | Basename  | Auth                   |
|---------------------|----------------------|-----------|------------------------|
| `/api/v1/alumni/alumni/`   | `AlumniViewSet`      | `alumni`  | `IsAuthenticated`      |
| `/api/v1/alumni/events/`   | `AlumniEventViewSet` | `event`   | `IsAuthenticated`      |

Both API ViewSets are full `ModelViewSet` (list / create / retrieve / update /
partial_update / destroy) gated only by `IsAuthenticated`. There are no
object-level permissions beyond authentication.

---

## View Access Patterns Per Role

### Role Permission Matrix (frontend views)

The `@direction_only` decorator expands to
`@role_required('secretary', 'direction', 'admin')`. Superusers bypass all
role checks.

| View               | student | professor | direction | parent | admin | prefet | accountant | secretary | librarian | registrar |
|--------------------|---------|-----------|-----------|--------|-------|--------|------------|-----------|-----------|-----------|
| `alumni_directory`   | R     | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `alumni_profile`     | R     | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `alumni_event_list`  | R     | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `alumni_event_detail`| R     | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `achievement_list`   | R     | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `donation_create`    | --    | --        | --        | --     | --    | --     | --         | --        | --        | --        |
| `alumni_create`      | --    | --        | CRU       | --     | CRU   | --     | --         | CRU       | --        | --        |
| `alumni_edit`        | --    | --        | CRU       | --     | CRU   | --     | --         | CRU       | --        | --        |

**Key**: R = Read, CRU = Create/Read/Update, -- = No access (redirected)

`donation_create` is special: any authenticated user can reach the URL, but
the view itself checks `request.user.student.alumni_record`. Only users who
have both a `Student` profile and an `Alumni` record linked to it can actually
submit the form. All other users see an error message and are redirected.

### REST API -- Role Matrix

Both API ViewSets use `permissions.IsAuthenticated` only. Every authenticated
user (regardless of role) gets full CRUD through the API. There is no
role-based filtering at the API layer.

### roles.py Permission Flags

The `School_System/roles.py` configuration grants alumni-specific permissions
to:

| Permission              | Direction | Secretary | Admin (inherits Direction) |
|------------------------|-----------|-----------|----------------------------|
| `manage_alumni`         | yes       | yes       | yes                        |
| `create_alumni_events`  | yes       | yes       | yes                        |
| `track_alumni_donations`| yes       | yes       | yes                        |
| `mark_students_as_alumni`| yes      | yes       | yes                        |

No other roles (Student, Parent, Professor, Prefet, Accountant, Librarian,
Registrar) have alumni management permissions in roles.py.

---

## Business Logic Workflows

### 1. Alumni Record Creation

```
Direction/Secretary/Admin user
    |
    v
GET /alumni/create/  -->  @direction_only check
    |
    v
AlumniForm rendered (fields: graduation_year, current_occupation,
    current_employer, industry, job_title, personal_email, phone,
    linkedin_url, city, country, willing_to_mentor)
    |
    v
POST --> form.save() --> Alumni record created
    |
    v
Redirect to /alumni/ (directory)
```

Note: The `AlumniForm` does NOT include the `student` field. The form must
be passed an `instance` or have the `student` set separately. Currently
`alumni_create` calls `form.save()` directly, so the `student` FK would need
to be handled (either the form is used in a context where `student` is set,
or the form would need to be extended).

### 2. Alumni Record Editing

```
Direction/Secretary/Admin user
    |
    v
GET /alumni/edit/<pk>/  -->  @direction_only check
    |
    v
AlumniForm pre-filled with existing record
    |
    v
POST --> form.save() --> Alumni record updated
    |
    v
Redirect to /alumni/profile/<pk>/
```

### 3. Donation Workflow

```
Authenticated user (must have Student + Alumni record)
    |
    v
GET /alumni/donate/
    |
    v
Check: request.user -> .student -> .alumni_record
    |
    +-- No alumni_record --> error message, redirect to directory
    |
    +-- Has alumni_record -->
            |
            v
        DonationForm rendered (fields: amount, purpose, purpose_details,
            is_anonymous)
            |
            v
        POST --> donation saved with:
            - alumni = current user's alumni record
            - transaction_id = uuid4()  (auto-generated)
            - payment_method = 'bank_transfer' (hardcoded)
            |
            v
        Success message --> redirect to directory
```

After creation, the Celery task `send_donation_thank_you` can be triggered
(manually or scheduled) to email a thank-you to the donor.

### 4. Event Lifecycle

```
AlumniEvent created (via admin or API)
    |
    +-- 7 days before event_date:
    |       send_upcoming_event_notifications (Celery beat, Monday 9 AM)
    |       Emails unregistered active alumni with newsletter_subscribed=True
    |       Limited to 100 alumni per event
    |
    +-- Before event:
    |       send_event_reminders(event_id) (triggered manually or via task)
    |       Emails registered attendees
    |
    +-- Event occurs
    |
    +-- Event becomes "past" (event_date < now)
            Displayed in "past events" section on event_list view
```

### 5. Donation Receipt Generation

```
AlumniDonation exists with tax_receipt_sent=False
    |
    v
generate_donation_receipts (Celery beat, Tuesday 4 AM)
    |
    v
For each donation without receipt:
    - Generate receipt number: TAX-{year}-{id:06d}
    - Set tax_receipt_number and tax_receipt_sent=True
    - Email receipt to non-anonymous donors with personal_email
```

### 6. Profile Staleness Detection

```
update_alumni_career_data (Celery beat, 1st of month at 10 AM)
    |
    v
Find alumni where:
    - is_active=True
    - updated_at < 1 year ago
    - personal_email is not blank
    |
    v
Send reminder email (max 50 per run)
```

---

## Celery Beat Schedule

| Task Name                              | Schedule                          | Function                              |
|----------------------------------------|-----------------------------------|---------------------------------------|
| `send-alumni-newsletter`               | 15th of each month at 10:00 AM   | `alumni.tasks.send_alumni_newsletter` |
| `send-upcoming-alumni-event-notifications` | Every Monday at 09:00 AM     | `alumni.tasks.send_upcoming_event_notifications` |
| `generate-donation-receipts`           | Every Tuesday at 04:00 AM        | `alumni.tasks.generate_donation_receipts` |
| `update-alumni-career-data-reminders`  | 1st of each month at 10:00 AM    | `alumni.tasks.update_alumni_career_data` |

Two additional tasks are defined but not in the beat schedule (invoked
on demand):

| Task                                     | Trigger               |
|------------------------------------------|-----------------------|
| `alumni.tasks.send_event_reminders`      | Called with `event_id` argument |
| `alumni.tasks.send_donation_thank_you`   | Called with `donation_id` argument |

---

## Data Flow Diagrams

### Read Flow -- Alumni Directory

```
Browser
  |
  | GET /alumni/?q=...
  v
@login_required
alumni_directory(request)
  |
  | Alumni.objects
  |   .select_related('student', 'student__student')
  |   .filter(is_active=True)
  |   .filter(Q(first_name) | Q(last_name) | Q(graduation_year)
  |           | Q(current_occupation) | Q(current_employer))
  v
Paginator(qs, 20)
  |
  v
Template: alumni/directory.html
  |
  v
HTML response
```

### Write Flow -- Donation Creation

```
Browser                         Django                          Database
  |                                |                               |
  | POST /alumni/donate/           |                               |
  |------------------------------->|                               |
  |                                | request.user.student          |
  |                                |   .alumni_record              |
  |                                |----lookup--------------------->|
  |                                |<---Alumni instance------------|
  |                                |                               |
  |                                | DonationForm(POST)            |
  |                                |   .is_valid()                 |
  |                                |                               |
  |                                | donation = form.save(         |
  |                                |   commit=False)               |
  |                                | donation.alumni = alumni      |
  |                                | donation.transaction_id =     |
  |                                |   uuid4()                     |
  |                                | donation.payment_method =     |
  |                                |   'bank_transfer'             |
  |                                | donation.save()               |
  |                                |----INSERT--------------------->|
  |                                |<---OK-------------------------|
  |                                |                               |
  |<-- 302 redirect to directory --|                               |
```

### Async Flow -- Newsletter Dispatch

```
Celery Beat (15th of month, 10 AM)
  |
  | Enqueue: send_alumni_newsletter
  v
Celery Worker
  |
  | Alumni.objects.filter(
  |     newsletter_subscribed=True,
  |     is_active=True
  | ).exclude(personal_email='')
  |
  | For each alumni:
  |     send_mail(
  |         to=alumni.personal_email,
  |         from="alumni@school.com"
  |     )
  |
  v
SMTP Server --> Recipient inbox
```

### Async Flow -- Event Notification Pipeline

```
Celery Beat (Monday 9 AM)
  |
  v
send_upcoming_event_notifications()
  |
  | Find events: is_active=True, event_date in [now, now+7d]
  | For each event:
  |     Get registered attendee IDs
  |     Find active alumni NOT in attendee list
  |         where newsletter_subscribed=True
  |         and personal_email != ''
  |     Send invite emails (limit: 100 per event)
  |
  v
SMTP Server
```

---

## Dependencies

### Inbound (other apps that reference alumni)

| Source File                        | What It Does                                      |
|------------------------------------|----------------------------------------------------|
| `tests/helpers.py`                | Creates Alumni and AlumniEvent fixtures for tests   |
| `tests/test_admin_registration.py`| Verifies alumni models are registered in admin      |
| `tests/test_model_methods_deep.py`| Tests `__str__`, `is_full`, `get_attendee_count`    |
| `tests/test_views_phase2.py`      | Integration tests for alumni frontend views         |
| `tests/test_tasks_deep.py`        | Tests all six Celery tasks                          |
| `School_System/celery.py`         | Registers 4 alumni tasks in beat schedule           |
| `School_System/roles.py`          | Defines `manage_alumni`, `create_alumni_events`, `track_alumni_donations` permissions |

### Outbound (alumni depends on these)

| Dependency               | Usage                                                    |
|--------------------------|----------------------------------------------------------|
| `accounts.Student`       | `Alumni.student` OneToOne FK                              |
| `accounts.User`          | `AlumniEvent.organizer` FK; accessed via `Student.student`|
| `accounts.decorators`    | `@direction_only` used by `alumni_create`, `alumni_edit`  |
| `django.contrib.auth`    | `get_user_model()` in models.py                           |
| `celery`                 | `@shared_task` for all 6 async tasks                      |
| `django.core.mail`       | `send_mail` in every Celery task                          |
| `rest_framework`         | ViewSets, serializers, permissions for API layer          |

### Dependency Diagram

```
                    +------------------+
                    |  accounts app    |
                    |  - User model    |
                    |  - Student model |
                    |  - decorators    |
                    +--------+---------+
                             |
              OneToOne / FK  |  @direction_only
                             v
                    +------------------+
                    |   alumni app     |
                    |  - Alumni        |
                    |  - AlumniEvent   |
                    |  - AlumniDonation|
                    |  - AlumniAchievement|
                    +--------+---------+
                             |
              @shared_task   |  send_mail()
                             v
              +--------------+---------------+
              |                              |
     +--------+--------+          +---------+--------+
     |  Celery / Redis  |          |   SMTP Server    |
     |  (task queue)    |          |   (email send)   |
     +-----------------+          +------------------+

              ^
              |
     +--------+--------+
     | School_System/   |
     | celery.py        |
     | (beat schedule)  |
     +-----------------+
```

---

## Admin Configuration

All four models are registered in `admin.py` with rich configurations:

| Model              | List Display                                           | Filters                                     | Actions                                     |
|-------------------|-------------------------------------------------------|---------------------------------------------|---------------------------------------------|
| `Alumni`           | student, graduation_year, current_occupation, current_employer, is_active | graduation_year, is_active, willing_to_mentor | activate_alumni, deactivate_alumni           |
| `AlumniEvent`      | title, event_type, event_date, location, attendee_count, is_active | event_type, event_date, is_active            | (none)                                       |
| `AlumniDonation`   | alumni, amount, currency, purpose, is_anonymous, tax_receipt_sent, donated_at | purpose, is_anonymous, currency, tax_receipt_sent, donated_at | mark_receipt_sent, mark_thank_you_sent       |
| `AlumniAchievement`| alumni, title, achievement_type, is_featured, is_published, achievement_date | achievement_type, is_featured, is_published  | feature_achievements, unfeature_achievements |

---

## Forms

| Form Class            | Model              | Exposed Fields                                                                                   |
|-----------------------|--------------------|-------------------------------------------------------------------------------------------------|
| `AlumniForm`          | Alumni             | graduation_year, current_occupation, current_employer, industry, job_title, personal_email, phone, linkedin_url, city, country, willing_to_mentor |
| `AlumniEventForm`     | AlumniEvent        | title, description, event_type, event_date, end_date, location, venue_details, max_attendees, registration_deadline, registration_fee |
| `DonationForm`        | AlumniDonation     | amount, purpose, purpose_details, is_anonymous                                                   |
| `AlumniAchievementForm` | AlumniAchievement | achievement_type, title, description, achievement_date, image, url                               |

Note: `AlumniEventForm` and `AlumniAchievementForm` are defined in
`forms.py` but are not currently used by any frontend view. They are
available for future use or for custom admin workflows.

---

## Serializers

| Serializer Class        | Model        | Fields   |
|------------------------|--------------|----------|
| `AlumniSerializer`      | Alumni       | `__all__`|
| `AlumniEventSerializer` | AlumniEvent  | `__all__`|

`AlumniDonation` and `AlumniAchievement` do not have serializers and are not
exposed through the REST API.

---

## Files in This App

```
alumni/
  __init__.py
  apps.py               -- AppConfig (name='alumni')
  models.py             -- Alumni, AlumniEvent, AlumniDonation, AlumniAchievement
  admin.py              -- Admin classes for all four models
  forms.py              -- AlumniForm, AlumniEventForm, DonationForm, AlumniAchievementForm
  serializers.py         -- AlumniSerializer, AlumniEventSerializer
  views_frontend.py      -- 8 frontend views (directory, profile, events, donate, etc.)
  views_api.py           -- AlumniViewSet, AlumniEventViewSet (DRF ModelViewSet)
  urls.py               -- api_urlpatterns + frontend_urlpatterns
  tasks.py              -- 6 Celery tasks (newsletter, reminders, receipts, etc.)
  migrations/
    0001_initial.py     -- Creates all 4 tables and 8 indexes
  tests/
    test_models.py
    test_forms.py
    test_admin.py
    test_tasks.py
    test_views_api.py
    test_views_frontend.py
```

No `signals.py` or `permissions.py` files exist in this app. Access control
is handled entirely through Django's `@login_required` decorator and the
`@direction_only` shortcut from `accounts.decorators`.

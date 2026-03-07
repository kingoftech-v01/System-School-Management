# Scheduling - TODO

## Backend

- [ ] Add role-based permission classes to API viewsets -- all viewsets use only `IsAuthenticated`; any logged-in user can create/modify/delete rooms, entries, and generations via the API (frontend views are properly restricted with `direction_only`)
- [ ] Add tenant filtering in `ScheduleEntryFilter.filter_professor_name` -- references `models.Q` but `models` is not imported in `filters.py`, causing a `NameError` at runtime
- [ ] Add ProfessorAvailability management views -- model exists but no frontend or API views for professors to set their availability preferences (only accessible via Django admin)
- [ ] Add date validation on `mark_cancellation` -- professor can cancel a class for any date including past dates; should restrict to future dates only
- [ ] Add date validation on `SubstitutionRequestForm` -- no check that the requested substitution date is in the future
- [ ] Add `is_approved` workflow to exceptions created by professors -- `mark_cancellation` auto-approves (`is_approved=True, approved_by=request.user`); professor-created cancellations should require direction approval
- [ ] Add uniqueness check before creating ScheduleException -- `mark_cancellation` does not check if an exception already exists for the same entry+date
- [ ] Add proper error handling for `xhtml2pdf` import failure in `export_timetable_pdf` -- currently silently falls back to HTML without informing the user
- [ ] Add generation status polling endpoint or WebSocket -- wizard redirects to results page immediately but async generation may still be running
- [ ] Add `is_published` enforcement -- `TimetableGeneration.is_published` field exists but is never set to True or checked; the intended "only one published generation per session+semester" constraint is not enforced
- [ ] Add rollback confirmation and cascade cleanup for `TimetableGeneration.rollback` API -- entries are deleted but no cleanup of related exceptions/notifications that reference those entries
- [ ] Add `send_daily_schedule_reminder` scheduling -- task exists but no Celery Beat configuration; the docstring says "8 PM" but nothing schedules it
- [ ] Add bi-weekly recurrence validation -- `is_active_on()` correctly checks ISO week parity, but the generation engine always creates entries with `recurrence='weekly'`; no way to generate bi-weekly entries
- [ ] Restrict `Session.objects.all()` in wizard step 1 -- queries all sessions without tenant filtering
- [ ] Add bulk operations for time slot creation -- currently must create one slot at a time; most schools have identical daily patterns

## Frontend

- [ ] Add confirmation dialog before deleting rooms, time slots, and schedule entries
- [ ] Add loading indicator on timetable generation (wizard step 3 submit) -- generation can take time but UI gives no feedback
- [ ] Add real-time schedule conflict feedback in ScheduleEntryForm -- the API has a `conflicts` endpoint but the form does not call it before submission
- [ ] Add filter persistence in room_list and substitution_list -- filters reset on page navigation
- [ ] Add drag-and-drop feedback in schedule editor -- the `move` API endpoint exists but no visible success/error toast on the frontend
- [ ] Add exception type icon/badge in exception_list -- all exceptions shown uniformly regardless of type
- [ ] Add child selector widget in parent_child_schedule -- currently uses a query param `?child_id=` but no visible UI for switching children
- [ ] Add empty state messages for views with no data (e.g., no entries for today, no substitution requests)

## Sidebar

- [ ] Add scheduling links to the sidebar for all roles -- calendar and my-schedule should be accessible from main navigation
- [ ] Add notification badge count in sidebar/header -- `unread_count` API endpoint exists but is not integrated into the base template

## Security

- [ ] **Critical**: API viewsets lack role-based permissions -- `RoomViewSet`, `TimeSlotViewSet`, `ScheduleEntryViewSet`, `TimetableGenerationViewSet` allow any authenticated user to create, update, and delete resources; only `IsAuthenticated` is enforced
- [ ] **Medium**: `substitution_review` does not verify the substitute_id belongs to a professor role -- direction can assign any user (including students) as a substitute
- [ ] **Medium**: `exception_create` form does not restrict `schedule_entry` queryset -- direction user could create exceptions for entries from other tenants if they guess the entry ID (the form queryset is unfiltered)
- [ ] **Medium**: `ScheduleExceptionForm` and `SubstitutionRequestForm` do not filter querysets by tenant -- foreign key dropdowns show all entries/professors across tenants
- [ ] **Low**: `room_delete` uses f-string in `_()` translation call -- `_(f'Room "{name}" has been deleted.')` bypasses i18n extraction
- [ ] **Low**: `export_timetable_pdf` accepts unvalidated `filiere_id`, `professor_id`, `room_id` query params -- should validate they belong to the current tenant
- [ ] **Low**: `bulk_create` API endpoint has no upper limit on number of entries -- could be abused to create thousands of entries in a single request
- [ ] **Low**: `notification_mark_read` does not filter by tenant -- a user could mark notifications from any tenant as read if they know the PK

## API

- [ ] Add `django-filter` integration to API viewsets -- `filters.py` defines FilterSets but they are not used in any viewset (`filterset_class` is never set)
- [ ] Add pagination to API viewsets -- no pagination configured; large tenants could return thousands of entries
- [ ] Add ordering support to API viewsets -- no `OrderingFilter` configured
- [ ] Add search support to Room and ScheduleEntry viewsets -- no `SearchFilter` configured
- [ ] Add rate limiting to API endpoints -- frontend views have `@ratelimit` but API viewsets do not
- [ ] Add `CalendarEventSerializer` usage -- serializer is defined but `calendar_feed` builds dicts manually instead of using it
- [ ] Add proper error response when `calendar_feed` receives invalid date format -- currently raises unhandled `ValueError` on malformed ISO dates
- [ ] Add `ProfessorAvailabilitySerializer` usage -- serializer exists but no ViewSet registered for it
- [ ] Add `ScheduleExceptionFilter` -- defined in `filters.py` but never used

## Testing

- [x] Admin tests exist (test_admin.py)
- [x] Form tests exist (test_forms.py)
- [x] Serializer tests exist (test_serializers.py)
- [x] Signal tests exist (test_signals.py)
- [x] Service tests exist (test_services.py)
- [x] Task tests exist (test_tasks.py)
- [x] Template tag tests exist (test_templatetags.py)
- [x] API view tests exist (test_views_api.py)
- [x] Frontend view tests exist (test_views_frontend.py)
- [ ] No tests for the engine module (generator.py, collector.py, scorer.py, local_search.py, validator.py) -- the most complex logic in the app is untested
- [ ] No tests for filters.py
- [ ] No model-level tests (test_models.py) -- `is_active_on()`, `duration_minutes`, `__str__` methods are untested

## Unnecessary Files

- [ ] No unnecessary files found

## Documentation

- [ ] Add docstrings to all engine module classes and methods -- `SoftScorer.score()` parameters are undocumented
- [ ] Add docstrings to `_get_entry_recipients` and `_build_exception_message` in services.py
- [ ] Document the generation algorithm constraints and scoring weights in a developer guide
- [ ] Document the Celery Beat schedule configuration needed for `send_schedule_change_notifications` and `send_daily_schedule_reminder`
- [ ] Add inline comments explaining the soft scoring weights in `scorer.py` (why 20/15/25/15/10?)

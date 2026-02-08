# Events - TODO

## Backend

- [ ] Add `event_edit` view (direction only) using existing EventForm
- [ ] Add `event_delete` view (direction only) with confirmation template
- [ ] Add URL patterns for edit (`<int:pk>/edit/`) and delete (`<int:pk>/delete/`)
- [ ] Add pagination to `event_list` view -- currently returns all events unpaginated
- [ ] Add filtering by event type and date range to `event_list` view

## Frontend

- [ ] Add "Edit" and "Delete" buttons to event detail template (direction only)
- [ ] Add "Create Event" button to event list template (direction only)
- [ ] Add event type filter dropdown and date range picker to list page
- [ ] Add pagination controls to event list template

## Sidebar

- [ ] Expand Events from single link to expandable menu with sub-links: "All Events", "Create Event" (direction only)

## Security

- [ ] CKEditor `allowedContent: True` applies to event descriptions -- stored XSS risk if user-submitted content is not sanitized

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to models.py (44 lines, no module docstring)

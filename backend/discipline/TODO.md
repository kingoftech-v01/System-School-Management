# Discipline - TODO

## Backend

- [ ] Add disciplinary action edit view -- no way to update incident details after creation
- [ ] Add disciplinary action delete view -- no way to remove erroneous records
- [ ] Add "resolve" action view -- `is_resolved` and `resolution_date` fields exist but no dedicated resolve endpoint
- [ ] Add severity filter to action list view -- currently no filtering at all
- [ ] Add student name search to action list view -- currently no search capability

## Frontend

- [ ] Add "Edit" button on action detail page
- [ ] Add "Delete" button on action detail page with confirmation dialog
- [ ] Add "Mark Resolved" button on action detail page (sets is_resolved=True and resolution_date)
- [ ] Add severity badge with color coding (minor=green, moderate=yellow, serious=orange, critical=red) on list
- [ ] Add filter dropdown for severity on action list page
- [ ] Add search bar for student name on action list page
- [ ] Add resolved/unresolved status indicator on action list page

## Sidebar

- [ ] Expand Discipline sidebar to show sub-links: All Actions, Create Action

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to models.py (52 lines, no module docstring)
- [ ] Add module docstring to views_frontend.py

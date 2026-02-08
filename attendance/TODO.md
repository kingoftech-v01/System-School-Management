# Attendance - TODO

## Backend

- [ ] Add attendance session edit view -- no way to change date/subject after creation
- [ ] Add attendance session delete view -- no way to remove erroneous sessions
- [ ] Add student create/edit/delete views for attendance-local Student model -- no CRUD for managing students
- [ ] Add group create/edit/delete views -- groups can only be managed via admin or API
- [ ] Add subject create/edit/delete views -- subjects can only be managed via admin or API

## Frontend

- [ ] Add "Edit" button on attendance detail page to re-mark attendance
- [ ] Add "Delete" button on attendance detail page with confirmation
- [ ] Add attendance percentage column to student list page
- [ ] Add date range filter to student attendance report page
- [ ] Add summary statistics bar (total present/absent/late) on the dashboard

## Sidebar

- [ ] Add "Student Reports" link to Attendance submenu -- currently no way to navigate to reports from sidebar
- [ ] Add "Groups" link to Attendance submenu -- group_list exists but is not in sidebar
- [ ] Add "Subjects" link to Attendance submenu -- subject_list exists but is not in sidebar

## Security

- [ ] Rate limiting on `take_attendance` (views_frontend.py:78) only protects POST, not GET -- add GET rate limiting too

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to models.py (217 lines, no module docstring)
- [ ] `tasks.py:20` TODO: "Implement attendance reminder logic" -- implement this Celery task
- [ ] `tasks.py:30` TODO: "Implement daily attendance stats generation" -- implement this Celery task
- [ ] `tasks.py:40` TODO: "Implement low attendance alert logic" -- implement this Celery task

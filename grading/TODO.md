# Grading - TODO

## Backend

- [ ] Fix duplicate `@login_required` decorator on `grade_entry_detail` view (line 395-396 in views_frontend.py)
- [ ] Add `grade_entry_edit` view to allow updating an existing grade entry
- [ ] Add `grade_entry_delete` view with confirmation
- [ ] Add `grade_curve_edit` view to allow updating an existing grade curve
- [ ] Add `grade_curve_delete` view with confirmation
- [ ] Add URL patterns for grade entry edit/delete and grade curve edit/delete

## Frontend

- [ ] Add "Edit" and "Delete" buttons to grade entry detail template (lecturer only)
- [ ] Add "Edit" and "Delete" buttons to grade curve detail template (direction only)
- [ ] Add export button to student gradebook (CSV or PDF)

## Sidebar

- [ ] Add "Peer Reviews" and "Grade Curves" sub-links to the Grading expandable menu (currently only Dashboard, Rubrics, Grade Entries)

## Security

- [ ] Duplicate `@login_required` decorator on `grade_entry_detail` (views_frontend.py:395-396) -- fix by keeping only one decorator

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Template `rubric_list.html` shows hardcoded "No data available" -- implement actual rubric iteration and CRUD buttons
- [ ] Add missing CRUD buttons in rubric list template

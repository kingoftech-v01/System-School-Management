# Enrollment - TODO

## Backend

- [ ] Add registration delete view -- no way to remove test or abandoned registrations
- [ ] Add registration edit view for direction -- can only review (approve/reject), not edit submitted data
- [ ] Add document delete view -- uploaded documents cannot be removed

## Frontend

- [ ] Add "Delete" button on enrollment detail page for direction (with confirmation)
- [ ] Add "Edit" button on enrollment detail page to correct submitted data
- [ ] Add delete icon on uploaded documents for direction users
- [ ] Add progress indicator (step 1/4, 2/4, etc.) in the registration form header
- [ ] Add inline document verification buttons on enrollment detail page (avoid separate page)

## Sidebar

- [ ] Add "Statistics" link under Enrollment submenu -- enrollment_statistics view exists but is not in sidebar
- [ ] Add "Export CSV" quick action link under Enrollment submenu

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Replace bare `except:` clauses in views_frontend.py with specific exception types
- [ ] `tasks.py:176` commented-out deletion code -- implement the deletion logic properly

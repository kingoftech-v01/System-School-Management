# Accounts - TODO

## Backend

- [ ] Add parent list view -- currently only `ParentAdd` exists, no list or detail view
- [ ] Add parent edit view -- no way to update parent info after creation
- [ ] Add parent delete view -- no way to remove parent records
- [ ] Add parent detail view -- no way to view parent profile individually
- [ ] Add confirmation step to `delete_staff` and `delete_student` views -- currently deletes on GET request without confirmation

## Frontend

- [ ] Add parent list template for browsing all parents
- [ ] Add parent edit template
- [ ] Add delete confirmation modal for students and lecturers (POST-based confirmation)
- [ ] Add student count badge to student list page header
- [ ] Add lecturer count badge to lecturer list page header

## Sidebar

- [ ] Add "Parents" submenu under ACADEMIC section with "Parent List" and "Add Parent" links
- [ ] Add "Staff List" link under Lecturers submenu (non-lecturer staff)

## Security

- [ ] `delete_staff` and `delete_student` perform DELETE on GET request (views_frontend.py:285-290, 371-376) -- must require POST with CSRF token
- [ ] Profile IDOR: `profile_single` (views_frontend.py:118) accesses any user by ID without tenant check -- add tenant filtering
- [ ] `StudentViewSet` (views_api.py:86-101) returns ALL students to any authenticated user -- add role-based queryset filtering
- [ ] 2FA secret key exposed in template context (views_frontend.py:986) -- avoid rendering raw secret key in HTML
- [ ] 2FA exempt path matching in middleware.py uses `startswith` -- could be bypassed with similar path prefixes
- [ ] `email_utils.py:59` bare `except:` with undefined variable `e` -- fix exception handler
- [ ] Username validation endpoint (views_api.py:130-156) allows user enumeration via timing differences

## Unnecessary Files

- [ ] Verify no duplicate empty `tests.py` exists alongside `accounts/tests/` test directory

## Documentation

- [ ] Add module docstring to `models.py` (380 lines, no module docstring)
- [ ] Add module docstring to `views.py`
- [ ] Add docstrings to User model methods
- [ ] Replace 16+ bare `except:` clauses in views.py with specific exception types (e.g., `ObjectDoesNotExist`, `ValueError`)

# Accounts - TODO

## Backend

- [x] Add parent list view (Completed as of 2026-02 -- `parent_list` in views_frontend.py)
- [x] Add parent edit view (Completed as of 2026-02 -- `parent_edit` in views_frontend.py)
- [x] Add parent delete view (Completed as of 2026-02 -- `parent_delete` in views_frontend.py)
- [x] Add parent detail view (Completed as of 2026-02 -- `parent_detail` in views_frontend.py)
- [ ] Add confirmation step to `delete_staff` and `delete_student` views -- currently deletes on GET request without confirmation
- [ ] Add bulk student import from CSV/Excel
- [ ] Add user account deactivation workflow (soft delete instead of hard delete)

## Frontend

- [x] Add parent list template for browsing all parents (Completed as of 2026-02)
- [x] Add parent edit template (Completed as of 2026-02)
- [ ] Add delete confirmation modal for students and lecturers (POST-based confirmation)
- [ ] Add student count badge to student list page header
- [ ] Add lecturer count badge to lecturer list page header
- [ ] Add profile completion indicator on user dashboard

## Sidebar

- [x] Add "Parents" submenu under ACADEMIC section with "Parent List" and "Add Parent" links (Completed as of 2026-02)
- [ ] Add "Staff List" link under Lecturers submenu (non-lecturer staff)

## Security

- [ ] `delete_staff` and `delete_student` perform DELETE on GET request (views_frontend.py:285-290, 371-376) -- must require POST with CSRF token
- [ ] Profile IDOR: `profile_single` (views_frontend.py:118) accesses any user by ID without tenant check -- add tenant filtering
- [ ] `StudentViewSet` (views_api.py:86-101) returns ALL students to any authenticated user -- add role-based queryset filtering
- [ ] 2FA secret key exposed in template context (views_frontend.py:986) -- avoid rendering raw secret key in HTML
- [ ] 2FA exempt path matching in middleware.py uses `startswith` -- could be bypassed with similar path prefixes
- [ ] `email_utils.py:59` bare `except:` with undefined variable `e` -- fix exception handler
- [ ] Username validation endpoint (views_api.py:130-156) allows user enumeration via timing differences

## API

- [ ] Add pagination to StudentViewSet and LecturerViewSet
- [ ] Add parent portal API endpoints (messages, appointments, permission slips)
- [ ] Add tenant-scoped filtering to all ViewSets

## Testing

- [ ] Add tests for invitation code workflow (generate, redeem, expiry)
- [ ] Add tests for parent portal views (dashboard, messaging, appointments)
- [ ] Add tests for account approval workflow
- [ ] Add tests for force password change flow

## Unnecessary Files

- [ ] Verify no duplicate empty `tests.py` exists alongside `accounts/tests/` test directory

## Documentation

- [ ] Add module docstring to `models.py` (665 lines, no module docstring)
- [ ] Add module docstring to `views.py`
- [ ] Add docstrings to User model methods
- [ ] Replace 16+ bare `except:` clauses in views.py with specific exception types (e.g., `ObjectDoesNotExist`, `ValueError`)

# Admissions - TODO

All frontend views are placeholders. These are the minimum items to make the app functional.

## Backend

- [ ] Implement `admission_session_list` view -- replace placeholder with actual list of sessions using template
- [ ] Implement `admission_apply` view -- replace placeholder with multi-step form using AdmissionApplicationForm
- [ ] Implement `admission_status` view -- replace placeholder with status lookup by email or application ID
- [ ] Implement `counseling_comment_create` view -- replace placeholder with form for adding counselor comments
- [ ] Add admission application detail view -- no URL exists for viewing a single application
- [ ] Add admission application list view for direction -- no admin-side list of all applications

## Frontend

- [ ] Create `admissions/session_list.html` template for listing admission sessions
- [ ] Create `admissions/application_form.html` template for the application form
- [ ] Create `admissions/status_check.html` template for public status checking
- [ ] Create `admissions/application_detail.html` template for viewing application details
- [ ] Create `admissions/application_list.html` template for direction to review all applications

## Sidebar

- [ ] Add "Admissions" entry to sidebar under MANAGEMENT section with sub-links: Sessions, Applications, Status Check

## Security

- [ ] `AdmissionSessionViewSet` (views_api.py:6) uses `AllowAny` permission -- exposes admission sessions publicly without authentication

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstrings to views_frontend.py (all views are currently placeholders)
- [ ] Add module docstring to models.py

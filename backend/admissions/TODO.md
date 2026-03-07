# Admissions - TODO

## Backend

- [x] Implement `admission_session_list` view -- lists active sessions with template (Completed -- `views_frontend.py:admission_session_list`)
- [x] Implement `admission_apply` view -- public multi-step form using AdmissionApplicationForm (Completed -- `views_frontend.py:admission_apply`)
- [x] Implement `admission_status` view -- status lookup by email using AdmissionStatusForm (Completed -- `views_frontend.py:admission_status`)
- [x] Implement `counseling_comment_create` view -- direction-only form for adding counselor comments (Completed -- `views_frontend.py:counseling_comment_create`)
- [x] Add admission application detail view -- direction-only single application view (Completed -- `views_frontend.py:admission_detail`)
- [x] Add admission application list view for direction -- paginated list with search and status filter (Completed -- `views_frontend.py:admission_list`)
- [ ] Add `program`, `previous_school`, `previous_grade`, `exam_scores` fields to AdmissionApplicationForm -- model has these fields but form does not expose them
- [ ] Add `transcript` and `birth_certificate` file upload fields to AdmissionApplicationForm -- model supports file uploads but form excludes them
- [ ] Wire `send_admission_confirmation_email` task to form submission -- task exists but is never called from `admission_apply` view
- [ ] Wire `send_status_update_email` task to status changes -- task exists but is never triggered when status changes via admin or API
- [ ] Add status transition validation -- currently any status can be set to any other status without business rule enforcement
- [ ] Add `@direction_only` or role-based permission to `AdmissionStudentViewSet` -- currently uses only `IsAuthenticated`, any logged-in user can CRUD all applications

## Frontend

- [ ] Create `admissions/session_list.html` template for listing admission sessions
- [ ] Create `admissions/apply.html` template for the application form
- [ ] Create `admissions/status.html` template for public status checking
- [ ] Create `admissions/admission_detail.html` template for viewing application details
- [ ] Create `admissions/admission_list.html` template for direction to review all applications
- [ ] Create `admissions/counseling_form.html` template for adding counseling comments

## Sidebar

- [ ] Add "Admissions" entry to sidebar under MANAGEMENT section with sub-links: Sessions, Applications, Status Check

## Security

- [ ] `AdmissionSessionViewSet` (views_api.py:6) uses `AllowAny` permission -- exposes admission sessions publicly without authentication
- [ ] `AdmissionStudentViewSet` (views_api.py:10) uses only `IsAuthenticated` -- any authenticated user (student, parent, etc.) can list, create, update, and delete all applications via the API
- [ ] `AdmissionStudentSerializer` uses `fields = '__all__'` -- exposes all model fields including internal fields (`reviewed_by`, `counselor`, `admitted`, `rejection_reason`) to any authenticated user
- [ ] No CSRF protection consideration for the public `admission_apply` view -- form submission is open to unauthenticated users
- [ ] Email sender address hardcoded as `admissions@school.com` in tasks.py -- should use `EMAIL_FROM_ADDRESS` from settings

## API

- [ ] Add pagination to `AdmissionStudentViewSet` -- currently returns all applications in a single response
- [ ] Add filtering by status, session, and program to `AdmissionStudentViewSet`
- [ ] Add role-based queryset scoping to `AdmissionStudentViewSet` -- students should only see their own applications
- [ ] Add `AdmissionPaymentSerializer` and `CounselingCommentSerializer` -- no API endpoints exist for payments or counseling comments
- [ ] Restrict `AdmissionStudentSerializer` fields based on user role -- public users should not see `reviewed_by`, `counselor`, `rejection_reason`
- [ ] Add `AdmissionSessionViewSet` write endpoints for direction/admin -- currently read-only, sessions can only be managed via Django admin

## Testing

- [ ] Add tests for `send_admission_confirmation_email` task with actual email sending (mock)
- [ ] Add tests for `send_status_update_email` task with all status message variants
- [ ] Add tests for `process_admission_payments` task end-to-end workflow
- [ ] Add tests for `send_counseling_reminders` task with multiple counselors
- [ ] Add integration test for full admission workflow (apply -> review -> counsel -> pay -> admit)
- [ ] Add tests for file upload validation on `transcript` and `birth_certificate` fields
- [ ] Add tests for `AdmissionStudentSerializer` field exposure and data integrity
- [ ] Add negative tests for API permission enforcement (student/parent attempting CRUD via API)

## Admin

- [ ] Fix `AdmissionStudentAdmin` fieldsets -- references `address` and `guardian_name` fields that do not exist on the model; should use `street_address`, `city`, `province`, `country`, `postal_code` and `guardian_first_name`, `guardian_middle_name`, `guardian_last_name`
- [ ] `approve_applications` admin action sets `status='admitted'` but does not set `admitted=True` or `admission_date` -- inconsistent with `process_admission_payments` task logic
- [ ] `reject_applications` admin action does not prompt for `rejection_reason`
- [ ] `move_to_counseling` admin action does not assign a counselor

## Unnecessary Files

- [ ] No unnecessary files found -- `tests.py` placeholder has been replaced by `tests/` package

## Documentation

- [x] Add module docstrings to views_frontend.py (Completed)
- [x] Add module docstring to models.py (Completed)

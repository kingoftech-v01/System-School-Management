# Enrollment - TODO

## Bugs

- [ ] **`RegistrationFormViewSet` ordering references non-existent field** (views_api.py:58-59) -- `ordering_fields` and `ordering` reference `created_at` but `RegistrationForm` only has `submitted_at`. This causes `FieldError` on any list/retrieve API call. Change `created_at` to `submitted_at`.
- [ ] **`RegistrationFormViewSet` search_fields reference old field names** (views_api.py:57) -- `search_fields` references `student_name` and `parent_name` which do not exist on the model. Should be `student_first_name`, `student_last_name`, `parent_first_name`, `parent_last_name`.
- [ ] **`RegistrationFormSerializer` references `created_at` and `updated_at`** (serializers.py:51-54) -- The `fields` list includes `created_at` and `updated_at`, but the model field is `submitted_at` (not `created_at`). The serializer also lists `updated_at` which exists but `created_at` does not. This causes `ImproperlyConfigured` errors.
- [ ] **`EnrollmentDocumentSerializer` references non-existent fields** (serializers.py:147-149) -- The `fields` list includes `file_name`, `file_size`, `verified_at`, and `verification_notes` which do not exist on the `EnrollmentDocument` model. The model only has `get_file_size()` method, `is_verified` boolean, and no `verified_at` or `verification_notes` fields.
- [ ] **`DocumentVerificationSerializer` references non-existent field** (serializers.py:193) -- The `fields` list includes `verification_notes` which does not exist on the `EnrollmentDocument` model. Only `is_verified` exists.
- [ ] **`IsDirectionUser` does not include `registrar` role** (accounts/permissions.py:18) -- The API permission `IsDirectionUser` checks for `secretary`, `direction`, `admin` but not `registrar`. This means registrar users can access frontend views (via `@registrar_only`) but NOT the equivalent API endpoints. The `registrar` role should be added to `IsDirectionUser` or a new `IsRegistrarUser` permission should be created.
- [ ] **`get_permissions()` overrides `@action` permission_classes** (views_api.py:93-98) -- The `get_permissions()` method returns `[IsAuthenticated()]` for actions not explicitly listed (including `pending` and `statistics`), which overrides the `permission_classes=[IsAuthenticated, IsDirectionUser]` set on the `@action` decorators. Students can access pending registrations and statistics via the API.
- [ ] **`upload_document` view has no authentication** (views_frontend.py:459) -- The document upload view accepts requests from anyone who knows the registration ID. There is no ownership check or authentication requirement. A malicious user could upload arbitrary files to any registration.
- [ ] **`auto_approve_complete_registrations` task does not create accounts** (tasks.py:241-243) -- The auto-approval task changes the status to `approved` but does not call `_create_accounts_for_enrollment()`, so auto-approved registrations will not have user accounts created.
- [ ] **Bare `except:` clause in `EnrollmentSearchForm.__init__`** (forms.py:436) -- Uses a bare `except:` when setting the filiere queryset, which catches all exceptions including `SystemExit` and `KeyboardInterrupt`. Should use `except Exception:` at minimum.
- [ ] **CSV export only applies name and status filters** (views_frontend.py:694-702) -- The export view applies `student_name` and `status` filters but has a comment `# ... (apply other filters)` for the remaining filters. The `enrollment_type`, `academic_year`, `filiere`, `date_from`, and `date_to` filters are not applied, so exports may include more data than the user expects.

## Backend

- [x] Add registration delete view -- `registration_delete` view implemented with GET confirmation page and POST to execute
- [x] Add registration edit view for direction -- `registration_edit` view implemented with `RegistrationEditForm`
- [x] Add document delete view -- `document_delete` view implemented (POST-only, cleans up file from storage)
- [ ] Add bulk registration import (CSV/Excel) -- no way to import multiple registrations at once
- [ ] Implement archival logic in `cleanup_old_rejected_registrations` task (tasks.py:176) -- Currently only logs count, deletion code is commented out; should move rejected registrations to an archive table or mark them archived
- [ ] Add filiere capacity enforcement at the model level -- capacity check only exists in `enrollment_review` view, not in the API review action or auto-approval task
- [ ] Add `@transaction.atomic` to the `enrollment_review` view -- status change, history creation, capacity check, and account creation should be wrapped in a single transaction to prevent partial updates on failure
- [ ] Add email notification for parent enrollment flow -- parent enrollment steps should trigger a notification to the parent's email confirming submission

## Frontend

- [x] Add "Delete" button on enrollment detail page for direction (with confirmation)
- [x] Add "Edit" button on enrollment detail page to correct submitted data
- [x] Add delete icon on uploaded documents for direction users
- [ ] Add progress indicator (step 1/4, 2/4, etc.) in the registration form header
- [ ] Add inline document verification buttons on enrollment detail page (avoid separate page)
- [ ] Add parent enrollment tracking dashboard -- parents should see a list of their submitted enrollments and their statuses
- [ ] Add document preview (PDF/image viewer) on enrollment detail page -- currently just shows file links

## Sidebar

- [ ] Add "Statistics" link under Enrollment submenu -- enrollment_statistics view exists but is not in sidebar
- [ ] Add "Export CSV" quick action link under Enrollment submenu

## Security

- [ ] Add authentication or ownership check to `upload_document` view -- anyone with a registration ID can upload documents
- [ ] Add CSRF protection verification for public registration steps -- ensure middleware is properly applied
- [ ] Add file content scanning for uploaded documents -- currently only validates extension and content type, not actual file content

## API

- [ ] Fix `RegistrationFormViewSet.ordering` to use `submitted_at` instead of `created_at`
- [ ] Fix `RegistrationFormViewSet.search_fields` to use actual model field names (`student_first_name`, `student_last_name`, etc.)
- [ ] Fix `RegistrationFormSerializer` to reference `submitted_at` instead of `created_at`
- [ ] Fix `EnrollmentDocumentSerializer` to remove non-existent fields (`file_name`, `file_size`, `verified_at`, `verification_notes`)
- [ ] Fix `DocumentVerificationSerializer` to remove non-existent `verification_notes` field
- [ ] Add `registrar` role to `IsDirectionUser` permission class or create `IsRegistrarUser`
- [ ] Add rate limiting to API ViewSets -- frontend views have `@ratelimit` but API has none
- [ ] Add API endpoint for parent enrollment flow -- parents can only enroll via frontend, not via API
- [ ] Add API endpoint for CSV export -- currently frontend-only

## Tests

- [ ] Fix form tests that use old field names (`student_name`, `address`, `parent_name`) -- `test_forms.py` tests reference fields that no longer exist after migration 0002; tests likely fail or pass vacuously
- [ ] Fix serializer tests that use old field names (`student_name`, `address`, `parent_name`) -- same issue as form tests
- [ ] Add test coverage for `_create_accounts_for_enrollment()` -- the account creation function has complex logic (username generation, Student/Parent profile creation, allauth EmailAddress) but no direct tests
- [ ] Add test coverage for parent enrollment flow (`parent_enroll_step1/2/3`) -- no tests exist for the 3-step parent enrollment wizard
- [ ] Add test for filiere capacity enforcement in `enrollment_review`
- [ ] Add test for CSV export with applied filters
- [ ] Add test for `send_enrollment_status_email` task with each status type
- [ ] Add test for `send_enrollment_reminders` task
- [ ] Add test for `auto_approve_complete_registrations` task
- [ ] Add test for `EnrollmentSearchForm` with all filter combinations
- [ ] Add test for `RegistrationEditForm` validation
- [ ] Add test for `DocumentUploadForm.clean_file()` with oversized files and invalid extensions

## Documentation

- [x] Replace bare `except:` clauses in views_frontend.py with specific exception types -- views_frontend.py no longer has bare except clauses (they were in the old code)
- [ ] `tasks.py:176` commented-out deletion code -- implement the archival/deletion logic properly
- [ ] Add docstrings to `_generate_temp_password` and `_create_accounts_for_enrollment` helper functions -- these are critical business logic functions
- [ ] Document the relationship between `@registrar_only` decorator and `IsDirectionUser` permission -- they grant access to different role sets (registrar is included in the decorator but not the API permission)

## Unnecessary Files

- [x] `tests.py` -- empty placeholder file removed (tests now in `tests/` directory)

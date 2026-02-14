# Certificates - TODO

## Backend

- [x] Add certificate edit view -- issued certificates cannot be edited (e.g., fix grade or date typo)
- [x] Implement actual PDF generation in `batch_generation_start` -- Celery task is commented out
- [x] Add certificate re-issue/unrevoke capability -- revoked certificates cannot be restored

Note: The edit view (`certificate_edit`) and reissue view (`certificate_reissue`) now exist in `views_frontend.py`. The batch generation Celery task (`generate_batch_certificates`) exists in `tasks.py` but the call from `batch_generation_start` is still commented out (see Celery section below).

- [ ] Wire up Celery task call in `batch_generation_start` -- both frontend view (line 589) and API action (line 280) have the `generate_batch_certificates.delay(batch.id)` call commented out
- [ ] Implement actual PDF generation logic -- `certificate.generate_pdf()` is referenced in `tasks.py:60` but the method does not exist on the Certificate model
- [ ] Add `status` field update to `'issued'` in API `revoke` action -- API revoke (views_api.py:177) sets `is_revoked=True` but does not update `status` to `'revoked'` (frontend revoke correctly calls `certificate.revoke()` which sets both)
- [ ] Add `revoked_by` tracking to API revoke action -- API revoke (views_api.py:177) does not record `revoked_by` user (frontend revoke correctly passes user to `certificate.revoke()`)

## Frontend

- [x] Add "Edit" button on certificate detail page for direction users
- [ ] Add status badge (issued/revoked/pending) with color coding on certificate list
- [ ] Add progress bar visualization on batch generation detail page
- [ ] Add filter buttons (by template, by status) on certificate list page

## Sidebar

- [ ] Expand Certificates sidebar entry to show sub-links: Dashboard, Templates, Certificates, Verification, Batch Generation

## Security

- [ ] Certificate verify API (views_api.py:86,126) uses `AllowAny` and leaks PII (student full name, grade) -- limit exposed data or require authentication
- [ ] API verify action (views_api.py:86) references `certificate.honors` field which does not exist on the Certificate model -- will raise `AttributeError` at runtime
- [ ] API `get_queryset` (views_api.py:75) crashes with `AnonymousUser` on `AllowAny` actions (`verify`, `verify_by_number`) because it tries to filter by `student__student=user` for non-staff users -- needs `AnonymousUser` guard
- [ ] API verification actions (views_api.py:110,152) pass string to `verified_by` but model has `verified_by_user` FK -- `CertificateVerification.objects.create(verified_by=...)` will fail; should use `verified_by_user` or pass `None` for anonymous
- [ ] API verify endpoints have no rate limiting -- frontend verification is rate-limited at 50/h per IP but API endpoints (`verify`, `verify_by_number`) have no throttling
- [ ] `CanManageTemplates` permission (permissions.py:57) allows unauthenticated read access to all template data via API -- consider requiring authentication for template list/detail

## API Consistency

- [ ] `CertificateTemplateViewSet.filterset_fields` references `certificate_type` and `is_default` (views_api.py:36) which do not exist on the `CertificateTemplate` model -- will raise `FieldError` when filtering
- [ ] `set_default` action references `certificate_type` and `is_default` fields (views_api.py:42-54) which do not exist on the model -- the entire action will fail
- [ ] `BatchCertificateGenerationViewSet` uses `select_related('created_by')` (views_api.py:254) but model FK is named `initiated_by` -- will raise `FieldError`
- [ ] API download action references `certificate.certificate_file` (views_api.py:221) but model field is `pdf_file` -- will raise `AttributeError`

## Admin

- [ ] `CertificateAdmin` fieldset references `honors` and `additional_info` fields (admin.py:71) which do not exist on the Certificate model -- admin detail page will crash
- [ ] `CertificateAdmin` fieldset references `certificate_file` field (admin.py:78) but model has `pdf_file` -- admin page will crash
- [ ] `CertificateVerificationAdmin` references `verified_by_email` and `notes` fields (admin.py:139,146,154) which do not exist on the model (model has `verified_by_user` FK and `verification_notes`) -- admin page will crash
- [ ] `BatchCertificateGenerationAdmin` references `created_by` and `grade_threshold` and `include_honors_only` fields (admin.py:172,179,181) which do not exist on the model (model has `initiated_by`, `min_grade`, `min_gpa`) -- admin page will crash

## Celery Tasks

- [ ] `generate_batch_certificates` task references `course.default_certificate_template` (tasks.py:27) which does not exist on the Course model -- will raise `AttributeError` if template is None
- [ ] `generate_batch_certificates` task references `course.passing_grade` (tasks.py:31) which does not exist on the Course model -- will raise `AttributeError`
- [ ] `generate_batch_certificates` task references `result.grade` as numeric for comparison (tasks.py:31) and passes to `determine_honors()` which expects numeric grade -- but Certificate model `grade` is CharField
- [ ] `generate_batch_certificates` task sets `honors=determine_honors(result.grade)` (tasks.py:56) but Certificate model has no `honors` field -- will raise `TypeError` on `Certificate.objects.create()`
- [ ] `generate_batch_certificates` task references `batch.created_by.email` (tasks.py:87) but model FK is `initiated_by` -- notification email will fail
- [ ] `send_expiring_certificate_reminders` task references `cert.expiry_date` (tasks.py:167) which does not exist on the Certificate model -- task will crash
- [ ] `send_certificate_notification` task is never called from any view or signal -- certificate issuance does not trigger notification

## Testing

- [ ] No test coverage for `certificate_edit` view with valid data (only tests nonexistent PK and permission denial)
- [ ] No test coverage for `certificate_reissue` view with an actual revoked certificate
- [ ] No test coverage for `certificate_download` with an actual PDF file attached
- [ ] No test coverage for `certificate_detail` or `certificate_list` with actual student-owned certificates
- [ ] No test coverage for `batch_generation_create` with valid form data and actual students
- [ ] No test for `generate_batch_certificates` Celery task end-to-end (only `determine_honors`, `cleanup`, and `integrity` are tested)
- [ ] No test for `send_certificate_notification` Celery task
- [ ] No test for `send_expiring_certificate_reminders` Celery task
- [ ] API view tests tolerate 500 responses due to source bugs -- once bugs are fixed, tests should assert exact status codes

## Documentation

- [x] `models.py:5` has comment placeholder `# Certificate content placeholders` instead of proper docstring -- add proper module docstring

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git; `.pyc` still exists in `__pycache__`)

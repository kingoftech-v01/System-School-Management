# Certificates - TODO

## Backend

- [ ] Add certificate edit view -- issued certificates cannot be edited (e.g., fix grade or date typo)
- [ ] Implement actual PDF generation in `batch_generation_start` -- Celery task is commented out
- [ ] Add certificate re-issue/unrevoke capability -- revoked certificates cannot be restored

## Frontend

- [ ] Add "Edit" button on certificate detail page for direction users
- [ ] Add status badge (issued/revoked/pending) with color coding on certificate list
- [ ] Add progress bar visualization on batch generation detail page
- [ ] Add filter buttons (by template, by status) on certificate list page

## Sidebar

- [ ] Expand Certificates sidebar entry to show sub-links: Dashboard, Templates, Certificates, Verification, Batch Generation

## Security

- [ ] Certificate verify API (views_api.py:86,126) uses `AllowAny` and leaks PII (student full name, grade) -- limit exposed data or require authentication

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] `models.py:5` has comment placeholder `# Certificate content placeholders` instead of proper docstring -- add proper module docstring

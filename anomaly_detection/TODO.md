# Anomaly Detection - TODO

## Bugs

- [ ] **Login detectors are defined but never wired** (detectors/login.py, signals.py) -- `BruteForceDetector`, `UnusualLoginTimeDetector`, and `DeviceChangeDetector` exist as detector classes but are not connected to any Django signal. No signal handler in `signals.py` calls them, so they are effectively dead code. They need to be wired to user login signals (e.g., `user_logged_in` from `django.contrib.auth.signals`) or integrated via middleware.
- [ ] **`DeviceChangeDetector` queries `analytics.ActivityLog` with wrong filter** (detectors/login.py:100) -- Filters on `student__student=user`, which assumes the ActivityLog has a `student` FK that itself has a `student` FK to User. This chain may not match the actual ActivityLog schema, and it only works for students, not staff/admin users.
- [ ] **`GradeJumpDetector` student name resolution is fragile** (detectors/grade.py:65) -- Uses `student.student.get_full_name()` which traverses `TakenCourse.student` (a Student profile) -> `.student` (the User). The `hasattr(student, 'student')` guard may be checking the wrong attribute, since `TakenCourse.student` is always a Student profile (which always has a `.student` FK to User). If the User FK is null, this will raise `AttributeError`.
- [ ] **`GradeAbnormallyHighDetector` has same student name fragility** (detectors/grade.py:124) -- Same issue as `GradeJumpDetector`: `student.student.get_full_name()` assumes the Student profile always has a linked User.
- [ ] **`GradeUnauthorizedChangeDetector` has same student name fragility** (detectors/grade.py:168, 193) -- Same `student.student.get_full_name()` pattern throughout all grade detectors.
- [ ] **`BaseDetector.get_anomaly_type()` cache ignores `is_enabled` toggle** (detectors/base.py:18-26) -- Once an AnomalyType is cached, disabling it via the admin (`is_enabled=False`) will not take effect for up to 300 seconds. The cache does not invalidate on model save.
- [ ] **`alert_acknowledge` allows re-acknowledging from any non-new status** (views_frontend.py:125) -- The guard checks `if alert.status not in ('new',)` to block re-processing, but the tuple condition means only `new` alerts can be acknowledged. However, the error message says "already been processed", which is misleading for `false_positive` alerts that were never acknowledged.
- [ ] **`alert_resolve` allows resolving `new` alerts without acknowledging first** (views_frontend.py:147) -- An alert can go directly from `new` to `resolved` or `false_positive`, skipping the `acknowledged` state. This may be intentional but is inconsistent with the lifecycle implied by the `acknowledged_by`/`acknowledged_at` fields.
- [ ] **No CSRF protection verification on POST views** (views_frontend.py) -- The `alert_acknowledge` and `alert_resolve` views accept POST but do not explicitly verify CSRF. Django's CSRF middleware handles this globally, but the views lack `{% csrf_token %}` enforcement documentation and no `@csrf_protect` decorator.

## Backend

- [ ] Wire login detectors to `user_logged_in` signal or authentication middleware -- `BruteForceDetector`, `UnusualLoginTimeDetector`, and `DeviceChangeDetector` are fully implemented but not triggered by any signal
- [ ] Add `tasks.py` with Celery periodic tasks -- No tasks file exists; consider adding: (1) periodic scan for stale `new` alerts, (2) daily anomaly summary digest email, (3) scheduled cleanup of old resolved alerts
- [ ] Add `serializers.py` with DRF serializers for API -- No serializers file exists; needed before API endpoints can be added
- [ ] Add `permissions.py` with DRF permission class -- No permissions file exists; needed for API endpoint authorization
- [ ] Add `forms.py` for alert management -- No forms file exists; the resolve view reads POST data directly (`request.POST.get('resolution')`) instead of using a validated form
- [ ] Populate `api_urlpatterns` in `urls.py` -- Currently `api_urlpatterns = []`; no REST API endpoints are available for anomaly data
- [ ] Add API endpoints for: listing alerts (with filters), alert detail, acknowledge, resolve, anomaly type listing, threshold management
- [ ] Add rate limiting to frontend views -- No `@ratelimit` decorator on any anomaly detection view; dashboard and list views could be rate-limited
- [ ] Invalidate `AnomalyType` cache when `is_enabled` is toggled in admin -- Either use a `post_save` signal on `AnomalyType` to clear the cache key, or reduce the cache TTL
- [ ] Add configurable alert deduplication -- The current system creates a new alert every time a detector fires, even for the same entity. Consider adding a deduplication window (e.g., no duplicate alert for the same `anomaly_type` + `object_id` within N minutes)
- [ ] Add `academic` domain detectors -- The `DOMAIN_CHOICES` includes `academic` (Academic Integrity) but no detectors exist for this domain
- [ ] Add module docstring to `models.py`, `signals.py`, `notifications.py`
- [ ] Remove or repurpose empty `views.py` -- Contains only the default Django stub

## Frontend

- [ ] Create templates for anomaly detection views -- The views reference `anomaly_detection/dashboard.html`, `alert_list.html`, `alert_detail.html`, and `anomaly_detection/email/alert_notification.html` but no templates directory or template files exist in the app
- [ ] Add sidebar navigation links for anomaly detection -- Dashboard and alert list should appear in the admin/direction sidebar
- [ ] Add alert count badge to navigation bar using `{{ anomaly_alert_count }}` from the context processor
- [ ] Add chart visualizations to the dashboard -- Severity and domain counts are computed but only passed as dictionaries; consider Chart.js or similar for visual representation
- [ ] Add alert timeline view showing anomaly trends over time
- [ ] Add bulk acknowledge/resolve actions for alert list
- [ ] Add export functionality (CSV/PDF) for alert reports

## Security

- [ ] **Frontend views use `@direction_only` but some anomaly types notify wider roles** -- Professors and accountants receive email notifications about anomalies they cannot view in the dashboard. Consider adding a read-only view for notified roles or expanding `@direction_only` to include `professor` and `accountant` for read access.
- [ ] **`notify_anomaly` sends to all users with matching roles regardless of school/tenant** -- In a multi-tenant deployment, anomaly notifications should be scoped to the tenant where the anomaly occurred. Currently, all direction/admin users across all tenants receive every notification.
- [ ] **No audit trail for alert status changes** -- When an alert is acknowledged or resolved, only the final `acknowledged_by`/`resolved_by` is recorded. There is no history log if an alert is re-resolved or if notes are edited.
- [ ] **Alert `details` JSONField may contain sensitive data** -- The details dict includes student names, email addresses, payment amounts, and transaction IDs. No PII scrubbing or access control is applied to this field.
- [ ] **Context processor queries on every request** -- `anomaly_alert_count()` runs `AnomalyAlert.objects.filter(status='new').count()` on every page load for privileged users. Consider caching this value.
- [ ] **`GenericForeignKey` on `AnomalyAlert` has no content type restriction** -- Any model can be linked as `related_object` with no validation. Consider adding `limit_choices_to` on the `content_type` field.

## Tests

- [ ] Add tests for login detectors (`BruteForceDetector`, `UnusualLoginTimeDetector`, `DeviceChangeDetector`) -- These detectors exist but have no test coverage
- [ ] Add tests for `BaseDetector.create_alert()` with `related_obj` parameter (GenericForeignKey path)
- [ ] Add integration tests that verify end-to-end flow: model save -> signal -> detector -> alert creation -> notification
- [ ] Add tests for `AnomalyThreshold` cascade delete behavior when parent `AnomalyType` is deleted
- [ ] Add tests for `AnomalyAlert` with GenericForeignKey lookup (`related_object` property)
- [ ] Add tests for `anomaly_alert_count` context processor with parent and prefet roles (verify they return 0)
- [ ] Add tests for seed migration `0002_seed_anomaly_types` -- verify all 13 types and their thresholds are created
- [ ] Add tests for `BaseDetector.get_anomaly_type()` caching behavior (cache hit vs. miss)
- [ ] Add tests for concurrent alert creation (race conditions in duplicate detection)
- [ ] Add API endpoint tests once `api_urlpatterns` is populated

## Unnecessary Files

- [ ] `views.py` -- Empty stub file (all views are in `views_frontend.py`); can be removed

# Anomaly Detection App

Automated detection and alerting system for suspicious patterns across grades, payments, enrollment, and login activity.

## Description

The anomaly detection app monitors data changes across the school management system via Django signals and raises alerts when anomalous patterns are detected. It covers four domains: grade anomalies (sudden jumps, abnormally high scores, unauthorized changes), payment anomalies (amount mismatches, double payments, status reversals, fee structure mismatches), enrollment anomalies (duplicates, invalid status transitions, unauthorized approvals), and login anomalies (brute force attempts, unusual login times, device changes).

Anomaly types and detection thresholds are fully configurable via the admin interface. When an anomaly is detected, an `AnomalyAlert` is created and email notifications are sent to users with configured roles. Alerts follow a lifecycle: new -> acknowledged -> resolved (or false_positive).

**Important**: The login domain detectors (`BruteForceDetector`, `UnusualLoginTimeDetector`, `DeviceChangeDetector`) are defined but not wired to any signal. They must be called manually or integrated via middleware/login signals. This is tracked in TODO.md.

## Main Features

- **Automated Grade Monitoring**: Detects sudden grade jumps (statistical + absolute thresholds), abnormally high grades (class average comparison), unauthorized grade changes (unallocated professors), and excessive grade modifications
- **Payment Fraud Detection**: Detects payment/invoice amount mismatches, double payments for the same invoice, suspicious payment status reversals (e.g., completed -> pending), and invoice/fee structure amount discrepancies
- **Enrollment Integrity**: Detects duplicate enrollment applications (same email + program + year), invalid enrollment status transitions, and enrollment approvals by unauthorized roles
- **Login Security**: Detects brute force login attempts (via django-axes), logins outside normal operating hours, and device/user-agent changes between sessions
- **Configurable Thresholds**: All detection parameters (standard deviation multipliers, jump thresholds, max changes, failure counts, time windows) are configurable per anomaly type via the `AnomalyThreshold` model
- **Role-Based Notifications**: Each anomaly type defines which roles receive email notifications (e.g., professors for grade issues, accountants for payment issues)
- **Alert Lifecycle Management**: Dashboard with severity/domain/status breakdowns, paginated alert list with filters, acknowledge and resolve workflows with notes
- **Context Processor**: Provides `anomaly_alert_count` template variable for displaying unread alert badges in navigation

## User Roles

The system has 10 roles. The anomaly detection app uses the following subset:

| Role | Frontend Access | Context Processor | Notification Target |
|------|----------------|-------------------|---------------------|
| student | No access | No (returns 0) | No |
| professor | No access | Yes (sees alert count) | Yes (grade anomalies) |
| direction | Full access (dashboard, list, detail, acknowledge, resolve) | Yes (sees alert count) | Yes (most anomaly types) |
| parent | No access | No (returns 0) | No |
| admin | Full access (dashboard, list, detail, acknowledge, resolve) | Yes (sees alert count) | Yes (all anomaly types) |
| prefet | No access | No (returns 0) | No |
| accountant | No access | Yes (sees alert count) | Yes (payment anomalies) |
| secretary | Full access (dashboard, list, detail, acknowledge, resolve) | Yes (sees alert count) | Yes (enrollment anomalies) |
| librarian | No access | No (returns 0) | No |
| registrar | No access | Yes (sees alert count) | No (not in default notify_roles) |

Frontend access is controlled by the `@direction_only` decorator, which permits `secretary`, `direction`, and `admin` roles.

## Models

- **`AnomalyType`** -- Admin-configurable anomaly type definitions. Fields: `code` (CharField, max 50, unique), `name` (CharField, max 200), `domain` (CharField, choices: grade/payment/enrollment/login/academic), `severity` (CharField, choices: low/medium/high/critical, default medium), `description` (TextField), `is_enabled` (BooleanField, default True), `notify_roles` (JSONField, list of role strings), `created_at`, `updated_at`. Ordered by `[domain, severity, code]`.

- **`AnomalyThreshold`** -- Configurable thresholds per anomaly type. Fields: `anomaly_type` (FK to AnomalyType, related_name `thresholds`), `key` (CharField, max 50), `value` (DecimalField, max_digits 10, decimal_places 2), `description` (CharField, max 200). Unique together: `[anomaly_type, key]`.

- **`AnomalyAlert`** -- Individual detected anomaly instances. Fields: `anomaly_type` (FK to AnomalyType, related_name `alerts`), `severity` (CharField, choices from AnomalyType.SEVERITY_CHOICES), `status` (CharField, choices: new/acknowledged/resolved/false_positive, default new), `title` (CharField, max 300), `details` (JSONField, default dict), `user` (FK to User, nullable, related_name `anomaly_alerts`), `content_type` (FK to ContentType, nullable), `object_id` (PositiveIntegerField, nullable), `related_object` (GenericForeignKey), `detected_at` (DateTimeField, auto_now_add), `acknowledged_by` (FK to User, nullable, related_name `acknowledged_anomalies`), `acknowledged_at` (DateTimeField, nullable), `resolved_by` (FK to User, nullable, related_name `resolved_anomalies`), `resolved_at` (DateTimeField, nullable), `notes` (TextField), `email_sent` (BooleanField, default False). Ordered by `[-detected_at]`. Indexed on `[status, -detected_at]`, `[anomaly_type, -detected_at]`, `[user, -detected_at]`.

## Detectors

All detectors extend `BaseDetector`, which provides `get_anomaly_type()`, `get_threshold(key, default)`, `create_alert(...)`, and an abstract `check(instance)` method.

| Detector | Code | Domain | Triggered By | Default Severity |
|----------|------|--------|-------------|-----------------|
| `GradeJumpDetector` | `grade_sudden_jump` | grade | Signal: `post_save` on `result.TakenCourse` | high |
| `GradeAbnormallyHighDetector` | `grade_abnormally_high` | grade | Signal: `post_save` on `result.TakenCourse` | medium |
| `GradeUnauthorizedChangeDetector` | `grade_unauthorized_change` | grade | Signal: `post_save` on `result.GradeHistory` | critical |
| `PaymentAmountMismatchDetector` | `payment_amount_mismatch` | payment | Signal: `post_save` on `payments.Payment` | critical |
| `DoublePaymentDetector` | `payment_double` | payment | Signal: `post_save` on `payments.Payment` (create only) | critical |
| `PaymentStatusReversalDetector` | `payment_status_reversal` | payment | Signal: `pre_save` on `payments.Payment` | high |
| `InvoiceFeeStructureMismatchDetector` | `payment_fee_mismatch` | payment | Signal: `post_save` on `payments.Invoice` (create only) | high |
| `DuplicateEnrollmentDetector` | `enrollment_duplicate` | enrollment | Signal: `post_save` on `enrollment.RegistrationForm` (create only) | high |
| `InvalidStatusTransitionDetector` | `enrollment_invalid_transition` | enrollment | Signal: `post_save` on `enrollment.RegistrationForm` (update only) | medium |
| `UnauthorizedApprovalDetector` | `enrollment_unauthorized_approval` | enrollment | Signal: `post_save` on `enrollment.RegistrationForm` (update only) | critical |
| `BruteForceDetector` | `login_brute_force` | login | Manual call (not wired to signal) | high |
| `UnusualLoginTimeDetector` | `login_unusual_time` | login | Manual call (not wired to signal) | low |
| `DeviceChangeDetector` | `login_device_change` | login | Manual call (not wired to signal) | medium |

## Seeded Anomaly Types

The migration `0002_seed_anomaly_types` seeds all 13 anomaly types with their default thresholds:

| Code | Thresholds |
|------|-----------|
| `grade_sudden_jump` | `std_dev_multiplier=2.00`, `jump_threshold=20.00` |
| `grade_abnormally_high` | `class_std_dev_multiplier=2.50` |
| `grade_unauthorized_change` | `max_changes_per_course=5.00` |
| `payment_amount_mismatch` | (none) |
| `payment_double` | (none) |
| `payment_status_reversal` | (none) |
| `payment_fee_mismatch` | (none) |
| `enrollment_duplicate` | (none) |
| `enrollment_invalid_transition` | (none) |
| `enrollment_unauthorized_approval` | (none) |
| `login_brute_force` | `failure_threshold=5.00`, `window_minutes=30.00` |
| `login_unusual_time` | `start_hour=6.00`, `end_hour=23.00` |
| `login_device_change` | (none) |

## URL Namespaces

- Frontend: `frontend:anomaly_detection:<view_name>`
- API: None (api_urlpatterns is empty)

### Frontend Routes

| URL Pattern | View | Name | Method |
|-------------|------|------|--------|
| `anomaly-detection/` | `anomaly_dashboard` | `dashboard` | GET |
| `anomaly-detection/alerts/` | `alert_list` | `alert_list` | GET |
| `anomaly-detection/alerts/<int:pk>/` | `alert_detail` | `alert_detail` | GET |
| `anomaly-detection/alerts/<int:pk>/acknowledge/` | `alert_acknowledge` | `alert_acknowledge` | POST |
| `anomaly-detection/alerts/<int:pk>/resolve/` | `alert_resolve` | `alert_resolve` | POST |

### API Endpoints

No API endpoints are currently defined (`api_urlpatterns = []`).

## Dependencies

### This App Depends On

- **`accounts`** -- User model (for alert FK relationships and notification recipients), `direction_only` decorator (for view access control), role constants
- **`result`** -- `TakenCourse` model (grade detection signals), `GradeHistory` model (unauthorized change detection), `CourseAllocation` model (authorization checking)
- **`payments`** -- `Payment` model (payment anomaly signals), `Invoice` model (invoice anomaly signals)
- **`enrollment`** -- `RegistrationForm` model (enrollment anomaly signals), `EnrollmentStatusHistory` model (transition validation)
- **`course`** -- `CourseAllocation` model (professor-course allocation checking in `GradeUnauthorizedChangeDetector`)
- **`analytics`** -- `ActivityLog` model (login history for `DeviceChangeDetector`)
- **`django.contrib.contenttypes`** -- `ContentType` model (for GenericForeignKey on `AnomalyAlert.related_object`)
- **`core`** -- `send_html_email` utility (for email notifications)
- **`django-axes`** -- Optional dependency for `BruteForceDetector` (graceful fallback if not installed)

### Apps That Depend On This App

- None directly (signals are registered via `apps.py` `ready()` hook, so the dependency is implicit)

## Configuration

### Context Processor

Add to `TEMPLATES[0]['OPTIONS']['context_processors']` in settings:

```python
'anomaly_detection.context_processors.anomaly_alert_count',
```

This provides `{{ anomaly_alert_count }}` in all templates for privileged roles.

### Cache

The `BaseDetector.get_anomaly_type()` method caches `AnomalyType` lookups for 300 seconds (5 minutes) using the default Django cache backend. Cache keys follow the pattern `anomaly_type_<code>`.

## Files

| File | Purpose |
|------|---------|
| `models.py` | 3 model definitions (AnomalyType, AnomalyThreshold, AnomalyAlert) |
| `views_frontend.py` | 5 template-based views (dashboard, list, detail, acknowledge, resolve) |
| `views.py` | Empty placeholder (unused) |
| `urls.py` | Frontend URL routing (5 routes), empty API URL list |
| `signals.py` | 6 signal handlers wiring detectors to model saves |
| `notifications.py` | `notify_anomaly()` function for role-based email alerts |
| `context_processors.py` | `anomaly_alert_count()` template context provider |
| `admin.py` | Admin registration for AnomalyType (with AnomalyThreshold inline) and AnomalyAlert |
| `apps.py` | App config with signal registration in `ready()` |
| `detectors/__init__.py` | Empty package init |
| `detectors/base.py` | `BaseDetector` abstract class with caching, threshold lookup, and alert creation |
| `detectors/grade.py` | 3 grade detectors (GradeJumpDetector, GradeAbnormallyHighDetector, GradeUnauthorizedChangeDetector) |
| `detectors/payment.py` | 4 payment detectors (PaymentAmountMismatchDetector, DoublePaymentDetector, PaymentStatusReversalDetector, InvoiceFeeStructureMismatchDetector) |
| `detectors/enrollment.py` | 3 enrollment detectors (DuplicateEnrollmentDetector, InvalidStatusTransitionDetector, UnauthorizedApprovalDetector) |
| `detectors/login.py` | 3 login detectors (BruteForceDetector, UnusualLoginTimeDetector, DeviceChangeDetector) |
| `migrations/0001_initial.py` | Database schema migration |
| `migrations/0002_seed_anomaly_types.py` | Data migration seeding 13 anomaly types with default thresholds |
| `tests/test_models.py` | Unit tests for all 3 models |
| `tests/test_detectors.py` | Unit tests for all detector classes across all domains |
| `tests/test_signals.py` | Tests for all 6 signal handlers |
| `tests/test_notifications.py` | Tests for the `notify_anomaly()` function |
| `tests/test_context_processors.py` | Tests for the `anomaly_alert_count()` context processor |
| `tests/test_views_frontend.py` | Tests for all 5 frontend views including permission checks |
| `tests/test_admin.py` | Tests for admin registration and configuration |

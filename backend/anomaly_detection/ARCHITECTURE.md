# Anomaly Detection App - Architecture

## Overview

The anomaly detection app is an event-driven monitoring system that listens to data changes across the school management platform and raises alerts when suspicious patterns are detected. It operates entirely through Django signals, requiring no explicit calls from the monitored apps (grades, payments, enrollment). The app defines a plugin-like detector architecture where each anomaly type is a self-contained class that implements a `check(instance)` method.

The app exposes a frontend dashboard for direction-level staff (secretary, direction, admin) and provides a template context processor for alert badge counts. There is no REST API currently.

## Directory Structure

```
anomaly_detection/
    __init__.py
    admin.py                     # Admin for AnomalyType (with threshold inline) and AnomalyAlert
    apps.py                      # App config; registers signals in ready()
    context_processors.py        # anomaly_alert_count() for template badges
    models.py                    # 3 models (AnomalyType, AnomalyThreshold, AnomalyAlert)
    notifications.py             # notify_anomaly() email notification function
    signals.py                   # 6 signal handlers wiring detectors to model events
    urls.py                      # Frontend URL routing (5 routes), empty API list
    views.py                     # Empty placeholder (unused)
    views_frontend.py            # 5 template-based views (dashboard, list, detail, acknowledge, resolve)
    detectors/
        __init__.py
        base.py                  # BaseDetector abstract class
        grade.py                 # 3 grade detectors
        payment.py               # 4 payment detectors
        enrollment.py            # 3 enrollment detectors
        login.py                 # 3 login detectors (not wired to signals)
    migrations/
        __init__.py
        0001_initial.py          # Schema migration
        0002_seed_anomaly_types.py  # Seeds 13 anomaly types with default thresholds
    tests/
        __init__.py
        test_admin.py
        test_context_processors.py
        test_detectors.py
        test_models.py
        test_notifications.py
        test_signals.py
        test_views_frontend.py
```

## Data Model

### Entity Relationship Diagram

```
AnomalyType
    |                                 accounts.User (external)
    | 1:N (thresholds)                    |    |    |
    v                                     |    |    |
AnomalyThreshold                          |    |    |
                                          |    |    |
AnomalyType                               |    |    |
    |                                     |    |    |
    | 1:N (alerts)                        |    |    |
    v                                     |    |    |
AnomalyAlert --(user)--------------------+    |    |
    |          --(acknowledged_by)-------------+    |
    |          --(resolved_by)----------------------+
    |
    +--(content_type + object_id)--> GenericForeignKey
                                       |
                                       +--> result.TakenCourse
                                       +--> result.GradeHistory
                                       +--> payments.Payment
                                       +--> payments.Invoice
                                       +--> enrollment.RegistrationForm
```

### Model Details

**AnomalyType**
- Represents a category of anomaly that the system can detect.
- Fields: `code` (unique identifier, e.g., `grade_sudden_jump`), `name`, `domain` (grade/payment/enrollment/login/academic), `severity` (low/medium/high/critical), `description`, `is_enabled`, `notify_roles` (JSON list of role strings), `created_at`, `updated_at`.
- The `code` field is used by detectors (`BaseDetector.anomaly_code`) to find their corresponding configuration.
- The `notify_roles` field determines which user roles receive email notifications when an alert of this type is created.
- Ordering: `[domain, severity, code]`.

**AnomalyThreshold**
- Key-value configuration parameters for a detector (e.g., `std_dev_multiplier=2.00`).
- Fields: `anomaly_type` (FK), `key`, `value` (Decimal), `description`.
- Constraint: `unique_together = [anomaly_type, key]`.
- Accessed by `BaseDetector.get_threshold(key, default)` which falls back to the default if no threshold row exists.

**AnomalyAlert**
- An individual detected anomaly instance.
- Fields: `anomaly_type` (FK), `severity`, `status` (new/acknowledged/resolved/false_positive), `title`, `details` (JSON dict with detection metadata), `user` (FK, the user involved in the anomaly), `content_type` + `object_id` + `related_object` (GenericForeignKey to the triggering model instance), `detected_at`, `acknowledged_by` (FK) + `acknowledged_at`, `resolved_by` (FK) + `resolved_at`, `notes`, `email_sent`.
- Three database indexes optimize common query patterns: `[status, -detected_at]` for dashboard queries, `[anomaly_type, -detected_at]` for domain filtering, `[user, -detected_at]` for per-user lookups.
- The `details` JSONField stores detection-specific metadata (scores, thresholds, student names, transaction IDs) for audit purposes.

## Detector Architecture

### Class Hierarchy

```
BaseDetector (detectors/base.py)
    |
    |-- anomaly_code = None
    |-- get_anomaly_type()        # Cached lookup of AnomalyType by code
    |-- get_threshold(key, default) # Configurable threshold lookup
    |-- create_alert(...)         # Creates AnomalyAlert + triggers notification
    |-- check(instance)           # Abstract: subclasses implement detection logic
    |
    +-- GradeJumpDetector              (anomaly_code = 'grade_sudden_jump')
    +-- GradeAbnormallyHighDetector    (anomaly_code = 'grade_abnormally_high')
    +-- GradeUnauthorizedChangeDetector (anomaly_code = 'grade_unauthorized_change')
    +-- PaymentAmountMismatchDetector  (anomaly_code = 'payment_amount_mismatch')
    +-- DoublePaymentDetector          (anomaly_code = 'payment_double')
    +-- PaymentStatusReversalDetector  (anomaly_code = 'payment_status_reversal')
    +-- InvoiceFeeStructureMismatchDetector (anomaly_code = 'payment_fee_mismatch')
    +-- DuplicateEnrollmentDetector    (anomaly_code = 'enrollment_duplicate')
    +-- InvalidStatusTransitionDetector (anomaly_code = 'enrollment_invalid_transition')
    +-- UnauthorizedApprovalDetector   (anomaly_code = 'enrollment_unauthorized_approval')
    +-- BruteForceDetector             (anomaly_code = 'login_brute_force')
    +-- UnusualLoginTimeDetector       (anomaly_code = 'login_unusual_time')
    +-- DeviceChangeDetector           (anomaly_code = 'login_device_change')
```

### Detector Lifecycle

1. A Django signal fires (e.g., `post_save` on `TakenCourse`).
2. The signal handler in `signals.py` instantiates the relevant detector(s).
3. The detector's `check(instance)` method runs the detection logic.
4. If an anomaly is found, `create_alert()` is called:
   a. `get_anomaly_type()` fetches the `AnomalyType` (with 5-minute cache).
   b. If the type is disabled (`is_enabled=False`), the alert is silently skipped.
   c. An `AnomalyAlert` record is created in the database.
   d. `notify_anomaly(alert)` is called to send email notifications.
5. All exceptions are caught and logged; the original save operation is never blocked.

### Caching Strategy

```
BaseDetector.get_anomaly_type()
    |
    v
Cache Lookup: key = 'anomaly_type_{code}'
    |
    |-- HIT --> Return cached AnomalyType
    |
    |-- MISS --> Query: AnomalyType.objects.filter(code=code, is_enabled=True).first()
                    |
                    |-- Found --> Cache for 300 seconds, return
                    |-- Not Found --> Return None (alert creation skipped)
```

**Known issue**: The cache does not invalidate when `is_enabled` is toggled in the admin. A disabled anomaly type continues to fire for up to 5 minutes.

## Signal Wiring

### Registered Signals (via apps.py ready())

```
result.TakenCourse (post_save)
    |
    +-- check_grade_anomalies
        |-- [total == 0] --> skip
        |-- GradeJumpDetector.check(instance)
        +-- GradeAbnormallyHighDetector.check(instance)

result.GradeHistory (post_save)
    |
    +-- check_grade_history_anomalies
        |-- [not created] --> skip
        +-- GradeUnauthorizedChangeDetector.check(instance)

payments.Payment (post_save)
    |
    +-- check_payment_anomalies
        |-- PaymentAmountMismatchDetector.check(instance)
        +-- [created] --> DoublePaymentDetector.check(instance)

payments.Payment (pre_save)
    |
    +-- check_payment_status_reversal
        |-- [not instance.pk] --> skip (new record)
        +-- PaymentStatusReversalDetector.check(instance)

payments.Invoice (post_save)
    |
    +-- check_invoice_anomalies
        |-- [not created] --> skip
        +-- InvoiceFeeStructureMismatchDetector.check(instance)

enrollment.RegistrationForm (post_save)
    |
    +-- check_enrollment_anomalies
        |-- [created] --> DuplicateEnrollmentDetector.check(instance)
        +-- [updated] --> InvalidStatusTransitionDetector.check(instance)
                          UnauthorizedApprovalDetector.check(instance)
```

### Unwired Detectors (login domain)

The following detectors are fully implemented but have no signal connection:

| Detector | Expected Trigger | Required Integration |
|----------|-----------------|---------------------|
| `BruteForceDetector` | Failed login attempts | `user_login_failed` signal or django-axes signal |
| `UnusualLoginTimeDetector` | Successful login | `user_logged_in` signal from `django.contrib.auth.signals` |
| `DeviceChangeDetector` | Successful login with user agent | `user_logged_in` signal + request middleware |

## Notification System

### Email Notification Flow

```
Detector.create_alert()
    |
    v
notify_anomaly(alert)
    |
    v
Read alert.anomaly_type.notify_roles
    |-- Empty? --> Default to ['direction', 'admin']
    v
Query: User.objects.filter(role__in=roles, is_active=True).exclude(email='')
    |
    |-- No recipients? --> Log and return
    v
core.utils.send_html_email(
    subject="[SEVERITY] Anomaly: {title}",
    recipient_list=[emails...],
    template='anomaly_detection/email/alert_notification.html',
    context={'alert': alert}
)
    |
    |-- Success --> alert.email_sent = True, save
    +-- Failure --> Log exception, email_sent remains False
```

### Default Notification Routing

| Anomaly Domain | Default Notified Roles |
|---------------|----------------------|
| Grade | professor, direction, admin |
| Payment | accountant, direction, admin |
| Enrollment | direction, admin, secretary |
| Login | admin |

## Request Flow

### Frontend (Template Views)

```
Browser Request
    |
    v
Django URL Router (urls.py: frontend_urlpatterns)
    |
    v
Decorators (applied in order):
    1. @login_required
    2. @direction_only  (allows: secretary, direction, admin)
    |
    v
View Function (views_frontend.py)
    |
    v
Model Query (models.py) --> Database
    |
    v
Template Rendering --> HTML Response
```

### Context Processor

```
Every Template Request
    |
    v
anomaly_alert_count(request)
    |
    |-- Not authenticated? --> return {'anomaly_alert_count': 0}
    |
    |-- Role in (direction, admin, accountant, professor, secretary, registrar)
    |   OR is_superuser?
    |       |
    |       v
    |   AnomalyAlert.objects.filter(status='new').count()
    |       |
    |       v
    |   return {'anomaly_alert_count': count}
    |
    +-- Other roles --> return {'anomaly_alert_count': 0}
```

## Authentication and Authorization

### Decorator Stack

All frontend views use the same two-decorator pattern:

| Decorator | Purpose | Allowed Roles |
|-----------|---------|---------------|
| `@login_required` | Ensures user is authenticated | All authenticated users |
| `@direction_only` | Restricts to direction-level roles | secretary, direction, admin |

### Role Access Matrix

| Capability | student | professor | direction | parent | admin | prefet | accountant | secretary | librarian | registrar |
|-----------|---------|-----------|-----------|--------|-------|--------|------------|-----------|-----------|-----------|
| View dashboard | No | No | Yes | No | Yes | No | No | Yes | No | No |
| View alert list | No | No | Yes | No | Yes | No | No | Yes | No | No |
| View alert detail | No | No | Yes | No | Yes | No | No | Yes | No | No |
| Acknowledge alert | No | No | Yes | No | Yes | No | No | Yes | No | No |
| Resolve alert | No | No | Yes | No | Yes | No | No | Yes | No | No |
| See alert badge (context) | No | Yes | Yes | No | Yes | No | Yes | Yes | No | Yes |
| Receive email notifications | No | Yes* | Yes* | No | Yes* | No | Yes* | Yes* | No | No |
| Manage types (admin) | No | No | No | No | Yes** | No | No | No | No | No |

\* Only if their role is listed in the anomaly type's `notify_roles` field.
\*\* Via Django admin site (requires `is_staff=True`).

### Access Control Gap

Professors and accountants can see the alert count badge in their navigation (via context processor) and receive email notifications about anomalies, but they cannot access the dashboard or any alert views (blocked by `@direction_only`). This creates a notification without actionable access.

## Alert Lifecycle

### State Machine

```
                +----> false_positive
                |
    new ----> acknowledged ----> resolved
     |                             ^
     +-----------------------------+
         (direct resolve allowed)
```

### State Transitions

| From | To | Action | View | Fields Updated |
|------|----|--------|------|----------------|
| new | acknowledged | Acknowledge | `alert_acknowledge` (POST) | `status`, `acknowledged_by`, `acknowledged_at` |
| new | resolved | Resolve directly | `alert_resolve` (POST) | `status`, `resolved_by`, `resolved_at`, `notes` |
| new | false_positive | Mark false positive | `alert_resolve` (POST, resolution=false_positive) | `status`, `resolved_by`, `resolved_at`, `notes` |
| acknowledged | resolved | Resolve | `alert_resolve` (POST) | `status`, `resolved_by`, `resolved_at`, `notes` |
| acknowledged | false_positive | Mark false positive | `alert_resolve` (POST, resolution=false_positive) | `status`, `resolved_by`, `resolved_at`, `notes` |

**Blocked transitions**: Resolved alerts cannot be re-resolved (warning shown). Acknowledged/resolved/false_positive alerts cannot be re-acknowledged (warning shown).

## Grade Detection Logic

### GradeJumpDetector

```
TakenCourse saved (total != 0)
    |
    v
Get past grades for this student (excluding zeros, excluding current)
    |
    |-- >= 3 past grades? --> Use personal statistics (mean, stdev)
    |
    +-- < 3 past grades? --> Get class grades for same course
            |
            |-- >= 2 class grades? --> Use class statistics
            +-- < 2 class grades? --> Skip (insufficient data)
    |
    v
Check 1: new_total > mean + (std_dev_multiplier * stdev)  [default: 2.0x]
Check 2: new_total > mean + jump_threshold                [default: 20 pts]
    |
    |-- Either check passes? --> Create alert
    +-- Neither passes? --> No alert
```

### GradeAbnormallyHighDetector

```
TakenCourse saved (total != 0)
    |
    v
Get class grades for same course (excluding zeros, excluding current)
    |
    |-- >= 3 class grades? --> Compute class mean + stdev
    +-- < 3 class grades? --> Skip (insufficient data)
    |
    v
Check: new_total > class_mean + (class_std_dev_multiplier * class_stdev)  [default: 2.5x]
    |
    |-- Passes? --> Create alert
    +-- Fails? --> No alert
```

### GradeUnauthorizedChangeDetector

```
GradeHistory created
    |
    v
Check 1: Is changed_by allocated to the course?
    |-- Superuser or direction/admin role? --> Skip check
    |-- CourseAllocation exists? --> Pass
    +-- No allocation? --> Create CRITICAL alert ("unauthorized grade change")
    |
    v
Check 2: Total change count on this TakenCourse > max_changes_per_course? [default: 5]
    |-- Yes --> Create HIGH alert ("excessive grade changes")
    +-- No --> Pass
```

## Payment Detection Logic

### PaymentAmountMismatchDetector

```
Payment saved
    |
    v
Has invoice? Has invoice.amount?
    |-- No --> Skip
    v
payment.amount != invoice.amount?
    |-- Yes --> Create alert with difference details
    +-- No --> Pass
```

### DoublePaymentDetector

```
Payment created (not on updates)
    |
    v
Count completed payments for same invoice > 1?
    |-- Yes --> Create alert with payment count
    +-- No --> Pass
```

### PaymentStatusReversalDetector

```
Payment pre_save (existing payment only)
    |
    v
Fetch old payment from DB, compare statuses
    |-- Same status? --> Skip
    v
Is transition valid per VALID_TRANSITIONS map?
    Valid: pending -> {processing, completed, failed}
           processing -> {completed, failed}
           completed -> {refunded}
           failed -> {pending, processing}
           refunded -> (none)
    |
    |-- Invalid transition? --> Create alert
    +-- Valid transition? --> Pass
```

### InvoiceFeeStructureMismatchDetector

```
Invoice created
    |
    v
Has fee_structure? Has amount?
    |-- No --> Skip
    v
invoice.amount != fee_structure.get_total_fee()?
    |-- Mismatch --> Create alert with difference
    +-- Match --> Pass
```

## Enrollment Detection Logic

### DuplicateEnrollmentDetector

```
RegistrationForm created
    |
    v
Query: same email + same filiere + same academic_year
       with status in (pending, under_review, approved, enrolled)
       excluding current registration
    |
    |-- Duplicates found? --> Create alert with duplicate IDs
    +-- No duplicates? --> Pass
```

### InvalidStatusTransitionDetector

```
RegistrationForm updated
    |
    v
Get most recent EnrollmentStatusHistory entry
    |-- No history? --> Skip
    v
Is old_status -> new_status in VALID_TRANSITIONS?
    Valid: pending -> {under_review, rejected}
           under_review -> {approved, rejected}
           approved -> {enrolled, rejected}
           rejected -> {pending}
           enrolled -> (none, terminal)
    |
    |-- Invalid? --> Create alert
    +-- Valid? --> Pass
```

### UnauthorizedApprovalDetector

```
RegistrationForm updated
    |
    v
Status is 'approved' or 'enrolled'?
    |-- No --> Skip
    v
Has reviewed_by?
    |-- No --> Skip
    v
Reviewer is superuser?
    |-- Yes --> Skip (superusers always authorized)
    v
Reviewer role in AUTHORIZED_ROLES (direction, admin, secretary, registrar)?
    |-- No --> Create CRITICAL alert
    +-- Yes --> Pass
```

## Cross-App Dependencies

### Incoming Dependencies (apps this app imports from)

```
accounts
    +-- User model (FK on AnomalyAlert: user, acknowledged_by, resolved_by)
    +-- decorators.direction_only (frontend view access)
    +-- get_user_model() (notification recipient queries)

result
    +-- TakenCourse (signal sender, grade detection)
    +-- GradeHistory (signal sender, unauthorized change detection)

payments
    +-- Payment (signal sender, payment detection)
    +-- Invoice (signal sender, fee mismatch detection)

enrollment
    +-- RegistrationForm (signal sender, enrollment detection)
    +-- EnrollmentStatusHistory (transition validation)

course
    +-- CourseAllocation (professor authorization check)

analytics
    +-- ActivityLog (device change detection, login history)

core
    +-- utils.send_html_email (email notifications)

django.contrib.contenttypes
    +-- ContentType (GenericForeignKey on AnomalyAlert)
```

### Outgoing Dependencies (apps that import from this app)

```
None (all integration is via signals registered in apps.py ready())
```

The anomaly detection app is designed to be a passive observer. It hooks into other apps via Django signals without requiring those apps to import anything from `anomaly_detection`. This means the app can be removed from `INSTALLED_APPS` without breaking any other app's functionality.

### Dependency Diagram

```
                    +-----------+
                    |  accounts |
                    | (User,    |
                    | decorators)|
                    +-----+-----+
                          |
              +-----------+-----------+
              |           |           |
        +-----+--+  +----+---+  +----+----+
        | result  |  |payments|  |enrollment|
        |(Taken   |  |(Payment|  |(Registra-|
        | Course, |  | Invoice|  | tionForm,|
        | Grade   |  |        |  | Status   |
        | History)|  |        |  | History) |
        +----+----+  +---+----+  +----+-----+
             |            |            |
             v            v            v
    +--------+------------+------------+---------+
    |                                            |
    |           anomaly_detection                |
    |                                            |
    |  signals.py <-- listens to all above       |
    |  detectors/ <-- analyzes instances         |
    |  models.py  <-- stores alerts              |
    |  notifications.py <-- emails roles         |
    |                                            |
    +--------------------------------------------+
              |                    |
              v                    v
        +-----+------+     +------+-----+
        |   course    |     |  analytics |
        |(CourseAlloc)|     |(ActivityLog)|
        +-------------+     +------------+
              |                    |
              v                    v
         +----+----+         +----+----+
         |  core   |         |  axes   |
         |(email)  |         |(optional)|
         +---------+         +---------+
```

## Key Design Decisions

### Signal-Driven Architecture

All anomaly detection is triggered by Django model signals (`post_save`, `pre_save`). This means:
- Monitored apps do not need to know about the anomaly detection app.
- Detection runs synchronously during the save operation (in the same database transaction).
- All exceptions are caught and logged, ensuring anomaly detection failures never block the original operation.
- The cost is added latency on every save of monitored models (mitigated by caching and early-exit conditions).

### Lazy Imports in Signal Handlers

Signal handlers in `signals.py` use local imports (`from anomaly_detection.detectors.grade import ...`) inside the function body rather than at module level. This avoids circular import issues since `apps.py` imports `signals.py` during Django startup, before all app models are fully loaded.

### Plugin-Style Detector Pattern

Each detector is a standalone class with a single `check(instance)` method. To add a new anomaly type:
1. Create a new detector class extending `BaseDetector`.
2. Set `anomaly_code` to match a code in the `AnomalyType` table.
3. Implement `check(instance)` with the detection logic.
4. Wire it to a signal in `signals.py`.
5. Add the corresponding `AnomalyType` row (via migration or admin).

### GenericForeignKey for Related Objects

`AnomalyAlert.related_object` uses Django's `GenericForeignKey` pattern (content_type + object_id) to link alerts to any model instance (TakenCourse, Payment, Invoice, RegistrationForm, etc.). This provides flexibility but sacrifices type safety and queryability (no reverse relation from the linked model to alerts).

### Configurable Thresholds via Database

Detection parameters are stored as `AnomalyThreshold` rows rather than hardcoded constants. This allows administrators to tune detection sensitivity without code changes. The `BaseDetector.get_threshold(key, default)` pattern ensures detectors work even without any configured thresholds (falling back to sensible defaults).

## Known Issues

See `TODO.md` for the full list. The most critical issues are:

1. **Login detectors are not wired** -- Three fully implemented detectors (`BruteForceDetector`, `UnusualLoginTimeDetector`, `DeviceChangeDetector`) have no signal connection and are never triggered.
2. **No API endpoints** -- `api_urlpatterns` is empty; no REST API is available for programmatic access to anomaly data.
3. **No templates exist** -- Frontend views reference templates that have not been created yet.
4. **Cache invalidation gap** -- Disabling an `AnomalyType` in the admin does not take effect for up to 5 minutes due to caching in `BaseDetector.get_anomaly_type()`.
5. **Notification scope is not tenant-aware** -- In a multi-tenant deployment, all direction/admin users across all tenants receive notifications for every anomaly regardless of which tenant generated it.
6. **Access control mismatch** -- Professors and accountants receive email notifications about anomalies but cannot access the dashboard or alert views to act on them.

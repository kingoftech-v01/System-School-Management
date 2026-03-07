# Analytics App Architecture

## Overview

The analytics app provides student engagement tracking, course completion monitoring,
learning outcomes analysis, at-risk student identification, and activity logging.
It serves both a template-based frontend (HTML views) and a RESTful API (DRF ViewSets).

---

## Model Relationships

```
+-------------------+        +-------------------+
|  accounts.Student |        |   course.Course   |
|  (OneToOne->User) |        | slug, title, code |
+--------+----------+        | program (FK)      |
         |                    +--------+----------+
         |                             |
         |    +------------------------+-------------------+
         |    |           |            |          |        |
         v    v           v            v          v        v
+------------------+  +-----------------+  +------------------+
| StudentEngagement|  | CourseCompletion |  |   ActivityLog    |
|------------------|  |-----------------|  |------------------|
| student (FK) ----+->| student (FK) ---+->| student (FK)     |
| course (FK,null)-+->| course (FK) ----+->| course (FK,null) |
| date             |  | enrolled_at     |  | activity_type    |
| login_count      |  | started_at      |  | activity_desc    |
| total_time_min   |  | completed_at    |  | url              |
| pages_viewed     |  | total_modules   |  | ip_address       |
| videos_watched   |  | completed_mod   |  | user_agent       |
| docs_downloaded  |  | completion_pct  |  | duration_seconds |
| forum_posts      |  | total_time_spent|  | metadata (JSON)  |
| forum_replies    |  | last_activity_at|  | created_at       |
| questions_asked  |  | is_completed    |  +------------------+
| questions_answrd |  | certificate_iss |
| quizzes_attemptd |  +-----------------+
| quizzes_complted |
| assignments_sub  |       +-------------------+
| engagement_score |       |  LearningOutcome  |
| created_at       |       |-------------------|
| updated_at       |       | course (FK) ------+-> course.Course
+------------------+       | outcome_name      |
                           | description       |
                           | assessment_method  |   choices: quiz, assignment,
                           | target_percentage  |            project, exam,
                           | is_active          |            discussion
                           | created_at         |
                           +--------+----------+
                                    |
                                    | (related_name='measurements')
                                    v
                           +---------------------+
                           | OutcomeMeasurement   |
                           |---------------------|
                           | outcome (FK) -------+-> LearningOutcome
                           | student (FK) -------+-> accounts.Student
                           | score               |
                           | max_score           |
                           | percentage (auto)   |
                           | assessment_name     |
                           | assessed_at         |
                           | meets_target (auto) |
                           +---------------------+

+------------------------------------------------------+
|                   AtRiskStudent                       |
|------------------------------------------------------|
| student (FK) -----------> accounts.Student            |
| course (FK) ------------> course.Course               |
| risk_level                choices: low, medium,       |
|                                    high, critical     |
| risk_score                0-100 scale                 |
| low_engagement (bool)     Risk factor flags           |
| low_attendance (bool)                                 |
| failing_grades (bool)                                 |
| no_recent_activity (bool)                             |
| missing_assignments (int)                             |
| intervention_needed (bool)                            |
| intervention_notes (text)                             |
| contacted_at (datetime)                               |
| contacted_by (FK) ------> accounts.User               |
| is_active (bool)                                      |
| resolved_at (datetime)                                |
| identified_at (auto)                                  |
| updated_at (auto)                                     |
+------------------------------------------------------+
```

### Unique Constraints

| Model              | Unique Together              |
|---------------------|------------------------------|
| StudentEngagement   | `(student, course, date)`    |
| CourseCompletion    | `(student, course)`          |

### Database Indexes

| Model              | Indexed Fields                              |
|---------------------|---------------------------------------------|
| StudentEngagement   | `(student, -date)`                          |
| StudentEngagement   | `(course, -date)`                           |
| StudentEngagement   | `(-engagement_score)`                       |
| CourseCompletion    | `(student, is_completed)`                   |
| CourseCompletion    | `(course, -completion_percentage)`          |
| OutcomeMeasurement  | `(outcome, meets_target)`                  |
| OutcomeMeasurement  | `(student, -assessed_at)`                  |
| ActivityLog         | `(student, -created_at)`                   |
| ActivityLog         | `(course, activity_type, -created_at)`     |
| ActivityLog         | `(activity_type, -created_at)`             |
| AtRiskStudent       | `(course, -risk_score)`                    |
| AtRiskStudent       | `(risk_level, is_active)`                  |

---

## View Access Patterns by Role

The app uses two different authorization mechanisms:

- **Frontend views**: Django decorators (`@login_required`, `@lecturer_required`, `@direction_only`, `@tenant_required`)
- **API views**: DRF permission classes (`CanViewAnalytics`, `CanViewOwnAnalytics`, etc.)

### Decorator Definitions

| Decorator            | Roles Allowed                           |
|----------------------|----------------------------------------|
| `@lecturer_required` | `professor` (+ superuser bypass)       |
| `@direction_only`    | `secretary`, `direction`, `admin` (+ superuser bypass) |
| `@tenant_required`   | Any authenticated user in the current tenant |

### API Permission Definitions

| Permission Class            | Who Gets Access                                    |
|----------------------------|----------------------------------------------------|
| `CanViewAnalytics`         | `is_staff` or `is_teacher` (note: `is_teacher` is not defined on User model -- likely a bug; may rely on `is_lecturer` boolean) |
| `CanViewOwnAnalytics`      | Any authenticated user; object-level checks restrict students to own data |
| `CanManageAtRiskStudents`  | `is_staff` or `is_teacher`                         |
| `CanViewActivityLogs`      | Any authenticated; object-level restricts students to own logs |
| `CanViewLearningOutcomes`  | Any authenticated; object-level checks enrolled courses for students |
| `CanManageLearningOutcomes`| Read: any authenticated; Write: `is_staff` or `is_teacher` |
| `CanExportAnalytics`       | `is_staff` or `is_teacher`                         |

### Per-Role Access Matrix -- Frontend Views

| View                        | student | professor | direction | admin | secretary | parent | prefet | accountant | librarian | registrar |
|-----------------------------|---------|-----------|-----------| ------|-----------|--------|--------|------------|-----------|-----------|
| `analytics_dashboard`       | Own     | Courses   | System    | System| System    | --     | --     | --         | --        | --        |
| `engagement_list`           | --      | All       | All       | All   | --        | --     | --     | --         | --        | --        |
| `engagement_detail`         | Own     | Any       | Any       | Any   | --        | --     | --     | --         | --        | --        |
| `completion_list`           | --      | All       | All       | All   | --        | --     | --     | --         | --        | --        |
| `completion_detail`         | Own     | Any       | Any       | Any   | --        | --     | --     | --         | --        | --        |
| `learning_outcome_list`     | --      | --        | All       | All   | All       | --     | --     | --         | --        | --        |
| `learning_outcome_create`   | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `learning_outcome_detail`   | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `learning_outcome_edit`     | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `learning_outcome_delete`   | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `at_risk_list`              | --      | Courses   | All       | All   | --        | --     | --     | --         | --        | --        |
| `at_risk_detail`            | --      | Courses   | Any       | Any   | --        | --     | --     | --         | --        | --        |
| `at_risk_intervene`         | --      | Courses   | Any       | Any   | --        | --     | --     | --         | --        | --        |
| `at_risk_resolve`           | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `activity_log_list`         | --      | All       | All       | All   | --        | --     | --     | --         | --        | --        |
| `analytics_reports`         | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |
| `export_engagement_csv`     | --      | --        | Yes       | Yes   | Yes       | --     | --     | --         | --        | --        |

Legend:
- **Own**: Can only see own data
- **Courses**: Scoped to courses allocated to the professor
- **All/Any**: Unrestricted access within the tenant
- **System**: System-wide aggregate view
- **--**: No access (redirected)

### Per-Role Access Matrix -- API ViewSets

| ViewSet (Resource)              | student         | professor/staff | direction/admin |
|---------------------------------|-----------------|-----------------|-----------------|
| `StudentEngagementViewSet`      | Own records     | All records     | All records     |
| `  /my_engagement`              | Own 30-day      | Own 30-day      | Own 30-day      |
| `  /trends`                     | --              | Yes             | Yes             |
| `  /recalculate`                | Own queryset    | All             | All             |
| `CourseCompletionViewSet`       | Own records     | All records     | All records     |
| `  /my_progress`                | Own             | Own             | Own             |
| `  /update_progress`            | --              | Yes             | Yes             |
| `LearningOutcomeViewSet`       | Enrolled courses| All (read+write)| All (read+write)|
| `  /achievement_report`         | --              | Yes             | Yes             |
| `OutcomeMeasurementViewSet`    | Own records     | All records     | All records     |
| `ActivityLogViewSet` (ReadOnly) | Own records     | --              | All records     |
| `  /my_activity`                | Own             | Own             | Own             |
| `  /activity_summary`           | --              | Yes             | Yes             |
| `AtRiskStudentViewSet`         | --              | Yes             | Yes             |
| `  /contact`                    | --              | Yes             | Yes             |
| `  /resolve`                    | --              | Yes             | Yes             |
| `  /recalculate_all`            | --              | Yes             | Yes             |
| `  /dashboard`                  | --              | Yes             | Yes             |
| `AnalyticsDashboardViewSet`    | --              | Yes             | Yes             |
| `  /course_dashboard`           | --              | Yes             | Yes             |
| `  /student_dashboard`          | Student's own   | Student's own   | Student's own   |

### Dashboard View Behavior by Role

The `analytics_dashboard` frontend view renders different content based on `request.user.role`:

```
analytics_dashboard(request)
    |
    +-- role == 'student'
    |       Query: StudentEngagement(student=self, last 30 days)
    |       Query: CourseCompletion(student=self)
    |       Shows: recent_engagement, completions, avg_engagement, total_courses
    |
    +-- role == 'lecturer'
    |       Query: CourseAllocation(lecturer=self) -> course_ids
    |       Query: StudentEngagement(course__in=course_ids) aggregated by course
    |       Query: AtRiskStudent(course__in=course_ids, is_active=True).count()
    |       Query: ActivityLog(course__in=course_ids, last 20)
    |       Shows: course_engagement, at_risk_count, recent_activity
    |
    +-- else (direction, admin, secretary, etc.)
            Query: System-wide StudentEngagement aggregates
            Query: AtRiskStudent(is_active=True).count()
            Query: CourseCompletion completion rate
            Shows: total_students, total_courses, avg_engagement,
                   at_risk_count, completion_rate
```

---

## Business Logic Workflows

### 1. Engagement Score Calculation

```
StudentEngagement.calculate_engagement_score()
    |
    +-- Login activity:      min(login_count * 5, 20)           max 20 pts
    +-- Time spent:          min(total_time_minutes / 3, 20)    max 20 pts
    +-- Content engagement:  min(pages*2 + videos*5 + docs*3, 20) max 20 pts
    +-- Interaction:         min(forum_posts*5 + replies*3 + questions*4, 20) max 20 pts
    +-- Assessments:         min(quizzes_completed*7 + assignments*10, 20) max 20 pts
    |
    +-- Total: min(sum, 100) -> saved to engagement_score
```

### 2. Course Completion Progress

```
CourseCompletion.update_progress()
    |
    +-- IF total_modules > 0:
    |       completion_percentage = (completed_modules / total_modules) * 100
    |       IF completion_percentage >= 100 AND NOT is_completed:
    |           is_completed = True
    |           completed_at = now()
    +-- save()
```

### 3. At-Risk Student Identification (Celery Task)

```
identify_at_risk_students()
    |
    +-- FOR each CourseCompletion WHERE is_completed=False:
    |       |
    |       +-- Check engagement (last 7 days avg < 30)
    |       |       Query: StudentEngagement(student, course, date>=week_ago)
    |       |
    |       +-- Check attendance (rate < 75%)
    |       |       Query: attendance.Attendance(student, course) -> present/total
    |       |
    |       +-- Check grades (grade < 60)
    |       |       Query: result.Result(student, course)
    |       |
    |       +-- Check recent activity (none in 14 days)
    |       |       Query: ActivityLog(student, course, created_at>=14d ago)
    |       |
    |       +-- Check missing assignments (past deadline, not submitted)
    |       |       Query: assignment.Assignment(course, deadline<now)
    |       |       Query: assignment.Submission(student, assignment, submitted=True)
    |       |
    |       +-- IF any risk factor OR missing_assignments > 2:
    |               AtRiskStudent.get_or_create(student, course, is_active=True)
    |               AtRiskStudent.calculate_risk_score()
    |
    +-- RETURN counts of new and updated records
```

### 4. Risk Score Calculation

```
AtRiskStudent.calculate_risk_score()
    |
    +-- low_engagement:       +25 pts
    +-- low_attendance:       +25 pts
    +-- failing_grades:       +30 pts
    +-- no_recent_activity:   +15 pts
    +-- missing_assignments:  min(count * 5, 20) pts
    |
    +-- risk_score = min(sum, 100)
    +-- risk_level:
    |       >= 75 -> 'critical'
    |       >= 50 -> 'high'
    |       >= 25 -> 'medium'
    |       <  25 -> 'low'
    +-- save()
```

### 5. At-Risk Intervention Workflow

```
    identify_at_risk_students (Celery)
        |
        v
    AtRiskStudent created (is_active=True, intervention_needed=True)
        |
        v
    send_at_risk_notifications (Celery)
        |   Sends email to course instructors for high/critical risk
        |   students that have NOT been contacted yet
        v
    at_risk_intervene (Frontend) or /contact (API)
        |   Sets: contacted_at, contacted_by, intervention_notes
        v
    at_risk_resolve (Frontend) or /resolve (API)
        |   Sets: is_active=False, resolved_at=now()
        v
    Record archived (is_active=False)
```

### 6. Learning Outcome Measurement (Celery Task)

```
measure_learning_outcomes()
    |
    +-- FOR each active LearningOutcome:
    |       |
    |       +-- IF assessment_method == 'quiz':
    |       |       Query: quiz.Sitting(course, complete=True, last 30 days)
    |       |       Create: OutcomeMeasurement(score, max_score)
    |       |
    |       +-- IF assessment_method == 'assignment':
    |               Query: assignment.Submission(course, graded, last 30 days)
    |               Create: OutcomeMeasurement(score, max_score)
    |
    +-- OutcomeMeasurement.save() auto-calculates:
            percentage = (score / max_score) * 100
            meets_target = percentage >= outcome.target_percentage
```

### 7. OutcomeMeasurement Auto-Calculation (Model save override)

```
OutcomeMeasurement.save()
    |
    +-- IF max_score > 0:
    |       percentage = (score / max_score) * 100
    |       meets_target = percentage >= outcome.target_percentage
    +-- super().save()
```

---

## Celery Tasks

| Task Name                               | Schedule  | Description                                       |
|-----------------------------------------|-----------|---------------------------------------------------|
| `analytics.calculate_daily_engagement`  | Daily     | Creates/updates StudentEngagement for yesterday for all active students |
| `analytics.update_course_completion`    | Daily     | Calls update_progress() on all incomplete CourseCompletion records |
| `analytics.identify_at_risk_students`   | Periodic  | Scans all incomplete enrollments, checks 5 risk factors, creates/updates AtRiskStudent |
| `analytics.send_at_risk_notifications`  | Periodic  | Emails instructors about high/critical uncontacted at-risk students |
| `analytics.generate_engagement_reports` | Weekly    | Aggregates weekly engagement stats, emails ADMINS with top/bottom courses |
| `analytics.cleanup_old_activity_logs`   | Periodic  | Deletes ActivityLog records older than 365 days |
| `analytics.measure_learning_outcomes`   | Periodic  | Creates OutcomeMeasurement records from quiz sittings and assignment submissions |

---

## Dependencies

### Inbound (other apps that reference analytics)

No other app directly imports from or has foreign keys into analytics models.
The analytics app is a leaf consumer of data from other apps.

### Outbound (analytics depends on these apps)

```
analytics
    |
    +-- accounts
    |       Student (FK from: StudentEngagement, CourseCompletion,
    |                         OutcomeMeasurement, ActivityLog, AtRiskStudent)
    |       User (FK from: AtRiskStudent.contacted_by)
    |       Decorators: lecturer_required, direction_only, tenant_required
    |
    +-- course
    |       Course (FK from: StudentEngagement, CourseCompletion,
    |                        LearningOutcome, ActivityLog, AtRiskStudent)
    |       CourseAllocation (queried in views to scope lecturer access)
    |
    +-- attendance  (queried in tasks.identify_at_risk_students)
    |       Attendance model -> attendance rate check
    |
    +-- result  (queried in tasks.identify_at_risk_students)
    |       Result model -> failing grades check
    |
    +-- assignment  (queried in tasks.identify_at_risk_students)
    |       Assignment model -> past-deadline assignments
    |       Submission model -> missing submission check
    |
    +-- quiz  (queried in tasks.measure_learning_outcomes)
    |       Sitting model -> quiz score extraction
    |
    +-- django_ratelimit  (rate limiting on all frontend views)
    |
    +-- rest_framework  (API ViewSets, permissions, serializers)
    |
    +-- django_filters  (DjangoFilterBackend on API ViewSets)
    |
    +-- celery  (shared_task for background processing)
```

### Dependency Diagram

```
 +-------------+   +----------+   +------------+
 | attendance  |   |  result  |   | assignment |
 +------+------+   +----+-----+   +-----+------+
        |               |               |
        +-------+-------+-------+-------+
                |               |
                v               v
          (tasks.py queries these at runtime)
                |
        +-------v--------+
        |   analytics    |<------- celery (tasks)
        +-------+--------+
                |
     +----------+----------+
     |                     |
     v                     v
+---------+          +-----------+
| accounts|          |   course  |
| Student |          |  Course   |
|  User   |          | CourseAll.|
+---------+          +-----------+
                           |
                     +-----+------+
                     |   quiz     |
                     |  Sitting   |
                     +------------+
```

---

## Data Flow Diagrams

### 1. Daily Engagement Pipeline

```
    Celery Beat (midnight)
         |
         v
    calculate_daily_engagement()
         |
         +-- Student.objects.filter(is_alumni=False, is_dropped=False)
         |
         +-- FOR each active student:
         |       StudentEngagement.get_or_create(student, date=yesterday)
         |       engagement.calculate_engagement_score()
         |           -> reads activity fields (login_count, pages_viewed, etc.)
         |           -> writes engagement_score (0-100)
         v
    StudentEngagement records updated
         |
         v
    Frontend dashboard / API reads aggregated data
```

### 2. At-Risk Detection and Intervention Pipeline

```
    Celery Beat
         |
         v
    identify_at_risk_students()
         |
         +-- Reads: CourseCompletion (incomplete)
         |          StudentEngagement (last 7 days)
         |          attendance.Attendance
         |          result.Result
         |          assignment.Assignment + Submission
         |
         +-- Writes: AtRiskStudent (create or update)
         |           -> calculate_risk_score()
         v
    send_at_risk_notifications()
         |
         +-- Reads: AtRiskStudent (high/critical, uncontacted)
         +-- Sends: Email to course.teachers
         v
    Instructor views at_risk_list (filtered by their courses)
         |
         v
    Instructor records intervention (at_risk_intervene)
         |
         +-- Writes: AtRiskStudent.contacted_at, contacted_by, intervention_notes
         v
    Direction resolves (at_risk_resolve)
         |
         +-- Writes: AtRiskStudent.is_active=False, resolved_at=now()
```

### 3. Learning Outcome Measurement Pipeline

```
    Direction creates LearningOutcome
         |  (via learning_outcome_create frontend or LearningOutcomeViewSet API)
         |  Fields: course, outcome_name, assessment_method, target_percentage
         v
    Celery Beat
         |
         v
    measure_learning_outcomes()
         |
         +-- Reads: LearningOutcome (is_active=True)
         |
         +-- IF method='quiz':
         |       Reads: quiz.Sitting (complete, last 30 days)
         |       Writes: OutcomeMeasurement
         |
         +-- IF method='assignment':
         |       Reads: assignment.Submission (graded, last 30 days)
         |       Writes: OutcomeMeasurement
         |
         +-- OutcomeMeasurement.save() auto-calculates:
         |       percentage, meets_target
         v
    Direction views learning_outcome_detail
         |  -> Shows: measurements, success_rate, avg_percentage
         |
    API: /outcomes/{id}/achievement_report
         -> Returns: total_students, successful, success_rate, avg_score
```

### 4. CSV Export Flow

```
    Direction user visits analytics_reports page
         |
         v
    export_engagement_csv (GET with optional query params)
         |
         +-- Reads: StudentEngagement (all, with optional date/course filters)
         |
         +-- Writes: HTTP response with CSV content
         |       Headers: Student, Course, Date, Login Count, Total Time,
         |                Pages Viewed, Videos Watched, Forum Posts,
         |                Forum Replies, Quizzes Completed,
         |                Assignments Submitted, Engagement Score
         v
    Browser downloads engagement_data.csv
```

---

## URL Structure

### Frontend URLs (namespace: `frontend:analytics`)

| URL Pattern                          | View Function             | Name                       |
|--------------------------------------|---------------------------|----------------------------|
| `/analytics/`                        | `analytics_dashboard`     | `analytics_dashboard`      |
| `/analytics/engagement/`             | `engagement_list`         | `engagement_list`          |
| `/analytics/engagement/<id>/`        | `engagement_detail`       | `engagement_detail`        |
| `/analytics/completions/`            | `completion_list`         | `completion_list`          |
| `/analytics/completions/<pk>/`       | `completion_detail`       | `completion_detail`        |
| `/analytics/outcomes/`               | `learning_outcome_list`   | `learning_outcome_list`    |
| `/analytics/outcomes/create/`        | `learning_outcome_create` | `learning_outcome_create`  |
| `/analytics/outcomes/<pk>/`          | `learning_outcome_detail` | `learning_outcome_detail`  |
| `/analytics/outcomes/<pk>/edit/`     | `learning_outcome_edit`   | `learning_outcome_edit`    |
| `/analytics/outcomes/<pk>/delete/`   | `learning_outcome_delete` | `learning_outcome_delete`  |
| `/analytics/at-risk/`               | `at_risk_list`            | `at_risk_list`             |
| `/analytics/at-risk/<pk>/`          | `at_risk_detail`          | `at_risk_detail`           |
| `/analytics/at-risk/<pk>/intervene/`| `at_risk_intervene`       | `at_risk_intervene`        |
| `/analytics/at-risk/<pk>/resolve/`  | `at_risk_resolve`         | `at_risk_resolve`          |
| `/analytics/activity-logs/`         | `activity_log_list`       | `activity_log_list`        |
| `/analytics/reports/`               | `analytics_reports`       | `analytics_reports`        |
| `/analytics/export/engagement/`     | `export_engagement_csv`   | `export_engagement_csv`    |

### API URLs (namespace: `api:v1:analytics`)

| Resource     | Endpoint Base           | ViewSet                        | Extra Actions                        |
|-------------|------------------------|--------------------------------|--------------------------------------|
| engagement  | `/api/analytics/engagement/`   | `StudentEngagementViewSet`  | `my_engagement`, `trends`, `recalculate` |
| completion  | `/api/analytics/completion/`   | `CourseCompletionViewSet`   | `my_progress`, `update_progress`     |
| outcomes    | `/api/analytics/outcomes/`     | `LearningOutcomeViewSet`    | `achievement_report`                 |
| measurements| `/api/analytics/measurements/` | `OutcomeMeasurementViewSet` | --                                   |
| activity-logs| `/api/analytics/activity-logs/`| `ActivityLogViewSet` (read-only) | `my_activity`, `activity_summary` |
| at-risk     | `/api/analytics/at-risk/`      | `AtRiskStudentViewSet`      | `contact`, `resolve`, `recalculate_all`, `dashboard` |
| dashboards  | `/api/analytics/dashboards/`   | `AnalyticsDashboardViewSet` | `course_dashboard`, `student_dashboard` |

---

## Forms

| Form                     | Model/Type     | Fields                                                      | Validation                        |
|--------------------------|----------------|-------------------------------------------------------------|-----------------------------------|
| `DateRangeFilterForm`    | Plain Form     | `start_date`, `end_date`                                   | start < end; max range 365 days   |
| `LearningOutcomeForm`   | ModelForm      | `course`, `outcome_name`, `description`, `assessment_method`, `target_percentage`, `is_active` | target 0-100 |
| `AtRiskInterventionForm` | ModelForm     | `intervention_notes`, `intervention_needed`                 | notes >= 10 chars if provided     |

---

## Admin Configuration

All six models are registered with customized `ModelAdmin` classes:

| Model               | Key Admin Features                                                         |
|----------------------|---------------------------------------------------------------------------|
| `StudentEngagement`  | Date hierarchy on `date`, engagement level color indicator, bulk recalculate action |
| `CourseCompletion`   | Progress bar visualization, mark completed / issue certificates / update progress actions |
| `LearningOutcome`   | Achievement rate display, activate/deactivate actions                      |
| `OutcomeMeasurement`| Performance indicator (meets target or not), date hierarchy on `assessed_at` |
| `ActivityLog`       | Truncated description, duration display, date hierarchy on `created_at`   |
| `AtRiskStudent`     | Risk factor list, risk level visualization with color bar, recalculate/intervene/resolve actions |

---

## Rate Limiting

All frontend views are rate-limited via `@ratelimit(key='user', rate=...)`:

| View Category             | Rate Limit |
|---------------------------|------------|
| Dashboard and list views  | 100/hour   |
| Detail views              | 100/hour   |
| Reports                   | 20/hour    |
| CSV Exports               | 20/hour    |

---

## Notes and Known Issues

1. **`is_teacher` property**: The API permission classes reference `request.user.is_teacher`,
   but this property is not defined on the User model. The User model has `is_lecturer`
   (boolean field) and `role` (CharField). This means API permissions for staff/teacher
   checks may not work as intended for the `is_teacher` branch. The `is_staff` check
   still functions correctly for Django staff users.

2. **No signals.py**: The analytics app has no signal handlers. All data aggregation
   is driven by Celery tasks rather than real-time signals.

3. **`lecturer_required` decorator**: Despite the name, this decorator checks for the
   `professor` role (not a boolean field). It is a legacy wrapper around
   `role_required('professor')`.

4. **Dashboard `else` branch**: The `analytics_dashboard` view treats any role other
   than `student` or `lecturer` as a direction-level user with system-wide access.
   This means parent, prefet, accountant, librarian, and registrar roles all fall
   into the system-wide dashboard view if they can pass the `@login_required` and
   `@tenant_required` checks, even though most other views restrict them.

5. **Activity log population**: The `ActivityLog` model exists but no code in the
   analytics app creates activity log entries. These records are expected to be
   created by other parts of the system (middleware, signals in other apps, or
   external instrumentation).

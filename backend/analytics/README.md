# Analytics App

Student engagement tracking, course completion analysis, learning outcomes measurement, and at-risk student identification.

## Description

The analytics app provides comprehensive data analytics for student engagement, course completion, learning outcomes, and at-risk student management. It supports role-based dashboards showing different metrics for students, lecturers, and direction. The app includes 13 frontend views with filtering, pagination, and date range selection.

## Main Features

- **Analytics Dashboard**: Role-based dashboard (student/lecturer/direction) with key metrics
- **Student Engagement**: Track login count, time spent, content viewed, forum activity, assessments
- **Course Completion**: Track module progress and completion percentages per student
- **Learning Outcomes**: Define outcomes with target percentages and measure student performance
- **At-Risk Students**: Identify at-risk students based on engagement, attendance, grades; record interventions
- **Activity Logs**: Detailed activity tracking (logins, page views, downloads, quiz submissions)
- **Reports**: Analytics reports page for direction

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full access: all views, create learning outcomes, view reports |
| professor/lecturer | View engagement for own courses, manage at-risk students in own courses |
| student | View own engagement data and completion stats |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| StudentEngagement | Automatic | Yes (list + detail) | N/A | No |
| CourseCompletion | Automatic | Yes (list + detail) | N/A | No |
| LearningOutcome | Yes | Yes (list + detail) | No | No |
| AtRiskStudent | Automatic | Yes (list + detail) | Yes (intervene) | No |
| ActivityLog | Automatic | Yes (list) | N/A | No |

## Models

- `StudentEngagement` -- student, course, date, login_count, total_time_minutes, engagement_score
- `CourseCompletion` -- student, course, completion_percentage, is_completed, certificate_issued
- `LearningOutcome` -- course, outcome_name, target_percentage
- `OutcomeMeasurement` -- outcome, student, score
- `AtRiskStudent` -- student, risk_level, risk_score, intervention_needed
- `ActivityLog` -- student, activity_type, details, timestamp

## Dependencies

- `accounts` (Student model, User model, role decorators)
- `course` (Course, CourseAllocation models)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:analytics:<view_name>`
- API: `api:v1:analytics:<resource-name>`

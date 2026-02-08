# Grading App

Rubric-based grading system with criteria management, grade entry using formsets, student gradebook, peer reviews, and grade curve application.

## Description

The grading app provides a comprehensive rubric-based assessment system. Lecturers create rubrics with criteria, enter grades using multi-criteria formsets, and view student gradebooks. The app also supports peer reviews with status tracking and grade curves managed by direction. All views are role-aware with appropriate permission checks.

## Main Features

- **Rubric CRUD**: Full create, list, detail, edit, delete with course association
- **Criteria CRUD**: Add, edit, delete criteria within rubrics
- **Grade Entry**: Enter grades using rubric + criterion formsets for multi-criteria scoring
- **Student Gradebook**: Aggregate statistics (count, average percentage)
- **Peer Reviews**: Review system with status tracking (pending, in_progress, completed)
- **Grade Curves**: Direction-only grade curve management with course association
- **Dashboard**: Role-aware (student sees grades, lecturer sees activity, direction sees stats)

## User Roles

| Role | Permissions |
|------|------------|
| direction | View all rubrics/grades, manage grade curves, system dashboard |
| lecturer | CRUD own rubrics/criteria, enter grades, view gradebook |
| student | View own gradebook, submit peer reviews |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| GradingRubric | Yes | Yes (list + detail) | Yes | Yes |
| RubricCriterion | Yes | Yes (via rubric) | Yes | Yes |
| RubricGrade | Yes | Yes (list + detail) | No | No |
| PeerReview | Yes (submit) | Yes (list) | No | No |
| GradeCurve | Yes | Yes (list + detail) | No | No |

## Models

- `GradingRubric` -- name, course FK, created_by FK, is_active, max_score
- `RubricCriterion` -- rubric FK, name, description, max_points, weight
- `RubricGrade` -- rubric FK, student FK, graded_by FK, total_score, percentage
- `CriterionGrade` -- rubric_grade FK, criterion FK, score, feedback
- `PeerReview` -- reviewer FK, reviewee FK, course FK, score, feedback, status
- `GradeCurve` -- course FK, applied_by FK, curve_type, adjustment_value, is_active

## Known Issues

- Duplicate `@login_required` decorator on `grade_entry_detail` (line 395-396 in views_frontend.py)

## Dependencies

- `accounts` (Student model)
- `course` (Course model)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:grading:<view_name>`
- API: `api:v1:grading:<resource-name>`

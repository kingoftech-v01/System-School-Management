# Events App

School event management for scheduling exams, holidays, meetings, activities, ceremonies, and deadlines with role-based audience targeting.

## Description

The events app manages school-wide events with type classification and target audience filtering. Direction users can create events targeting specific audiences (all, students, parents, staff), and the system supports Celery-based email reminders for next-day events.

## Main Features

- **Event Creation**: Direction creates events with type, dates, location, and audience
- **Event Listing**: Role-based visibility (students see student/all events, parents see parent/all, etc.)
- **Event Detail**: Full event information display
- **Email Reminders**: Celery task sends reminders for next-day events

## User Roles

| Role | Permissions |
|------|------------|
| direction | Create events, view all events |
| professor | View staff + all events |
| student | View student + all events |
| parent | View parent + all events |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Event | Yes | Yes (list + detail) | No | No |

## Models

- `Event` -- tenant FK, title, description, event_type (exam/holiday/meeting/activity/ceremony/deadline), start_date, end_date, location, target_audience (all/students/parents/staff), send_reminder

## Dependencies

- `core` (School model for tenant)
- `django-ratelimit`
- `celery` (for reminder tasks)

## URL Namespace

- Frontend: `frontend:events:<view_name>`
- API: `api:v1:events:<resource-name>`

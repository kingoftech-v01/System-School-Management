# Course App

Academic program, course, allocation, and resource management.

## Description

The course app manages the academic structure: programs (departments), courses within programs, course-to-lecturer allocation, student course registration and drop, and educational resources (file uploads and video tutorials). It provides complete CRUD operations for all entities with filtering and pagination.

## Main Features

- **Programs**: Full CRUD with filtering (list, add, detail, edit, delete)
- **Courses**: Full CRUD within programs (add, detail, edit, delete) with slug-based URLs
- **Course Allocation**: Assign courses to lecturers, edit allocations, deallocate
- **Course Registration**: Students register for and drop courses in current semester
- **File Uploads**: Upload, edit, delete course documentation files
- **Video Tutorials**: Upload, view, edit, delete course video content
- **My Courses**: Role-aware view showing lecturer's assigned courses or student's taken courses

## User Roles

| Role | Permissions |
|------|------------|
| admin/lecturer | Full CRUD on programs, courses, allocations, files, videos |
| student | Register/drop courses, view course details, access resources |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Program | Yes | Yes (list + detail) | Yes | Yes |
| Course | Yes | Yes (detail) | Yes | Yes |
| CourseAllocation | Yes | Yes (list) | Yes | Yes (deallocate) |
| Upload (file) | Yes | Yes (via course) | Yes | Yes |
| UploadVideo | Yes | Yes (single + via course) | Yes | Yes |

## Models

- `Program` -- title, summary
- `Course` -- slug, title, code, credit, summary, program FK, level, year, semester, is_elective
- `CourseAllocation` -- lecturer FK, courses M2M
- `Upload` -- title, course FK, file (validated extensions)
- `UploadVideo` -- title, slug, course FK, video, summary
- `CourseOffer` -- semester course offerings by department head

## Dependencies

- `accounts` (Student model for registration, role decorators)
- `core` (Semester for registration filtering)
- `result` (TakenCourse for registration tracking)
- `django-filter`

## URL Namespace

- Frontend: `frontend:course:<view_name>`
- API: `api:v1:course:<resource-name>`

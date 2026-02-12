# Course App

Academic program, course, allocation, and resource management.

## Description

The course app manages the academic structure: programs (departments), courses within programs, course-to-lecturer allocation, student course registration and drop, and educational resources (file uploads and video tutorials). It provides complete CRUD operations for all entities with filtering, pagination, i18n support via modeltranslation, and activity logging. Both legacy views (views.py) and modern frontend views (views_frontend.py) are available with different permission models.

## Main Features

- **Programs**: Full CRUD with filtering (list, add, detail, edit, delete) and search
- **Courses**: Full CRUD within programs (add, detail, edit, delete) with slug-based URLs
- **Course Allocation**: Assign courses to lecturers via checkbox M2M, edit allocations, deallocate
- **Course Registration**: Students register for and drop courses filtered by current semester/level/program
- **File Uploads**: Upload, edit, delete course documentation (pdf, docx, xls, ppt, zip, rar, 7zip)
- **Video Tutorials**: Upload, view, edit, delete course video content (mp4, mkv, wmv, 3gp, avi, mp3)
- **My Courses**: Role-aware view showing lecturer's assigned courses or student's taken courses
- **All Courses**: Cross-program course listing with search and pagination
- **Activity Logging**: All model CRUD operations logged to ActivityLog via signals

## User Roles

| Role | Permissions |
|------|------------|
| admin | Full CRUD on programs, courses, allocations, files, videos |
| direction | Full CRUD on programs, courses, allocations (via @direction_only) |
| professor | CRUD on files/videos for allocated courses, view allocations |
| student | Register/drop courses, view course details, access resources |
| parent | View course info (read-only via parent portal) |
| prefet | No direct access |
| accountant | No direct access |
| secretary | No direct access |
| librarian | No direct access |
| registrar | No direct access |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Program | Yes | Yes (list + detail) | Yes | Yes |
| Course | Yes | Yes (detail + all list) | Yes | Yes |
| CourseAllocation | Yes | Yes (list) | Yes | Yes (deallocate) |
| Upload (file) | Yes | Yes (via course) | Yes | Yes |
| UploadVideo | Yes | Yes (single + via course) | Yes | Yes |

## Models

- `Program` -- title, summary; custom manager with `search()` and activity logging
- `Course` -- slug (auto-generated), title, code, credit, summary, program FK, level, year, semester, is_elective; `current_semester` property
- `CourseAllocation` -- lecturer FK (User), courses M2M (Course), session FK (optional)
- `Upload` -- title, course FK, file (validated extensions: pdf, docx, xls, ppt, zip, rar, 7zip)
- `UploadVideo` -- title, slug (auto-generated), course FK, video, summary
- `CourseOffer` -- dep_head FK (stub model for department head course offerings)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | /api/v1/course/programs/ | List/create programs |
| GET/PUT/DELETE | /api/v1/course/programs/{id}/ | Program detail |
| GET | /api/v1/course/programs/{id}/courses/ | Program's courses |
| GET/POST | /api/v1/course/courses/ | List/create courses |
| GET/PUT/DELETE | /api/v1/course/courses/{slug}/ | Course detail (by slug) |
| GET | /api/v1/course/courses/{slug}/documentation/ | Course files |
| GET | /api/v1/course/courses/{slug}/videos/ | Course videos |
| GET | /api/v1/course/courses/{slug}/lecturers/ | Course lecturers |
| GET/POST | /api/v1/course/allocations/ | Allocation list/create |
| POST | /api/v1/course/allocations/{id}/deallocate/ | Deallocate |
| GET/POST | /api/v1/course/uploads/ | File uploads |
| GET/POST | /api/v1/course/videos/ | Video uploads |
| GET | /api/v1/course/registration/available_courses/ | Available courses for student |
| GET | /api/v1/course/registration/registered_courses/ | Student's registered courses |
| POST | /api/v1/course/registration/register/ | Bulk register courses |
| POST | /api/v1/course/registration/drop/ | Bulk drop courses |

## Dependencies

- `accounts` (User, Student models for registration, role decorators)
- `core` (Semester for registration filtering, ActivityLog for audit)
- `result` (TakenCourse for registration tracking)
- `django-filter`, `modeltranslation`

## URL Namespace

- Frontend: `frontend:course:<view_name>`
- API: `api:v1:course:<resource-name>`

## File Structure

```text
course/
  models.py              -- Program, Course, CourseAllocation, Upload, UploadVideo, CourseOffer
  views.py               -- Legacy views with @lecturer_required decorator
  views_frontend.py      -- Modern views with @direction_only decorator
  views_api.py           -- DRF ViewSets (Program, Course, Allocation, Upload, Video, Registration)
  urls.py                -- Frontend + API URL routing
  serializers.py         -- DRF serializers with dynamic file URLs
  forms.py               -- Program, Course, Allocation, Upload forms
  filters.py             -- ProgramFilter, CourseAllocationFilter (django-filter)
  decorators.py          -- Course calendar/add-drop check
  admin.py               -- TranslationAdmin for Program, Course, Upload
  translation.py         -- modeltranslation config
  tests/                 -- Test suite
```

# Course - Architecture

## Overview

The course app manages the academic structure of the system: programs (departments), courses, lecturer-course allocations, student registration, and educational resources. It is a central dependency for many other apps (result, quiz, grading, scheduling, filieres) and relies on accounts for user identity and core for academic periods.

## Models & Relationships

### Entity-Relationship Summary

```text
Program ──1:N──> Course
Course ──N:M──> User (via CourseAllocation)
Course ──1:N──> Upload
Course ──1:N──> UploadVideo
CourseAllocation ──N:1──> User (lecturer)
CourseAllocation ──N:M──> Course
CourseOffer ──N:1──> User (dep_head)
```

### Model Details

#### Program

- **Purpose**: Academic department or program of study
- **Key Fields**: title, summary
- **Managers**: `ProgramManager` with `search()` method
- **Signals**: `post_save` and `post_delete` log to ActivityLog

#### Course

- **Purpose**: Individual academic course within a program
- **Key Fields**: slug (auto), title, code, credit, summary, program FK, level (100-600), year (1-6), semester (First/Second), is_elective
- **Relationships**: FK to Program
- **Business Rules**:
  - Slug auto-generated from title via `pre_save` signal using `unique_slug_generator`
  - `current_semester` property returns course's semester display
- **Signals**: `post_save` and `post_delete` log to ActivityLog

#### CourseAllocation

- **Purpose**: Links lecturers to courses they teach
- **Key Fields**: lecturer FK (User), courses M2M (Course), session FK (Session, optional)
- **Business Rules**: A lecturer can be allocated multiple courses; courses can have multiple lecturers

#### Upload

- **Purpose**: Course documentation files
- **Key Fields**: title, course FK, file (FileField with extension validation)
- **Business Rules**: Allowed extensions: pdf, docx, doc, xls, xlsx, ppt, pptx, zip, rar, 7zip

#### UploadVideo

- **Purpose**: Course video tutorials
- **Key Fields**: title, slug (auto), course FK, video (FileField), summary
- **Business Rules**: Allowed formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3

#### CourseOffer

- **Purpose**: Department head course offerings (stub model)
- **Key Fields**: dep_head FK (User)

## View Logic Flow

### Frontend Views (`views_frontend.py`)

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| `ProgramFilterView` | GET | Yes | all | Program list with filtering |
| `program_add` | GET/POST | Yes | direction | Create program |
| `program_detail` | GET | Yes | all | Program detail + courses |
| `program_edit` | GET/POST | Yes | direction | Edit program |
| `program_delete` | POST | Yes | direction | Delete program |
| `course_single` | GET | Yes | all | Course detail page |
| `course_add` | GET/POST | Yes | direction | Add course to program |
| `course_edit` | GET/POST | Yes | direction | Edit course |
| `course_delete` | POST | Yes | direction | Delete course |
| `CourseAllocationFormView` | GET/POST | Yes | direction | Allocate courses |
| `CourseAllocationFilterView` | GET | Yes | direction | List allocations |
| `course_registration` | GET/POST | Yes | student | Register for courses |
| `course_drop` | POST | Yes | student | Drop a course |
| `user_course_list` | GET | Yes | all | My courses (role-aware) |
| `course_list_all` | GET | Yes | all | All courses with search |
| `program_search` | GET | Yes | all | Program search with pagination |
| File/Video CRUD | GET/POST | Yes | lecturer+ | Upload/edit/delete resources |

### API Views (`views_api.py`)

| ViewSet | Methods | Auth | Description |
|---------|---------|------|-------------|
| `ProgramViewSet` | CRUD + `courses` action | Yes | Program management |
| `CourseViewSet` | CRUD + `documentation`, `videos`, `lecturers` | Yes | Course management (slug lookup) |
| `CourseAllocationViewSet` | CRUD + `deallocate` | Yes | Allocation management |
| `UploadViewSet` | CRUD + `download` | Yes | File management |
| `UploadVideoViewSet` | CRUD | Yes | Video management |
| `CourseRegistrationViewSet` | Custom actions | Yes | `available_courses`, `registered_courses`, `register`, `drop` |

### Key Patterns

- Dual view architecture: `views.py` (legacy, @lecturer_required) and `views_frontend.py` (modern, @direction_only)
- Lecturer authorization checks: views verify lecturer is allocated to course before allowing file/video modifications
- Slug-based URLs for courses and videos (auto-generated via signals)
- Activity logging on all model create/update/delete operations

## Business Logic

### Core Workflows

#### Course Registration

1. Student visits `/course/registration/`
2. View filters courses by student's program, level, and current semester
3. Shows courses not yet registered (excludes existing TakenCourse entries)
4. Student selects courses and submits
5. TakenCourse entries created for each selected course

#### Course Drop

1. Student visits registration page
2. Selects course to drop
3. TakenCourse entry deleted

#### File Upload

1. Lecturer navigates to course detail
2. System verifies lecturer is allocated to the course
3. Lecturer uploads file (extension validated)
4. Upload entry created linked to course

### Validation Rules

- File upload extensions: pdf, docx, doc, xls, xlsx, ppt, pptx, zip, rar, 7zip
- Video upload formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3
- Course slug uniqueness enforced via `unique_slug_generator`

## Inter-App Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
|-----|----------------------|---------|
| `accounts` | User, Student, role decorators | Lecturer allocation, student registration |
| `core` | Semester, Session, ActivityLog, utils | Registration filtering, audit logging, slug generation |
| `result` | TakenCourse | Registration tracking (check existing registrations) |

### Apps That Depend On This App

| App | What They Use | Purpose |
|-----|--------------|---------|
| `accounts` | Program | Student.program FK |
| `result` | Course | TakenCourse.course FK |
| `grading` | Course | Rubric-based grading |
| `quiz` | Course | Quiz association |
| `filieres` | Course | FiliereSubject.subject FK |
| `scheduling` | Course | Schedule entry course reference |
| `certificates` | Course | Certificate course reference |
| `analytics` | Course, CourseAllocation | Engagement tracking |
| `notes` | Course | Professor notes |
| `search` | Program, Course | Cross-model search |

### Dependency Diagram

```text
accounts (User, Student) ──> [COURSE] <── core (Semester, ActivityLog)
result (TakenCourse) ────────>   │
                                 │
                                 ▼
              result, grading, quiz, filieres,
              scheduling, certificates, analytics,
              notes, search
```

## Data Flow

### Course Registration Flow

```text
Student Request (POST /course/registration/)
    │
    ▼
views_frontend.py::course_registration
    │
    ├── Filter by: student.program + student.level + current_semester
    ├── Exclude: already registered (TakenCourse)
    │
    ▼
For each selected course:
    TakenCourse.objects.create(student=student, course=course)
    │
    ▼
Redirect to user_course_list
```

## Technical Notes

- `decorators.py` executes a module-level database query (`CourseSetting.objects.filter(add_drop=True)`) at import time -- can cause import errors if the table doesn't exist
- Dual view files (views.py and views_frontend.py) exist with overlapping functionality but different permission models
- All model signals defined inline in models.py using `@receiver` decorator
- Course and UploadVideo slugs auto-generated via `pre_save` signal using `unique_slug_generator` from `core.utils`
- Translation support via modeltranslation for Program, Course, and Upload models

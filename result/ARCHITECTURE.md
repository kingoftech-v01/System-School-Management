# Result - Architecture

## Overview

The result app is the grading and academic performance engine of the system. It handles score entry by lecturers, automatic grade/GPA/CGPA calculation, grade appeal workflows, immutable audit trails, configurable grade weights, and PDF document generation. It depends heavily on `accounts` (Student), `course` (Course), and `core` (Session, Semester) and is a leaf-level app with no downstream dependents.

## Models & Relationships

### Entity-Relationship Summary

```
Student (accounts) ──1:N──> TakenCourse
Course (course) ──1:N──> TakenCourse
Student ──1:N──> Result
Student ──1:N──> GradeAppeal
Student ──1:N──> Transcript
TakenCourse ──1:N──> GradeAppeal
TakenCourse ──1:N──> GradeHistory
Course ──1:1──> GradeComponentWeight
Program (course) ──1:1──> GradeComponentWeight
Semester (core) ──1:N──> Transcript (start/end)
User (accounts) ──1:N──> GradeAppeal (reviewed_by)
User ──1:N──> GradeHistory (changed_by)
User ──1:N──> Transcript (generated_by)
```

### Model Details

#### TakenCourse
- **Purpose**: Records a student's enrollment and scores in a specific course
- **Key Fields**: assignment, mid_exam, quiz, attendance, final_exam (input); total, grade, point, comment (auto-computed)
- **Relationships**: student FK -> Student, course FK -> Course
- **Business Rules**:
  - `save()` override: auto-computes total -> grade -> point -> comment
  - Grade derived from GRADE_BOUNDARIES lookup (90->A+, 85->A, ..., 0->F)
  - Point = course.credit * GRADE_POINT_MAPPING[grade]
  - `calculate_gpa()`: sum(points) / sum(credits) for current semester
  - `calculate_cgpa()`: sum(points) / sum(credits) across all semesters

#### Result
- **Purpose**: Stores computed GPA/CGPA per student per semester
- **Key Fields**: gpa, cgpa, semester (CharField with choices), session, level
- **Relationships**: student FK -> Student
- **Business Rules**: Created/updated automatically during score entry

#### GradeComponentWeight
- **Purpose**: Configurable weights for grade components (must sum to 100)
- **Key Fields**: assignment_weight, mid_exam_weight, quiz_weight, attendance_weight, final_exam_weight (all Decimal, default: 10/20/10/10/50)
- **Relationships**: course FK -> Course (OneToOne) OR program FK -> Program (OneToOne)
- **Business Rules**: `clean()` validates weights sum to exactly 100; `save()` calls `full_clean()`

#### GradeAppeal
- **Purpose**: Student-initiated grade review workflow
- **Key Fields**: reason, supporting_documents (FileField), status, review_notes, decision
- **Relationships**: taken_course FK -> TakenCourse, student FK -> Student, reviewed_by FK -> User
- **Business Rules**:
  - Status flow: submitted -> under_review -> approved/rejected -> resolved
  - `approve(reviewer, notes)` and `reject(reviewer, notes)` methods set status + timestamp
  - One active appeal per student per course enforced in view

#### GradeHistory
- **Purpose**: Immutable audit trail for every grade change
- **Key Fields**: old_* and new_* for all 7 fields (assignment through grade), changed_by, change_reason
- **Relationships**: taken_course FK -> TakenCourse, changed_by FK -> User
- **Business Rules**: Read-only (created during score entry, never updated)

#### Transcript
- **Purpose**: Generated PDF transcript storage and certification
- **Key Fields**: transcript_type (official/unofficial/partial), pdf_file (FileField), is_certified, certification_number (unique)
- **Relationships**: student FK -> Student, start_semester/end_semester FKs -> Semester, generated_by FK -> User

## View Logic Flow

### Frontend Views

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| add_score | GET | login + lecturer | lecturer | Select course for score entry |
| add_score_for | GET/POST | login + lecturer | lecturer | Enter scores for students in course; creates GradeHistory |
| grade_result | GET | login + student | student | View grades with semester breakdown |
| assessment_result | GET | login + student | student | View assessment breakdowns |
| result_sheet_pdf_view | GET | login + lecturer | lecturer | Generate PDF result sheet for course |
| course_registration_form | GET | login + student | student | Generate PDF course registration form |
| grade_appeal_create | GET/POST | login + student | student | Submit grade appeal for a taken course |
| grade_appeal_list | GET | login | student/lecturer/direction | List appeals (role-scoped) |
| grade_appeal_detail | GET | login | student (own only)/lecturer/direction | View appeal detail |

### API Views

| ViewSet | Methods | Auth | Roles | Description |
|---------|---------|------|-------|-------------|
| TakenCourseViewSet | CRUD + my_grades + by_semester | IsAuthenticated | all | Grade management |
| ResultViewSet | CRUD + my_results + calculate_gpa | IsAuthenticated | all | GPA/result queries |
| GradeComponentWeightViewSet | CRUD | IsAuthenticated | all | Weight configuration |
| GradeAppealViewSet | CRUD + my_appeals + approve + reject | IsAuthenticated | student write; lecturer approve/reject | Appeal workflow |
| GradeHistoryViewSet | Read-only | IsAuthenticated | all | Audit trail |
| TranscriptViewSet | CRUD + my_transcripts + certify | IsAuthenticated | admin certify | Transcript management |

### Key Patterns

- **Decorator-based auth**: `@lecturer_required` for score entry, `@student_required` for grade views
- **Role-scoped queries**: `grade_appeal_list` checks user.role to filter appeals (student -> own, lecturer -> allocated courses, direction/admin -> all)
- **Auto-computation on save**: TakenCourse.save() computes total, grade, point, comment
- **Audit trail**: Every POST to `add_score_for` creates a GradeHistory entry

## Business Logic

### Core Workflows

#### 1. Score Entry (Lecturer)
1. Lecturer selects course from allocated courses (`add_score`)
2. System verifies lecturer is allocated to course
3. Lecturer enters scores for each student (5 fields per student)
4. For each student in POST data:
   a. Capture old values for audit
   b. Set new scores on TakenCourse
   c. Auto-compute total, grade, point, comment via model methods
   d. Save TakenCourse (triggers auto-compute in save())
   e. Create GradeHistory record (old -> new)
   f. Calculate GPA and CGPA
   g. Create or update Result record

#### 2. Grade Calculation

```
total = assignment + mid_exam + quiz + attendance + final_exam
grade = GRADE_BOUNDARIES lookup (90->A+, 85->A, ..., 0->F)
point = course.credit * GRADE_POINT_MAPPING[grade]
comment = PASS if grade not in [F, NG] else FAIL

GPA = sum(point for courses in current semester) / sum(credit for courses)
CGPA = sum(point for all courses) / sum(credit for all courses)
```

#### 3. Grade Appeal Workflow
1. Student clicks "Appeal" on grade result -> `grade_appeal_create`
2. System checks for existing active appeal (submitted/under_review)
3. Student fills reason + optional supporting documents
4. Appeal saved with status='submitted'
5. Lecturer/direction views appeal list -> filtered by role
6. Reviewer approves/rejects via API action (sets reviewed_by, review_notes, reviewed_at)
7. Appeal resolved -> resolved_at timestamp set

#### 4. PDF Generation (Result Sheet)
1. Lecturer requests PDF for a course
2. System verifies lecturer allocation
3. ReportLab generates PDF with school branding, course info, student table
4. PDF saved to `MEDIA_ROOT/result_sheet/` and served inline

### Validation Rules

- Score fields: Decimal 0.00 to 100.00 (validated in form)
- Grade weights: Must sum to exactly 100% (model + form validation)
- Grade appeal: One active appeal per student per course (view-level check)
- Transcript certification_number: Unique across all transcripts

### Grade Boundaries

| Min Score | Grade | Point | Comment |
|-----------|-------|-------|---------|
| 90 | A+ | 4.0 | PASS |
| 85 | A | 4.0 | PASS |
| 80 | A- | 3.75 | PASS |
| 75 | B+ | 3.5 | PASS |
| 70 | B | 3.0 | PASS |
| 65 | B- | 2.75 | PASS |
| 60 | C+ | 2.5 | PASS |
| 55 | C | 2.0 | PASS |
| 50 | C- | 1.75 | PASS |
| 45 | D | 1.0 | PASS |
| 0 | F | 0.0 | FAIL |

## Inter-App Dependencies

### Depends On

| App | Models Used | Purpose |
|-----|------------|---------|
| accounts | Student | FK on TakenCourse, Result, GradeAppeal, Transcript |
| accounts | User | FK on GradeAppeal (reviewed_by), GradeHistory (changed_by), Transcript (generated_by) |
| accounts | decorators | lecturer_required, student_required |
| course | Course | FK on TakenCourse; allocated_course relation for lecturer verification |
| course | Program | FK on GradeComponentWeight |
| core | Session, Semester | Session/semester filtering; Result fields; Transcript semester range |
| core | School | School name for PDF generation |

### Depended On By

| App | What They Use | Purpose |
|-----|--------------|---------|
| (none currently) | -- | Leaf-level app |

### Dependency Diagram

```
accounts.Student ──────────┐
accounts.User ─────────────┤
                           v
core.Session ──────> [result] <── course.Course
core.Semester ─────/          \── course.Program
core.School ──────/
```

## Data Flow

### Score Entry Flow

```
Lecturer -> add_score (select course)
         -> add_score_for (GET: show students + scores)
         -> add_score_for (POST: process scores)
            |-- For each student:
            |   |-- Capture old values
            |   |-- Set new scores
            |   |-- TakenCourse.save() -> auto-compute total/grade/point/comment
            |   |-- Create GradeHistory (audit)
            |   |-- Calculate GPA/CGPA
            |   |-- Create/update Result
            |-- Redirect to same page with success message
```

### Grade Appeal Flow

```
Student -> grade_appeal_create (POST: submit appeal)
        -> GradeAppeal created (status=submitted)
        -> Lecturer/Direction -> grade_appeal_list (filtered by role)
        -> API: POST /appeals/{id}/approve/ or /reject/
        -> GradeAppeal updated (status, reviewed_by, review_notes, reviewed_at)
```

## Technical Notes

- **Custom save() on TakenCourse**: All derived fields (total, grade, point, comment) are auto-computed on every save, making them read-only in practice despite being model fields
- **ReportLab PDF generation**: Both `result_sheet_pdf_view` and `course_registration_form` generate PDFs on-the-fly and serve them inline; files are also saved to disk
- **get_full_name as property**: Used correctly in frontend views (e.g., `request.user.get_full_name`) but incorrectly in API view `calculate_gpa` as `get_full_name()` with parentheses
- **No tenant filtering in API**: API ViewSets query all records globally without tenant filtering -- security concern for multi-tenant deployment
- **Grade boundaries hardcoded**: GRADE_BOUNDARIES and GRADE_POINT_MAPPING are module-level constants in models.py, not configurable per tenant
- **Legacy score entry**: `add_score_for` POST handler processes form data manually (not via Django form) -- iterates over POST keys to extract student scores

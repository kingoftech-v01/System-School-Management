# Result App

Student result management with score entry by lecturers, automatic GPA/CGPA calculation, grade derivation, grade appeals workflow, audit trail, and PDF result sheet generation.

## Description

The result app handles student grades and results. Lecturers enter scores for allocated courses (assignment, mid_exam, quiz, attendance, final_exam), and the system automatically calculates total, grade, point, comment, GPA, and CGPA. Students can view their grade results with semester-wise breakdown and submit grade appeals. The app generates PDF result sheets and course registration forms using ReportLab, maintains an immutable audit trail of all grade changes, and supports configurable grade component weights.

## Main Features

- **Score Entry**: Lecturer enters scores for allocated courses in current semester
- **Bulk Entry**: Multi-field score entry per course (assignment, mid_exam, quiz, attendance, final_exam)
- **Auto Calculation**: Total, grade, point, comment, GPA, and CGPA derived automatically on save
- **Grade Results**: Student views grades with semester-wise breakdown
- **Assessment Results**: Student views assessment breakdowns
- **Grade Appeals**: Students submit appeals; lecturers/direction review and approve/reject
- **Audit Trail**: Immutable GradeHistory records every grade change with before/after values
- **Configurable Weights**: GradeComponentWeight allows per-course or per-program weight customization
- **PDF Result Sheet**: Lecturer generates PDF result sheet per course
- **PDF Registration Form**: Student generates course registration form PDF
- **REST API**: Full CRUD API with DRF ViewSets for all models

## User Roles

| Role | Permissions |
|------|------------|
| professor (lecturer) | Enter scores for allocated courses, generate PDF result sheets, review grade appeals |
| student | View own grades/assessments, generate registration form PDF, submit grade appeals |
| direction | View all grade appeals, full access to results |
| admin | Full access via API (superuser), certify transcripts |
| parent | View student grades (via parent portal, indirect) |
| prefet | No direct access |
| accountant | No direct access |
| secretary | No direct access |
| librarian | No direct access |
| registrar | Certify transcripts (via API) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| TakenCourse (scores) | Yes (via entry) | Yes (grade results) | Yes (re-entry) | No |
| Result (GPA) | Automatic | Yes | Automatic | No |
| GradeComponentWeight | Yes (API) | Yes | Yes | Yes |
| GradeAppeal | Yes (student) | Yes (list + detail) | Yes (review) | No |
| GradeHistory | Automatic | Yes (read-only) | No | No |
| Transcript | Yes (API) | Yes | Yes (certify) | Yes |

## Models

- `TakenCourse` -- student FK (Student), course FK (Course), assignment, mid_exam, quiz, attendance, final_exam, total (auto), grade (auto), point (auto), comment (auto); custom save() computes all derived fields
- `Result` -- student FK, gpa, cgpa, semester, session, level
- `GradeComponentWeight` -- course FK (OneToOne) or program FK (OneToOne), assignment_weight, mid_exam_weight, quiz_weight, attendance_weight, final_exam_weight; weights must sum to 100
- `GradeAppeal` -- taken_course FK, student FK, reason, supporting_documents, status (submitted/under_review/approved/rejected/resolved), reviewed_by FK, review_notes, decision
- `GradeHistory` -- taken_course FK, old_* and new_* for all 7 grade fields, changed_by FK, change_reason, changed_at
- `Transcript` -- student FK, transcript_type (official/unofficial/partial), start_semester FK, end_semester FK, pdf_file, is_certified, certification_number

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/taken-courses/` | List/create taken courses |
| GET/PUT/PATCH | `/api/taken-courses/{id}/` | Taken course detail/update |
| GET | `/api/taken-courses/my_grades/` | Current student's grades |
| GET | `/api/taken-courses/by_semester/?semester_id=` | Courses by semester |
| GET/POST | `/api/results/` | List/create results |
| GET | `/api/results/my_results/` | Current student's results |
| GET | `/api/results/calculate_gpa/` | Calculate GPA/CGPA for student |
| GET/POST | `/api/grade-weights/` | List/create grade weights |
| GET/PUT/DELETE | `/api/grade-weights/{id}/` | Weight detail/update/delete |
| GET/POST | `/api/appeals/` | List/create grade appeals |
| GET | `/api/appeals/my_appeals/` | Current student's appeals |
| POST | `/api/appeals/{id}/approve/` | Approve appeal (lecturer/admin) |
| POST | `/api/appeals/{id}/reject/` | Reject appeal (lecturer/admin) |
| GET | `/api/grade-history/` | List grade history (read-only) |
| GET/POST | `/api/transcripts/` | List/create transcripts |
| GET | `/api/transcripts/my_transcripts/` | Current student's transcripts |
| POST | `/api/transcripts/{id}/certify/` | Certify transcript (admin) |

## Known Issues

- Bare `except:` clauses in API views (`my_grades`, `my_results`, etc.) swallow all exceptions
- Hardcoded "COMPUTER SICENCE & ENGINEERING" (typo) in `course_registration_form` certification text
- `get_full_name` used as property (correct) but API `calculate_gpa` calls it as method `get_full_name()` (line 161 views_api.py)
- Commented-out code blocks in `add_score_for` and `result_sheet_pdf_view`

## Dependencies

- `reportlab` (PDF generation)
- `core` (Session, Semester, School models)
- `course` (Course model)
- `accounts` (Student model; `lecturer_required`, `student_required` decorators)
- `django-filter` (API filtering)
- `djangorestframework` (API views)

## Configuration

- `settings.SEMESTER_CHOICES` -- used by Result model for semester field
- `settings.LEVEL_CHOICES` -- used by Result model for level field
- `settings.FIRST` / `settings.SECOND` -- semester string constants used in PDF generation
- `settings.STATICFILES_DIRS[0]` -- used for brand logo in PDF
- `settings.MEDIA_ROOT` -- used for PDF file storage

## URL Namespace

- Frontend: `frontend:result:<view_name>`
- API: `api:v1:result:<resource-name>`

## File Structure

```
result/
  __init__.py
  admin.py
  apps.py
  forms.py              # 8 forms: TakenCourseForm, ScoreEntryForm, ResultForm, GradeComponentWeightForm, GradeAppealForm, GradeAppealReviewForm, TranscriptRequestForm, BulkScoreUploadForm
  models.py             # 6 models: TakenCourse, Result, GradeComponentWeight, GradeAppeal, GradeHistory, Transcript
  serializers.py        # DRF serializers for all models
  views.py              # Legacy views (may be empty/deprecated)
  views_api.py          # 6 ViewSets: TakenCourse, Result, GradeComponentWeight, GradeAppeal, GradeHistory, Transcript
  views_frontend.py     # 8 frontend views: score entry, grade results, PDF generation, grade appeals
  urls.py               # Frontend + API URL routing with DRF router
  README.md
  TODO.md
```

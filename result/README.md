# Result App

Student result management with score entry by lecturers, automatic GPA/CGPA calculation, grade derivation, and PDF result sheet generation.

## Description

The result app handles student grades and results. Lecturers enter scores for allocated courses (assignment, mid_exam, quiz, attendance, final_exam), and the system automatically calculates total, grade, point, comment, GPA, and CGPA. Students can view their grade results with semester-wise breakdown. The app also generates PDF result sheets and course registration forms using ReportLab.

## Main Features

- **Score Entry**: Lecturer enters scores for allocated courses in current semester
- **Bulk Entry**: Multi-field score entry per course (assignment, mid_exam, quiz, attendance, final_exam)
- **Auto Calculation**: Total, grade, point, comment, GPA, and CGPA derived automatically
- **Grade Results**: Student views grades with semester-wise breakdown
- **Assessment Results**: Student views assessment breakdowns
- **PDF Result Sheet**: Lecturer generates PDF result sheet per course
- **PDF Registration Form**: Student generates course registration form PDF

## User Roles

| Role | Permissions |
|------|------------|
| lecturer | Enter scores for allocated courses, generate PDF result sheets |
| student | View own grades, assessments, generate registration form PDF |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| TakenCourse (scores) | Yes (via entry) | Yes (grade results) | Yes (re-entry) | No |
| Result (GPA) | Automatic | Yes | N/A | N/A |
| GradeAppeal | No views | No views | No views | No views |
| Transcript | No views | No views | No views | No views |

## Known Issues

- **HIGH**: Grade entry IDOR -- `add_score_for` fetches any course by PK without verifying the lecturer teaches it
- Bare `except:` clauses in `grade_result` and `add_score_for` swallow all exceptions
- Non-namespaced `reverse_lazy("add_score_for")` in POST redirect -- could resolve to wrong URL
- Hardcoded university names in PDF generation (lines 485, 496, 509 in views_frontend.py)
- Typo "Siganture" in result_sheet_pdf_view and course_registration_form
- Commented-out code (lines 85-91) should be implemented or replaced

## Models

- `TakenCourse` -- student FK, course FK, assignment, mid_exam, quiz, attendance, final_exam, total, grade, point, comment
- `Result` -- student FK, gpa, cgpa, semester FK, session FK, level
- `GradeComponentWeight` -- configurable weights per component
- `GradeAppeal` -- student FK, course FK, reason, status, resolution
- `GradeHistory` -- audit trail for grade changes
- `Transcript` -- student FK, generated PDF, generation date

## Dependencies

- `reportlab` (PDF generation)
- `core` (Session, Semester models)
- `course` (Course model)
- `accounts` (Student model)

## URL Namespace

- Frontend: `frontend:result:<view_name>`
- API: `api:v1:result:<resource-name>`

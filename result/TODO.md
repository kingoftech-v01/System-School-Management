# Result - TODO

## Backend

- [ ] Replace hardcoded university/school/department names in `course_registration_form` with dynamic values from tenant School model (partially done: school_name uses School.objects.first() but certification text still hardcodes "COMPUTER SICENCE & ENGINEERING")
- [ ] Fix bare `except:` clauses in API views (views_api.py: my_grades, my_results, calculate_gpa, my_appeals, my_transcripts) -- catch specific exceptions
- [ ] Fix `get_full_name()` called as method in views_api.py:161 `calculate_gpa` -- should be `get_full_name` (property)
- [ ] Fix typo "Siganture" to "Signature" in `result_sheet_pdf_view` and `course_registration_form`
- [ ] Fix typo "COMPUTER SICENCE" to "COMPUTER SCIENCE" in course_registration_form certification text
- [x] Add GradeAppeal views: students submit grade appeals, lecturers see appeals for their courses -- implemented (grade_appeal_create, grade_appeal_list, grade_appeal_detail)
- [x] Add GradeHistory audit trail on score entry -- implemented in add_score_for POST handler
- [ ] Add Transcript generation view using existing Transcript model -- model and API exist, no frontend view
- [ ] Add lecturer authorization check to `result_sheet_pdf_view` -- partially done (checks allocated_course)
- [ ] Add GradeComponentWeight management frontend views (currently API-only)
- [ ] Add BulkScoreUploadForm processing view (form exists, no view)

## Frontend

- [x] Add "Appeal Grade" button on student grade results page for each course
- [ ] Add "Generate Transcript" button on student grade results page
- [ ] Add success/error flash messages for score entry feedback (currently only "Successfully Recorded!")
- [ ] Add grade history view for students/lecturers to see past changes
- [ ] Add grade component weight configuration UI (currently API-only)

## Sidebar

- [ ] Add "Grade Appeals" sub-link to Results expandable menu (currently: Add Score, Grade Results, Assessments)
- [ ] Add "Transcripts" sub-link for students

## Security

- [x] **HIGH**: Grade entry `add_score_for` now verifies lecturer is allocated to course before grading (both GET and POST)
- [ ] Bare `except:` clauses in API views swallow all exceptions -- catch specific exceptions
- [ ] Add tenant filtering to API ViewSets (currently no tenant scoping on API queries)
- [ ] Add rate limiting to frontend views (currently none)
- [ ] GradeAppeal detail view allows any non-student authenticated user to view any appeal (should scope to lecturer's courses or direction/admin only)

## API

- [ ] Fix `get_full_name()` property call in `ResultViewSet.calculate_gpa` (views_api.py:161)
- [ ] Add tenant filtering to all ViewSet querysets
- [ ] Add pagination configuration (relies on global DRF settings)
- [ ] Add proper permission classes beyond IsAuthenticated (role-based for write operations)
- [ ] Add bulk score upload API endpoint using BulkScoreUploadForm

## Testing

- [ ] Add model tests for TakenCourse auto-calculation (save -> total, grade, point, comment)
- [ ] Add model tests for GPA/CGPA calculation methods
- [ ] Add view tests for score entry (add_score, add_score_for)
- [ ] Add view tests for grade appeal workflow (create, list, detail)
- [ ] Add API tests for all 6 ViewSets
- [ ] Add form validation tests (score ranges, weight sum = 100)
- [ ] Test grade boundary edge cases (exactly 90, 85, 80, etc.)
- [ ] Test audit trail creation in GradeHistory

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (can be replaced with tests/ directory)
- [ ] `views.py` -- legacy file, check if still used or can be removed

## Documentation

- [ ] Hardcoded text in PDF generation should be documented as known limitation
- [ ] Add docstrings to serializers.py
- [ ] Document grade boundary table and point mapping in README or code comments

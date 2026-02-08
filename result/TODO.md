# Result - TODO

## Backend

- [ ] Replace hardcoded university/school/department names in `course_registration_form` with dynamic values from tenant School model (lines 485, 496, 509)
- [ ] Fix bare `except:` clauses in `grade_result` (line 247) and `add_score_for` (line 177) -- catch specific exceptions (e.g., `Result.DoesNotExist`)
- [ ] Fix non-namespaced `reverse_lazy("add_score_for")` in `add_score_for` POST handler (line 197) -- change to `reverse_lazy("frontend:result:add_score_for")`
- [ ] Fix typo "Siganture" to "Signature" in `result_sheet_pdf_view` and `course_registration_form`
- [ ] Add GradeAppeal views: students submit grade appeals, lecturers see appeals for their courses -- model exists, no views
- [ ] Add Transcript generation view using existing Transcript model -- model exists, no views

## Frontend

- [ ] Add "Appeal Grade" button on student grade results page for each course
- [ ] Add "Generate Transcript" button on student grade results page
- [ ] Add success/error flash messages for score entry feedback

## Sidebar

- [ ] Add "Grade Appeals" sub-link to Results expandable menu (currently: Add Score, Grade Results, Assessments)

## Security

- [ ] **HIGH**: Grade entry `add_score_for` (views_frontend.py:86) fetches `Course.objects.get(pk=id)` without verifying the lecturer teaches that course -- IDOR vulnerability
- [ ] Bare `except:` clauses in `grade_result` (line 247) and `add_score_for` (line 177) swallow all exceptions -- catch specific exceptions
- [ ] Non-namespaced `reverse_lazy("add_score_for")` in POST handler (line 197) -- could resolve to wrong URL

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Hardcoded university names in PDF generation (lines 474, 485, 498) with TODO comments -- implement dynamic values from tenant School model
- [ ] Typo "Siganture" in result_sheet_pdf_view (line 441) and course_registration_form (line 568) -- fix to "Signature"
- [ ] Commented-out code (lines 85-91) should be implemented or replaced with working code

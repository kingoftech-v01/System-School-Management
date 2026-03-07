# Course - TODO

## Backend

- [x] Add course list view (all courses) (Completed as of 2026-02 -- `course_list_all` in views_frontend.py)
- [x] Add search across all programs (Completed as of 2026-02 -- `program_search` in views_frontend.py)
- [ ] Add batch course allocation -- currently must allocate one lecturer at a time
- [ ] Add course prerequisite system (prerequisite FK on Course model)

## Frontend

- [ ] Add course count badge on program list items
- [ ] Add student count on course detail page (number of students registered)
- [ ] Add "Drop Course" confirmation modal on course registration page
- [ ] Add breadcrumb navigation on course detail page (Program > Course)

## Sidebar

- [ ] No changes needed -- sidebar already shows Programs, Allocations, Registration, My Courses

## Security

- [ ] No critical security issues found

## API

- [ ] Add pagination to CourseRegistrationViewSet responses
- [ ] Add filtering by level/semester to course list endpoint
- [ ] Add course search endpoint

## Testing

- [ ] Add tests for course registration/drop workflow
- [ ] Add tests for file upload extension validation
- [ ] Add tests for slug auto-generation on Course and UploadVideo

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)
- [ ] `decorators.py` -- contains mostly commented-out code and module-level query execution

## Documentation

- [ ] Add module docstring to models.py
- [ ] `CourseAddForm` missing `is_elective` field -- model has `is_elective` but form does not expose it

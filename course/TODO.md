# Course - TODO

## Backend

- [ ] Add course list view (all courses) -- currently courses are only visible within a program detail
- [ ] Add search across all programs on program list -- ProgramFilterView uses filters but no text search
- [ ] Add batch course allocation -- currently must allocate one lecturer at a time

## Frontend

- [ ] Add course count badge on program list items
- [ ] Add student count on course detail page (number of students registered)
- [ ] Add "Drop Course" confirmation modal on course registration page
- [ ] Add breadcrumb navigation on course detail page (Program > Course)

## Sidebar

- [ ] No changes needed -- sidebar already shows Programs, Allocations, Registration, My Courses

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to models.py
- [ ] `CourseAddForm` missing `is_elective` field -- model has `is_elective` but form does not expose it

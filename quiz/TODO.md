# Quiz - TODO

## Backend

- [ ] Fix non-namespaced redirect in `MCQuestionCreate.form_valid` -- change `"mc_create"` to `"frontend:quiz:mc_create"` (line 153)
- [ ] Add Essay question create view -- model exists but no frontend view for creating essay questions
- [ ] Add TrueFalse question create view -- model exists but no frontend view
- [ ] Add MC question edit view -- currently can only create, not edit MC questions
- [ ] Add `@ratelimit` decorators to quiz views for consistency with other apps

## Frontend

- [ ] Add "Add Essay Question" and "Add True/False Question" buttons on quiz detail/question management page
- [ ] Add "Edit" button on MC question display for lecturers
- [ ] Add question count and question type breakdown on quiz list page

## Sidebar

- [ ] Add "Quiz List" and "Quiz Marking" sub-links to Quiz expandable menu -- currently only "My Progress" is shown

## Security

- [ ] Non-namespaced redirect in `MCQuestionCreate.form_valid` -- `"mc_create"` should be `"frontend:quiz:mc_create"` (line 153) -- could redirect to wrong URL

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to views_frontend.py

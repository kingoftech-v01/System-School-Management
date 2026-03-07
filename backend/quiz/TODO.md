# Quiz - TODO

## Backend

- [ ] Fix non-namespaced redirect in `MCQuestionCreate.form_valid` -- change `"mc_create"` to `"frontend:quiz:mc_create"` (line 153)
- [ ] Add Essay question create view -- model exists but no frontend view for creating essay questions
- [ ] Add TrueFalse question create view -- model exists but no frontend view
- [ ] Add MC question edit view -- currently can only create, not edit MC questions
- [ ] Add `@ratelimit` decorators to quiz views for consistency with other apps
- [ ] Fix admin `MCQuestionAdmin.fieldsets` -- line 69 of admin.py has string concatenation bug (`"figure" "quiz" "choice_order"` produces `"figurequizchoice_order"`)
- [ ] Register `TrueFalseQuestion` in admin.py -- currently not registered with `admin.site.register()`
- [ ] Implement `Progress.list_all_cat_scores()` -- currently returns empty dict `{}`
- [ ] Add course ownership validation to `QuizTake` -- students can currently attempt quizzes from courses they are not enrolled in
- [ ] Populate `utils.py` or remove empty placeholder file

## Frontend

- [ ] Add "Add Essay Question" and "Add True/False Question" buttons on quiz detail/question management page
- [ ] Add "Edit" button on MC question display for lecturers
- [ ] Add question count and question type breakdown on quiz list page
- [ ] Display time remaining countdown during timed quiz sittings
- [ ] Show `time_spent` on quiz result page after completion

## Sidebar

- [ ] Add "Quiz List" and "Quiz Marking" sub-links to Quiz expandable menu -- currently only "My Progress" is shown

## Security

- [ ] Non-namespaced redirect in `MCQuestionCreate.form_valid` -- `"mc_create"` should be `"frontend:quiz:mc_create"` (line 153) -- could redirect to wrong URL
- [ ] Add `@ratelimit` to `QuizTake` and `quiz_list` views to prevent abuse
- [ ] Validate that students can only access quizzes for courses they are enrolled in (frontend and API)

## API

- [ ] Add `TrueFalseQuestionViewSet` to `views_api.py` -- TF questions have no API endpoint
- [ ] Register TF question ViewSet in `urls.py` `api_router`
- [ ] Add `TrueFalseQuestionSerializer` to `serializers.py`
- [ ] Add `ChoiceSerializer` and nest it inside `MCQuestionSerializer` -- choices are not currently exposed via the API
- [ ] Add pagination configuration to all ViewSets (currently using DRF global defaults)
- [ ] Add throttling/rate limiting to API endpoints
- [ ] Implement `submit_answer` action logic in `SittingViewSet` -- current implementation is a simplified stub
- [ ] Add quiz time limit enforcement on the API side -- `start_quiz` does not check `is_time_expired()`
- [ ] Add `my_progress` custom action to `ProgressViewSet` for convenience endpoint

## Testing

- [ ] Add tests for `QuizTake` FormView -- sequential question flow, answer submission, final result
- [ ] Add tests for `QuizMarkingDetail` POST -- toggle incorrect questions, score adjustment
- [ ] Add tests for `EssayQuestionCreate` and `TFQuestionCreate` frontend views
- [ ] Add tests for `MCQuestionEdit` (UpdateView) frontend view
- [ ] Add tests for `SittingViewSet` custom actions (`submit_answer`, `complete`)
- [ ] Add tests for `QuizViewSet` custom actions (`questions`, `start_quiz`, `my_quizzes`)
- [ ] Add tests for `ProgressViewSet` queryset filtering (student vs lecturer)
- [ ] Add tests for quiz time limit enforcement (`is_time_expired`, `get_time_remaining`)
- [ ] Add tests for `Sitting.mark_quiz_complete()` time_spent calculation
- [ ] Add tests for `Progress.update_score()` CSV parsing edge cases
- [ ] Add tests for `_check_course_ownership` helper function
- [ ] Increase overall test coverage -- current test files exist for models, forms, serializers, admin, templatetags, views_api, and views_frontend but coverage gaps remain

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to views_frontend.py
- [ ] Add docstrings to all form classes in forms.py
- [ ] Document the CSV score format used by `Progress.score` field
- [ ] Document the `question_order` and `question_list` CSV format used by `Sitting`

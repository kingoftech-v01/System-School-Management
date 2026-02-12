# Grading - TODO

## Backend

- [ ] Fix duplicate `@login_required` decorator on `grade_entry_detail` view (line 395-396 in views_frontend.py)
- [ ] Add `is_finalized` field to `RubricGrade` model (referenced in `tasks.py` and `views_api.py` but not defined in `models.py`)
- [ ] Fix `GradingRubricViewSet` queryset -- `select_related('assignment')` references a field that does not exist on the model (should be `course` only)
- [ ] Fix `PeerReviewViewSet.submit()` -- sets `status='submitted'` but model choices only allow `pending`, `in_progress`, `completed`, `expired`
- [ ] Fix `PeerReviewViewSet` queryset -- `select_related('assignment')` should be `select_related('course')`
- [ ] Add `students_affected` M2M field to `GradeCurve` model (referenced in `admin.py` and `serializers.py` but not defined)
- [ ] Add `custom_parameters` JSONField to `GradeCurve` model (referenced in `admin.py` and `serializers.py` but not defined)
- [ ] Add `assignment_description` field to `PeerReview` model (referenced in `admin.py` fieldsets but not defined)
- [ ] Add `is_required` field to `RubricCriterion` model (referenced in `RubricCriterionSerializer` but not defined)
- [ ] Add `assignment_type` field to `GradingRubric` model (referenced in `GradingRubricSerializer` and `RubricCreateSerializer` but not defined)
- [ ] Reconcile `GradeCurve` curve_type choices between model (`linear`, `sqrt`, `bell`, `custom`) and tasks.py (`flat_boost`, `percentage_boost`, `square_root`, `set_mean`)
- [ ] Reconcile `GradeCurveSerializer` field `adjustment_value` with model fields `adjustment_factor` and `add_points`
- [ ] Add validation to prevent total rubric criteria weight from exceeding 100%
- [ ] Add bulk grade entry view for grading multiple students on the same rubric at once

## Frontend

- [ ] Add "Edit" and "Delete" buttons to grade entry detail template (lecturer only)
- [ ] Add "Edit" and "Delete" buttons to grade curve detail template (direction only)
- [ ] Add export button to student gradebook (CSV or PDF)
- [ ] Add grade distribution chart to rubric detail page
- [ ] Add "Assign Peer Reviews" button for lecturers (triggers `assign_peer_reviews` Celery task)

## Sidebar

- [ ] Add "Peer Reviews" and "Grade Curves" sub-links to the Grading expandable menu (currently only Dashboard, Rubrics, Grade Entries)

## Security

- [ ] Duplicate `@login_required` decorator on `grade_entry_detail` (views_frontend.py:395-396) -- fix by keeping only one decorator
- [ ] Add CSRF protection verification for all POST endpoints in API views
- [ ] Add object-level permission checks for `RubricCriterionViewSet` (currently only checks `CanCreateRubrics`, not rubric ownership)

## API

- [ ] Add pagination to all API ViewSets (currently using DRF defaults, should be explicit)
- [ ] Add API endpoint for student gradebook (aggregate stats per student)
- [ ] Add API endpoint for grading dashboard statistics
- [ ] Add `GradeCurve.apply()` method and wire it to the `GradeCurveViewSet.preview()` action for real curve application
- [ ] Add API throttling configuration separate from frontend `@ratelimit`
- [ ] Add OpenAPI/Swagger documentation for all API endpoints
- [ ] Add bulk create endpoint for `CriterionGrade` (grading all criteria in one request)
- [ ] Fix `CriterionGradeViewSet` -- currently read-only but criterion grades should be editable by graders

## Testing

- [ ] Add unit tests for `GradingRubric.get_total_weight()` method
- [ ] Add unit tests for `RubricGrade.calculate_grade()` method
- [ ] Add unit tests for all 6 DRF permission classes in `permissions.py`
- [ ] Add integration tests for rubric CRUD frontend views (test role-based access for all 10 roles)
- [ ] Add integration tests for grade entry create/edit/delete flow with formsets
- [ ] Add integration tests for peer review list (student vs lecturer view)
- [ ] Add integration tests for grade curve CRUD (direction-only access)
- [ ] Add integration tests for grading dashboard (role-specific context data)
- [ ] Add API tests for all ViewSet actions (CRUD + custom actions)
- [ ] Add API tests for serializer validation (passing_score > max_score, weight bounds, score bounds)
- [ ] Add tests for Celery tasks (`send_grade_notifications`, `assign_peer_reviews`, `apply_grade_curve`)
- [ ] Add tests for `CriterionGradeFormSet` with rubric-based dynamic form construction
- [ ] Remove empty `tests.py` placeholder file

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Template `rubric_list.html` shows hardcoded "No data available" -- implement actual rubric iteration and CRUD buttons
- [ ] Add missing CRUD buttons in rubric list template
- [ ] Add inline help text to grade entry form explaining weighted scoring
- [ ] Add tooltips to admin color-coded grade displays explaining the scale

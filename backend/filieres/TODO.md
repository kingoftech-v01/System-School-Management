# Filieres - TODO

## Backend

- [x] Add `edit_subject` view to allow editing coefficient, year, semester, credits on an existing FiliereSubject
- [x] Add `edit_requirement` view to allow editing an existing FiliereRequirement
- [x] Add `remove_requirement` view with confirmation -- now implemented (POST-only with redirect)
- [x] Add URL patterns for subject edit, requirement edit, and requirement delete
- [ ] Add bulk subject import (CSV/Excel) for populating filiere curricula
- [ ] Add `clone_filiere` view to duplicate a filiere with all its subjects and requirements
- [ ] Use configurable rate limits instead of hardcoded values in view decorators

## Frontend

- [x] Add "Edit" button next to each subject in filiere detail template
- [x] Add "Edit" and "Remove" buttons next to each requirement in filiere detail template
- [ ] Add total credits display per year/semester in filiere detail page
- [ ] Add drag-and-drop reordering for requirements (uses `order` field)
- [ ] Add confirmation modal before removing subjects/requirements (currently uses separate confirm page)

## Sidebar

- [ ] Expand Filieres from single link to expandable menu with sub-links: "All Filieres", "Create Filiere" (direction only)

## Security

- [ ] No critical security issues found
- [ ] Consider adding tenant validation in `FiliereSubjectForm` subject queryset (currently relies on tenant filtering through programs relation)

## API

- [ ] Add pagination to FiliereViewSet (currently relies on global DRF pagination settings)
- [ ] Add `curriculum` custom action to return subjects grouped by year/semester (matching frontend detail view logic)
- [ ] Add bulk subject creation endpoint
- [ ] Add OpenAPI/Swagger documentation annotations

## Testing

- [ ] Add model tests for Filiere, FiliereSubject, FiliereRequirement
- [ ] Add view tests for all 10 frontend views (CRUD + subject/requirement management)
- [ ] Add API tests for all 3 ViewSets
- [ ] Add form validation tests (FiliereForm code uniqueness, FiliereSubjectForm duplicate prevention)
- [ ] Test safety check: deletion prevented when students are enrolled

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (can be replaced with tests/ directory)

## Documentation

- [x] Template `filiere_list.html` shows hardcoded "No data available" instead of iterating records -- verify rendering is correct
- [ ] Add docstrings to serializers.py

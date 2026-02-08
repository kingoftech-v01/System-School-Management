# Filieres - TODO

## Backend

- [ ] Add `edit_subject` view to allow editing coefficient, year, semester, credits on an existing FiliereSubject
- [ ] Add `edit_requirement` view to allow editing an existing FiliereRequirement
- [ ] Add `remove_requirement` view with confirmation -- currently only add_requirement exists
- [ ] Add URL patterns for subject edit, requirement edit, and requirement delete

## Frontend

- [ ] Add "Edit" button next to each subject in filiere detail template
- [ ] Add "Edit" and "Remove" buttons next to each requirement in filiere detail template
- [ ] Add total credits display per year/semester in filiere detail page

## Sidebar

- [ ] Expand Filieres from single link to expandable menu with sub-links: "All Filieres", "Create Filiere" (direction only)

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Template `filiere_list.html` shows hardcoded "No data available" instead of iterating records -- implement actual data rendering

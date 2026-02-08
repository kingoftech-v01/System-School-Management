# Filieres App

Academic program (filiere) management with subject assignments, admission requirements, and enrollment tracking per tenant.

## Description

The filieres app manages academic tracks/programs with their associated subjects and admission requirements. It provides full CRUD for filieres with search and filtering, subject management with coefficients, and requirement management. Enrollment counts are annotated on list views, and safety checks prevent deletion of filieres with enrolled students.

## Main Features

- **Filiere CRUD**: Full create, list, detail, edit, delete with search and filter
- **Subject Management**: Add/remove subjects per filiere with coefficient, year, semester, credits
- **Requirement Management**: Add admission requirements per filiere
- **Enrollment Tracking**: Enrollment count annotations on list view
- **Safety Checks**: Prevents deletion of filieres with enrolled students

## User Roles

| Role | Permissions |
|------|------------|
| direction | Full CRUD for filieres, subjects, requirements |
| all authenticated | View filiere list and detail |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Filiere | Yes | Yes (list + detail) | Yes | Yes (with safety check) |
| FiliereSubject | Yes | Yes (via detail) | No | Yes |
| FiliereRequirement | Yes | Yes (via detail) | No | No |

## Models

- `Filiere` -- tenant FK, name, code, level, duration_years, capacity, is_active, coordinator FK, description
- `FiliereSubject` -- filiere FK, subject FK, coefficient, is_mandatory, year, semester, credits, hours_per_week
- `FiliereRequirement` -- filiere FK, requirement_type, description, is_mandatory

## Dependencies

- `core` (School model for tenant)
- `course` (Course model for subject linkage)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:filieres:<view_name>`
- API: `api:v1:filieres:<resource-name>`

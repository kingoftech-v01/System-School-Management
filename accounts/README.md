# Accounts App

User authentication, registration, and profile management for the School Management System.

## Description

The accounts app handles all user lifecycle operations including registration, authentication, profile management, and role-based dashboards. It supports five user roles (student, professor, direction, parent, admin) with corresponding dashboards. The app also provides Two-Factor Authentication (2FA) via TOTP and PDF export of user lists.

## Main Features

- **User Registration**: Student self-registration with username validation (AJAX)
- **Profile Management**: View/edit profile, change password, upload profile picture
- **Student Management**: Full CRUD (list, add, edit, delete) with filtering and PDF export
- **Lecturer Management**: Full CRUD (list, add, edit, delete) with filtering and PDF export
- **Parent Management**: Add parent linked to a student
- **Role-Based Dashboards**: Separate dashboards for student, parent, professor, direction
- **Two-Factor Authentication**: TOTP-based 2FA setup, disable, and management
- **Admin Panel**: Admin-only settings page

## User Roles

| Role | Permissions |
|------|------------|
| admin | Full CRUD on students, lecturers, parents; access admin panel |
| direction | School-wide dashboard with statistics |
| professor | Professor dashboard with teaching info |
| student | Personal dashboard with grades, attendance, courses |
| parent | Dashboard with child's academic info |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Student | Yes | Yes (list + detail) | Yes | Yes |
| Lecturer | Yes | Yes (list + detail) | Yes | Yes |
| Parent | Yes | No list view | No | No |
| Profile | N/A | Yes | Yes | N/A |

## Models

- `User` (AbstractUser) -- role, tenant, approval_status, employee_or_student_id, profile fields
- `Student` -- level, program, is_alumni, is_dropped, graduation_date, registration_number
- `Parent` -- student FK, relationship, first_name, last_name, phone, email, address
- `DepartmentHead` -- department coordinator

## Dependencies

- `course` (Program model for student enrollment)
- `core` (Session, Semester models)
- `result` (TakenCourse for grade data)
- `django-filter`, `xhtml2pdf`, `django-otp`, `qrcode`, `django-countries`

## URL Namespace

- Frontend: `frontend:accounts:<view_name>`
- API: `api:v1:accounts:<resource-name>`

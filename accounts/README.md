# Accounts App

User authentication, registration, profile management, and parent portal for the School Management System.

## Description

The accounts app handles the full user lifecycle: registration (student self-signup, invitation-based onboarding for parents and staff), authentication with Two-Factor (TOTP), profile management, role-based dashboards, and a comprehensive parent portal with messaging, appointments, and permission slips. It supports 10 user roles with approval workflows and invitation codes for controlled account creation.

## Main Features

- **User Registration**: Student self-registration with AJAX username validation, invitation-based signup for parents and staff
- **Profile Management**: View/edit profile, change password, upload profile picture (auto-resized to 300x300), force password change on first login
- **Student Management**: Full CRUD (list, add, edit, delete) with filtering, PDF export, auto-generated registration numbers
- **Lecturer Management**: Full CRUD (list, add, edit, delete) with filtering and PDF export
- **Parent Management**: Full CRUD (list, add, detail, edit, delete)
- **Role-Based Dashboards**: Separate dashboards for all 10 roles via unified_dashboard
- **Two-Factor Authentication**: TOTP-based 2FA setup, disable, and management
- **Invitation Codes**: One-time codes for parent/staff account creation with expiration
- **Account Approval**: Workflow for new account approval (not_requested -> pending -> approved/declined)
- **Parent Portal**: Full-featured portal with child selection, grades, attendance, timetable, messaging, appointments, permission slips, disciplinary records, events, and invoices

## User Roles

| Role | Permissions |
|------|------------|
| admin | Full CRUD on students, lecturers, parents; access admin panel; generate invitation codes |
| direction | School-wide dashboard, session/semester CRUD, generate invitation codes |
| professor | Professor dashboard with teaching info; receive parent messages and appointment requests |
| student | Personal dashboard with grades, attendance, courses |
| parent | Parent portal with child's academic info, messaging, appointments, permission slips |
| prefet | Discipline officer dashboard (via core unified_dashboard) |
| accountant | Financial dashboard (via core unified_dashboard) |
| secretary | Academic management dashboard (via core unified_dashboard) |
| librarian | Library management dashboard (via core unified_dashboard) |
| registrar | Enrollment/certificate management dashboard (via core unified_dashboard) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Student | Yes | Yes (list + detail) | Yes | Yes |
| Lecturer | Yes | Yes (list + detail) | Yes | Yes |
| Parent | Yes | Yes (list + detail) | Yes | Yes |
| Profile | N/A | Yes | Yes | N/A |
| InvitationCode | Yes (admin) | Yes (admin) | No | Yes (deactivate) |
| ParentTeacherMessage | Yes | Yes (inbox) | No | No |
| ParentTeacherAppointment | Yes | Yes (list) | Yes (status) | No |
| PermissionSlip | Yes (staff) | Yes | Yes (sign/decline) | No |

## Models

- `User` (AbstractUser) -- role, tenant FK, approval_status, employee_or_student_id, profile fields, must_change_password, country
- `Student` -- student O2O User, level, program FK, is_alumni, is_dropped, graduation_date, registration_number (auto-generated)
- `Parent` -- user FK, student FK, relationship, first_name, last_name, phone, email
- `DepartmentHead` -- user O2O, department FK (Program)
- `InvitationCode` -- code, role, linked_student FK, created_by FK, used_by FK, is_active, expires_at
- `ParentTeacherMessage` -- sender FK, recipient FK, student FK, subject, body, is_read, parent_initiated
- `ParentTeacherAppointment` -- parent FK, teacher FK, student FK, date, time_slot, status, reason, notes
- `PermissionSlip` -- student FK, title, description, created_by FK, deadline, status, signed_by FK

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | /api/v1/accounts/users/ | List/create users |
| GET/PUT/DELETE | /api/v1/accounts/users/{id}/ | User detail/update/delete |
| GET | /api/v1/accounts/students/ | List students |
| GET | /api/v1/accounts/lecturers/ | List lecturers |
| GET | /api/v1/accounts/staff/ | List staff users |
| POST | /api/v1/accounts/validate-username/ | Check username availability |
| POST | /api/v1/accounts/2fa/setup/ | Setup TOTP 2FA |
| POST | /api/v1/accounts/2fa/disable/ | Disable 2FA |

## Dependencies

- `course` (Program model for student enrollment)
- `core` (School model for tenant, Session, Semester)
- `result` (TakenCourse for grade data on student dashboard)
- `django-filter`, `xhtml2pdf`, `django-otp`, `qrcode`, `django-countries`, `Pillow`

## Configuration

- `INVITATION_CODE_EXPIRY_DAYS`: Default expiry for invitation codes (default: 7)
- `LECTURER_ID_PREFIX`: Prefix for lecturer employee IDs
- `STUDENT_ID_PREFIX`: Prefix for student IDs

## URL Namespace

- Frontend: `frontend:accounts:<view_name>`
- API: `api:v1:accounts:<resource-name>`

## File Structure

```text
accounts/
  models.py              -- User, Student, Parent, DepartmentHead, InvitationCode, portal models
  views_frontend.py      -- Student/lecturer/parent CRUD, profile, 2FA, signup flows
  views_parent.py        -- Parent portal views (dashboard, grades, messages, appointments)
  views_api.py           -- DRF ViewSets for User, Student, Lecturer, Staff + 2FA API
  urls.py                -- Frontend + API URL routing (125+ URL patterns)
  serializers.py         -- DRF serializers for all models
  forms.py               -- Registration, profile, student/lecturer forms
  decorators.py          -- Role-based view decorators
  permissions.py         -- DRF permission classes
  middleware.py           -- RoleMiddleware, AuditLoggingMiddleware, AuthSecurityMiddleware, 2FA enforcement
  context_processors.py  -- Template context for user role info
  validators.py          -- ASCIIUsernameValidator
  admin.py               -- UserAdmin, InvitationCodeAdmin, SecureAdminSite
  tests/                 -- Test suite
```

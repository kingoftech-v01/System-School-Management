# Accounts - Architecture

## Overview

The accounts app is the identity and access management layer of the system. It defines the custom User model (AbstractUser) with RBAC, the Student/Parent/DepartmentHead profiles, invitation codes for controlled onboarding, and a full parent portal for family engagement. Nearly every other app depends on accounts for user identity and role-based access control.

## Models & Relationships

### Entity-Relationship Summary

```text
User ──1:1──> Student ──N:1──> Program (course app)
User ──1:N──> Parent ──N:1──> Student
User ──1:1──> DepartmentHead ──N:1──> Program
User ──1:N──> InvitationCode (created_by / used_by)
Student ──1:N──> InvitationCode (linked_student)
User ──1:N──> ParentTeacherMessage (sender / recipient)
Parent ──1:N──> ParentTeacherAppointment
Student ──1:N──> PermissionSlip
```

### Model Details

#### User (AbstractUser)

- **Purpose**: Central identity model for all system users
- **Key Fields**: role (10 choices), tenant FK (School), approval_status, employee_or_student_id, must_change_password, gender, phone, picture, country, date_of_birth
- **Relationships**: FK to `core.School` via `tenant`
- **Business Rules**:
  - `get_full_name` is a `@property` (NOT callable) -- returns first+middle+last or username
  - Profile picture auto-resized to 300x300 on save
  - Picture deleted on user delete (unless default)
  - `role` field has `default='student'` -- tests must set role explicitly
- **Managers**: `CustomUserManager` with `search()`, `get_student_count()`, `get_lecturer_count()`

#### Student

- **Purpose**: Extended student profile linked to User
- **Key Fields**: level (Bachelor/Master), program FK, is_alumni, is_dropped, graduation_date, registration_number (auto-generated)
- **Relationships**: O2O to User, FK to `course.Program`
- **Business Rules**:
  - `registration_number` auto-generated on save: format `YY-DEPT-SERIAL` (e.g., 24-CS-001)
  - `mark_as_alumni()` and `mark_as_dropped()` lifecycle methods
  - Deleting Student also deletes the linked User
- **Managers**: `StudentManager` (default), `ActiveStudentManager`, `AlumniManager`, `DroppedStudentManager`

#### Parent

- **Purpose**: Links a parent/guardian user to a student
- **Key Fields**: user FK, student FK, first_name, last_name, phone, email, relation_ship
- **Relationships**: FK to User, FK to Student

#### DepartmentHead

- **Purpose**: Designates a user as department coordinator
- **Key Fields**: user O2O, department FK (Program)

#### InvitationCode

- **Purpose**: One-time codes for controlled account creation (parent/staff)
- **Key Fields**: code (XXXX-XXXX format), role, linked_student FK, expires_at, used_at
- **Business Rules**:
  - `is_valid` property checks: is_active AND not used AND not expired
  - `redeem(user)` marks code as used and deactivates it
  - `generate_code()` class method ensures uniqueness

#### ParentTeacherMessage

- **Purpose**: Scoped messaging between parents and teachers about a specific student
- **Key Fields**: sender FK, recipient FK, student FK, subject, body, is_read, parent_initiated
- **Business Rules**: `clean()` validates sender/recipient relationship to student

#### ParentTeacherAppointment

- **Purpose**: Scheduled meetings between parents and teachers
- **Key Fields**: parent FK, teacher FK, student FK, date, time_slot (30-min slots), status, reason
- **Business Rules**: unique_together on (teacher, date, time_slot) prevents double-booking

#### PermissionSlip

- **Purpose**: Documents requiring parent signature
- **Key Fields**: student FK, title, description, deadline, status, signed_by FK
- **Business Rules**: `sign()` and `decline()` methods; `is_expired` property checks deadline

## View Logic Flow

### Frontend Views (`views_frontend.py`)

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| `register` | GET/POST | No | - | Student self-registration |
| `signup_hub` | GET | No | - | Role-based signup gateway |
| `student_activate` | GET/POST | No | - | Student activation with ID |
| `parent_invitation_step1/2` | GET/POST | No | - | Parent invite code signup |
| `staff_invitation_step1/2` | GET/POST | No | - | Staff invite code signup |
| `profile` | GET | Yes | all | View own profile |
| `profile_single` | GET | Yes | all | View any user profile |
| `profile_update` | GET/POST | Yes | all | Edit own profile |
| `change_password` | GET/POST | Yes | all | Change password |
| `LecturerFilterView` | GET | Yes | admin/direction | Lecturer list with filtering |
| `staff_add_view` | GET/POST | Yes | admin/direction | Add lecturer |
| `StudentListView` | GET | Yes | admin/direction | Student list |
| `parent_list` | GET | Yes | admin/direction | List all parents |
| `parent_detail` | GET | Yes | admin/direction | Parent detail view |
| `setup_2fa` | GET/POST | Yes | all | TOTP setup with QR code |
| `admin_panel` | GET | Yes | admin | Admin settings page |

### Parent Portal Views (`views_parent.py`)

| View | Method | Auth | Roles | Description |
|------|--------|------|-------|-------------|
| `parent_dashboard` | GET | Yes | parent | Parent home with child overview |
| `parent_select_child` | GET | Yes | parent | Switch active child |
| `parent_child_grades` | GET | Yes | parent | View child's grades |
| `parent_child_attendance` | GET | Yes | parent | View child's attendance |
| `parent_messages_inbox` | GET | Yes | parent | Message inbox |
| `parent_messages_compose` | GET/POST | Yes | parent | Send message to teacher |
| `parent_appointments` | GET | Yes | parent | List appointments |
| `parent_appointment_request` | GET/POST | Yes | parent | Request appointment |
| `parent_permission_slips` | GET | Yes | parent | View permission slips |
| `parent_sign_permission_slip` | POST | Yes | parent | Sign/decline a slip |

### API Views (`views_api.py`)

| ViewSet | Methods | Auth | Description |
|---------|---------|------|-------------|
| `UserViewSet` | CRUD | Yes | User management |
| `StudentViewSet` | list, retrieve | Yes | Student listing |
| `LecturerViewSet` | list, retrieve | Yes | Lecturer listing |
| `StaffViewSet` | list, retrieve | Yes | Staff listing |
| `ValidateUsernameAPIView` | POST | No | Username check |
| `Setup2FAAPIView` | POST | Yes | TOTP setup |
| `Disable2FAAPIView` | POST | Yes | Disable 2FA |

### Key Patterns

- `@login_required` + `@admin_required`/`@lecturer_required` decorators for access control
- `RoleMiddleware` sets `request.user_role` from `User.role` field
- `AuditLoggingMiddleware` logs mutating requests to sensitive paths to ActivityLog
- `AuthSecurityMiddleware` checks account active status and tenant subscription
- `Require2FAMiddleware` enforces 2FA for staff roles (professor, direction, admin, etc.)

## Business Logic

### Core Workflows

#### Student Registration (Self-Signup)

1. Student enters ID number on `/signup/student/`
2. System verifies parent connection via `/signup/student/verify/`
3. Student sets password on `/signup/student/password/`
4. Account created with `role='student'`, `must_change_password=False`

#### Parent Invitation Signup

1. Admin generates invitation code via admin panel
2. Parent enters code at `/signup/parent/`
3. System validates code (not expired, not used, role=parent)
4. Parent completes registration at `/signup/parent/complete/`
5. Code redeemed via `InvitationCode.redeem(user)`

#### Staff Invitation Signup

1. Admin generates role-specific invitation code
2. Staff enters code at `/signup/staff/`
3. System validates and assigns the code's role to new user
4. Account created with `must_change_password=True`

#### Student Registration Number Generation

1. On `Student.save()`, if `registration_number` is empty
2. Generate format: `YY-DEPT-SERIAL` (e.g., 24-CS-001)
3. Query last serial for same year+dept prefix
4. Increment serial number

### Validation Rules

- Username must match `ASCIIUsernameValidator` (letters, digits, @/./+/-/_ only)
- InvitationCode checked: `is_active AND used_at IS NULL AND expires_at > now()`
- ParentTeacherMessage validates sender/recipient relationship to student
- Appointment unique_together prevents teacher double-booking

## Inter-App Dependencies

### This App Depends On

| App | Models/Utilities Used | Purpose |
|-----|----------------------|---------|
| `core` | School | User.tenant FK |
| `course` | Program | Student.program FK, DepartmentHead.department FK |
| `result` | TakenCourse | Student dashboard grade data |

### Apps That Depend On This App

| App | What They Use | Purpose |
|-----|--------------|---------|
| `core` | User, Student, Parent, decorators | Dashboard data, role checks |
| `course` | User (is_lecturer), Student | Course allocation, registration |
| `result` | Student | Score entry and grade tracking |
| `scheduling` | User (professor) | Professor schedule assignments |
| `grading` | Student | Rubric grading |
| `quiz` | User (AUTH_USER_MODEL) | Quiz attempts |
| `attendance` | User | Teacher attendance marking |
| `analytics` | Student, User | Engagement tracking |
| `certificates` | Student | Certificate issuance |
| `notes` | User | Professor notes |
| `forums` | User | Forum posts |
| `discipline` | User | Disciplinary actions |
| `library` | User | Book borrowing |
| `payments` | User | Payment processing |

### Dependency Diagram

```text
             core (School) ──> [ACCOUNTS] <── course (Program)
                                   │          result (TakenCourse)
                                   │
                                   ▼
                    Nearly all other apps depend on
                    User, Student, Parent, decorators
```

## Data Flow

### Request/Response Flow

```text
User Request
    │
    ▼
middleware.py (RoleMiddleware, AuditLogging, AuthSecurity, 2FA)
    │
    ▼
urls.py (route matching)
    │
    ├── views_frontend.py (HTML views)
    │   ├── forms.py (validation)
    │   └── models.py (User/Student/Parent CRUD)
    │
    ├── views_parent.py (parent portal)
    │   └── models.py (messaging, appointments, slips)
    │
    └── views_api.py (DRF endpoints)
        ├── serializers.py (validation + serialization)
        └── models.py (data access)
    │
    ▼
Template / JSON Response
```

### Key Data Paths

- **User Login**: Request -> django.contrib.auth -> RoleMiddleware sets role -> Dashboard redirect
- **Student CRUD**: Form -> User + Student create (auto registration_number) -> redirect
- **Parent Message**: Compose form -> validate parent/teacher/student relationship -> save -> inbox
- **2FA Setup**: Generate TOTP secret -> QR code -> user confirms -> TOTPDevice created

## Technical Notes

- `get_full_name` is a `@property` (NOT a callable method) -- use `user.get_full_name` without parentheses
- Profile picture auto-resized via PIL on `User.save()` (wrapped in bare except for missing file handling)
- Student deletion cascades to User deletion (overridden `delete()` method)
- `InvitationCode.generate_code()` uses retry loop to ensure uniqueness
- Middleware stack: RoleMiddleware -> AuditLoggingMiddleware -> AuthSecurityMiddleware -> Require2FAMiddleware
- `SecureAdminSite` in admin.py requires confirmed TOTP device for admin access
- Legacy boolean fields (`is_student`, `is_lecturer`, `is_parent`) kept alongside `role` field for backward compatibility

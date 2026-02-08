# SCHOLARA – Global School Operating System
## MVP Specification Document

**Slogan:** *"One Platform. Every School. Every Country."*

**Version:** 1.0  
**Date:** December 29, 2025  
**Document Classification:** Technical Specification

---

## Executive Summary

**Scholara** is a cloud-based, multi-tenant School Management System (SaaS) designed to support K-12, higher education, and tertiary institutions across multiple countries (Canada, USA, France, Haiti, and others). The platform unifies Student Information System (SIS), Learning Management System (LMS), ERP, and mass notification capabilities into a single, configuration-driven operating system.

### Core Strengths
- **Fully configurable academic models** supporting different countries, grading scales, and credit systems
- **Multi-campus with HQ control** ensuring consistency while allowing local autonomy
- **Smart mass notifications** (SMS, email, push, voice) triggered by SIS events and configurable policies
- **Role-based access** with campus-specific and school-wide rules
- **Export/import configuration templates** for rapid multi-tenant deployment
- **Analytics and early-warning systems** to identify at-risk students
- **Flexible assessment timelines** supporting both fixed semesters and year-defined exam schedules
- **Teacher and admin autonomy** with guardrails set by HQ

The MVP focuses on the core SIS functionality (enrollment, grades, credits, notifications, and analytics) with extensibility for LMS, finance, and documents in Phase 2.

---

## Document Structure

### Pages 1–3: Vision, Architecture, and Personas
- Product vision and target markets
- High-level system architecture (multi-tenant, microservices, tech stack)
- Key user personas and roles

### Pages 4–6: Core Data Model
- Student, program, grading, and credit entities
- Multi-country education system templates
- School year and assessment periods

### Pages 7–9: Academic Configuration
- Configurable grading scales and passing rules
- Program/filière definitions and campus availability
- Configuration templates and export/import

### Pages 10–12: Enrollment and Academic Records
- Student enrollment workflows
- Transcript and academic history management
- Progress tracking and graduation checks

### Pages 13–15: Mass Notifications and Events
- Event-driven notification system (no internal chat)
- Targeting by role, program, campus, and custom rules
- Multi-channel delivery (SMS, email, push, voice)

### Pages 16–18: Analytics, Reporting, and Extensibility
- Dashboard and analytics engine
- Early-warning system for at-risk students
- Regulatory reporting and integrations
- API-first architecture and roadmap

---

## Page 1: Vision and Product Definition

### 1.1 Problem Statement

Schools globally struggle with fragmented systems:
- Multiple disconnected tools (SIS, LMS, finance, communication)
- Different rules per country and institution requiring custom builds
- Difficulty managing multi-campus organizations with consistent policies
- Limited real-time visibility into student progress and risk

### 1.2 Solution: Scholara Operating System

Scholara is a **single platform** that:
- Works for K-12, colleges, universities, academies, and tutoring centers
- Adapts to each country's education system (Canada, USA, France, Haiti, etc.)
- Supports multi-campus organizations with HQ-controlled templates
- Provides intelligent notifications, analytics, and insights in one place

### 1.3 Target Markets

**Primary:** Canadian (Quebec, Ontario) and French-speaking institutions needing multi-country support  
**Secondary:** International schools, education networks, and multi-campus groups worldwide  
**Tertiary:** Small academies and tutoring centers that want enterprise features without enterprise cost

### 1.4 MVP Scope

The MVP delivers **core SIS + notifications + analytics**:
- Multi-tenant infrastructure with role-based access
- Configurable academic models (grading, credits, programs)
- Enrollment, attendance, and grades
- Mass notifications triggered by SIS events
- Basic analytics and early-warning dashboards
- Export/import of configuration templates

**Out of MVP:** Internal messaging, LMS content, finance module, e-signature, app marketplace (planned for Phase 2)

---

## Page 2: System Architecture and Tech Stack

### 2.1 Architecture Overview

Scholara is built on a **multi-tenant, API-first, event-driven architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Tailwind)                 │
│            (Web app + responsive mobile interface)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    REST/GraphQL API Layer                       │
│                  (Django REST Framework)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Core Business Logic                          │
│     (Multi-tenant Django application with pluggable modules)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────┬──────────────────────┬──────────────────┐
│  PostgreSQL Database │  Redis Cache/Events  │  File Storage    │
│  (Tenant-isolated)   │  (Task Queue + Pub/Sub) │  (S3-compatible)│
└──────────────────────┴──────────────────────┴──────────────────┘
```

### 2.2 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18+, TypeScript, Tailwind CSS, React Query |
| **Backend** | Django 4.2+, Django REST Framework, Celery |
| **Database** | PostgreSQL 14+ (per-tenant schema isolation) |
| **Cache/Queue** | Redis (Celery tasks, cache, Pub/Sub) |
| **Authentication** | JWT + OAuth2 (Google, Microsoft for future) |
| **Search** | PostgreSQL full-text or Elasticsearch (Phase 2) |
| **Deployment** | Docker + Docker Compose, Kubernetes (future) |
| **Monitoring** | Prometheus, ELK stack (Phase 2) |

### 2.3 Multi-Tenancy Strategy

- **Schema-based isolation**: Each tenant has its own PostgreSQL schema (`tenant_a`, `tenant_b`, etc.)
- **Shared application code**: One Django codebase serves all tenants
- **Tenant context middleware**: Automatically routes requests to the correct schema based on subdomain or API key
- **Data privacy**: Complete isolation; no cross-tenant data leakage possible

### 2.4 Deployment Model

**SaaS Cloud-hosted** (AWS/Azure/DigitalOcean):
- Multi-tenant shared infrastructure
- Automatic backups and disaster recovery
- Scalable to 1000s of institutions
- Optional: on-premise or hybrid for large organizations (Phase 2)

---

## Page 3: User Personas and Roles

### 3.1 Core User Roles

| Role | Responsibilities | Tenure |
|------|------------------|--------|
| **System Administrator** | Tenant setup, user management, backup, support | Permanent |
| **HQ Configuration Manager** | Define programs, grading scales, campuses, policies | Permanent |
| **Principal / Campus Director** | Approve grades, manage campus staff, local decisions | Academic year |
| **Registrar / Academic Secretary** | Enroll students, manage transcripts, graduation checks | Permanent |
| **Teacher / Instructor** | Enter grades, create assessments, submit attendance | Per course/term |
| **Parent / Guardian** | View student grades, attendance, receive alerts | Academic year |
| **Student** | View own grades, transcripts, timetable, assignments | Academic year |
| **Finance Officer** | Manage fees, tuition, generate billing reports | Permanent |
| **IT Support** | Technical troubleshooting, user password resets | Permanent |

### 3.2 Persona Profiles

**Marie (HQ Academic Director, Canada)**
- Manages 5 campuses across Quebec and Ontario
- Defines grading scales, programs, and assessment calendars once per year
- Ensures all campuses follow the same rules
- Exports configuration to replicate to partner schools

**Jamal (Secondary Teacher, Haiti)**
- Teaches Math and Physics
- Enters grades after each contrôle
- Needs to see which students are at risk of failing
- Wants notifications to parents when grades drop below passing

**Sophia (Registrar, France)**
- Handles student enrollment and transcript generation
- Needs transcripts formatted per French/BAC standards
- Exports academic records for ministry compliance
- Manages graduation eligibility checks

**Pierre (Principal, Multi-campus Group)**
- Oversees 3 campuses
- Reviews and approves high-level policies set by HQ
- Monitors campus-level analytics (pass rates, attendance)
- Investigates issues flagged by early-warning system

---

## Page 4: Core Data Model – Entities

### 4.1 Tenant and Organization

```
Tenant (SaaS organization)
├── name, country_template (Canada, USA, France, Haiti)
├── primary_language (FR/EN)
├── default_grading_scale_id (FK)
├── configuration_template_version
└── created_at, updated_at

Campus (physical location within tenant)
├── tenant_id (FK)
├── name, code, address
├── timezone
├── phone, email
└── is_active

ConfigurationTemplate (reusable set of rules)
├── tenant_id (FK)
├── name, version
├── country_template
├── included_programs (M2M)
├── included_grading_scales (M2M)
├── export_file_path (for backup/replication)
└── created_by, created_at
```

### 4.2 Student and Enrollment

```
Student (core entity)
├── tenant_id (FK)
├── student_id (unique per tenant), first_name, last_name, dob
├── email, phone
├── primary_language (FR/EN)
├── enrollment_status (active, graduated, withdrawn)
├── current_program_id (FK, can have multiple)
├── current_campus_id (FK)
├── parent_guardians (M2M)
└── created_at, updated_at

Enrollment (student in program at campus in school year)
├── student_id (FK)
├── program_id (FK)
├── campus_id (FK)
├── school_year_id (FK)
├── enrollment_date, withdrawal_date
├── status (enrolled, dropped, graduated, transferred)
├── progress_tracking (GPA, credits_earned, transcript)
└── created_at, updated_at

Guardian (parent/emergency contact)
├── tenant_id (FK)
├── name, relationship, email, phone
├── notification_preferences (SMS, email, push)
└── students (M2M, can follow multiple students)
```

### 4.3 Program and Curriculum

```
Program (degree, diploma, or path)
├── tenant_id (FK)
├── name, code (e.g., "DES-General", "Science Filière")
├── level (primary, secondary, CEGEP, undergraduate, graduate)
├── country_template
├── available_campuses (M2M, controls where this program runs)
├── grading_scale_id (FK, default for program)
├── credits_required_to_graduate (total)
├── passing_average_threshold (e.g., 60, 70)
├── honours_threshold (optional)
├── curriculum_version
├── duration_years
├── created_by, updated_at

Course (subject)
├── tenant_id (FK)
├── name, code (e.g., "MATH101")
├── description
├── credits_value
├── is_core (required), is_elective
├── prerequisite_courses (M2M)
└── created_at, updated_at

CourseInProgram (join entity with rules)
├── course_id (FK)
├── program_id (FK)
├── grading_scale_id (FK, can override program default)
├── credits_value (can differ per program)
├── weight_in_program (coefficient, e.g., 2.0)
├── passing_mark (e.g., 60%, can override program default)
├── status (required, elective, conditional)
└── created_at, updated_at
```

### 4.4 Academic Calendar and School Year

```
SchoolYear (e.g., 2025-2026)
├── tenant_id (FK)
├── name, code
├── start_date, end_date
├── academic_calendar_type (semester_based or control_based)
├── configuration_template_id (FK, defines rules for this year)
├── is_active
└── created_at, updated_at

Semester / Term (if calendar_type = semester_based)
├── school_year_id (FK)
├── name (e.g., "Fall Semester", "Trimestre 1")
├── code
├── start_date, end_date
├── exam_period_start, exam_period_end
├── campus_specific_dates (JSON, allows campus overrides)
└── created_at, updated_at

Contrôle / AssessmentPeriod (if calendar_type = control_based or for exams)
├── school_year_id (FK)
├── name, code
├── type (controle, exam, quiz_window, midterm, final)
├── defined_by (HQ, CAMPUS, TEACHER)
├── target_programs (M2M, which programs affected)
├── target_levels (M2M, which grades affected)
├── target_campuses (M2M, if not all campuses)
├── default_start_date, default_end_date
├── date_lock_policy (fixed, limited_shift, free)
├── campus_date_overrides (JSON, per-campus date adjustments)
├── status (planned, ongoing, completed)
└── created_by, created_at, updated_at
```

### 4.5 Grading and Credits

```
GradingScale (defines how grades are measured)
├── tenant_id (FK)
├── name, code
├── scale_type (0_to_100, 0_to_20, 0_to_400, letter_A_F, gpa_4_0)
├── min_value, max_value (e.g., 0, 100)
├── passing_threshold (e.g., 60)
├── honours_threshold (optional)
├── grading_bands (JSON array of {min, max, grade_letter, description})
│  Example: [{min: 90, max: 100, letter: 'A', desc: 'Excellent'}]
├── country_context (Canada, USA, France, Haiti)
├── conversion_table (JSON, for converting to other scales)
└── created_at, updated_at

Assessment (a test, project, or evaluation within a course)
├── course_section_id (FK)
├── name (e.g., "Midterm Exam", "Project 1")
├── type (exam, assignment, project, participation, lab)
├── grading_scale_id (FK)
├── weight_in_course (e.g., 0.3 = 30%)
├── max_points
├── assessment_period_id (FK, optional, links to Contrôle or exam window)
├── due_date / assessment_date
├── created_by, created_at

Grade (student's score for an assessment)
├── student_id (FK)
├── assessment_id (FK)
├── raw_score (e.g., 85 out of 100)
├── graded_by_teacher_id (FK)
├── submitted_date
├── status (draft, final, disputed)
├── feedback (text or rubric)
├── created_at, updated_at

CourseGrade (final grade in a course for a student)
├── student_id (FK)
├── course_section_id (FK)
├── final_grade (weighted average, e.g., 82)
├── grading_scale_id (FK)
├── pass_fail (true/false)
├── credits_earned (if passed)
├── credits_failed (if failed, for repeat tracking)
├── recorded_date
└── created_at, updated_at
```

---

## Page 5: Grading Scales and Multi-Country Support

### 5.1 Grading Scale Examples

**Canada (Quebec Secondary, 0–100)**
- Scale: 0 to 100 percentage
- Passing: 60%
- Grading bands: A (90–100), B (80–89), C (70–79), D (60–69), F (<60)
- Also tracked as R-score for CEGEP equivalence

**Canada (Primary, A–F)**
- Scale: Letter grades A–F
- Passing: D (60%)
- Conversion to percentage for reporting

**Haiti (Secondary, 0–100)**
- Scale: 0 to 100
- Passing: 65%
- Same course can have 0–400 scale in one filière, 0–200 in another
- Multiple exam sessions per year (January, April, July)

**France (Baccalauréat, 0–20)**
- Scale: 0 to 20
- Passing: 10/20 or higher
- Coefficients per subject (e.g., Math = 5, French = 3)
- Calculation: (grade × coefficient) / total coefficients

**USA (GPA 0–4.0, Letter Grade)**
- Scale: A–F with GPA equivalents
- Passing: D (1.0 GPA) or C (2.0 GPA) depending on program
- Weighted for honors courses (e.g., A in honors = 5.0)

### 5.2 Configurable Thresholds

Each `Program` and `CourseInProgram` can override:

```json
{
  "grading_scale_id": "haiti-0-100",
  "passing_mark": 65,
  "honours_threshold": 85,
  "scale_overrides": {
    "science_filiere": {
      "grading_scale_id": "haiti-0-400",
      "passing_mark": 240,
      "honours_threshold": 340
    },
    "literature_filiere": {
      "grading_scale_id": "haiti-0-200",
      "passing_mark": 130,
      "honours_threshold": 170
    }
  }
}
```

### 5.3 Multi-Country Templates

When a tenant is created or imports a configuration:

1. **Country Template Selection**: Choose Canada, USA, France, Haiti, or "Custom"
2. **Default Grading Scale**: Automatically set based on country
3. **Calendar Type**: Semester-based or control-based
4. **Levels and Stages**: Pre-populate typical grade/year structure
5. **Customization**: Admin can adjust passing grades, add scales, modify structures

---

## Page 6: Multi-Campus and Configuration Hierarchy

### 6.1 Campus Assignment and Control

```
Tenant (HQ level)
├── ConfigurationTemplate v1.0 (set once per school year)
│   ├── Program: "Science" (available at Campus A, B, C)
│   ├── Program: "Arts" (available at Campus A, D)
│   ├── Program: "Primary" (available at all campuses)
│   ├── GradingScale: Canada-0-100
│   ├── Semester: Fall (Sep 5 – Dec 20)
│   ├── Semester: Winter (Jan 8 – Apr 30)
│   └── [Other rules, notification policies, etc.]
│
├── Campus A (Montreal)
│   ├── Uses ConfigurationTemplate v1.0
│   ├── Allowed Programs: Science, Arts, Primary
│   ├── Date Overrides: Winter semester start → Jan 10 (2 days later)
│   ├── Enrolled students: 500
│   └── Staff: 50
│
├── Campus B (Quebec City)
│   ├── Uses ConfigurationTemplate v1.0
│   ├── Allowed Programs: Science, Primary
│   ├── Date Overrides: None (strict adherence)
│   ├── Enrolled students: 300
│   └── Staff: 30
│
└── Campus C (Gatineau)
    ├── Uses ConfigurationTemplate v1.0 (different version planned for 2026)
    ├── Allowed Programs: Primary
    ├── Date Overrides: None
    ├── Enrolled students: 150
    └── Staff: 15
```

### 6.2 Permission Model

| Action | HQ Only | Campus Director | Teacher | Notes |
|--------|---------|-----------------|---------|-------|
| Create/edit Program | ✓ | | | Defines curriculum |
| Assign Program to Campus | ✓ | | | Controls who can use it |
| Set Grading Scale | ✓ | | | Global standard |
| Define Semester Dates | ✓ | | | HQ sets, campus adjusts ±days |
| Define Contrôles | ✓ | | | HQ proposes dates |
| Shift Contrôle Date | | ✓ | | Campus-specific, if allowed |
| Create Assessment Period | | | ✓ | Teacher freedom (university) |
| Enter Grades | | | ✓ | Per course |
| Approve Grade Changes | ✓ | ✓ | | Depends on policy |
| Export Configuration | ✓ | | | For backup/replication |
| Import Configuration | ✓ | | | New tenant setup |

### 6.3 Export / Import Configuration File

**Format**: JSON (or ZIP with JSON + metadata)

```json
{
  "export_version": "1.0",
  "export_date": "2025-12-29",
  "tenant_name": "Quebec School Network",
  "country_template": "Canada",
  "campuses": [
    {"id": "campus_a", "name": "Montreal", "timezone": "America/Toronto"},
    {"id": "campus_b", "name": "Quebec City", "timezone": "America/Toronto"}
  ],
  "programs": [
    {
      "id": "prog_sci",
      "name": "Science",
      "level": "secondary",
      "available_campuses": ["campus_a", "campus_b"],
      "grading_scale_id": "scale_can_0_100",
      "passing_average": 60,
      "courses": [
        {"code": "MATH101", "name": "Calculus", "credits": 3, "weight": 1.5},
        {"code": "PHY101", "name": "Physics", "credits": 3, "weight": 1.5}
      ]
    }
  ],
  "grading_scales": [
    {
      "id": "scale_can_0_100",
      "name": "Canada 0-100",
      "scale_type": "0_to_100",
      "grading_bands": [
        {"min": 90, "max": 100, "letter": "A"},
        {"min": 80, "max": 89, "letter": "B"}
      ]
    }
  ],
  "school_year": {
    "name": "2025-2026",
    "start_date": "2025-09-05",
    "calendar_type": "semester_based",
    "semesters": [
      {"name": "Fall", "start": "2025-09-05", "end": "2025-12-20"}
    ]
  },
  "notification_policies": [
    {"event": "student_failing_course", "channels": ["email", "sms"]}
  ]
}
```

**Import Workflow**:
1. New tenant uploads file
2. System validates structure and uniqueness (e.g., no duplicate program codes)
3. Optional: map campus IDs and codes if different from source
4. Confirm and import
5. New tenant has identical configuration

---

## Page 7: Enrollment and Student Records

### 7.1 Enrollment Workflow

```
Step 1: Student Application (not in MVP)
        ↓
Step 2: Admission Decision
        ↓
Step 3: Enroll Student in Program + Campus + SchoolYear
        ├── Create Enrollment record
        ├── Assign to courses based on program requirements
        ├── Notify guardians
        └── Generate timetable
        ↓
Step 4: Student Attends Classes
        ├── Teacher records attendance
        ├── Teacher enters grades for assessments
        └── System tracks progress
        ↓
Step 5: At End of Term/Semester
        ├── Calculate course grades
        ├── Check passing/failing
        ├── Trigger notifications (low grades, risk of failure)
        ├── Generate progress report
        └── Determine next steps (pass, retry, graduate)
        ↓
Step 6: Graduation Check (if applicable)
        ├── Has student completed all required courses?
        ├── Are all minimum grades met?
        ├── Are credits sufficient?
        ├── If yes → mark as graduated, generate diploma
        ├── If no → enroll in next year or required repeats
        └── Send transcript to registrar
```

### 7.2 Student Record Structure

```
Student Enrollment Record:
├── Enrollment ID: ENR-2025-001234
├── Student: Alice Johnson (ID: STU-00567)
├── Program: Secondary Science (Level: Sec 4)
├── Campus: Montreal
├── School Year: 2025-2026
├── Academic Status: Active
│
├── Enrolled Courses:
│   ├── MATH101 (Calculus) – 3 credits, weight 1.5
│   ├── PHY101 (Physics) – 3 credits, weight 1.0
│   ├── CHM101 (Chemistry) – 3 credits, weight 1.0
│   └── ENG101 (English) – 3 credits, weight 0.5
│
├── Grades (in progress):
│   ├── MATH101:
│   │   ├── Midterm Exam: 78/100 (weight 0.4) → 78
│   │   ├── Final Exam: TBD (weight 0.4)
│   │   ├── Assignment 1: 85/100 (weight 0.1) → 8.5
│   │   ├── Participation: 90/100 (weight 0.1) → 9
│   │   └── Current Grade: 84 (likely passing)
│   │
│   ├── PHY101:
│   │   ├── Midterm Exam: 65/100 (weight 0.5) → 65
│   │   ├── Lab: 72/100 (weight 0.5) → 72
│   │   └── Current Grade: 68.5 (passing, but close to alert threshold)
│   │
│   └── CHM101:
│       ├── Midterm Exam: 52/100 (weight 0.5) → 52
│       └── Alert: **FAILING** (below 60% threshold)
│
├── Overall Progress:
│   ├── Program GPA: 73.8 (out of 100)
│   ├── Credits Earned (in progress): 9 out of 12
│   ├── Risk Status: HIGH (1 failing course)
│   └── Recommendation: Immediate intervention
│
└── Last Update: 2025-12-29 12:00 PM
```

### 7.3 Transcript and Academic History

```
Official Transcript:
├── Student Name: Alice Johnson
├── Student ID: STU-00567
├── Program: Secondary Science (Sec 4)
├── School Year: 2025-2026
├── Campus: Montreal
├── Grading Scale: Canada 0-100
│
├── Course Results:
│   ├── MATH101 (Calculus) – 3 cr – 84 – PASS
│   ├── PHY101 (Physics) – 3 cr – 69 – PASS
│   ├── CHM101 (Chemistry) – 3 cr – 52 – FAIL
│   └── ENG101 (English) – 3 cr – 78 – PASS
│
├── Credits Summary:
│   ├── Completed: 9 credits
│   ├── Required: 12 credits
│   ├── In Progress: 3 credits (CHM101 to repeat)
│   └── Still Needed: 0 (after successful repeat)
│
├── Program Average: 70.8%
├── Status: ON TRACK (with required repeat of CHM101)
├── Notes: "Student must retake CHM101 in Winter 2026 semester."
│
└── Generated: 2025-12-29 – Registrar: Marie Dubois
```

### 7.4 Graduation Eligibility Check

```
Graduation Check Algorithm (per program):

FOR each student IN (program, school_year)
  required_credits = program.credits_required_to_graduate
  earned_credits = SUM(course_grade.credits_earned WHERE status = PASSED)
  program_average = AVG(course_grade.final_grade)
  
  IF earned_credits >= required_credits
    AND program_average >= program.passing_average_threshold
    AND all mandatory courses are PASSED
  THEN
    status = GRADUATED
    trigger_notification("Graduation eligible", student, guardians)
    generate_diploma()
  ELSE
    status = NOT ELIGIBLE
    reason = [missing_credits, low_average, failed_mandatory]
    trigger_notification("Graduation requirements not met", student, registrar)
  END IF
END FOR
```

---

## Page 8: Assessment and Grading

### 8.1 Assessment Types and Workflows

**Semester-Based Schools (Canada, Quebec Secondary)**

```
School Year: 2025-2026
├── Semester 1: Sep 5 – Dec 20
│   ├── Week 1-10: Classes
│   ├── Week 11: Exam period (Contrôle 1)
│   │   ├── HQ defines: Dec 9–13 (all campuses)
│   │   ├── Campus A: Dec 9–13 (as scheduled)
│   │   ├── Campus B: Dec 10–14 (±1 day allowed)
│   │   └── All teachers create assessments in this window
│   ├── Week 12: Grade entry deadline
│   └── Week 13: Grades finalized, progress reports sent
│
├── Semester 2: Jan 8 – Apr 30
│   ├── Week 1-15: Classes
│   ├── Week 16: Exam period (Contrôle 2)
│   ├── Week 17: Grade entry
│   └── Week 18: Transcripts and graduation check
│
└── Summer (May–Aug): Retakes/makeup exams
```

**Control-Based Schools (Haiti Secondary)**

```
School Year: 2025-2026
├── HQ Defines (per year): "4 contrôles + 1 final exam"
│   ├── Contrôle 1: October (Weeks 4-6)
│   ├── Contrôle 2: December (Weeks 12-14)
│   ├── Contrôle 3: February (Weeks 20-22)
│   ├── Contrôle 4: April (Weeks 28-30)
│   └── Final Exam: June (Weeks 36-38)
│
├── Teachers create assessments during these windows
├── Dates can be shifted ±5 days per campus if needed
├── If a contrôle is postponed, HQ updates all affected classes
│
└── Each contrôle can target:
    ├── All grades (Sec 1–4)
    ├── Only Science filière
    ├── Only Campus A
    └── Custom selection of classes
```

**University / Teacher-Driven (Canada, Quebec University)**

```
Program Calendar: Fall Term (Sep–Dec), Winter Term (Jan–Apr)

Per Course Section (e.g., MATH101-001):
├── Teacher chooses assessment mix:
│   ├── 3 quizzes (5% each = 15%)
│   ├── Midterm exam (30%)
│   ├── Group project (25%)
│   ├── Final exam (30%)
│   └── Participation (5%)
│
├── Teacher sets dates (within term constraints):
│   ├── Quiz 1: Week 3
│   ├── Midterm: Week 6–7
│   ├── Project: Week 10
│   └── Final exam: Exam period (week 14+)
│
├── Teacher enters grades after each assessment
├── System calculates running GPA
└── Student can see progress in real-time
```

### 8.2 Grade Calculation Engine

```python
def calculate_course_grade(student_id, course_section_id):
    assessments = Assessment.filter(course_section_id=course_section_id)
    grades = Grade.filter(student_id=student_id, assessment_id__in=assessments)
    
    weighted_sum = 0
    total_weight = 0
    
    for assessment in assessments:
        grade = Grade.get(student_id=student_id, assessment_id=assessment.id)
        
        if grade is None or grade.status != FINAL:
            continue  # Skip incomplete assessments
        
        # Convert grade to scale (if needed)
        normalized_grade = normalize_to_scale(
            grade.raw_score,
            assessment.grading_scale,
            course_section.grading_scale
        )
        
        weighted_sum += normalized_grade * assessment.weight_in_course
        total_weight += assessment.weight_in_course
    
    if total_weight == 0:
        return None  # No grades yet
    
    final_grade = weighted_sum / total_weight
    
    # Check passing
    passing_threshold = CourseInProgram.get(
        course_id=course_section.course_id,
        program_id=student.enrollment.program_id
    ).passing_mark or student.enrollment.program.passing_average_threshold
    
    is_passing = final_grade >= passing_threshold
    
    return CourseGrade(
        student_id=student_id,
        course_section_id=course_section_id,
        final_grade=final_grade,
        pass_fail=is_passing,
        credits_earned=course_section.credits if is_passing else 0,
        recorded_date=now()
    )
```

---

## Page 9: Analytics and Early-Warning System

### 9.1 Dashboards and Views

**For Teachers:**
```
Course Dashboard (MATH101-001)
├── Class Roster: 30 students
├── Grade Distribution:
│   ├── A (90+): 5 students (17%)
│   ├── B (80–89): 10 students (33%)
│   ├── C (70–79): 9 students (30%)
│   ├── D (60–69): 4 students (13%)
│   └── F (<60): 2 students (7%)
├── Class Average: 77.4 / 100
├── Alerts:
│   ├── 🔴 2 students failing (need intervention)
│   ├── 🟡 4 students at risk (65–69%)
│   └── ✅ Others on track
└── Action: [View failing students] [Send alert] [Adjust difficulty?]
```

**For Registrar:**
```
Program Performance Dashboard
├── Program: Secondary Science (Sec 4)
├── Total Enrollment: 120 students
├── Performance Metrics:
│   ├── Pass Rate: 92% (110 students passed)
│   ├── Failure Rate: 8% (10 students failing)
│   ├── Dropout Rate: 2% (2 students withdrew)
│   └── Average GPA: 76.2 / 100
├── By Campus:
│   ├── Montreal: 92% pass rate, 77 avg
│   ├── Quebec City: 93% pass rate, 75 avg
│   └── Gatineau: 89% pass rate, 73 avg
├── Risk Students:
│   ├── 🔴 10 students (failing 1+ courses)
│   ├── 🟡 15 students (low attendance)
│   └── 🟠 8 students (approaching withdrawal)
└── Actions: [View details] [Generate report] [Send alerts]
```

**For Principal / Campus Director:**
```
Campus Overview Dashboard
├── Total Students: 500
├── Overall Health Score: 88/100 (Good)
├── Key Metrics:
│   ├── Academic: 88% pass rate
│   ├── Attendance: 94% average attendance
│   ├── Retention: 96% (4 withdrawals)
│   └── Graduation: 91% on-track (9% need repeat)
├── Trends (this month):
│   ├── 📈 Pass rate up 2% from last month
│   ├── 📉 Attendance down 1%
│   ├── 💹 Graduation rate stable
│   └── ⚠️ Repeat rate up 3% (monitor)
├── Comparisons:
│   ├── vs. other campuses: Above average
│   ├── vs. provincial standard: On par
│   └── vs. last year: Improving
└── Top Issues: [High dropout in Arts program] [Low attendance week 8–10]
```

**For Parent/Guardian:**
```
Student Progress Tracker (Alice Johnson)
├── Student ID: STU-00567
├── Program: Secondary Science – Sec 4
├── This Semester GPA: 73.8 / 100
├── Course Breakdown:
│   ├── ✅ MATH101: 84 (Excellent)
│   ├── ✅ PHY101: 69 (Satisfactory, needs work)
│   ├── 🔴 CHM101: 52 (FAILING) ← Needs immediate attention
│   └── ✅ ENG101: 78 (Good)
├── Alerts:
│   ├── 🔴 URGENT: Alice is failing Chemistry
│   ├── Action: Schedule meeting with teacher (click here)
│   ├── Tutor recommended: Yes (recommend local Chemistry tutor)
│   └── Next Assessment: Chemistry retake in January
├── Attendance: 95% (excellent)
└── Trend: Improving overall except Chemistry
```

### 9.2 Early-Warning System

The system monitors and alerts automatically:

```
Alert Triggers:

1. GRADE ALERTS
   ├── If course_grade < passing_threshold
   │   └── Send notification: "Student failing [Course]"
   │       To: Student, Parents, Teacher, Registrar
   │       Channel: SMS, Email, App Push
   │
   ├── If course_grade TRENDING DOWN (3 consecutive assessments lower)
   │   └── Send notification: "Grade trend alert"
   │       To: Student, Parents, Teacher
   │
   └── If course_grade < honours_threshold (if applicable)
       └── Send notification: "Below honors"
           To: Student, Parents

2. ATTENDANCE ALERTS
   ├── If absences > threshold (e.g., 5+ absences in term)
   │   └── Send notification: "Attendance warning"
   │       To: Student, Parents, Registrar
   │
   └── If repeated absences on same day (e.g., Fridays)
       └── Send notification: "Pattern detected"
           To: Registrar, Principal

3. GRADUATION ELIGIBILITY
   ├── If student approaching end of program
   │   ├── If on track for graduation: "Congratulations, on track"
   │   └── If not on track: "Graduation requirements at risk"
   │       To: Student, Parents, Registrar
   │
   └── Trigger action: "Graduation check" 60 days before end

4. ASSESSMENT PERIOD ALERTS
   ├── 2 weeks before: "Contrôle [X] in 2 weeks"
   │   To: All enrolled students
   │
   ├── 1 week before: "Contrôle [X] reminder"
   │   To: Students, Parents
   │
   ├── 1 day before: "Contrôle [X] tomorrow, venue [location]"
   │   To: Students, Teachers, Invigilators
   │
   └── After exam: "Results posted for Contrôle [X]"
       To: Students, Parents

5. DEADLINE ALERTS
   ├── Grade entry deadlines
   │   To: Teachers
   │
   ├── Transcript request deadlines
   │   To: Registrars
   │
   └── Payment deadlines (Phase 2)
       To: Parents, Finance
```

---

## Page 10: Mass Notification System

### 10.1 Notification Architecture (No Internal Chat)

Scholara provides **outbound-only** communication:

- **No internal messaging**: Students, teachers, and parents do NOT message each other within Scholara
- **Mass alerts only**: Triggered by events (grades posted, contrôle coming, payment due, emergency)
- **Multi-channel delivery**: SMS, email, push notification, (optional voice for emergencies)
- **Simple, actionable**: Recipients get information and are expected to act outside the system (call school, check email, read website)

### 10.2 Notification Policies

Policies define **who gets notified about what events**:

```
Policy: "Low Grade Alert"
├── Trigger Event: Course grade falls below passing threshold
├── Conditions:
│   ├── Applies to: [All programs] or [specific programs]
│   ├── Grade threshold: 60%
│   ├── Delay: Send immediately or after grade finalized
│   └── Frequency: Once per course per semester (not spam)
│
├── Recipients:
│   ├── [✓] Student
│   ├── [✓] Parent/Guardian
│   ├── [✓] Teacher
│   ├── [✓] Registrar
│   └── [ ] Principal (optional, if campus-wide pattern)
│
├── Channels (per recipient type):
│   ├── Student: Email, App Push (not SMS, student usually has access)
│   ├── Parent: SMS, Email, App Push (SMS for immediate attention)
│   ├── Teacher: Email, App Push (for their records)
│   └── Registrar: Email (for logging)
│
└── Customization by campus: Allow campus to add/remove recipients

Policy: "Attendance Alert"
├── Trigger: Absences exceed 5 in a semester
├── Recipients: Student, Parent, Registrar, Principal
├── Channels: SMS (urgent), Email
├── Customization: Per campus threshold (some may use 4, others 6)

Policy: "Contrôle Reminder"
├── Trigger: Assessment period starting (2 weeks before, 1 week, 1 day)
├── Recipients: All enrolled students + parents
├── Channels: Email, App Push
├── Customization: HQ sets policy, campus adjusts timing if needed

Policy: "Graduation Congratulations"
├── Trigger: Student meets graduation requirements
├── Recipients: Student, Parent, Registrar
├── Channels: Email, App Push
└── Customization: Optional custom message per school
```

### 10.3 Targeting Rules

Policies use **role-based and data-driven targeting**:

```
Target Groups:

1. By Role + Program:
   - "All parents of Secondary Science students"
   - "All teachers in Science filière"
   - "All registrars at Campus A"

2. By Academic Status:
   - "Students with GPA < 65"
   - "Students with 5+ absences"
   - "Students at risk of graduation failure"

3. By Campus/School:
   - "All students at Campus B"
   - "All parents at [specific campus]"

4. By Custom Rule:
   - "Students enrolled in both Math AND Physics"
   - "New students in their first semester"
   - "Students repeating a course for 2nd time"

Example Query:
SELECT DISTINCT u.email, u.phone FROM users u
JOIN enrollments e ON u.student_id = e.student_id
JOIN programs p ON e.program_id = p.id
WHERE p.name = 'Science' 
  AND e.school_year_id = 2025-2026
  AND (SELECT AVG(cg.final_grade) 
       FROM course_grades cg 
       WHERE cg.student_id = u.student_id) < 65
```

### 10.4 Multi-Channel Delivery

```
Notification Delivery Flow:

Event Triggered
  ├─ Grade Posted for Student X
  ├─ Check: Is grade < passing threshold? YES
  ├─ Load Policy: "Low Grade Alert"
  ├─ Determine Recipients:
  │   ├─ Student X (email, push)
  │   ├─ Parents of Student X (SMS, email, push)
  │   ├─ Teacher (email)
  │   └─ Registrar (email)
  │
  ├─ Delivery Queue (Celery tasks):
  │   ├─ [TASK 1] Send email to student@example.com
  │   ├─ [TASK 2] Send SMS to +1-514-123-4567 (parent)
  │   ├─ [TASK 3] Send push to student's app
  │   ├─ [TASK 4] Send email to teacher@school.ca
  │   └─ [TASK 5] Send email to registrar@school.ca
  │
  ├─ Delivery Logs (tracked):
  │   ├─ Email: sent, delivered, bounced
  │   ├─ SMS: sent, delivered, failed (no credit, invalid number)
  │   ├─ Push: sent, delivered, dismissed
  │   └── Voice: sent, left voicemail, answered
  │
  └─ Dashboard shows delivery status (for audit/compliance)

Retry Logic:
├─ Failed emails: retry after 5 min, 30 min, 1 hour (max 3 times)
├─ Bounced emails: mark as invalid, don't retry
├─ Failed SMS: retry after 1 min, 5 min (max 2 times)
├─ No retry for push/voice (attempt once, log)
└─ Notify admin if high failure rate (>10%)
```

### 10.5 Notification Preferences

Users can customize what they receive (where policy allows):

```
Parent Notification Settings:

Channel Preferences:
├─ SMS: [Enabled] (for urgent alerts only)
├─ Email: [Enabled] (for all notifications)
├─ App Push: [Enabled]
└─ Voice Call: [Disabled]

Alert Preferences:
├─ Low grades: [Enabled, SMS + Email]
├─ Attendance: [Enabled, Email only]
├─ Contrôle reminders: [Enabled, Email only]
├─ Graduation status: [Enabled, Email + SMS]
├─ Emergency alerts: [Always enabled, override user preference]
└─ Marketing/newsletters: [Disabled]

Contact Info:
├─ Mobile: +1-514-555-1234
├─ Email: parent@gmail.com
├─ Alternate: +1-514-555-5678 (secondary contact)
└─ Language: French

Quiet Hours (optional):
├─ Don't send SMS/calls: 8 PM – 8 AM
├─ Email is OK anytime
└─ Emergency alerts always go through
```

---

## Page 11: Notifications and Events – Detailed Examples

### 11.1 Event-to-Notification Mapping

**Event 1: Grade Posted**

```
When: Teacher submits final grade for assessment
Trigger Condition: Assessment.status = FINAL
Action:
  1. Calculate course grade (if all assessments submitted)
  2. Check if pass/fail status changed
  3. If failing: trigger alert
  4. If passing: no alert (neutral event)

Notifications Sent:
├─ If FAILING:
│  ├─ "⚠️ Low Grade Alert: Alice is failing Chemistry"
│  │  To: Student (email + app push)
│  │  To: Parent (SMS + email)
│  │  To: Teacher (email)
│  │  To: Registrar (log entry)
│  │
│  └─ Message template:
│     "Dear Parent, Alice has received a grade of 52% in Chemistry.
│      This is below the passing threshold of 60%. Please contact
│      the teacher to discuss support options. [Action Button]"
│
├─ If TRENDING DOWN:
│  ├─ "📉 Grade Trend: Chemistry score declining"
│  │  To: Student, Parent, Teacher
│  │
│  └─ Suggestion: "Consider tutoring or office hours"
│
└─ If OTHERWISE PASSING:
   └─ No alert (saves notification fatigue)
```

**Event 2: Contrôle Scheduled**

```
When: HQ or principal creates new assessment period (Contrôle)
Trigger: AssessmentPeriod.status = PLANNED, start_date = T + 14 days

2 Weeks Before:
├─ Notification: "Contrôle 2 in 2 weeks (Dec 9–13)"
├─ Recipients: All enrolled students + parents
├─ Channels: Email, App Push
├─ Message: "Important: Science examination period starting Dec 9.
│           Review your study materials. See details → [Link]"
├─ Content: Exam dates, venue, bring items, FAQ

1 Week Before:
├─ Notification: "Contrôle 2 reminder – 1 week away"
├─ Recipients: Same
├─ Channels: SMS (more urgent), Email
├─ Message: "Reminder: Contrôle 2 starts December 9. Good luck!"

1 Day Before:
├─ Notification: "Contrôle 2 starts tomorrow"
├─ Recipients: Students, Teachers (invigilators), Registrar
├─ Channels: Email, App Push
├─ Message for students: "Exam tomorrow, Room 301, 9 AM. Bring ID."
├─ Message for teachers: "Confirm invigilator assignment. Materials ready?"
└─ Message for registrar: "Final attendance confirmed. Seat plan attached."

After Exam:
├─ Notification: "Contrôle 2 results posted"
├─ Recipients: Students + Parents
├─ Channels: App Push (immediate), Email
├─ Message: "Your results are now available. View your score → [Link]"
└─ Detail: Average score, how you compare, next steps (if failing)
```

**Event 3: Enrollment Status Change**

```
When: Student is added to program
Trigger: Enrollment.status = ENROLLED

Notifications:
├─ To Student:
│  └─ "Welcome to Secondary Science! You are enrolled in:
│      - Mathematics (3 credits)
│      - Physics (3 credits)
│      - Chemistry (3 credits)
│      - English (3 credits)
│      Your classes start Sep 5. View schedule → [Link]"
│
├─ To Parent:
│  └─ "Your child [Student Name] has been enrolled in Secondary Science.
│      Fall semester starts Sep 5. Payment is due by Sep 15.
│      [View Invoice] [Pay Now]"
│
└─ To Registrar (for logging):
   └─ "[LOG] New enrollment: STU-00567 → Science 2025-2026"
```

### 11.2 Bulk Notification Examples

**Scenario 1: Emergency Alert (Fire Alarm, School Closure)**

```
Trigger: Principal marks school closure (weather, emergency)
Type: EMERGENCY (overrides all preferences)

Recipients:
├─ All students at campus
├─ All parents of students at campus
├─ All staff at campus
└─ (even if they opted out of notifications)

Message:
"🔴 EMERGENCY: [School Name] Campus [X] is CLOSED today due to [reason].
All classes cancelled. All staff do not report. Students stay home.
More info: [Link] | Questions: [Phone] | Follow us: [Social]"

Channels:
├─ SMS (primary – gets through even if email down)
├─ Email (for record)
├─ App Push
├─ Voice call (optional, for staff confirmation)
└─ Social media (posted simultaneously)

Delivery:
├─ Send to parents first (most critical)
├─ Send to students immediately after
├─ Log all sends for compliance
└─ Expect 80–90% delivery within 2 minutes
```

**Scenario 2: End-of-Term Grade Report**

```
Trigger: All grades finalized for semester
Batch: Send to all students in school

Recipients:
├─ Each student (personalized)
└─ Each parent (all children they follow)

Message to Student (personalized):
"Your Fall 2025 grades are now available:
- Mathematics: 84 ✅
- Physics: 69 ✅
- Chemistry: 52 ❌ FAILING
- English: 78 ✅

Program Average: 73.8 / 100
Action: [View Details] [Get Help] [Schedule Meeting]"

Message to Parent:
"[Student Name]'s Fall 2025 grades are ready.
Summary: 3 passing, 1 failing
Program average: 73.8 / 100
Chemistry needs attention. [Contact Teacher]"

Timing:
├─ Send after all grades finalized (Friday 3 PM)
├─ Stagger delivery (1,000 emails/min to avoid server spike)
├─ Expect delivery within 30 minutes
└─ Confirm delivery rate (>95% success)
```

**Scenario 3: Campus-Specific Announcement**

```
Trigger: Campus director posts announcement

Audience:
├─ All students enrolled at this campus (all programs)
├─ All staff at this campus
├─ Parents of students at this campus
└─ Exclude: Other campuses, archived students

Message:
"📢 Campus Announcement: Montreal Campus
Parking lot will be closed Dec 15–17 for maintenance.
Please use alternate lot. Apologies for inconvenience."

Channels:
├─ Email (full announcement)
├─ App Push (summary)
└─ Option: SMS for urgent updates

Tracking:
├─ Log views (who opened email, tapped push)
├─ Send report: "1,234 delivered, 892 opened, 45% opened within 2 hours"
└─ Resend option: For those who didn't open within 24 hours
```

---

## Page 12: System Administration and Configuration

### 12.1 Admin Portal – Setup Wizard

When a new tenant signs up:

```
Step 1: Organization Info
├─ Organization name: "Quebec School Network"
├─ Country template: Canada (pre-fills calendar, default scales)
├─ Primary language: French
├─ Default language for admins: French / English
└─ [NEXT]

Step 2: Campuses
├─ Campus 1: Montreal (timezone: EST)
├─ Campus 2: Quebec City (timezone: EST)
├─ Campus 3: Gatineau (timezone: EST)
└─ [NEXT]

Step 3: Academic Structure
├─ Select country preset: Canada (Quebec)
├─ Calendar type: Semester-based
├─ Grading scale: 0–100 (percentage)
├─ Passing threshold: 60%
├─ Honours threshold: 85%
├─ [NEXT]

Step 4: Programs
├─ Create Program: Secondary Science
│  ├─ Level: Secondary
│  ├─ Available at: Montreal, Quebec City
│  ├─ Default grading scale: Canada 0–100
│  ├─ Credits required: 12
│  ├─ Courses: MATH101, PHY101, CHM101, ENG101
│  └─ [Add Course]
├─ Create Program: Primary
│  └─ Level: Primary
│  └─ Available at: All campuses
└─ [NEXT]

Step 5: School Year
├─ Name: 2025-2026
├─ Start: Sep 5, 2025
├─ End: Jun 30, 2026
├─ Calendar type: Semester-based
├─ Semester 1: Sep 5 – Dec 20 (exam Dec 9–13)
├─ Semester 2: Jan 8 – Apr 30 (exam May 5–10)
└─ [NEXT]

Step 6: Users (Admin Accounts)
├─ Create HQ Configuration Manager:
│  ├─ Name: Marie Dubois
│  ├─ Email: marie@schoolnetwork.ca
│  ├─ Role: HQ Configuration Manager
│  └─ Send invite
├─ Create Campus Registrar (Montreal):
│  ├─ Name: Jean Provost
│  ├─ Email: jean@montreal.schoolnetwork.ca
│  ├─ Role: Registrar (campus scope)
│  └─ Send invite
└─ [NEXT]

Step 7: Notification Policies (Pre-set defaults)
├─ Low Grade Alert: [✓] Enabled
├─ Attendance Alert: [✓] Enabled
├─ Contrôle Reminder: [✓] Enabled
├─ Graduation Alert: [✓] Enabled
└─ [NEXT]

Step 8: Review & Confirm
├─ Summary of setup
├─ [EDIT] [LAUNCH]
└─ → System creates schema, initializes config, sends invites
```

### 12.2 Tenant Configuration Management

HQ Admin can:

```
Dashboard: Configuration Management
├─ Current Configuration Template: v2.0 (2025-2026)
│  ├─ Created: Aug 1, 2025
│  ├─ Active campuses: 3
│  ├─ Active programs: 8
│  └─ [View details]
│
├─ Action: Create New Version
│  └─ (for 2026-2027 school year)
│     ├─ Copy all settings from v2.0 as baseline
│     ├─ Modify as needed
│     └─ Set activation date: Aug 1, 2026
│
├─ Action: Export Configuration
│  └─ Download JSON file
│     ├─ Programs, grading scales, school year, policies
│     ├─ Ready to import to another tenant
│     └─ [Download]
│
├─ Action: Import Configuration
│  └─ Upload JSON from another school
│     ├─ Validates structure
│     ├─ Maps campus codes
│     └─ [Confirm & Import]
│
├─ Audit Log:
│  ├─ Nov 15: Marie created new grading scale "Canada 0-20"
│  ├─ Nov 10: Jean added campus "Laval"
│  ├─ Oct 20: Marie updated passing threshold for Science program
│  └─ [View full history]
│
└─ Notifications Settings (Global):
   ├─ [Edit] Low Grade Alert policy
   ├─ [Edit] Attendance Alert policy
   ├─ [Add] Custom alert for repeat courses
   └─ [Preview] How they look to users
```

### 12.3 Role and Permission Matrix

```
Role / Permission    | HQ Config | Campus Dir | Registrar | Teacher
──────────────────────────────────────────────────────────────────────
Create Program       |    ✓      |            |           |        
Assign Program Campus|    ✓      |            |           |        
Set Grading Scale    |    ✓      |            |           |        
Define Semester Dates|    ✓      |            |           |        
Shift Exam Date      |            |    ✓       |     ✓     |        
Create Assessment    |            |            |     ✓     |    ✓   
Enter Grades         |            |            |     ✓     |    ✓   
Approve Grade Change |    ✓      |    ✓       |     ✓     |        
View All Grades      |    ✓      |    ✓       |     ✓     |    ✓*  
View Transcript      |    ✓      |    ✓       |     ✓     |        
Export Configuration |    ✓      |            |           |        
Manage Users         |    ✓      |    ✓       |           |        
Send Alerts          |    ✓      |    ✓       |     ✓     |        
View Analytics       |    ✓      |    ✓       |     ✓     |    ✓*  
──────────────────────────────────────────────────────────────────────
✓ = Full access
✓* = Limited (own courses/class only)
```

---

## Page 13: Reporting and Regulatory Compliance

### 13.1 Automated Reports

The system generates configurable reports per country/region:

```
Report: Secondary Attendance Summary
├─ Period: Fall 2025 Semester
├─ Campus: Montreal
├─ Output format: PDF, Excel
├─ Content:
│  ├─ Student roster with attendance %
│  ├─ Days absent (count and dates)
│  ├─ Chronic absence flag (>10% absenteeism)
│  ├─ Trend: declining, stable, improving
│  └─ List of students at risk
├─ Recipients: Principal, Registrar
└─ Frequency: Monthly

Report: Grade Distribution Analysis
├─ By: Program, Campus, Grade Range
├─ Metrics:
│  ├─ Pass rate per course
│  ├─ Average score
│  ├─ Grade distribution (A/B/C/D/F counts)
│  ├─ Compare to previous year
│  └─ Identify outlier courses
├─ Export: CSV (for further analysis)
└─ Use: Identify struggling programs, celebrate successes

Report: Graduation Tracking
├─ Cohort: All Sec 5 students (graduating class)
├─ Status count:
│  ├─ On track: 95 students (79%)
│  ├─ At risk: 20 students (17%)
│  ├─ Will graduate: 100 (estimated)
│  └─ Will need retake: 15 students (12%)
├─ Detail: Per student, missing requirements
└─ Action: Identify students needing intervention 6 months early

Report: Regulatory / Ministry Reporting
├─ Jurisdiction: Quebec Ministry of Education
├─ Report type: Annual statistics
├─ Data exported:
│  ├─ Total enrollment
│  ├─ Graduation rates
│  ├─ Pass rates by level
│  └─ Demographic breakdown
├─ Format: XML (Quebec format)
└─ Automated: Exported once per year (deadlines handled)
```

### 13.2 Data Privacy and Audit

```
Compliance Features:

GDPR / FERPA Compliance:
├─ Data residency: Canada (with option for EU)
├─ Encryption: AES-256 at rest, TLS in transit
├─ Access logs: All user actions logged with timestamp
├─ Data export: Parents can request download of student data
├─ Data deletion: Aged records can be purged after N years
└─ Consent management: Track parental consent for notifications

Audit Trail (immutable logs):
├─ User login: Who, when, from where (IP)
├─ Data changes: Who changed what field, from/to values, when
├─ Grade changes: All corrections tracked with reason
├─ Configuration changes: Who modified programs, policies, scales
├─ Report access: Who downloaded what report, when
└─ 7-year retention: Standard education record keeping

Example Audit Entry:
"2025-12-28 14:35:22 | User: jean@montreal.ca | Action: Grade Change
 | Student: STU-00567 | Course: CHM101 | Old: 52 | New: 58 
 | Reason: 'Grading error corrected by teacher review'
 | Approved by: marie@schoolnetwork.ca"
```

---

## Page 14: API and Integrations

### 14.1 REST API Design

Scholara provides a full REST API for extensibility:

```
Authentication: JWT Bearer Token
Rate Limit: 1000 requests/minute per tenant
Base URL: https://api.scholara.com/v1

Endpoints (Core SIS):

GET /tenants/{tenant_id}/students
├─ List all students (paginated)
├─ Query: ?program_id=&campus_id=&status=active
├─ Response: [{id, name, email, program, enrollment_status}]

GET /tenants/{tenant_id}/students/{student_id}
├─ Get student details
├─ Includes: enrollments, grades, transcript

POST /tenants/{tenant_id}/students/{student_id}/grades
├─ Bulk import grades from external system
├─ Body: [{assessment_id, student_id, raw_score}]
├─ Returns: List of created grades with validation

GET /tenants/{tenant_id}/programs
├─ List programs
├─ Response: [{id, name, level, available_campuses}]

GET /tenants/{tenant_id}/analytics/dashboard
├─ Get dashboard data (pass rates, at-risk students, etc.)
├─ Returns: JSON for dashboard UI

POST /tenants/{tenant_id}/notifications/send
├─ Send custom notification (rare, for integrations)
├─ Body: {target_group, message, channels, policy_id}
├─ Returns: {notification_id, status, delivery_log}

GET /tenants/{tenant_id}/reports/graduation
├─ Export graduation tracking report
├─ Response: CSV or JSON
```

### 14.2 Webhook Events

For real-time integrations:

```
Event: student.grade_posted
├─ When: New grade added for a student
├─ Payload: {student_id, course_id, grade_value, timestamp}
├─ Use: HR system alerts teacher for grading discrepancy

Event: student.enrollment_created
├─ When: New student enrolled
├─ Payload: {student_id, program_id, campus_id, start_date}
├─ Use: LMS auto-creates course shell, HR notifies campus

Event: assessment_period.started
├─ When: Contrôle or exam window begins
├─ Payload: {period_id, name, start_date, target_groups}
├─ Use: Calendar system adds event, notification hub prepares alerts

Event: student.graduation_eligible
├─ When: Student completes requirements
├─ Payload: {student_id, program_id, completion_date}
├─ Use: Registrar triggers diploma printing, parent email
```

### 14.3 Third-Party Integrations (Phase 2)

Planned partnerships:

```
Learning Management System (LMS):
├─ LTI 1.3 integration (Canvas, Moodle, D2L)
├─ Sync enrollments: Scholara → LMS (auto-create sections)
├─ Sync grades: LMS → Scholara (pull final course grades)
├─ Use case: Large schools keep LMS for content, Scholara for SIS

Finance/Billing:
├─ Stripe for online payment processing
├─ Auto-sync invoices from Scholara → Stripe
├─ Track payment status in student record
├─ Notification: Payment due/overdue alerts

ERP Systems:
├─ Odoo, SAP Business One (future)
├─ Sync student/staff data for HR
├─ Sync fees/tuition to accounting module
├─ Use case: Multi-department organizations (school + corporate)

Library Management:
├─ Koha, Alma (future)
├─ Sync student enrollments
├─ Track library access by student
└─ Fine notifications integrated into Scholara

Communication:
├─ Slack, Teams, email (future)
├─ Bi-directional: Scholara alerts → Slack
├─ Use case: Teachers get alerts in their preferred app
```

---

## Page 15: Roadmap and Extensibility

### 15.1 MVP Release (Phase 1 – Q1 2026)

**Core Deliverables:**
- Multi-tenant SaaS platform (Django + React)
- Student enrollment and academic records
- Configurable grading and credits (Canada, USA, France, Haiti templates)
- Mass notification system (email, SMS, push)
- Role-based access control
- Analytics dashboards
- Configuration export/import
- REST API (v1)

**Not Included (Deferred):**
- Internal messaging (by design)
- LMS content delivery (light version in Phase 2)
- Finance module (invoicing, payment tracking)
- E-signature integration
- Advanced analytics (ML-driven predictions)
- On-premise deployment
- Blockchain credentials

### 15.2 Phase 2 (Q2–Q3 2026)

**Learning Management:**
- Assignment submission and grading
- Simple quiz engine
- Document storage (syllabi, readings)
- LTI integration with Canvas/Moodle
- Attendance tracking (expanded)

**Finance Module:**
- Tuition billing and invoicing
- Fee management
- Scholarship/bursary tracking
- Payment integrations (Stripe, PayPal)
- Automated payment reminders

**Advanced Analytics:**
- Predictive at-risk student modeling (ML)
- Cohort analysis
- Institutional effectiveness dashboards
- Customizable report builder

### 15.3 Phase 3+ (Q4 2026 and Beyond)

**Ecosystem:**
- App marketplace for custom integrations
- Third-party plugins (Odoo, SAP, HR systems)
- White-label options for partners
- Mobile app (iOS/Android native)

**Global Expansion:**
- Additional country templates (Australia, Singapore, UK)
- Multi-currency support
- Localization (20+ languages)
- Compliance certifications (SOC 2, ISO 27001)

**AI and Automation:**
- AI tutor chatbot (homework help)
- Automated scheduling (smart timetable generation)
- Transcript generation (AI-powered, multi-format)
- Competency mapping (cross-curriculum tracking)

---

## Page 16: Technical Architecture (Deep Dive)

### 16.1 Database Schema Organization

```
PostgreSQL Schema Layout:

Public Schema (shared):
├── auth_user (Django built-in)
├── auth_group (roles/permissions)
├── tenant (tenant master table)
└── tenant_plan (SaaS subscription info)

Per-Tenant Schema (tenant_{id}):
├── Students & Enrollment:
│   ├── student
│   ├── guardian
│   ├── enrollment
│   └── enrollment_history
│
├── Academic:
│   ├── program
│   ├── course
│   ├── course_in_program
│   ├── school_year
│   ├── semester
│   └── assessment_period
│
├── Grading:
│   ├── grading_scale
│   ├── grading_band
│   ├── assessment
│   ├── grade
│   ├── course_grade
│   └── transcript
│
├── Organization:
│   ├── campus
│   ├── configuration_template
│   ├── notification_policy
│   └── notification_log
│
└── Admin:
    ├── user_role
    ├── audit_log
    └── system_settings
```

### 16.2 Django App Structure

```
scholara/
├── core/                        # Shared multi-tenant logic
│   ├── models.py                # Tenant, Campus, ConfigTemplate
│   ├── middleware.py            # Tenant context routing
│   ├── permissions.py           # Custom permission classes
│   └── serializers.py           # API serializers
│
├── academics/                   # SIS core
│   ├── models.py                # Student, Program, Enrollment, Grade
│   ├── views.py                 # API endpoints
│   ├── serializers.py           # DRF serializers
│   ├── services/                # Business logic
│   │   ├── enrollment.py        # Enroll student, check graduation
│   │   ├── grading.py           # Calculate grades, check passing
│   │   └── transcript.py        # Generate transcripts
│   └── migrations/              # Database migrations
│
├── notifications/               # Mass notification engine
│   ├── models.py                # Notification, NotificationPolicy, Log
│   ├── views.py                 # API to send notifications
│   ├── tasks.py                 # Celery tasks (email, SMS, push)
│   ├── channels/                # Multi-channel adapters
│   │   ├── email.py             # SendGrid/AWS SES
│   │   ├── sms.py               # Twilio
│   │   ├── push.py              # Firebase Cloud Messaging
│   │   └── voice.py             # Twilio voice
│   ├── events.py                # Event triggers
│   └── policies.py              # Policy engine
│
├── analytics/                   # Dashboards and reports
│   ├── views.py                 # Dashboard API endpoints
│   ├── services/                # Analytics engines
│   │   ├── early_warning.py     # At-risk detection
│   │   ├── reports.py           # Generate reports (PDF, CSV)
│   │   └── aggregation.py       # Stats aggregation
│   └── templates/               # Dashboard data structures
│
├── api/                         # REST API layer
│   ├── urls.py                  # Route definitions
│   ├── viewsets.py              # DRF ViewSets
│   └── filters.py               # Query filtering
│
├── tests/                       # Test suite
│   ├── test_enrollment.py       # Unit tests
│   ├── test_grading.py
│   ├── test_notifications.py
│   ├── test_api.py
│   └── conftest.py              # Pytest fixtures
│
└── settings/                    # Django configuration
    ├── base.py                  # Base settings
    ├── local.py                 # Local development
    └── production.py            # Production settings
```

### 16.3 Celery Task Queue

```
Celery Task Hierarchy:

notifications/
├── send_email_task(recipient_email, template_id, context)
│   └── Retry: 3x on failure
│   └── Queue: email
│
├── send_sms_task(phone_number, message)
│   └── Retry: 2x on failure
│   └── Queue: sms
│
├── send_push_notification_task(user_id, title, body)
│   └── No retry (fire-and-forget)
│   └── Queue: push
│
└── process_event_task(event_type, event_data, tenant_id)
    └── When a grade is posted:
        1. Determine recipients (student, parents, teacher, registrar)
        2. Load notification policy
        3. Create notification tasks for each channel
        4. Queue them (prioritized by urgency)

academics/
├── calculate_course_grade_task(student_id, course_section_id)
│   └── Runs after each grade entered
│   └── Updates CourseGrade record
│   └── Triggers grade-change events
│
└── graduation_check_task(student_id, program_id)
    └── Runs end-of-semester
    └── Checks credits, average, requirements
    └── Triggers graduation notification if eligible

admin/
└── nightly_analytics_aggregation_task(tenant_id)
    └── Runs at 2 AM (after school hours)
    └── Pre-calculates dashboard stats
    └── Updates early-warning flags
    └── Prepares daily reports
```

---

## Page 17: Security and Performance

### 17.1 Security Considerations

```
Authentication & Authorization:
├── JWT tokens (issued on login)
│   ├── Expires in 24 hours
│   ├── Refresh tokens (valid 30 days) for rotation
│   └── Revoke on logout
├── Multi-tenancy isolation:
│   ├── Middleware enforces tenant context per request
│   ├── Database-level schema isolation (no shared tables)
│   ├── Row-level security on multi-tenant tables (impossible in MVP)
│   └── No cross-tenant data leakage possible
├── Role-based access control:
│   ├── Django permissions (view_student, change_grade, etc.)
│   ├── Custom permission checks per endpoint
│   └── Audit log of all permission-denied attempts

Data Protection:
├── At rest: AES-256 encryption for sensitive fields
│   ├── Student PII (name, email, phone, date of birth)
│   └── Guardian contact info
├── In transit: TLS 1.3 (all HTTP → HTTPS)
├── Backups: Encrypted, replicated, tested quarterly
└── Deletion: Soft delete with GDPR right-to-be-forgotten

Third-Party API Security:
├── SMS (Twilio): API key in secrets manager
├── Email (SendGrid): API key rotated quarterly
├── Push notifications (Firebase): Service account JSON encrypted
└── Never store plain-text secrets in code/config

Compliance:
├── GDPR: Data residency (Canada or EU), consent tracking
├── FERPA: Access logs, parental consent for notifications
├── SOC 2 (Phase 2): Third-party audit, compliance dashboard
└── Penetration testing: Quarterly (external), continuous (internal)
```

### 17.2 Performance and Scalability

```
Database Optimization:
├── Indexes on:
│   ├── Foreign keys (tenant_id, student_id, program_id, etc.)
│   ├── Frequently filtered fields (status, school_year_id)
│   ├── Time-based queries (created_at, updated_at)
│   └── Full-text search (student name, course code)
├── Query optimization:
│   ├── SELECT_RELATED for FK joins
│   ├── PREFETCH_RELATED for reverse FK
│   ├── Aggregate queries for dashboard stats
│   └── Connection pooling (PgBouncer)

Caching Strategy:
├── Redis for:
│   ├── Session data (24-hour expiry)
│   ├── Dashboard stats (1-hour TTL, refresh on demand)
│   ├── Grading scale definitions (24-hour TTL)
│   ├── User permissions (1-hour TTL)
│   └── Rate limiting (per-user, per-IP)
├── Avoid caching:
│   ├── Student PII (security sensitive)
│   ├── Current grades (must be fresh)
│   └── Notification logs (audit sensitive)

Asynchronous Processing:
├── Celery tasks:
│   ├── Email/SMS delivery (async, 5-30 second delay acceptable)
│   ├── Grade calculations (async, trigger on submission)
│   ├── Report generation (async, download when ready)
│   └── Analytics aggregation (nightly batch)
├── Sync operations (user expects <200ms):
│   ├── Login, user listing, grade view
│   ├── Policy checks, notifications (if simple)
│   └── Dashboard data (cached, served from Redis)

Load Testing Targets (MVP):
├── Concurrent users: 10,000 per tenant
├── Requests per second: 100
├── API response time: <200ms (P95)
├── Dashboard load: <500ms (P95)
└── Email delivery: <30 seconds (SLA)
```

---

## Page 18: Deployment and Operations

### 18.1 Deployment Architecture

```
Infrastructure (AWS):

Frontend:
├─ CloudFront CDN
│  ├─ Serves React SPA
│  ├─ Cache busting on deploy
│  └─ SSL/TLS cert (ACM)
└─ S3 bucket for static assets

Backend (ECS Fargate):
├─ Django application containers
│  ├─ Auto-scaling (2–20 instances based on CPU/memory)
│  ├─ Load balancer (ALB) in front
│  ├─ Health checks (every 30 seconds)
│  └─ Rolling deploy (blue-green strategy)
├─ Environment variables (from Secrets Manager):
│  ├─ DATABASE_URL
│  ├─ REDIS_URL
│  ├─ SECRET_KEY (rotated quarterly)
│  ├─ TWILIO_AUTH_TOKEN, SENDGRID_API_KEY
│  └─ LOG_LEVEL (DEBUG/INFO/ERROR)

Database (RDS PostgreSQL):
├─ Multi-AZ for high availability
├─ Automated backups (daily, 30-day retention)
├─ Read replicas for analytics queries
├─ Parameter group for performance tuning
└─ Security group: only ECS traffic allowed

Cache (ElastiCache Redis):
├─ Multi-AZ (failover in <30 seconds)
├─ 6 GB cluster (for MVP, scales to 100 GB)
├─ Eviction policy: allkeys-lru
└─ Backup: daily snapshots to S3

Message Queue (RabbitMQ or SQS):
├─ Dead-letter queue for failed tasks
├─ Task retry logic (exponential backoff)
└─ Monitoring: CloudWatch metrics

Monitoring & Logging:
├─ CloudWatch Logs (centralized, 7-day retention)
├─ Datadog or New Relic (Phase 2):
│  ├─ APM (application performance)
│  ├─ Infrastructure metrics
│  ├─ Alerts (CPU, memory, error rate)
│  └─ Dashboards (operations team)
├─ Sentry for error tracking
│  ├─ Automatic error alerts
│  ├─ Release tracking
│  └─ Source map support
└─ Custom CloudWatch metrics:
   ├─ API request latency
   ├─ Notification delivery success rate
   ├─ Grade calculations per minute
   └─ Active users per tenant
```

### 18.2 Deployment Process

```
Release Pipeline:

1. Develop & Test (Developers)
   ├─ Branch: feature/xyz
   ├─ Tests: Jest (frontend) + Pytest (backend)
   ├─ Coverage: >80%
   └─ [Push to GitHub]

2. Code Review (Peers)
   ├─ PR review on GitHub
   ├─ Security scan (SAST): Bandit, npm audit
   ├─ Dependency check: Dependabot alerts
   └─ [Approve → Merge to main]

3. Continuous Integration (GitHub Actions)
   ├─ Unit tests (all suites pass)
   ├─ Integration tests (API endpoints)
   ├─ Build Docker image
   └─ Push to ECR (container registry)

4. Staging Deployment (Automated)
   ├─ Deploy to staging environment (identical to prod)
   ├─ Database: copy of production (sanitized)
   ├─ Smoke tests (can log in, create student, post grade)
   ├─ Manual QA (2–4 hours)
   └─ [Approved → ready for production]

5. Production Deployment (On-Demand)
   ├─ Time: Business hours only (Wed–Fri afternoon)
   ├─ Strategy: Blue-green (2 ECS deployments)
   │   ├─ Green (new): deploy, route 0% traffic
   │   ├─ Warm up (5 min): check health
   │   ├─ Cut over: route 100% traffic to green
   │   └─ Keep blue (old) for 1 hour rollback window
   ├─ Communication:
   │   ├─ Announce maintenance 1 week prior
   │   ├─ Send email to admins 24 hours before
   │   └─ Slack notification at deploy start
   ├─ Duration: 15–30 minutes (mostly automated)
   └─ Rollback: <5 minutes if needed

6. Post-Deployment Monitoring
   ├─ Watch error rate (should be <0.1%)
   ├─ Check API latency (should be normal)
   ├─ Verify database performance
   ├─ Monitor Celery task queue (no buildup)
   └─ Send "deployment complete" Slack message
```

### 18.3 Operations Runbook

```
On-Call Playbook:

Incident: High API Error Rate (>5%)
├─ Step 1: Check Sentry dashboard
├─ Step 2: Identify pattern (which endpoints, which tenants)
├─ Step 3: Check CloudWatch metrics (CPU, memory, database)
├─ Step 4: If database: scale up replicas or RDS instance
├─ Step 5: If application: check logs for timeout/crash
├─ Step 6: If code issue: rollback to previous version
├─ Step 7: Notify engineering team for root-cause analysis

Incident: Notification Delivery Failure
├─ Check Celery queue depth (RabbitMQ)
├─ If high: scale up workers (add ECS tasks)
├─ If low: check SMS/email provider status pages
├─ If provider down: queue tasks, resume when up
├─ Manual retry: Re-queue failed tasks from admin panel

Incident: Student Grades Not Visible
├─ Check if grade was actually saved to database (query manually)
├─ If saved: likely caching issue → flush Redis
├─ If not saved: check application logs for validation errors
├─ If data loss: restore from backup (RDS snapshot)

Daily Checks:
├─ Morning: Review Datadog dashboard (CPU, memory, response time)
├─ Backup: Confirm overnight backup completed successfully
├─ Notification queue: Verify <100 pending tasks (normal)
├─ Error rate: Should be <0.1%
└─ If issues found: escalate to engineering

Weekly Checks:
├─ Database size: Monitor growth (should be predictable)
├─ Read replica lag: <100ms is normal
├─ Cost analysis: Review AWS bill
└─ Performance: Run synthetic tests from multiple regions
```

---

## Final Notes

This specification provides a complete roadmap for building **Scholara**, a world-class multi-tenant school management system. The MVP (Phase 1) focuses on core SIS functionality, configurable academic models for multiple countries, and an intelligent notification system—no internal messaging by design.

**Key strengths of this design:**
- Fully configurable without hardcoding country-specific rules
- HQ-controlled templates ensure consistency across campuses while allowing local autonomy
- Event-driven notifications enable real-time, multi-channel communication
- Extensible API and webhook system allow future integrations with LMS, finance, and third-party tools
- Pragmatic scope (MVP) with clear roadmap to full platform

**Technology choices:**
- Django + PostgreSQL: Proven, secure, multi-tenant capable
- React: Modern frontend for administrators and teachers
- Celery + Redis: Robust async task processing for notifications and analytics
- Docker + Kubernetes: Scalable cloud-native deployment

**Timeline:**
- Phase 1 (MVP): Q1 2026 – Core SIS, notifications, multi-country templates
- Phase 2: Q2–Q3 2026 – LMS, finance, advanced analytics
- Phase 3+: Q4 2026 onward – Ecosystem, global expansion, AI features

---

**Document prepared for:** Development and Architectural Planning  
**Last updated:** December 29, 2025  
**Next review:** When MVP development begins  

---
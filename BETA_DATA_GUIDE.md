# Beta Data Generation Guide

## Overview
This guide explains how to use the `generate_beta_data` management command to populate your School Management System with comprehensive test data.

## Quick Start

### Generate default data (50 students):
```bash
venv/Scripts/python.exe manage.py generate_beta_data --settings=School_System.settings.development
```

### Generate custom number of students:
```bash
venv/Scripts/python.exe manage.py generate_beta_data --users 100 --settings=School_System.settings.development
```

### Clear existing data and regenerate:
```bash
venv/Scripts/python.exe manage.py generate_beta_data --clear --users 50 --settings=School_System.settings.development
```

## What Data Gets Generated

The script creates comprehensive, realistic data across all 24 apps:

### 1. **Core Academic Data**
- 4 academic sessions (past 2 years + current + next year)
- 2 semesters (First & Second)
- 5 academic programs (CS, IT, SE, Data Science, Cybersecurity)
- ~40 courses (8 per program, across all levels)

### 2. **Users & Accounts**
- 1 admin user
- 1 direction user
- 10 lecturers
- N students (default 50, customizable)
- Parents for first 20 students
- All with realistic names, emails, phone numbers, addresses

### 3. **Course Management**
- Course allocations (lecturers assigned to courses)
- Student enrollments (4-6 courses per student)
- Registration forms (90% approved, 10% pending)

### 4. **Attendance**
- 30 days of attendance records
- Multiple sessions per day
- 80% present, 15% absent, 5% late distribution
- Individual student reports
- Daily attendance statistics

### 5. **Grades & Results**
- CA scores (15-30/30)
- Exam scores (35-70/70)
- Total scores and letter grades (A+ to F)
- Realistic grade distribution
- Comments based on performance

### 6. **Library**
- 100 books across 6 categories
- Library settings (borrow rules, fines)
- Borrow records for 30 students
- 75% returned books, 25% still borrowed
- Overdue fines where applicable

### 7. **Events**
- 15 events (seminars, workshops, conferences, competitions, social)
- Event registrations (10-30 students per event)
- Mix of past, current, and upcoming events

### 8. **News & Announcements**
- 10 news items
- Categories: important, notification, announcement

### 9. **Disciplinary Records**
- 20 disciplinary actions
- Types: warning, suspension, probation, expulsion
- Severity levels: minor, moderate, serious, critical
- Mix of resolved and active cases

### 10. **Certificates**
- Certificate template (Course Completion)
- Certificates issued to 30% of students
- Unique certificate numbers

### 11. **Forums**
- 5 categories (General, Academic Help, Announcements, Events, Off-Topic)
- 30 discussion threads
- 1-10 posts per thread
- Pinned and locked threads

### 12. **Analytics**
- Student engagement records (30 days, every 3 days)
  - Login counts
  - Time spent
  - Pages viewed
  - Engagement scores
- Course completion tracking
- At-risk student identification (10% of students)
- Learning outcome measurements

### 13. **Grading Rubrics**
- 15 grading rubrics across courses
- 4 criteria per rubric (Content, Organization, Critical Thinking, Presentation)
- Rubric grades for enrolled students
- Peer review records

### 14. **Quizzes**
- 10 quizzes across different courses
- 5 questions per quiz
- 4 multiple choice answers per question
- Mix of single-attempt and multi-attempt quizzes

### 15. **Payments**
- Tuition payment records for all students
- Mix of completed, pending, and failed payments
- Various payment methods (cash, transfer, card)
- Realistic amounts (50k-100k)

### 16. **Course Materials**
- Lecture notes uploads
- Video uploads
- Distributed across 20 courses

## Default Login Credentials

After generation, use these credentials to test different user roles:

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| **Admin** | admin | admin123 | Full system access |
| **Direction** | director | director123 | Director/Principal access |
| **Student** | student1 | student123 | Student account (student1-studentN) |
| **Lecturer** | lecturer1 | lecturer123 | Lecturer account (lecturer1-lecturer10) |
| **Parent** | parent1 | parent123 | Parent account (parent1-parent20) |

## Command Options

```bash
python manage.py generate_beta_data [OPTIONS]

Options:
  --users N       Number of students to generate (default: 50)
  --clear         Clear existing data before generating (DESTRUCTIVE!)
  --settings      Django settings module to use
```

## Important Notes

### ⚠️ Data Clearing Warning
The `--clear` flag will **permanently delete** all existing data except superusers. Use with caution!

### 📊 Performance
- Generating 50 students takes approximately 1-2 minutes
- Generating 100 students takes approximately 3-5 minutes
- All data generation runs in a single transaction for consistency

### 🔍 What's NOT Cleared
When using `--clear`, these items are preserved:
- Superuser accounts
- Django migrations
- Static files
- Media files

### 📝 Realistic Data
All data is generated using the Faker library for realistic:
- Names (first and last)
- Email addresses
- Phone numbers
- Addresses
- Dates and times
- Text content (paragraphs, sentences)

## Verification After Generation

### 1. Check user counts:
```bash
venv/Scripts/python.exe manage.py shell --settings=School_System.settings.development
```
```python
from accounts.models import User, Student
print(f"Total users: {User.objects.count()}")
print(f"Students: {Student.objects.count()}")
print(f"Lecturers: {User.objects.filter(role='lecturer').count()}")
print(f"Parents: {User.objects.filter(role='parent').count()}")
```

### 2. Check course data:
```python
from course.models import Course, Program
from result.models import TakenCourse
print(f"Programs: {Program.objects.count()}")
print(f"Courses: {Course.objects.count()}")
print(f"Enrollments: {TakenCourse.objects.count()}")
```

### 3. Check attendance:
```python
from attendance.models import Attendance, AttendanceReport
print(f"Attendance sessions: {Attendance.objects.count()}")
print(f"Individual reports: {AttendanceReport.objects.count()}")
```

## Troubleshooting

### Error: "No module named 'faker'"
```bash
venv/Scripts/pip.exe install faker factory-boy
```

### Error: Foreign key constraint errors
Make sure you're using the correct settings (development vs production):
```bash
python manage.py generate_beta_data --settings=School_System.settings.development
```

### Error: Permission denied
Run the command from the project root directory where `manage.py` is located.

### Data looks inconsistent
Use the `--clear` flag to start fresh:
```bash
python manage.py generate_beta_data --clear --users 50 --settings=School_System.settings.development
```

## Use Cases

### For Testing
```bash
# Small dataset for quick testing
python manage.py generate_beta_data --users 10
```

### For Demo/Presentation
```bash
# Medium dataset for realistic demo
python manage.py generate_beta_data --users 50
```

### For Load Testing
```bash
# Large dataset for performance testing
python manage.py generate_beta_data --users 200
```

### For Fresh Start
```bash
# Clear everything and start fresh
python manage.py generate_beta_data --clear --users 50
```

## Data Relationships

The script maintains proper relationships:
- Students → enrolled in courses → have grades, attendance
- Lecturers → allocated to courses → grade students
- Parents → linked to students → can view child's data
- Courses → belong to programs → have materials, quizzes
- Attendance → linked to courses → tracks student presence
- Payments → linked to students and sessions
- Events → have registrations from students
- Forum threads → have posts from users
- Certificates → issued to students for courses

## Next Steps

After generating data:
1. Start the development server
2. Log in with any of the default credentials
3. Navigate through different dashboards
4. Test all features with realistic data
5. Verify reports and analytics display correctly

## Support

If you encounter issues:
1. Check that all migrations are applied
2. Verify database permissions
3. Ensure all apps are in INSTALLED_APPS
4. Check the console output for specific errors

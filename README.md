# Aurelius - School Management System

> **"Shaping Tomorrow's Leaders Today"** / *Fingere Duces Crastini Hodie*

A comprehensive school management platform built as a monorepo with a Django REST API backend, a React 19 + Vite web frontend, and an Expo Router React Native mobile app. Targets K-12 and higher-education institutions with deep feature coverage: admissions, enrollment, grading, attendance, library, events, discipline, safeguarding, alumni, payments and more.

## Architecture

```
System-School-Management/
├── backend/          # Django REST API (Django 4.0.8, Python 3.10+)
│   ├── School_System/        # Django project (settings.base/development/production, urls, asgi, wsgi)
│   ├── accounts/             # Users, JWT auth, profiles, roles
│   ├── admissions/           # Admission applications
│   ├── enrollment/           # Student enrollment + class assignment
│   ├── course/               # Courses, sections, syllabi
│   ├── filieres/             # Programs / tracks (FR: filieres)
│   ├── grading/              # Grades, grade books, report cards
│   ├── notes/                # Marks / scores
│   ├── result/               # Final results, transcripts
│   ├── quiz/                 # Online quizzes
│   ├── attendance/           # Attendance tracking
│   ├── dailystat/            # Daily statistics
│   ├── scheduling/           # Timetables, room booking
│   ├── events/               # Calendar events
│   ├── library/              # Library catalogue + lending
│   ├── forums/               # Discussion forums
│   ├── articles/             # News / articles
│   ├── notices/              # Announcements
│   ├── certificates/         # Certificate generation
│   ├── payments/             # Fees, invoicing, payment tracking
│   ├── discipline/           # Disciplinary records
│   ├── safeguarding/         # Safeguarding / child-protection records
│   ├── alumni/               # Alumni network
│   ├── reports/              # Reporting engine
│   ├── analytics/            # Analytics dashboards
│   ├── anomaly_detection/    # ML anomaly detection on student patterns
│   ├── search/               # Cross-entity search
│   ├── audit/                # Audit logging
│   ├── monitoring/           # Ops monitoring
│   ├── core/                 # Shared utilities
│   └── requirements/         # base.txt / development.txt / production.txt
│
├── frontend/         # Web dashboard
│   # Vite + React 19 + TypeScript + Tailwind v4 (via @tailwindcss/vite)
│   # TanStack Query v5, Zustand v5, React Router 7, Axios
│
├── mobile/           # Mobile app (Expo SDK 55, React Native 0.83.2, React 19)
│   # expo-router for file-based routing
│   # expo-secure-store for token storage
│   # TanStack Query v5, Zustand v5, Axios
│
├── media/            # Uploaded files
├── scripts/          # Operational scripts
└── Makefile          # Common dev commands
```

## Tech stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django **4.0.8**, Django REST Framework, django-filter, django-crispy-forms + Bootstrap 5, django-modeltranslation, ReportLab |
| **Database** | PostgreSQL (prod), SQLite (dev) |
| **Frontend** | React **19.2**, Vite, TypeScript, Tailwind CSS v4 (`@tailwindcss/vite`), TanStack Query v5, Zustand v5, React Router 7, Axios |
| **Mobile** | Expo SDK 55 (`expo-router`), React Native 0.83.2, React 19, `expo-secure-store`, TanStack Query v5, Zustand v5 |
| **Auth** | JWT (SimpleJWT) |
| **i18n** | `django-modeltranslation` (server-side) + `django.middleware.locale.LocaleMiddleware` |

## Quick start

### Backend (Django API)

```bash
cd backend
python -m venv ../venv
../venv/bin/activate            # Linux/Mac
# ../venv/Scripts/activate      # Windows

pip install -r requirements/development.txt

python manage.py migrate --settings=School_System.settings.development
python manage.py seed_initial_data --settings=School_System.settings.development
python manage.py create_demo_data --settings=School_System.settings.development
python manage.py runserver 9000 --settings=School_System.settings.development
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev            # Vite dev server (default: http://localhost:5173)
```

The frontend expects the backend on port 9000. Adjust the base URL via an env file or the axios client in `src/`.

### Mobile (Expo Router)

```bash
cd mobile
npm install
npx expo start         # then press a (Android), i (iOS), or w (web)
```

## API

All API endpoints live under `/api/v1/`. Authentication uses JWT tokens (access + refresh) via `djangorestframework-simplejwt`.

- Login: `POST /api/v1/accounts/auth/login/`
- Refresh: `POST /api/token/refresh/`
- User profile: `GET /api/v1/accounts/users/me/`

The backend ships ~29 Django apps providing full CRUD for courses, students, attendance, payments, grading, library, discipline, events and more.

## Demo credentials

After running `create_demo_data`:

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Professor | `prof1` | `professor1@school.edu` | `password123` |
| Student | `student1` | `student1@school.edu` | `password123` |
| Parent | `parent1` | `parent1@email.com` | `password123` |
| Direction | `direction1` | `direction1@school.edu` | `password123` |

## Repository notes

- `django-crm-admin-dashboard-template-2025-12-31-11-19-14-utc.zip` at the root is a third-party dashboard template used as reference material for the frontend. It is not built or used by the running application.
- `.env` is present in the repo; treat it as sample configuration only and use `.env.developpement.example` / `.env.production.example` to build your own local env files.

## License

Proprietary.
